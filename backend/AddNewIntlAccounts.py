"""Add new bank accounts from InternationalBankRegistry (auto-sync)"""

import random

from DataStore import DataStore
from InternationalBankRegistry import InternationalAccount, InternationalBankRegistry


def extract_banks_by_country(registry):
    """Extract unique banks per country from existing accounts"""
    banks_by_country = {}

    for account in registry.accounts.values():
        country = account.country
        if country not in banks_by_country:
            banks_by_country[country] = {}

        bank_key = (account.bank_name, account.swift_code)
        if bank_key not in banks_by_country[country]:
            banks_by_country[country][bank_key] = {
                "name": account.bank_name,
                "swift": account.swift_code,
                "currency": account.currency,
                "prefix": account.swift_code[:4],
            }

    return banks_by_country


# Load existing registry
print("Loading existing accounts...")
registry = DataStore.load_international_accounts()
initial_count = len(registry.accounts)

print(f"✓ Loaded {initial_count} existing accounts")

# Extract existing banks
existing_banks_by_country = extract_banks_by_country(registry)

# Create a NEW temporary registry to get the FULL bank list
print("\n🔍 Scanning InternationalBankRegistry for bank definitions...")
temp_registry = InternationalBankRegistry()  # This generates with ALL banks
all_banks_by_country = extract_banks_by_country(temp_registry)

print("✓ Found banks in registry code")

# Find NEW banks (present in code but not in saved data)
new_banks_to_add = {}

for country, banks in all_banks_by_country.items():
    for bank_key, bank_info in banks.items():
        # Check if this bank exists in the saved data
        if (
            country not in existing_banks_by_country
            or bank_key not in existing_banks_by_country[country]
        ):
            if country not in new_banks_to_add:
                new_banks_to_add[country] = {}
            new_banks_to_add[country][bank_key] = bank_info

# Show summary
print("\n" + "=" * 80)
print("BANK COMPARISON")
print("=" * 80)

for country in sorted(
    set(list(existing_banks_by_country.keys()) + list(all_banks_by_country.keys()))
):
    existing_count = len(existing_banks_by_country.get(country, {}))
    total_count = len(all_banks_by_country.get(country, {}))
    new_count = len(new_banks_to_add.get(country, {}))

    status = ""
    if new_count > 0:
        status = f"🆕 +{new_count} new"
    elif existing_count == total_count:
        status = "✅ Up to date"

    print(f"{country:<15} {existing_count:>2}/{total_count:<2} banks  {status}")

print("=" * 80)

if not new_banks_to_add or all(len(banks) == 0 for banks in new_banks_to_add.values()):
    print("\n✅ All banks from InternationalBankRegistry are already in the dataset!")
    print(f"   Current total: {initial_count} accounts")
    exit(0)

# Show details of new banks
print("\n🆕 NEW BANKS TO ADD:")
print("-" * 80)
total_new_banks = 0
for country, banks in new_banks_to_add.items():
    if banks:
        print(f"\n{country}:")
        for bank_info in banks.values():
            print(f"   • {bank_info['name']} ({bank_info['swift']})")
            total_new_banks += 1

print("-" * 80)
print(f"Total: {total_new_banks} new banks")

# Ask for confirmation
ACCOUNTS_PER_BANK = 10
total_new_accounts = total_new_banks * ACCOUNTS_PER_BANK

confirm = (
    input(
        f"\nAdd {ACCOUNTS_PER_BANK} accounts for each bank? ({total_new_accounts} total) (yes/no): "
    )
    .strip()
    .lower()
)
if confirm not in ["yes", "y"]:
    print("❌ Cancelled. No changes made.")
    exit(0)

