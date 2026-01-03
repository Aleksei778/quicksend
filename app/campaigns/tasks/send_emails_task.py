import time
from datetime import datetime

from campaigns.models.campaign import Campaign
from campaigns.schemas.create_message import CreateMessage
from campaigns.services.campaign_service import CampaignService
from common.celery.celery_app import celery_app
from common.log.logger import logger
from google_integration.gmail.services.gmail_service import GoogleGmailService
from subscriptions.services.subscription_service import SubscriptionService


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
async def send_emails_task(
    campaign: Campaign,
    subscription_service: SubscriptionService,
    campaign_service: CampaignService,
    google_gmail_service: GoogleGmailService,
):
    results = {
        "total": len(campaign.recipients),
        "sent": 0,
        "failed": 0,
        "errors": [],
        "message_ids": [],
    }

    for recipient in campaign.recipients:
        can_send, remaining = await subscription_service.check_if_user_can_send_emails(
            campaign.user
        )

        if not can_send:
            results["errors"].append(
                {"recipient": recipient, "error": "Daily limit reached during campaign"}
            )
            results["failed"] += 1
            break

        try:
            raw_message = await campaign_service.create_message_with_attachment(
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

            response = await google_gmail_service.send_email_via_gmail(
                user=campaign.user,
                raw=raw_message,
            )

            await campaign_service.increment_user_sent_count(campaign.user)

            results["sent"] += 1
            results["message_ids"].append(response.get("id"))

            logger.info(f"Email sent to {recipient}. Message ID: {response.get('id')}")

            time.sleep(0.5)

        except Exception as e:
            results["failed"] += 1
            results["errors"].append({"recipient": recipient, "error": str(e)})

            logger.error(f"Failed to send to {recipient}: {str(e)}")

    logger.info(
        f"Campaign completed for user {campaign.user}: "
        f"{results['sent']} sent, {results['failed']} failed"
    )

    return {
        "status": "completed",
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": campaign.user.id,
        "results": results,
    }
