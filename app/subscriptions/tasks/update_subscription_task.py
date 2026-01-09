import time
from datetime import datetime

from kombu import Queue, Exchange

from app.campaigns.models.campaign import Campaign
from app.campaigns.schemas.create_message import CreateMessage
from app.campaigns.services.campaign_service import CampaignService
from app.common.celery.celery_app import celery_app
from app.common.log.logger import logger
from app.google_integration.gmail.services.gmail_service import GoogleGmailService


subscriptions_exchange = Exchange(name="subscriptions", type="direct")
subscriptions_queue = Queue(
    name="subscriptions",
    exchange=subscriptions_exchange,
    routing_key="subscriptions",
)