# Sample names by region
names_by_region = {
    "UAE": {
        "first": [
            "Ahmed",
            "Fatima",
            "Mohammed",
            "Aisha",
            "Ali",
            "Layla",
            "Omar",
            "Sara",
            "Hassan",
            "Noor",
        ],
        "last": [
            "Al Maktoum",
            "Al Nahyan",
            "Khan",
            "Sheikh",
            "Abdullah",
            "Rahman",
            "Hussein",
            "Malik",
            "Saleh",
            "Khalid",
        ],
    },
    "USA": {
        "first": [
            "John",
            "Mary",
            "Michael",
            "Jennifer",
            "David",
            "Linda",
            "James",
            "Patricia",
            "Robert",
            "Elizabeth",
        ],
        "last": [
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
        ],
    },
    "UK": {
        "first": [
            "Oliver",
            "Olivia",
            "George",
            "Amelia",
            "Harry",
            "Isla",
            "Jack",
            "Ava",
            "Jacob",
            "Emily",
        ],
        "last": [
            "Smith",
            "Jones",
            "Taylor",
            "Brown",
            "Williams",
            "Wilson",
            "Johnson",
            "Davies",
            "Robinson",
            "Wright",
        ],
    },
    "Singapore": {
        "first": [
            "Wei",
            "Mei",
            "Jun",
            "Hui",
            "Chen",
            "Lin",
            "Kai",
            "Yan",
            "Ming",
            "Ying",
        ],
        "last": [
            "Tan",
            "Lim",
            "Lee",
            "Ng",
            "Ong",
            "Wong",
            "Goh",
            "Chua",
            "Chan",
            "Koh",
        ],
    },
    "Japan": {
        "first": [
            "Haruto",
            "Yui",
            "Sota",
            "Hina",
            "Yuto",
            "Sakura",
            "Ren",
            "Rin",
            "Kaito",
            "Mao",
        ],
        "last": [
            "Sato",
            "Suzuki",
            "Takahashi",
            "Tanaka",
            "Watanabe",
            "Ito",
            "Yamamoto",
            "Nakamura",
            "Kobayashi",
            "Kato",
        ],
    },
}

# Default names for other countries
default_names = {
    "first": [
        "Alex",
        "Sam",
        "Jordan",
        "Taylor",
        "Morgan",
        "Casey",
        "Riley",
        "Drew",
        "Quinn",
        "Avery",
    ],
    "last": [
        "Anderson",
        "Thomas",
        "Jackson",
        "White",
        "Harris",
        "Martin",
        "Thompson",
        "Garcia",
        "Martinez",
        "Robinson",
    ],
}

print("\n📝 Adding accounts...\n")

accounts_added = 0

for country, banks in new_banks_to_add.items():
    if not banks:
        continue

    # Get appropriate names for this country
    names = names_by_region.get(country, default_names)

    for bank_info in banks.values():
        bank_accounts = 0
        attempts = 0
        max_attempts = 50

        while bank_accounts < ACCOUNTS_PER_BANK and attempts < max_attempts:
            attempts += 1

            # Generate unique account details
            first_name = random.choice(names["first"])
            last_name = random.choice(names["last"])
            account_holder = f"{first_name} {last_name}"

            # Generate country-specific account number
            if country == "UAE":
                account_number = f"AE{random.randint(10, 99)}{bank_info['prefix']}{random.randint(100000000, 999999999)}"
            elif country == "USA":
                account_number = f"US{random.randint(10, 99)}{bank_info['prefix']}{random.randint(1000000000, 9999999999)}"
            elif country == "UK":
                account_number = f"GB{random.randint(10, 99)}{bank_info['prefix']}{random.randint(10000000, 99999999)}{random.randint(1000000, 9999999)}"
            elif country == "Singapore":
                account_number = f"SG{random.randint(10, 99)}{bank_info['prefix']}{random.randint(1000000000, 9999999999)}"
            else:
                account_number = f"{country[:2].upper()}{random.randint(10, 99)}{bank_info['prefix']}{random.randint(100000000, 999999999)}"

            # Check if account already exists
            if account_number in registry.accounts:
                continue

            # Create new account
            account = InternationalAccount(
                account_holder=account_holder,
                account_number=account_number,
                bank_name=bank_info["name"],
                swift_code=bank_info["swift"],
                country=country,
                currency=bank_info["currency"],
                balance=round(random.uniform(50000, 500000), 2),
            )

            registry.accounts[account_number] = account
            accounts_added += 1
            bank_accounts += 1

        print(f"   ✓ {bank_info['name']:<45} Added {bank_accounts} accounts")

print(f"\n✅ Successfully added {accounts_added} new accounts!")

# Save updated registry
print("\nSaving to file...")
DataStore.save_international_accounts(registry, verbose=True)

final_count = len(registry.accounts)

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Initial accounts:  {initial_count}")
print(f"New accounts:      +{accounts_added}")
print(f"Final total:       {final_count}")
print("=" * 80)

print("\n✅ Dataset synchronized with InternationalBankRegistry!")
print("✓ All existing transfers and history preserved!")
print("✓ Run this script anytime you add banks to InternationalBankRegistry.py")
