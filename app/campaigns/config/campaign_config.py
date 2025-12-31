from pydantic_settings import BaseSettings, SettingsConfigDict


class CampaignSettings(BaseSettings):
    IMAGE_MAX_SIZE: int = 25 * 1024 * 1024

campaign_settings = CampaignSettings()
