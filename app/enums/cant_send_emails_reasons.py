from enum import Enum


class CantSendEmailsReasons(Enum):
    NO_SUBSCRIPTIONS = "No subscriptions"
    NO_ACTIVE_SUBSCRIPTION = "No active subscription"
    LIMIT_EXCEEDED = "Limit exceeded"
    CAN_SEND_EMAILS = "Can send emails"
