from enum import Enum


class CampaignStatus(Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PROCESS = "process"
    SENT = "sent"
    FAILED = "failed"
