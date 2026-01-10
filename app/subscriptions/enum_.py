from enum import Enum
import calendar
from datetime import datetime


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

    def get_days_count(self) -> int:
        year = datetime.today().year
        month = datetime.today().month

        match self:
            case self.TRIAL:
                return 10
            case self.STANDARD, self.PREMIUM:
                return calendar.monthrange(year, month)[1]
            case _:
                raise ValueError(
                    "SubscriptionPlan:get_days_count: Invalid subscription plan"
                )
