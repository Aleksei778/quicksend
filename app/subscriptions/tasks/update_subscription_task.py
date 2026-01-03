import time
from datetime import datetime

from kombu import Queue, Exchange

from campaigns.models.campaign import Campaign
from campaigns.schemas.create_message import CreateMessage
from campaigns.services.campaign_service import CampaignService
from common.celery.celery_app import celery_app
from common.log.logger import logger
from google_integration.gmail.services.gmail_service import GoogleGmailService


subscriptions_exchange = Exchange(name="subscriptions", type="direct")
subscriptions_queue = Queue(
    name="subscriptions",
    exchange=subscriptions_exchange,
    routing_key="subscriptions",
)
