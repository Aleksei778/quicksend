from pydantic_settings import BaseSettings


class CampaignConfig(BaseSettings):
    IMAGE_MAX_SIZE: int = 25 * 1024 * 1024


campaign_config = CampaignConfig()
