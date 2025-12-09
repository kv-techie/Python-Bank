"""
International Bank Registry
Maintains database of international bank accounts for wire transfers
"""

import random
from datetime import datetime
from typing import Dict, List, Optional


class InternationalAccount:
    """Represents an international bank account"""

    def __init__(
        self,
        account_number: str,
        account_holder: str,
        bank_name: str,
        swift_code: str,
        country: str,
        currency: str,
        balance: float = 0.0,
    ):
        self.account_number = account_number
        self.account_holder = account_holder
        self.bank_name = bank_name
        self.swift_code = swift_code
        self.country = country
        self.currency = currency
        self.balance = balance
        self.transactions: List[Dict] = []

    def receive_transfer(
        self, amount: float, sender_name: str, sender_country: str, swift_ref: str
    ):
        """Record incoming international transfer"""
        self.balance += amount

        transaction = {
            "timestamp": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            "type": "INCOMING_WIRE",
            "amount": amount,
            "from": f"{sender_name}, {sender_country}",
            "swift_ref": swift_ref,
            "resulting_balance": self.balance,
        }

        self.transactions.append(transaction)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "account_number": self.account_number,
            "account_holder": self.account_holder,
            "bank_name": self.bank_name,
            "swift_code": self.swift_code,
            "country": self.country,
            "currency": self.currency,
            "balance": self.balance,
            "transactions": self.transactions,
        }

    @staticmethod
    def from_dict(data: dict) -> "InternationalAccount":
        """Create from dictionary"""
        acc = InternationalAccount(
            account_number=data["account_number"],
            account_holder=data["account_holder"],
            bank_name=data["bank_name"],
            swift_code=data["swift_code"],
            country=data["country"],
            currency=data["currency"],
            balance=data.get("balance", 0.0),
        )
        acc.transactions = data.get("transactions", [])
        return acc


