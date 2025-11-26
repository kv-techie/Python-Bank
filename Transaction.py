from dataclasses import dataclass, field
from typing import Optional
from BankClock import BankClock
from TransactionRegistry import TransactionRegistry

@dataclass
class Transaction:
    """Represents a financial transaction in the banking system"""
    
    type: str
    amount: float
    resulting_balance: float
    id: str = field(default_factory=TransactionRegistry.generate_id)
    timestamp: str = field(default_factory=BankClock.get_formatted_datetime)
    cheque_id: Optional[str] = None
    category: Optional[str] = None
    merchant: Optional[str] = None
    payment_method: Optional[str] = None
    metadata: Optional[str] = None  # Added for arbitrary data (e.g. loan EMI info)

    def to_dict(self) -> dict:
        """
        Convert transaction to dictionary for JSON serialization
        
        Returns:
            Dictionary representation of the transaction
        """
        return {
            "id": self.id,
            "type": self.type,
            "amount": self.amount,
            "resultingBalance": self.resulting_balance,
            "timestamp": self.timestamp,
            "chequeId": self.cheque_id,
            "category": self.category,
            "merchant": self.merchant,
            "paymentMethod": self.payment_method,
            "metadata": self.metadata  # Include metadata in serialization
        }

    @staticmethod
    def from_dict(data: dict) -> 'Transaction':
        """
        Create a Transaction from dictionary
        
        Args:
            data: Dictionary containing transaction data
            
        Returns:
            Transaction instance
        """
        return Transaction(
            id=data.get("id", TransactionRegistry.generate_id()),
            type=data["type"],
            amount=data["amount"],
            resulting_balance=data["resultingBalance"],
            timestamp=data.get("timestamp", BankClock.get_formatted_datetime()),
            cheque_id=data.get("chequeId"),
            category=data.get("category"),
            merchant=data.get("merchant"),
            payment_method=data.get("paymentMethod"),
            metadata=data.get("metadata")       # Load metadata if present
        )
    
    def get_formatted_amount(self) -> str:
        """
        Get formatted amount string with currency symbol
        
        Returns:
            Formatted amount string (e.g., "Rs. 1,500.00")
        """
        return f"Rs. {self.amount:,.2f}"
    
    def get_formatted_balance(self) -> str:
        """
        Get formatted resulting balance string
        
        Returns:
            Formatted balance string (e.g., "Rs. 15,000.00")
        """
        return f"Rs. {self.resulting_balance:,.2f}"
    
    def is_debit(self) -> bool:
        """
        Check if this is a debit transaction (money going out)
        
        Returns:
            True if transaction is a debit type
        """
        debit_types = [
            "WITHDRAW", "NEFT_SENT", "RTGS_SENT", "INTER_ACCOUNT_SENT",
            "AMB_FEE", "AMB_FEE_SETTLED", "EXPENSE", "BILL_PAYMENT",
            "TAX_DEDUCTED"
        ]
        return self.type in debit_types
    
    def is_credit(self) -> bool:
        """
        Check if this is a credit transaction (money coming in)
        
        Returns:
            True if transaction is a credit type
        """
        credit_types = [
            "DEPOSIT", "NEFT_RECEIVED", "RTGS_RECEIVED", 
            "INTER_ACCOUNT_RECEIVED", "SALARY"
        ]
        return self.type in credit_types
    
    def get_transaction_type_display(self) -> str:
        """
        Get user-friendly display name for transaction type
        
        Returns:
            Formatted transaction type string
        """
        type_mappings = {
            "DEPOSIT": "Deposit",
            "WITHDRAW": "Withdrawal",
            "NEFT_SENT": "NEFT Transfer (Sent)",
            "NEFT_RECEIVED": "NEFT Transfer (Received)",
            "RTGS_SENT": "RTGS Transfer (Sent)",
            "RTGS_RECEIVED": "RTGS Transfer (Received)",
            "INTER_ACCOUNT_SENT": "Inter-Account Transfer (Sent)",
            "INTER_ACCOUNT_RECEIVED": "Inter-Account Transfer (Received)",
            "AMB_FEE": "Average Monthly Balance Fee",
            "AMB_FEE_SETTLED": "AMB Fee Settlement",
            "EXPENSE": "Expense",
            "BILL_PAYMENT": "Bill Payment",
            "SALARY": "Salary Credit",
            "TAX_DEDUCTED": "Tax Deduction (TDS)"
        }
        return type_mappings.get(self.type, self.type.replace("_", " ").title())
    
    def get_display_line(self, show_category: bool = True) -> str:
        """
        Get a single-line display string for the transaction
        
        Args:
            show_category: Whether to include category/merchant info
            
        Returns:
            Formatted display line
        """
        parts = [
            f"{self.id:<15}",
            f"{self.timestamp:<20}",
            f"{self.get_transaction_type_display():<25}",
            f"{self.get_formatted_amount():>15}",
            f"{self.get_formatted_balance():>15}"
        ]
        
        if show_category and (self.category or self.merchant):
            category_info = self.category or ""
            merchant_info = self.merchant or ""
            if category_info and merchant_info:
                parts.append(f"({category_info} - {merchant_info})")
            elif category_info:
                parts.append(f"({category_info})")
            elif merchant_info:
                parts.append(f"({merchant_info})")
        
        return " ".join(parts)
    
    def __repr__(self) -> str:
        """String representation of the transaction"""
        return f"Transaction({self.id}, {self.type}, Rs. {self.amount:.2f})"
    
    def __str__(self) -> str:
        """User-friendly string representation"""
        return f"{self.get_transaction_type_display()}: {self.get_formatted_amount()} on {self.timestamp}"
    
    def __eq__(self, other) -> bool:
        """Check equality based on transaction ID"""
        if not isinstance(other, Transaction):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash based on transaction ID"""
        return hash(self.id)

# Transaction type constants for easy reference
class TransactionType:
    """Constants for transaction types"""
    
    # Credit types (money in)
    DEPOSIT = "DEPOSIT"
    NEFT_RECEIVED = "NEFT_RECEIVED"
    RTGS_RECEIVED = "RTGS_RECEIVED"
    INTER_ACCOUNT_RECEIVED = "INTER_ACCOUNT_RECEIVED"
    SALARY = "SALARY"
    
    # Debit types (money out)
    WITHDRAW = "WITHDRAW"
    NEFT_SENT = "NEFT_SENT"
    RTGS_SENT = "RTGS_SENT"
    INTER_ACCOUNT_SENT = "INTER_ACCOUNT_SENT"
    EXPENSE = "EXPENSE"
    BILL_PAYMENT = "BILL_PAYMENT"
    
    # Fee types
    AMB_FEE = "AMB_FEE"
    AMB_FEE_SETTLED = "AMB_FEE_SETTLED"
    TAX_DEDUCTED = "TAX_DEDUCTED"
    
    @staticmethod
    def get_all_credit_types() -> list:
        """Get list of all credit transaction types"""
        return [
            TransactionType.DEPOSIT,
            TransactionType.NEFT_RECEIVED,
            TransactionType.RTGS_RECEIVED,
            TransactionType.INTER_ACCOUNT_RECEIVED,
            TransactionType.SALARY
        ]
    
    @staticmethod
    def get_all_debit_types() -> list:
        """Get list of all debit transaction types"""
        return [
            TransactionType.WITHDRAW,
            TransactionType.NEFT_SENT,
            TransactionType.RTGS_SENT,
            TransactionType.INTER_ACCOUNT_SENT,
            TransactionType.EXPENSE,
            TransactionType.BILL_PAYMENT,
            TransactionType.AMB_FEE,
            TransactionType.AMB_FEE_SETTLED,
            TransactionType.TAX_DEDUCTED
        ]
