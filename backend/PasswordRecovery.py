#!/usr/bin/env python3
"""
Password Recovery Module
Handles forgot password, OTP generation, security questions, and password reset
"""

import random
import string
from datetime import datetime, timedelta
from typing import Optional, Tuple

from .DataStore import DataStore


class PasswordRecoveryManager:
    """Manages password recovery operations"""

    # Security Questions Pool
    SECURITY_QUESTIONS = [
        "What is your mother's maiden name?",
        "What was the name of your first pet?",
        "What city were you born in?",
        "What is your favorite book?",
        "What was your childhood nickname?",
        "What is the name of your first school?",
        "What is your favorite movie?",
        "What was the make of your first car?",
        "What is your favorite food?",
        "What is the name of the street you grew up on?",
    ]

    # Configuration
    OTP_LENGTH = 6
    OTP_VALIDITY_MINUTES = 10
    MAX_OTP_ATTEMPTS = 3
    MIN_PASSWORD_LENGTH = 6
    ADMIN_CODE = "ADMIN2025"  # Change this in production!

    @staticmethod
    def generate_otp() -> str:
        """Generate a random OTP"""
        return "".join(
            random.choices(string.digits, k=PasswordRecoveryManager.OTP_LENGTH)
        )

    @staticmethod
    def get_otp_expiry() -> datetime:
        """Get OTP expiry datetime"""
        from .BankClock import BankClock

        return BankClock.now() + timedelta(
            minutes=PasswordRecoveryManager.OTP_VALIDITY_MINUTES
        )

    @staticmethod
    def is_otp_expired(expiry: datetime) -> bool:
        """Check if OTP is expired"""
        from .BankClock import BankClock

        return BankClock.now() > expiry

    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """
        Validate password strength
        Returns: (is_valid, message)
        """
        if len(password) < PasswordRecoveryManager.MIN_PASSWORD_LENGTH:
            return (
                False,
                f"Password must be at least {PasswordRecoveryManager.MIN_PASSWORD_LENGTH} characters long",
            )

        if password.isspace() or not password.strip():
            return False, "Password cannot be empty or contain only spaces"

        return True, "Password is valid"

    @staticmethod
    def display_security_questions():
        """Display numbered list of security questions"""
        print("\nAvailable Security Questions:")
        for idx, question in enumerate(PasswordRecoveryManager.SECURITY_QUESTIONS, 1):
            print(f"    {idx}. {question}")

    @staticmethod
    def get_security_question_by_index(index: int) -> Optional[str]:
        """Get security question by index (1-based)"""
        if 1 <= index <= len(PasswordRecoveryManager.SECURITY_QUESTIONS):
            return PasswordRecoveryManager.SECURITY_QUESTIONS[index - 1]
        return None


