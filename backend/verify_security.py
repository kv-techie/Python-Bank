import sys
import os
sys.path.append(os.path.join(os.getcwd(), "backend"))

from Bank import Bank
from Customer import Customer

from werkzeug.security import check_password_hash

def test_security_hashing():
    print("Testing Security Hashing...")
    bank = Bank()
    
    # Check existing hashed user
    username = "kedvin"
    password = "password123" # Assuming this was the old password
    
    customer = bank.authenticate(username, password)
    if customer:
        print(f"[OK] Authentication successful for {username} with hashed password.")
        print(f"Hashed Password in Data: {customer.password}")
    else:
        print(f"[FAIL] Authentication failed for {username}. Check migration.")

    # Test new registration hashing
    new_user = "security_test"
    new_pass = "secure_pass_2026"
    
    print(f"\nRegistering new user: {new_user}...")
    cust, acc = bank.register_customer(
        username=new_user,
        password=new_pass,
        first_name="Security",
        last_name="Tester",
        dob="1990-01-01",
        gender="Other",
        phone_number="9999999999",
        email="security@test.com",
        account_type="Savings"
    )
    
    print(f"Stored Password: {cust.password}")
    if cust.password.startswith("pbkdf2:sha256:"):
        print("[OK] New password is correctly hashed.")
    else:
        print("[FAIL] New password is NOT hashed.")
        
    if check_password_hash(cust.password, new_pass):
        print("[OK] New password verification works.")
    else:
        print("[FAIL] New password verification failed.")

if __name__ == "__main__":
    test_security_hashing()
