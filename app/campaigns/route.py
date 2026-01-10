import json
from datetime import datetime
from typing import Annotated, Optional
import pytz
from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, status, File
from fastapi.responses import JSONResponse

from app.campaigns.services.attachment import AttachmentService, get_attachment_service
from app.campaigns.services.campaign import CampaignService, get_campaign_service
from app.campaigns.services.recipient import RecipientService, get_recipient_service
from app.campaigns.services.send import SendService, get_send_service
from app.subscriptions.service import SubscriptionService, get_subscription_service
from app.jwt_auth.dependency import get_current_user
from common.utils.logger import logger
from common.users.model import User
# from campaigns.tasks.send_emails_task import send_emails_task


router = APIRouter(prefix="/campaign", tags=["Campaigns"])


@router.post("/start", response_model=None)
async def start_campaign(
    body: Annotated[str, Form(...)],
    current_user: Annotated[User, Depends(get_current_user)],
    attachment_service: Annotated[AttachmentService, Depends(get_attachment_service)],
    recipient_service: Annotated[RecipientService, Depends(get_recipient_service)],
    campaign_service: Annotated[CampaignService, Depends(get_campaign_service)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
    send_service: Annotated[SendService, Depends(get_send_service)],
    files: Optional[list[UploadFile]] = File(None),
) -> JSONResponse | None:
    campaign_data = json.loads(body) if body else {}
    print('Нет ошибки 1 ')
    logger.info(campaign_data)

    recipients = campaign_data.get("recipients", [])

    if not recipients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
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
    print('Нет ошибки 2')
    campaign_recipients = []
    for recipient in recipients:
        campaign_recipient = await recipient_service.create_recipient(
            campaign=campaign,
            email=recipient,
        )

        campaign_recipients.append(campaign_recipient)

    campaign_attachments = []
    if files:
        for file in files:
            prepared_attachment = await attachment_service.prepare_attachment_for_gmail(file)

            campaign_attachment = await attachment_service.create_attachment(
                campaign=campaign,
                filename=prepared_attachment["filename"],
                size=prepared_attachment["size"],
                mimetype=prepared_attachment["mimetype"],
                content=prepared_attachment["content"],
            )
            campaign_attachments.append(campaign_attachment)

    print('Нет ошибки 3 ')
    if campaign_data.get("date") and campaign_data.get("time") and campaign_data.get("timezone"):
        scheduled_datetime, timezone = campaign_service.process_time_for_campaign_time(
            campaign_date=campaign_data.get("date"),
            campaign_time=campaign_data.get("time"),
            campaign_timezone=campaign_data.get("timezone"),
        )

        await campaign_service.set_started_at_and_timezone_for_campaign(
            campaign=campaign,
            started_at=scheduled_datetime,
            timezone=timezone,
        )

        # send_emails_task.apply_async(
        #     args=[campaign.id, campaign_service, subscription_service, google_gmail_service],
        #     queue="campaigns",
        #     eta=scheduled_datetime,
        # )
    else:
        await campaign_service.set_started_at_and_timezone_for_campaign(
            campaign=campaign,
            started_at=datetime.now(pytz.utc),
            timezone="UTC",
        )

        await send_service.send_campaign(campaign.id)
    print('Нет ошибки 4 ')

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": "Campaign successfully created"},
    )


@router.get("/all")
async def get_all_campaigns(
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "campaigns": current_user.campaigns,
        },
    )


@router.get("/statistics")
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
            "recipients_count": recipients_count,
        },
    )
