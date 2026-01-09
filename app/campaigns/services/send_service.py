from fastapi import Depends
from typing import Annotated

from app.campaigns.models.campaign import Campaign
from app.campaigns.schemas.create_message import CreateMessage
from app.campaigns.services.campaign_service import CampaignService, get_campaign_service
from app.common.kafka.producer import GmailProducer, get_gmail_producer
from app.common.log.logger import logger
from app.google_integration.gmail.services.gmail_service import GoogleGmailService, get_google_gmail_service
from app.subscriptions.services.subscription_service import SubscriptionService, get_subscription_service


class SendService:
    def __init__(
        self,
        campaign_service: CampaignService,
        subscription_service: SubscriptionService,
        google_gmail_service: GoogleGmailService,
        gmail_producer: GmailProducer,
    ) -> None:
        self._campaign_service = campaign_service
        self._subscription_service = subscription_service
        self._google_gmail_service = google_gmail_service
        self._gmail_producer = gmail_producer

    async def send_campaign(self, campaign: Campaign):
        await self._gmail_producer.start_producer()

        for recipient in campaign.recipients:
            can_send, remaining = await self._subscription_service.check_if_user_can_send_emails(
                campaign.user
            )

            if not can_send:
                break

            try:
                raw_message = await self._campaign_service.create_message_with_attachment(
                    CreateMessage(
                        sender_email=campaign.user.email,
                        sender_name=campaign.user.name,
                        recipient=recipient,
                        subject=campaign.subject,
                        body=campaign.body_template,
                        attachments=campaign.attachments,
                        inline_images=None,
                    )
                )

                await self._gmail_producer.send_message_to_kafka(
                    key=campaign.user.email,
                    data={
                        'message': raw_message,
                        'recipient': recipient
                    },
                )

                await self._campaign_service.increment_user_sent_count(campaign.user)

            except Exception as e:
                logger.error(f"Failed to send to {recipient}: {str(e)}")

        logger.info(
            f"Campaign completed for user {campaign.user}: "
        )


async def get_send_service(
    campaign_service: Annotated[CampaignService, Depends(get_campaign_service)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
    google_gmail_service: Annotated[GoogleGmailService, Depends(get_google_gmail_service)],
    gmail_producer: Annotated[GmailProducer, Depends(get_gmail_producer)]
) -> SendService:
    return SendService(
        campaign_service=campaign_service,
        subscription_service=subscription_service,
        google_gmail_service=google_gmail_service,
        gmail_producer=gmail_producer,
    )
