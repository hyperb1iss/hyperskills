"""Loyalty points earned on purchases."""

TIER_MULTIPLIERS = {"standard": 1, "silver": 2, "gold": 3}
SIGNUP_BONUS = 250


def multiplier_for(tier):
    try:
        return TIER_MULTIPLIERS[tier]
    except KeyError:
        raise ValueError(f"unknown loyalty tier {tier!r}") from None


def points_for(amount, tier="standard"):
    """Points for a purchase amount in integer cents: one per whole dollar, times the tier multiplier."""
    whole_dollars = amount // 100
    return whole_dollars * multiplier_for(tier)


def points_after_purchase(balance, amount, tier="standard", first_order=False):
    earned = points_for(amount, tier)
    if first_order:
        earned += SIGNUP_BONUS
    return balance + earned
