import os
import json
import csv
import shutil
from typing import List, Optional
from threading import Lock
import re

class DataStore:
    """Data persistence layer for bank accounts and customers"""

    JSON_PATH = "data/bank_data.json"
    CSV_PATH = "data/accounts.csv"
    ACTIVITY_PATH = "data/account_activity.csv"
    CUSTOMER_JSON_PATH = "data/customers.json"
    LOANS_JSON_PATH = "data/loans.json"  # <-- Loan path added

    _lock = Lock()

    @staticmethod
    def _ensure_dir(filepath: str):
        """Ensure parent directory exists for a file"""
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    @staticmethod
    def _atomic_replace(tmp_file: str, dest_file: str, label: str):
        """Atomically replace destination file with temporary file"""
        DataStore._ensure_dir(dest_file)

        try:
            # Try atomic move first
            shutil.move(tmp_file, dest_file)
        except Exception as e:
            print(f"[DataStore] Failed to move temporary {label} file: {e}")
            try:
                # Fallback: copy and delete
                shutil.copy2(tmp_file, dest_file)
                os.remove(tmp_file)
            except Exception as ex:
                print(f"[DataStore] Copy fallback also failed for {label}: {ex}")

    @staticmethod
    def _ensure_activity_header():
        """Ensure activity log file exists with header"""
        if not os.path.exists(DataStore.ACTIVITY_PATH):
            DataStore._ensure_dir(DataStore.ACTIVITY_PATH)
            with open(DataStore.ACTIVITY_PATH, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "username", "accountNumber", "action",
                    "amount", "mode", "resultingBalance", "txnId",
                    "chequeId", "metadata"
                ])

    @staticmethod
    def append_activity(
        timestamp: str,
        username: str,
        account_number: str,
        action: str,
        amount: Optional[float] = None,
        mode: Optional[str] = None,
        resulting_balance: Optional[float] = None,
        txn_id: Optional[str] = None,
        cheque_id: Optional[str] = None,
        metadata: Optional[str] = None
    ):
        """
        Append an activity record to the activity log

        Args:
            timestamp: Timestamp of the activity
            username: Username associated with the activity
            account_number: Account number
            action: Action performed
            amount: Transaction amount (optional)
            mode: Transfer mode (optional)
            resulting_balance: Resulting balance after transaction (optional)
            txn_id: Transaction ID (optional)
            cheque_id: Cheque ID (optional)
            metadata: Additional metadata (optional)
        """
        with DataStore._lock:
            DataStore._ensure_activity_header()

            with open(DataStore.ACTIVITY_PATH, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp,
                    username,
                    account_number,
                    action,
                    str(amount) if amount is not None else "",
                    mode if mode else "",
                    str(resulting_balance) if resulting_balance is not None else "",
                    txn_id if txn_id else "",
                    cheque_id if cheque_id else "",
                    metadata if metadata else ""
                ])

    @staticmethod
    def load_accounts() -> List:
        """
        Load accounts from storage and replay activity log

        Returns:
            List of Account objects
        """
        from Account import Account

        with DataStore._lock:
            accounts = []

            # Try loading from JSON first
            if os.path.exists(DataStore.JSON_PATH):
                try:
                    with open(DataStore.JSON_PATH, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        accounts = [Account.from_dict(acc_data) for acc_data in data]
                except Exception as e:
                    print(f"[DataStore] Error loading JSON accounts: {e}")
                    accounts = []

            # Fallback to CSV if JSON fails or doesn't exist
            elif os.path.exists(DataStore.CSV_PATH):
                try:
                    with open(DataStore.CSV_PATH, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            try:
                                account = Account.create_account(
                                    customer_id="",
                                    username=row['username'],
                                    password=row['password'],
                                    first_name=row['firstName'],
                                    last_name=row['lastName'],
                                    dob=row['dob'],
                                    gender=row['gender'],
                                    account_type=row['accountType'],
                                    account_number=row['accountNumber']
                                )
                                account.balance = float(row.get('balance', 0.0))
                                account.failed_attempts = int(row.get('failedAttempts', 0))
                                account.locked = row.get('locked', 'false').lower() == 'true'
                                accounts.append(account)
                            except Exception as e:
                                print(f"[DataStore] Error parsing CSV row: {e}")
                except Exception as e:
                    print(f"[DataStore] Error loading CSV accounts: {e}")

            # Replay activity log
            DataStore._load_and_replay_activity(accounts)

            return accounts

    @staticmethod
    def _load_and_replay_activity(accounts: List):
        """
        Replay activity log to restore transaction history

        Args:
            accounts: List of Account objects to replay into
        """
        from Transaction import Transaction

        if not os.path.exists(DataStore.ACTIVITY_PATH):
            return

        # Create lookup maps
        by_username = {acc.username: acc for acc in accounts}
        by_account_number = {acc.account_number: acc for acc in accounts}

        try:
            with open(DataStore.ACTIVITY_PATH, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    try:
                        timestamp = row.get('timestamp', '')
                        username = row.get('username', '')
                        account_no = row.get('accountNumber', '')
                        action = row.get('action', '')
                        amount_str = row.get('amount', '')
                        res_bal_str = row.get('resultingBalance', '')
                        txn_id = row.get('txnId', '')
                        cheque_id = row.get('chequeId', '')
                        metadata = row.get('metadata', '')  # <- added metadata

                        account = by_account_number.get(account_no) or by_username.get(username)
                        if not account:
                            continue

                        transaction_actions = [
                            "DEPOSIT", "WITHDRAW", "NEFT_SENT", "NEFT_RECEIVED",
                            "RTGS_SENT", "RTGS_RECEIVED", "INTER_ACCOUNT_SENT",
                            "INTER_ACCOUNT_RECEIVED", "AMB_FEE", "AMB_FEE_SETTLED",
                            "BILL_PAYMENT", "EXPENSE", "SALARY_CREDIT"
                        ]
                        if action in transaction_actions and amount_str and res_bal_str:
                            try:
                                amount = float(amount_str)
                                res_balance = float(res_bal_str)
                                if txn_id and not any(t.id == txn_id for t in account.transactions):
                                    txn = Transaction(
                                        id=txn_id,
                                        type=action,
                                        amount=amount,
                                        resulting_balance=res_balance,
                                        timestamp=timestamp,
                                        cheque_id=cheque_id if cheque_id else None,
                                        metadata=metadata  # Store metadata in Transaction
                                    )
                                    account.transactions.append(txn)
                                    account.balance = res_balance
                            except ValueError:
                                pass
                    except Exception as e:
                        print(f"[DataStore] Error replaying activity row: {e}")

        except Exception as e:
            print(f"[DataStore] Error reading activity log: {e}")

    @staticmethod
    def save_accounts(accounts: List):
        """
        Save accounts to JSON and CSV storage

        Args:
            accounts: List of Account objects to save
        """
        with DataStore._lock:
            # Save to JSON
            temp_json = DataStore.JSON_PATH + ".tmp"
            try:
                DataStore._ensure_dir(temp_json)
                with open(temp_json, 'w', encoding='utf-8') as f:
                    account_dicts = [acc.to_dict() for acc in accounts]
                    json.dump(account_dicts, f, indent=2)

                DataStore._atomic_replace(temp_json, DataStore.JSON_PATH, "JSON")
            except Exception as e:
                print(f"[DataStore] Error saving accounts to JSON: {e}")
                if os.path.exists(temp_json):
                    os.remove(temp_json)

            # Save to CSV
            temp_csv = DataStore.CSV_PATH + ".tmp"
            try:
                DataStore._ensure_dir(temp_csv)
                with open(temp_csv, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        "username", "password", "firstName", "lastName", "dob",
                        "gender", "accountType", "accountNumber", "balance",
                        "failedAttempts", "locked"
                    ])

                    for acc in accounts:
                        writer.writerow([
                            acc.username,
                            acc.password,
                            acc.first_name,
                            acc.last_name,
                            acc.dob,
                            acc.gender,
                            acc.account_type,
                            acc.account_number,
                            acc.balance,
                            acc.failed_attempts,
                            acc.locked
                        ])

                DataStore._atomic_replace(temp_csv, DataStore.CSV_PATH, "CSV")
            except Exception as e:
                print(f"[DataStore] Error saving accounts to CSV: {e}")
                if os.path.exists(temp_csv):
                    os.remove(temp_csv)

    @staticmethod
    def load_customers() -> List:
        """
        Load customers from JSON storage

        Returns:
            List of Customer objects
        """
        from Customer import Customer

        with DataStore._lock:
            if os.path.exists(DataStore.CUSTOMER_JSON_PATH):
                try:
                    with open(DataStore.CUSTOMER_JSON_PATH, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        return [Customer.from_dict(cust_data) for cust_data in data]
                except Exception as e:
                    print(f"[DataStore] Error loading customers: {e}")
                    return []
            return []

    @staticmethod
    def save_customers(customers: List):
        """
        Save customers to JSON storage

        Args:
            customers: List of Customer objects to save
        """
        with DataStore._lock:
            temp_json = DataStore.CUSTOMER_JSON_PATH + ".tmp"
            try:
                DataStore._ensure_dir(temp_json)
                with open(temp_json, 'w', encoding='utf-8') as f:
                    customer_dicts = [cust.to_dict() for cust in customers]
                    json.dump(customer_dicts, f, indent=2)

                DataStore._atomic_replace(temp_json, DataStore.CUSTOMER_JSON_PATH, "CUSTOMER_JSON")
            except Exception as e:
                print(f"[DataStore] Error saving customers: {e}")
                if os.path.exists(temp_json):
                    os.remove(temp_json)

    @staticmethod
    def load_accounts_without_replay() -> List:
        """
        Load accounts from storage without replaying activity log

        Returns:
            List of Account objects
        """
        from Account import Account

        with DataStore._lock:
            if os.path.exists(DataStore.JSON_PATH):
                try:
                    with open(DataStore.JSON_PATH, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        return [Account.from_dict(acc_data) for acc_data in data]
                except Exception as e:
                    print(f"[DataStore] Error loading accounts without replay: {e}")
            return []

    # ---------------------------------------------------
    # --- LOAN MODULE EXTENSION ---
    @staticmethod
    def save_loans(loans: List):
        """
        Save loans to JSON storage

        Args:
            loans: List of Loan objects to save
        """
        from loan import Loan
        DataStore._ensure_dir(DataStore.LOANS_JSON_PATH)
        with open(DataStore.LOANS_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump([loan.to_dict() for loan in loans], f, indent=2)

    @staticmethod
    def load_loans() -> List:
        """
        Load loans from JSON storage

        Returns:
            List of Loan objects
        """
        from loan import Loan
        if not os.path.exists(DataStore.LOANS_JSON_PATH):
            return []
        with open(DataStore.LOANS_JSON_PATH, 'r', encoding='utf-8') as f:
            return [Loan.from_dict(obj) for obj in json.load(f)]


# ------------------------------------------
# Utility function to parse metadata from string

def parse_metadata(metadata_str: Optional[str]) -> dict:
    """
    Parse semicolon-separated key=value pairs in metadata string.
    Example: "category=Transport;merchant=Metro;method=Debit Card"
    """
    result = {}
    if metadata_str:
        parts = metadata_str.split(';')
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                result[key.strip()] = value.strip()
    return result

# ------------------------------------------
# Example function to print transactions, with merchant and method info

def print_transaction_history(account):
    """
    Print transaction history with merchant and method extracted from metadata.
    """
    for txn in account.transactions:
        meta = parse_metadata(getattr(txn, 'metadata', ''))
        merchant = meta.get("merchant", "N/A")
        method = meta.get("method", "N/A")
        print(f"{txn.id: <13} {txn.timestamp}  {txn.type: <10}  Rs. {txn.amount:.2f}  Rs. {txn.resulting_balance:.2f} INR")
        print(f"    Merchant: {merchant} | Method: {method}")