class InternationalBankRegistry:
    """Registry of international bank accounts"""

    def __init__(self, silent=False):
        """Initialize with sample international accounts"""
        self.accounts: Dict[str, InternationalAccount] = {}  # account_number -> account
        self._generate_sample_accounts()
        if not silent:
            print(
                f"✓ Loaded {len(self.accounts)} international accounts across {len(self._get_unique_countries())} countries"
            )

    def _get_unique_countries(self) -> set:
        """Get set of unique countries"""
        return set(acc.country for acc in self.accounts.values())

    def _generate_sample_accounts(self):
        """Generate diverse sample international accounts"""

        # Bank templates with realistic data
        banks = [
            # USA
            {
                "name": "Bank of America",
                "swift": "BOFAUS3N",
                "country": "USA",
                "currency": "USD",
                "prefix": "US29BOFA",
            },
            {
                "name": "Chase Bank",
                "swift": "CHASUS33",
                "country": "USA",
                "currency": "USD",
                "prefix": "US33CHAS",
            },
            {
                "name": "Wells Fargo",
                "swift": "WFBIUS6S",
                "country": "USA",
                "currency": "USD",
                "prefix": "US64WFBI",
            },
            {
                "name": "Goldman Sachs Bank USA",
                "swift": "GSCMUS33",
                "country": "USA",
                "currency": "USD",
                "prefix": "US68GSCM",
            },
            {
                "name": "Citibank",
                "swift": "CITIUS33",
                "country": "USA",
                "currency": "USD",
                "prefix": "US83CITI",
            },
            # UK
            {
                "name": "HSBC UK",
                "swift": "HSBCGB2L",
                "country": "UK",
                "currency": "GBP",
                "prefix": "GB29HSBC",
            },
            {
                "name": "Barclays",
                "swift": "BARCGB22",
                "country": "UK",
                "currency": "GBP",
                "prefix": "GB82BARC",
            },
            {
                "name": "Lloyds Bank",
                "swift": "LOYDGB21",
                "country": "UK",
                "currency": "GBP",
                "prefix": "GB94LOYD",
            },
            {
                "name": "NatWest Group",
                "swift": "NWBKGB2L",
                "country": "UK",
                "currency": "GBP",
                "prefix": "GB15NWBK",
            },
            {
                "name": "Santander UK plc",
                "swift": "ABBYGB2L",
                "country": "UK",
                "currency": "GBP",
                "prefix": "GB75ABBY",
            },
            # EUROPE
            {
                "name": "Deutsche Bank",
                "swift": "DEUTDEFF",
                "country": "Germany",
                "currency": "EUR",
                "prefix": "DE89DEUT",
            },
            {
                "name": "BNP Paribas",
                "swift": "BNPAFRPP",
                "country": "France",
                "currency": "EUR",
                "prefix": "FR76BNPA",
            },
            {
                "name": "ING Bank",
                "swift": "INGBNL2A",
                "country": "Netherlands",
                "currency": "EUR",
                "prefix": "NL91INGB",
            },
            {
                "name": "UBS Group AG",
                "swift": "UBSWCHZH",
                "country": "Switzerland",
                "currency": "CHF",
                "prefix": "CH93UBSW",
            },
            {
                "name": "Crédit Agricole SA",
                "swift": "AGRIFRPP",
                "country": "France",
                "currency": "EUR",
                "prefix": "FR14AGRI",
            },
            # ASIA PACIFIC
            {
                "name": "DBS Bank",
                "swift": "DBSSSGSG",
                "country": "Singapore",
                "currency": "SGD",
                "prefix": "SG45DBSS",
            },
            {
                "name": "OCBC Bank",
                "swift": "OCBCSGSG",
                "country": "Singapore",
                "currency": "SGD",
                "prefix": "SG72OCBC",
            },
            {
                "name": "ANZ Bank",
                "swift": "ANZBAU3M",
                "country": "Australia",
                "currency": "AUD",
                "prefix": "AU28ANZB",
            },
            {
                "name": "Commonwealth Bank",
                "swift": "CTBAAU2S",
                "country": "Australia",
                "currency": "AUD",
                "prefix": "AU65CTBA",
            },
            {
                "name": "MUFG Bank, Ltd.",
                "swift": "BOTKJPJT",
                "country": "Japan",
                "currency": "JPY",
                "prefix": "JP18BOTK",
            },
            # MIDDLE EAST
            {
                "name": "Emirates NBD",
                "swift": "EBILAEAD",
                "country": "UAE",
                "currency": "AED",
                "prefix": "AE07EBIL",
            },
            {
                "name": "First Abu Dhabi Bank",
                "swift": "NBADAEAA",
                "country": "UAE",
                "currency": "AED",
                "prefix": "NBADAEAA",
            },
            {
                "name": "Dubai Islamic Bank",
                "swift": "DUIBAEAD",
                "country": "UAE",
                "currency": "AED",
                "prefix": "DUIBAEAD",
            },
            {
                "name": "Abu Dhabi Commercial Bank",
                "swift": "ADCBAEAA",
                "country": "UAE",
                "currency": "AED",
                "prefix": "ADCBAEAA",
            },
            {
                "name": "Abu Dhabi Islamic Bank",
                "swift": "ABDIAEAD",
                "country": "UAE",
                "currency": "AED",
                "prefix": "ABDIAEAD",
            },
            {
                "name": "Mashreqbank PSC",
                "swift": "BOMLAEAD",
                "country": "UAE",
                "currency": "AED",
                "prefix": "BOMLAEAD",
            },
            {
                "name": "National Bank of Fujairah",
                "swift": "NBFUAEAF",
                "country": "UAE",
                "currency": "AED",
                "prefix": "NBFUAEAF",
            },
            {
                "name": "Ajman Bank",
                "swift": "AJMNAEAJ",
                "country": "UAE",
                "currency": "AED",
                "prefix": "AJMNAEAJ",
            },
            {
                "name": "Commercial Bank of Dubai",
                "swift": "CBDUAEAD",
                "country": "UAE",
                "currency": "AED",
                "prefix": "CBDUAEAD",
            },
            # CANADA
            {
                "name": "RBC Royal Bank",
                "swift": "ROYCCAT2",
                "country": "Canada",
                "currency": "CAD",
                "prefix": "CA89ROYC",
            },
            {
                "name": "TD Canada Trust",
                "swift": "TDOMCATTTOR",
                "country": "Canada",
                "currency": "CAD",
                "prefix": "CA05TDOM",
            },
            {
                "name": "Bank of Montreal",
                "swift": "BOFMCAM2",
                "country": "Canada",
                "currency": "CAD",
                "prefix": "CA74BOFM",
            },
            {
                "name": "Scotiabank",
                "swift": "NOSCCATT",
                "country": "Canada",
                "currency": "CAD",
                "prefix": "CA16NOSC",
            },
            {
                "name": "Canadian Imperial Bank of Commerce",
                "swift": "CIBCCATT",
                "country": "Canada",
                "currency": "CAD",
                "prefix": "CA11CIBC",
            },
        ]

        # First and last names for diversity
        first_names = [
            "James",
            "Mary",
            "John",
            "Patricia",
            "Robert",
            "Jennifer",
            "Michael",
            "Linda",
            "William",
            "Elizabeth",
            "David",
            "Barbara",
            "Richard",
            "Susan",
            "Joseph",
            "Jessica",
            "Thomas",
            "Sarah",
            "Charles",
            "Karen",
            "Christopher",
            "Nancy",
            "Daniel",
            "Lisa",
            "Matthew",
            "Betty",
            "Anthony",
            "Margaret",
            "Mark",
            "Sandra",
            "Donald",
            "Ashley",
            "Steven",
            "Kimberly",
            "Paul",
            "Emily",
            "Andrew",
            "Donna",
            "Joshua",
            "Michelle",
            "Kenneth",
            "Dorothy",
            "Kevin",
            "Carol",
            "Brian",
            "Amanda",
            "George",
            "Melissa",
            "Edward",
            "Deborah",
            "Ronald",
            "Stephanie",
            "Timothy",
            "Rebecca",
            "Jason",
            "Sharon",
            "Jeffrey",
            "Laura",
            "Ryan",
            "Cynthia",
            "Jacob",
            "Kathleen",
            "Gary",
            "Amy",
        ]

        last_names = [
            "Smith",
            "Johnson",
            "Williams",
            "Brown",
            "Jones",
            "Garcia",
            "Miller",
            "Davis",
            "Rodriguez",
            "Martinez",
            "Hernandez",
            "Lopez",
            "Gonzalez",
            "Wilson",
            "Anderson",
            "Thomas",
            "Taylor",
            "Moore",
            "Jackson",
            "Martin",
            "Lee",
            "Thompson",
            "White",
            "Harris",
            "Clark",
            "Lewis",
            "Robinson",
            "Walker",
            "Young",
            "Hall",
            "Allen",
            "King",
            "Wright",
            "Scott",
            "Green",
            "Baker",
            "Adams",
            "Nelson",
            "Carter",
            "Mitchell",
            "Roberts",
            "Turner",
            "Phillips",
            "Campbell",
            "Parker",
            "Evans",
            "Edwards",
            "Collins",
        ]

        # Generate 20 accounts per bank (17 banks × 20 = 340 accounts, but we'll limit to ~180)
        num_accounts_per_bank = 20

        for bank_info in banks:
            for i in range(num_accounts_per_bank):
                # Generate account number
                random_digits = "".join([str(random.randint(0, 9)) for _ in range(10)])
                account_number = f"{bank_info['prefix']}{random_digits}"

                # Generate holder name
                first = random.choice(first_names)
                last = random.choice(last_names)
                holder_name = f"{first} {last}"

                # Generate random balance (more realistic distribution)
                balance = round(random.uniform(1000, 500000), 2)

                account = InternationalAccount(
                    account_number=account_number,
                    account_holder=holder_name,
                    bank_name=bank_info["name"],
                    swift_code=bank_info["swift"],
                    country=bank_info["country"],
                    currency=bank_info["currency"],
                    balance=balance,
                )

                self.accounts[account_number] = account

    def find_account_by_number(
        self, account_number: str
    ) -> Optional[InternationalAccount]:
        """Find account by account number"""
        return self.accounts.get(account_number)

    def list_sample_accounts(self, limit=None):
        """
        Return a list of sample account information dictionaries

        Args:
            limit: Maximum number of accounts to return (default: all)

        Returns:
            List of dicts with keys: holder, country, bank, account, swift, currency
        """
        result = []
        accounts_list = list(self.accounts.values())

        # Limit if specified
        if limit:
            accounts_list = accounts_list[:limit]

        for acc in accounts_list:
            result.append(
                {
                    "holder": acc.account_holder,
                    "country": acc.country,
                    "bank": acc.bank_name,
                    "account": acc.account_number,
                    "swift": acc.swift_code,
                    "currency": acc.currency,
                }
            )

        return result

    def validate_transfer_details(
        self, account_number: str, swift_code: str, account_holder: str
    ) -> tuple[bool, str, Optional[InternationalAccount]]:
        """Validate international transfer details"""

        account = self.find_account_by_number(account_number)

        if not account:
            return False, "Account number not found in international registry", None

        if account.swift_code != swift_code:
            return False, f"SWIFT code mismatch. Expected: {account.swift_code}", None

        if account.account_holder.lower() != account_holder.lower():
            return (
                False,
                f"Account holder name mismatch. Expected: {account.account_holder}",
                None,
            )

        return True, "Transfer details validated successfully", account

    def get_accounts_by_country(self, country: str) -> List[InternationalAccount]:
        """Get all accounts for a specific country"""
        return [acc for acc in self.accounts.values() if acc.country == country]

    def get_accounts_by_currency(self, currency: str) -> List[InternationalAccount]:
        """Get all accounts for a specific currency"""
        return [acc for acc in self.accounts.values() if acc.currency == currency]

    def get_statistics(self) -> dict:
        """Get registry statistics"""
        all_accounts = list(self.accounts.values())

        stats = {
            "total_accounts": len(all_accounts),
            "by_country": {},
            "by_currency": {},
            "total_balance_usd_equivalent": 0.0,
        }

        # Count by country and currency
        for acc in all_accounts:
            stats["by_country"][acc.country] = (
                stats["by_country"].get(acc.country, 0) + 1
            )
            stats["by_currency"][acc.currency] = (
                stats["by_currency"].get(acc.currency, 0) + 1
            )

            # Rough USD conversion for total (simplified)
            if acc.currency == "USD":
                stats["total_balance_usd_equivalent"] += acc.balance
            elif acc.currency == "EUR":
                stats["total_balance_usd_equivalent"] += acc.balance * 1.1
            elif acc.currency == "GBP":
                stats["total_balance_usd_equivalent"] += acc.balance * 1.27
            elif acc.currency == "INR":
                stats["total_balance_usd_equivalent"] += acc.balance / 83.12
            else:
                stats["total_balance_usd_equivalent"] += acc.balance  # Rough estimate

        return stats

    def to_dict(self) -> dict:
        """Convert registry to dictionary"""
        return {
            "accounts": {
                acc_num: acc.to_dict() for acc_num, acc in self.accounts.items()
            }
        }

    @staticmethod
    def from_dict(data: dict, silent=True) -> "InternationalBankRegistry":
        """Create registry from dictionary"""
        registry = InternationalBankRegistry.__new__(InternationalBankRegistry)
        registry.accounts = {}

        for acc_num, acc_data in data.get("accounts", {}).items():
            registry.accounts[acc_num] = InternationalAccount.from_dict(acc_data)

        if not silent:
            print(
                f"✓ Loaded {len(registry.accounts)} international accounts across {len(registry._get_unique_countries())} countries"
            )
        return registry
