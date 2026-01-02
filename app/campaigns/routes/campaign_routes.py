import json
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from starlette import status
from starlette.responses import JSONResponse

from campaigns.services.attachment_service import AttachmentService
from campaigns.services.campaign_service import CampaignService
from campaigns.services.recipient_service import RecipientService
from subscriptions.services.subscription_service import SubscriptionService
from users.dependencies.get_current_user import get_current_user
from users.models.user import User


campaign_router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@campaign_router.post("/start")
async def start_campaign(
    body: Annotated[str, Form(..., min_length=10)],
    files: Annotated[list[UploadFile], File([])],
    current_user: Annotated[User, Depends(get_current_user)],
    subscription_service: Annotated[SubscriptionService, Depends()],
    attachment_service: Annotated[AttachmentService, Depends()],
    recipient_service: Annotated[RecipientService, Depends()],
    campaign_service: Annotated[CampaignService, Depends()],
) -> None:
    campaign_data = json.loads(body) if body else {}

    recipients = campaign_data.get("recipients", [])

    if not recipients:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Please provide recipients",
        )

    can_send, message = await subscription_service.check_if_user_can_send_emails(
        user=current_user,
        current_recipients_count=len(recipients),
    )

    if not can_send:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message
        )

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
        prepared_attachment = await attachment_service.prepare_attachment_for_gmail(file)

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
        camp_date = campaign_data.get("date")
        camp_time = campaign_data.get("time")

        naive_datetime = datetime.strptime(f"{camp_date} {camp_time}", "%Y-%m-%d %H:%M")
        user_timezone = timezone(campaign_data.get("timezone"))

        scheduled_datetime = user_timezone.localize(naive_datetime)
        email_data = {
            "sender_email": sender_email,
            "sender_name": sender_name,
            "recipients": recipients,
            "subject": subject,
            "body_template": body_template,
            "attachments": prep_attachments,
        }

        task = send_campaign.apply_async(
            args=[email_data], queue="email_campaigns", eta=scheduled_datetime
        )

        return JSONResponse(
            content=""
        )

    else:
        await mass_email_campaign(
            sender=sender_email,
            recipients=recipients,
            subject=subject,
            body_template=body_template,
            attachments=prep_attachments,
            sender_name=sender_name,
        )
        print(f"Рассылка начата в {datetime.now().strftime('%Y-%m-%d %H:%M')}.")

        return JSONResponse(
            content=
        )


@campaign_router.get("/all")
async def get_all_campaigns(
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    return JSONResponse({
        "campaigns": current_user.campaigns,
    })


@campaign_router.get("/statistics")
async def get_campaigns_statistics(
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    campaigns = current_user.campaigns

    recipients_count = 0
    for campaign in campaigns:
        recipients_count += len(campaign.recipients)

    return JSONResponse({
        "campaigns_count": len(campaigns),
        "recipients_count": len(recipients_count),
    })
