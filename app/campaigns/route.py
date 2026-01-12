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
from campaigns.schema import CampaignRequest
from common.users.model import User
from common.utils.logger import logger

# from campaigns.tasks.send_emails_task import send_emails_task


router = APIRouter(prefix="/campaign", tags=["Campaigns"])


@router.post("/start", response_model=None)
async def start_campaign(
    campaign_request: CampaignRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    attachment_service: Annotated[AttachmentService, Depends(get_attachment_service)],
    recipient_service: Annotated[RecipientService, Depends(get_recipient_service)],
    campaign_service: Annotated[CampaignService, Depends(get_campaign_service)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
    send_service: Annotated[SendService, Depends(get_send_service)],
) -> JSONResponse | None:
    logger.info(f"Received campaign request data: {campaign_request.model_dump()}")

    can_send, message = await subscription_service.check_if_user_can_send_emails(
        current_user
    )

    if not can_send:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)

    sender_name = f"{current_user.first_name} {current_user.last_name}"

    campaign = await campaign_service.create_campaign_for_user(
        sender_name=sender_name,
        subject=campaign_request.subject,
        body_template=campaign_request.body,
        user=current_user,
    )

    await recipient_service.bulk_create_recipients(campaign.id, campaign_request.recipients)

    if campaign_request.files:
        await attachment_service.bulk_create_attachments(
            campaign_id=campaign.id,
            files_data=[file.to_dict() for file in campaign_request.files]
        )

    if campaign_request.need_to_schedule():
        scheduled_datetime, timezone = await campaign_service.process_time_for_campaign_time(
            campaign_date=campaign_request.date,
            campaign_time=campaign_request.time,
            campaign_timezone=campaign_request.timezone,
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
