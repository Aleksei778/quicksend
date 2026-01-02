from enum import Enum


class SubscriptionPlan(Enum):
    STANDARD = "standard"
    PREMIUM = "premium"
    TRIAL = "trial"

    def get_recipients_limit(self) -> int:
        match self:
            case self.TRIAL:
                return 50
            case self.STANDARD:
                return 500
            case self.PREMIUM:
                return 2000
            case _:
                raise ValueError(
                    "SubscriptionPlan:get_recipients_limit: Invalid subscription plan"
                )
