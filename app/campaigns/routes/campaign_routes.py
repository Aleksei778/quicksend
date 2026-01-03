import json
from datetime import datetime
from typing import Annotated, Optional
import pytz
from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from starlette import status
from starlette.responses import JSONResponse

from campaigns.services.attachment_service import (
    AttachmentService,
    get_attachment_service,
)
from campaigns.services.campaign_service import CampaignService, get_campaign_service
from campaigns.services.recipient_service import RecipientService, get_recipient_service
from google_integration.gmail.services.gmail_service import (
    GoogleGmailService,
    get_google_gmail_service,
)
from subscriptions.services.subscription_service import (
    SubscriptionService,
    get_subscription_service,
)
from users.dependencies.get_current_user import get_current_user
from users.models.user import User
from campaigns.tasks.send_emails_task import send_emails_task


campaign_router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@campaign_router.post("/start")
async def start_campaign(
    body: Annotated[str, Form(..., min_length=10)],
    files: Annotated[Optional[list[UploadFile]], None],
    current_user: Annotated[User, Depends(get_current_user)],
    attachment_service: Annotated[AttachmentService, Depends(get_attachment_service)],
    recipient_service: Annotated[RecipientService, Depends(get_recipient_service)],
    campaign_service: Annotated[CampaignService, Depends(get_campaign_service)],
    subscription_service: Annotated[
        SubscriptionService, Depends(get_subscription_service)
    ],
    google_gmail_service: Annotated[
        GoogleGmailService, Depends(get_google_gmail_service)
    ],
) -> JSONResponse:
    campaign_data = json.loads(body) if body else {}

    recipients = campaign_data.get("recipients", [])

    if not recipients:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Please provide recipients",
        )

    can_send, message = await subscription_service.check_if_user_can_send_emails(
        current_user
    )

    if not can_send:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)

    sender_name = f"{current_user.first_name} {current_user.last_name}"
    subject = campaign_data.get("subject", "")
    body_template = campaign_data.get("body", "")

    campaign = await campaign_service.create_campaign_for_user(
        sender_name=sender_name,
        subject=subject,
        body_template=body_template,
        user=current_user,
    )

    campaign_attachments = []
    for file in files:
        prepared_attachment = await attachment_service.prepare_attachment_for_gmail(
            file
        )

        campaign_attachment = await attachment_service.create_attachment(
            campaign=campaign,
            filename=prepared_attachment["filename"],
            size=prepared_attachment["size"],
            mimetype=prepared_attachment["mimetype"],
            content=prepared_attachment["content"],
        )
        campaign_attachments.append(campaign_attachment)

    campaign_recipients = []
    for recipient in recipients:
        campaign_recipient = await recipient_service.create_recipient(
            campaign=campaign,
            email=recipient["email"],
        )

        campaign_recipients.append(campaign_recipient)

    if campaign_data.get("date") and campaign_data.get("time"):
        scheduled_datetime = campaign_service.process_time_for_campaign_time(
            campaign_date=campaign_data.get("date"),
            campaign_time=campaign_data.get("time"),
            user_timezone_str=current_user.timezone,
        )
    else:
        scheduled_datetime = datetime.now(pytz.utc)

    send_emails_task.apply_async(
        args=[campaign, campaign_service, subscription_service, google_gmail_service],
        queue="email_campaigns",
        eta=scheduled_datetime,
    )

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": "Campaign successfully created"},
    )


@campaign_router.get("/all")
async def get_all_campaigns(
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "campaigns": current_user.campaigns,
        },
    )


@campaign_router.get("/statistics")
async def get_campaigns_statistics(
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    campaigns = current_user.campaigns

    recipients_count = 0
    for campaign in campaigns:
        recipients_count += len(campaign.recipients)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "campaigns_count": len(campaigns),
            "recipients_count": len(recipients_count),
        },
    )
