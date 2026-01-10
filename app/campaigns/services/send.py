from fastapi import Depends
from typing import Annotated

from app.campaigns.schema import CreateMessage
from app.campaigns.services.campaign import CampaignService, get_campaign_service
from app.utils.kafka.producer import GmailProducer, get_gmail_producer
from app.subscriptions.service import SubscriptionService, get_subscription_service
from common.utils.logger import logger
from common.google.gmail.service import GoogleGmailService, get_google_gmail_service


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

    async def send_campaign(self, campaign_id: int):
        campaign = await self._campaign_service.eager_get_campaign_for_sending(campaign_id)

        if not campaign:
            raise Exception(
                f"SendService:send_campaign: not found campaign with id {campaign_id}"
            )

        await self._gmail_producer.start_producer()

        for recipient in campaign.recipients:
            can_send, remaining = await self._subscription_service.check_if_user_can_send_emails(campaign.user)

            if not can_send:
                break

            try:
                raw_message = await self._campaign_service.create_message_with_attachment(
                    CreateMessage(
                        sender_email=campaign.user.email,
                        sender_name=f"{campaign.user.first_name} {campaign.user.last_name}",
                        recipient=recipient.email,
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
                        'recipient': recipient.email
                    },
                )

                await self._campaign_service.increment_user_sent_count(campaign.user)

            except Exception as e:
                logger.error(f"Failed to send to {recipient.email}: {str(e)}")

        await self._gmail_producer.stop_producer()

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