class CustomerPasswordRecovery:
    """Mixin class to add password recovery capabilities to Customer"""

    def __init__(self):
        """Initialize password recovery attributes"""
        self.security_question: Optional[str] = None
        self.security_answer: Optional[str] = None
        self.password_reset_otp: Optional[str] = None
        self.otp_expiry: Optional[datetime] = None
        self.otp_attempts: int = 0

    def set_security_question(self, question: str, answer: str) -> bool:
        """
        Set security question and answer
        Returns: True if successful
        """
        if not question or not answer:
            return False

        self.security_question = question
        self.security_answer = answer.lower().strip()
        return True

    def verify_security_answer(self, answer: str) -> bool:
        """Verify security answer (case-insensitive)"""
        if not self.security_answer:
            return False
        return self.security_answer == answer.lower().strip()

    def has_security_question(self) -> bool:
        """Check if security question is set"""
        return self.security_question is not None and self.security_answer is not None

    def generate_password_reset_otp(self) -> str:
        """
        Generate and store OTP for password reset
        Returns: Generated OTP
        """
        self.password_reset_otp = PasswordRecoveryManager.generate_otp()
        self.otp_expiry = PasswordRecoveryManager.get_otp_expiry()
        self.otp_attempts = 0
        return self.password_reset_otp

    def verify_password_reset_otp(self, otp: str) -> Tuple[bool, str]:
        """
        Verify password reset OTP
        Returns: (success, message)
        """
        # Check if OTP was generated
        if not self.password_reset_otp:
            return False, "No OTP generated. Please request a new one."

        # Check expiry
        if PasswordRecoveryManager.is_otp_expired(self.otp_expiry):
            self.clear_otp_data()
            return False, "OTP expired. Please request a new one."

        # Check attempts
        if self.otp_attempts >= PasswordRecoveryManager.MAX_OTP_ATTEMPTS:
            self.clear_otp_data()
            return False, "Maximum attempts exceeded. Please request a new OTP."

        # Increment attempts
        self.otp_attempts += 1

        # Verify OTP
        if otp == self.password_reset_otp:
            return True, "OTP verified successfully"
        else:
            remaining = PasswordRecoveryManager.MAX_OTP_ATTEMPTS - self.otp_attempts
            return False, f"Invalid OTP. {remaining} attempt(s) remaining."

    def reset_password(self, new_password: str) -> Tuple[bool, str]:
        """
        Reset password after OTP verification
        Returns: (success, message)
        """
        # Validate password
        is_valid, message = PasswordRecoveryManager.validate_password(new_password)
        if not is_valid:
            return False, message

        # Update password
        self.password = new_password
        self.clear_otp_data()

        return True, "Password reset successfully"

    def clear_otp_data(self):
        """Clear OTP-related data"""
        self.password_reset_otp = None
        self.otp_expiry = None
        self.otp_attempts = 0

    def get_password_recovery_dict(self) -> dict:
        """Get password recovery data as dictionary for serialization"""
        return {
            "security_question": self.security_question,
            "security_answer": self.security_answer,
            "password_reset_otp": self.password_reset_otp,
            "otp_expiry": self.otp_expiry.isoformat() if self.otp_expiry else None,
            "otp_attempts": self.otp_attempts,
        }

    def load_password_recovery_dict(self, data: dict):
        """Load password recovery data from dictionary"""
        self.security_question = data.get("security_question")
        self.security_answer = data.get("security_answer")
        self.password_reset_otp = data.get("password_reset_otp")

        if data.get("otp_expiry"):
            self.otp_expiry = datetime.fromisoformat(data["otp_expiry"])
        else:
            self.otp_expiry = None

        self.otp_attempts = data.get("otp_attempts", 0)


