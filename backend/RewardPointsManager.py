from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from Card import CreditCard


class RewardPointsManager:
    """Manage credit card reward points - earning, redemption, and tracking"""

    # Redemption rates
    REDEMPTION_RATE = 1  # 1 point = Rs. 0.25
    MIN_REDEMPTION_POINTS = 100  # Minimum 100 points to redeem

    # Earning rates (can vary by card type in future)
    BASE_EARNING_RATE = 0.01  # 1% = 1 point per Rs. 100 spent

    @staticmethod
    def calculate_points_value(points: float) -> float:
        """
        Calculate monetary value of reward points

        Args:
            points: Number of reward points

        Returns:
            Monetary value in rupees
        """
        return points * RewardPointsManager.REDEMPTION_RATE

    @staticmethod
    def calculate_required_points(amount: float) -> float:
        """
        Calculate points required for a specific amount

        Args:
            amount: Amount in rupees

        Returns:
            Number of points needed
        """
        return amount / RewardPointsManager.REDEMPTION_RATE

    @staticmethod
    def can_redeem(card: "CreditCard", points: float) -> Tuple[bool, str]:
        """
        Check if points can be redeemed

        Args:
            card: Credit card object
            points: Points to redeem

        Returns:
            (can_redeem, reason)
        """
        if points < RewardPointsManager.MIN_REDEMPTION_POINTS:
            return (
                False,
                f"Minimum {RewardPointsManager.MIN_REDEMPTION_POINTS} points required for redemption",
            )

        if points > card.reward_points:
            return (False, f"Insufficient points. Available: {card.reward_points:.0f}")

        # Check if card is active
        if card.blocked:
            return (False, "Card is blocked. Cannot redeem points")

        if card.is_expired():
            return (False, "Card has expired. Cannot redeem points")

        return (True, "Valid redemption")

    @staticmethod
    def redeem_for_bill_payment(
        card: "CreditCard", points: float, outstanding_amount: float
    ) -> Tuple[bool, str, float]:
        """
        Redeem points towards credit card bill payment

        Args:
            card: Credit card object
            points: Points to redeem
            outstanding_amount: Current outstanding amount on card

        Returns:
            (success, message, redemption_value)
        """
        # Validate redemption
        can_redeem, reason = RewardPointsManager.can_redeem(card, points)
        if not can_redeem:
            return (False, reason, 0.0)

        # Calculate redemption value
        redemption_value = RewardPointsManager.calculate_points_value(points)

        # Can't redeem more than outstanding
        if redemption_value > outstanding_amount:
            max_points = RewardPointsManager.calculate_required_points(
                outstanding_amount
            )
            return (
                False,
                f"Redemption value (Rs. {redemption_value:.2f}) exceeds outstanding amount (Rs. {outstanding_amount:.2f}). Maximum redeemable: {max_points:.0f} points",
                0.0,
            )

        # Deduct points from card
        card.reward_points -= points

        # Record redemption in history
        if not hasattr(card, "redemption_history"):
            card.redemption_history = []

        from BankClock import BankClock

        card.redemption_history.append(
            {
                "date": BankClock.today().isoformat(),
                "points_redeemed": points,
                "redemption_value": redemption_value,
                "redemption_type": "BILL_PAYMENT",
                "remaining_points": card.reward_points,
            }
        )

        return (
            True,
            f"Successfully redeemed {points:.0f} points for Rs. {redemption_value:.2f}",
            redemption_value,
        )

    @staticmethod
    def get_redemption_options(card: "CreditCard", outstanding_amount: float) -> dict:
        """
        Get various redemption options for a card

        Args:
            card: Credit card object
            outstanding_amount: Current outstanding amount

        Returns:
            Dictionary with redemption options
        """
        available_points = card.reward_points
        max_redeemable_value = min(
            RewardPointsManager.calculate_points_value(available_points),
            outstanding_amount,
        )
        max_redeemable_points = RewardPointsManager.calculate_required_points(
            max_redeemable_value
        )

        options = {
            "available_points": available_points,
            "points_value": RewardPointsManager.calculate_points_value(
                available_points
            ),
            "max_redeemable_points": max_redeemable_points,
            "max_redeemable_value": max_redeemable_value,
            "min_redemption_points": RewardPointsManager.MIN_REDEMPTION_POINTS,
            "can_redeem": available_points >= RewardPointsManager.MIN_REDEMPTION_POINTS,
        }

        # Preset options
        if available_points >= RewardPointsManager.MIN_REDEMPTION_POINTS:
            options["presets"] = []

            # 25% of available points
            if available_points * 0.25 >= RewardPointsManager.MIN_REDEMPTION_POINTS:
                points_25 = available_points * 0.25
                value_25 = RewardPointsManager.calculate_points_value(points_25)
                if value_25 <= outstanding_amount:
                    options["presets"].append(
                        {
                            "label": "25% of points",
                            "points": points_25,
                            "value": value_25,
                        }
                    )

            # 50% of available points
            if available_points * 0.50 >= RewardPointsManager.MIN_REDEMPTION_POINTS:
                points_50 = available_points * 0.50
                value_50 = RewardPointsManager.calculate_points_value(points_50)
                if value_50 <= outstanding_amount:
                    options["presets"].append(
                        {
                            "label": "50% of points",
                            "points": points_50,
                            "value": value_50,
                        }
                    )

            # 75% of available points
            if available_points * 0.75 >= RewardPointsManager.MIN_REDEMPTION_POINTS:
                points_75 = available_points * 0.75
                value_75 = RewardPointsManager.calculate_points_value(points_75)
                if value_75 <= outstanding_amount:
                    options["presets"].append(
                        {
                            "label": "75% of points",
                            "points": points_75,
                            "value": value_75,
                        }
                    )

            # All available points (or max redeemable)
            if max_redeemable_points >= RewardPointsManager.MIN_REDEMPTION_POINTS:
                options["presets"].append(
                    {
                        "label": "All points (Maximum)",
                        "points": max_redeemable_points,
                        "value": max_redeemable_value,
                    }
                )

        return options

    @staticmethod
    def show_redemption_summary(card: "CreditCard", limit: int = 10):
        """
        Display redemption history for a card

        Args:
            card: Credit card object
            limit: Number of recent redemptions to show
        """
        if not hasattr(card, "redemption_history") or not card.redemption_history:
            print("\n📊 No redemption history available")
            return

        print("\n" + "=" * 70)
        print("REWARD POINTS REDEMPTION HISTORY")
        print("=" * 70)

        recent_redemptions = card.redemption_history[-limit:]

        total_points_redeemed = 0
        total_value_redeemed = 0

        print(f"\n{'Date':<12} {'Points':<12} {'Value':<15} {'Type':<20} {'Balance'}")
        print("-" * 70)

        for redemption in recent_redemptions:
            date_str = redemption.get("date", "Unknown")[:10]
            points = redemption.get("points_redeemed", 0)
            value = redemption.get("redemption_value", 0)
            r_type = redemption.get("redemption_type", "Unknown")
            balance = redemption.get("remaining_points", 0)

            print(
                f"{date_str:<12} {points:<12.0f} Rs. {value:<12.2f} {r_type:<20} {balance:.0f}"
            )

            total_points_redeemed += points
            total_value_redeemed += value

        print("-" * 70)
        print(
            f"{'TOTAL':<12} {total_points_redeemed:<12.0f} Rs. {total_value_redeemed:<12.2f}"
        )
        print("=" * 70)

        print(
            f"\n💎 Current Balance: {card.reward_points:.0f} points (Rs. {RewardPointsManager.calculate_points_value(card.reward_points):.2f})"
        )

    @staticmethod
    def calculate_earning_potential(
        monthly_spending: float, earning_rate: float = BASE_EARNING_RATE
    ) -> dict:
        """
        Calculate potential reward earnings based on spending

        Args:
            monthly_spending: Expected monthly spending
            earning_rate: Earning rate (default 1%)

        Returns:
            Dictionary with earning projections
        """
        monthly_points = monthly_spending * earning_rate
        annual_points = monthly_points * 12

        monthly_value = RewardPointsManager.calculate_points_value(monthly_points)
        annual_value = RewardPointsManager.calculate_points_value(annual_points)

        return {
            "monthly_spending": monthly_spending,
            "monthly_points": monthly_points,
            "monthly_value": monthly_value,
            "annual_points": annual_points,
            "annual_value": annual_value,
            "earning_rate_percent": earning_rate * 100,
        }


class RewardCatalog:
    """Catalog of reward redemption options (future expansion)"""

    # In future, can add more redemption options like:
    # - Gift vouchers
    # - Shopping discounts
    # - Travel bookings
    # - Cashback to account
    # - Statement credit

    @staticmethod
    def get_available_redemptions() -> list:
        """Get list of available redemption options"""
        return [
            {
                "id": "BILL_PAYMENT",
                "name": "Credit Card Bill Payment",
                "description": "Use points to pay your credit card bill",
                "rate": RewardPointsManager.REDEMPTION_RATE,
                "min_points": RewardPointsManager.MIN_REDEMPTION_POINTS,
                "available": True,
            },
            # Future options can be added here
            # {
            #     "id": "CASHBACK",
            #     "name": "Cashback to Bank Account",
            #     "description": "Transfer point value to your bank account",
            #     "rate": 0.20,  # Lower rate for cashback
            #     "min_points": 500,
            #     "available": False  # Coming soon
            # }
        ]