class PasswordRecoveryUI:
    """UI components for password recovery flows"""

    @staticmethod
    def setup_security_question_flow(customer) -> bool:
        """
        Interactive flow to setup security question
        Returns: True if successful
        """
        print("\n" + "=" * 60)
        print("SETUP SECURITY QUESTION")
        print("=" * 60)
        print("\nPlease select a security question for password recovery:")

        PasswordRecoveryManager.display_security_questions()

        num_questions = len(PasswordRecoveryManager.SECURITY_QUESTIONS)

        while True:
            try:
                choice = int(input(f"\nSelect question (1-{num_questions}): "))
                question = PasswordRecoveryManager.get_security_question_by_index(
                    choice
                )

                if question:
                    break
                else:
                    print(f"[FAIL] Please enter a number between 1 and {num_questions}")
            except ValueError:
                print("[FAIL] Invalid input. Please enter a number.")

        answer = input(f"\n{question}\nYour Answer: ").strip()

        if not answer:
            print("[FAIL] Answer cannot be empty")
            return False

        if customer.set_security_question(question, answer):
            print("[SUCCESS] Security question set successfully")
            return True
        else:
            print("[FAIL] Failed to set security question")
            return False

    @staticmethod
    def forgot_password_flow(bank) -> bool:
        """
        Complete forgot password flow
        Returns: True if password was reset successfully
        """
        print("\n" + "=" * 60)
        print("FORGOT PASSWORD")
        print("=" * 60)

        # Step 1: Get Customer ID
        customer_id = input("\nEnter your Customer ID: ").strip()
        if not customer_id:
            print("[FAIL] Customer ID is required")
            input("\nPress Enter to continue...")
            return False

        customer = bank.get_customer(customer_id)
        if not customer:
            print("[FAIL] Customer not found")
            input("\nPress Enter to continue...")
            return False

        # Step 2: Check if security question exists (legacy customer handling)
        if not customer.has_security_question():
            return PasswordRecoveryUI.legacy_customer_password_reset(customer, bank)

        # Step 3: Verify Security Question
        print(f"\nSecurity Question: {customer.security_question}")
        answer = input("Your Answer: ").strip()

        if not customer.verify_security_answer(answer):
            print("[FAIL] Incorrect answer. Password reset failed.")
            input("\nPress Enter to continue...")
            return False

        print("[SUCCESS] Security answer verified!")

        # Step 4: OTP Verification
        if not PasswordRecoveryUI.otp_verification_flow(customer):
            return False

        # Step 5: Set New Password
        if PasswordRecoveryUI.set_new_password_flow(customer):
            DataStore.save_customers(bank.customers)  # ← FIXED
            return True

        return False

    @staticmethod
    def otp_verification_flow(customer) -> bool:
        """
        OTP verification flow
        Returns: True if OTP verified successfully
        """
        # Generate OTP
        otp = customer.generate_password_reset_otp()

        print("\n" + "=" * 60)
        print("OTP VERIFICATION")
        print("=" * 60)
        print("\n📧 OTP sent to registered email/phone")
        print(f"🔐 Your OTP: {otp}")  # In production, send via email/SMS
        print(f"⏰ Valid for {PasswordRecoveryManager.OTP_VALIDITY_MINUTES} minutes")
        print(f"🔢 You have {PasswordRecoveryManager.MAX_OTP_ATTEMPTS} attempts")

        # Verify OTP
        for attempt in range(PasswordRecoveryManager.MAX_OTP_ATTEMPTS):
            otp_input = input(
                f"\nEnter OTP (Attempt {attempt + 1}/{PasswordRecoveryManager.MAX_OTP_ATTEMPTS}): "
            ).strip()

            success, message = customer.verify_password_reset_otp(otp_input)

            if success:
                print(f"[SUCCESS] {message}")
                return True
            else:
                print(f"[FAIL] {message}")

        input("\nPress Enter to continue...")
        return False

    @staticmethod
    def set_new_password_flow(customer) -> bool:
        """
        Set new password flow
        Returns: True if password set successfully
        """
        print("\n" + "=" * 60)
        print("SET NEW PASSWORD")
        print("=" * 60)
        print("\nPassword Requirements:")
        print(f"  • Minimum {PasswordRecoveryManager.MIN_PASSWORD_LENGTH} characters")
        print("  • Avoid using personal information")

        max_attempts = 3
        for attempt in range(max_attempts):
            new_password = input("\nEnter new password: ").strip()
            confirm_password = input("Confirm new password: ").strip()

            if new_password != confirm_password:
                print("[FAIL] Passwords do not match. Try again.")
                if attempt < max_attempts - 1:
                    continue
                else:
                    input("\nPress Enter to continue...")
                    return False

            success, message = customer.reset_password(new_password)

            if success:
                print(f"\n[SUCCESS] {message}")
                print("You can now login with your new password.")
                input("\nPress Enter to continue...")
                return True
            else:
                print(f"[FAIL] {message}")

        input("\nPress Enter to continue...")
        return False

    @staticmethod
    def legacy_customer_password_reset(customer, bank) -> bool:
        """
        Handle password reset for legacy customers without security questions
        Returns: True if successful
        """
        print("\n" + "=" * 60)
        print("[WARN]  LEGACY ACCOUNT DETECTED")
        print("=" * 60)
        print("\nThis account was created before security questions were required.")
        print("\nPassword reset options:")
        print("1. Admin-Assisted Reset (Requires authorization code)")
        print("2. Contact Bank Support")
        print("3. Cancel")

        choice = input("\nSelect option: ").strip()

        if choice == "1":
            return PasswordRecoveryUI.admin_assisted_reset(customer, bank)
        elif choice == "2":
            print("\n📞 Please contact bank support at:")
            print("   Phone: 1800-XXX-XXXX")
            print("   Email: support@scalabank.com")
            input("\nPress Enter to continue...")
            return False
        else:
            return False

    @staticmethod
    def admin_assisted_reset(customer, bank) -> bool:
        """
        Admin-assisted password reset for legacy accounts
        Returns: True if successful
        """
        print("\n" + "=" * 60)
        print("ADMIN-ASSISTED PASSWORD RESET")
        print("=" * 60)

        admin_code = input("\nEnter admin authorization code: ").strip()

        if admin_code != PasswordRecoveryManager.ADMIN_CODE:
            print("[FAIL] Invalid authorization code")
            input("\nPress Enter to continue...")
            return False

        print("[SUCCESS] Admin authorization successful")

        # OTP verification
        if not PasswordRecoveryUI.otp_verification_flow(customer):
            return False

        # Set new password
        if not PasswordRecoveryUI.set_new_password_flow(customer):
            return False

        # Prompt to setup security question
        print("\n" + "=" * 60)
        print("[WARN]  SECURITY QUESTION SETUP REQUIRED")
        print("=" * 60)
        print("\nTo enable self-service password reset in the future,")
        print("please setup a security question now.")

        choice = input("\nSetup security question? (y/n): ").strip().lower()

        if choice in ["y", "yes"]:
            if PasswordRecoveryUI.setup_security_question_flow(customer):
                DataStore.save_customers(bank.customers)  # ← FIXED
                print("[SUCCESS] Account security fully updated!")

        input("\nPress Enter to continue...")
        return True

    @staticmethod
    def change_security_question_flow(customer, bank) -> bool:
        """
        Change existing security question
        Returns: True if successful
        """
        print("\n" + "=" * 60)
        print("CHANGE SECURITY QUESTION")
        print("=" * 60)

        if not customer.has_security_question():
            print("\n[WARN]  No security question currently set.")
            return PasswordRecoveryUI.setup_security_question_flow(customer)

        print(f"\nCurrent Question: {customer.security_question}")

        # Verify current answer
        answer = input("\nVerify current answer: ").strip()
        if not customer.verify_security_answer(answer):
            print("[FAIL] Incorrect answer. Cannot change security question.")
            input("\nPress Enter to continue...")
            return False

        print("[SUCCESS] Verified!")

        # Setup new question
        if PasswordRecoveryUI.setup_security_question_flow(customer):
            DataStore.save_customers(bank.customers)  # ← FIXED
            print("\n[SUCCESS] Security question updated successfully!")
            input("\nPress Enter to continue...")
            return True

        return False

    @staticmethod
    def prompt_legacy_customer_setup(customer, bank) -> bool:
        """
        Prompt legacy customer to setup security question on login
        Returns: True if setup completed
        """
        print("\n" + "=" * 60)
        print("[SECURE] SECURITY SETUP REQUIRED")
        print("=" * 60)
        print("\nFor account security, please set up a security question.")
        print("This helps you recover your password if you forget it.")
        print("=" * 60)

        print("\n" + "=" * 60)
        print("[WARN]  SECURITY SETUP REQUIRED")
        print("=" * 60)
        print("\nFor account security, please setup a security question.")
        print("This is required for password recovery.")

        choice = input("\nSetup now? (y/n): ").strip().lower()

        if choice in ["y", "yes"]:
            if PasswordRecoveryUI.setup_security_question_flow(customer):
                DataStore.save_customers(bank.customers)  # ← FIXED
                print("\n[SUCCESS] Security question setup complete!")
                input("\nPress Enter to continue...")
                return True
            else:
                print(
                    "\n[WARN]  You can setup security question later from Account Settings"
                )
                input("\nPress Enter to continue...")
                return False
        else:
            print("\n[WARN]  Reminder: Setup security question from Account Settings")
            print("    to enable password recovery feature.")
            input("\nPress Enter to continue...")
            return False
