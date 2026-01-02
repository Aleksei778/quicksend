import json
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from starlette import status
from starlette.responses import JSONResponse

from campaigns.services.attachment_service import AttachmentService
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
) -> None:
    campaign_data = json.loads(body) if body else {}
    recipients = campaign_data.get("recipients", [])

    can_send, message = await subscription_service.check_if_user_can_send_emails(current_user, len(recipients))

    if not can_send:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message
        )

    for file in files:
        prepared_attachment = await attachment_service.prepare_attachment_for_gmail(file)
        attachments.append(prepared_attachment)

    sender_email = current_user.email
    sender_name = f"{current_user.first_name} {current_user.last_name}"
    subject = campaign_data.get("subject", "")
    body_template = campaign_data.get("body", "")

    prep_attachments = [
        {
            "filename": att["filename"],
            "content_type": att["content_type"],
            "size": att["size"],
            "data": att["encoded_content"],
        }
        for att in attachments
    ]
    attachment_paths = [
        prep_attachment["filename"] for prep_attachment in prep_attachments
    ]

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
        print(email_data)
        print(scheduled_datetime)
        task = send_campaign.apply_async(
            args=[email_data], queue="email_campaigns", eta=scheduled_datetime
        )

        print(f"Рассылка запланирована на {camp_date} {camp_time}.")
        await db_manager.create_campaign(
            sender_name=sender_name,
            subject=subject,
            body_template=body_template,
            recipients=recipients,
            attachment_files=attachment_paths,
            campaign_time=naive_datetime,
            user_id=current_user.id,
        )
        return JSONResponse(
            {
                "message": f"Кампания запланирована на {scheduled_datetime.strftime('%Y-%m-%d %H:%M')}",
                "task_id": task.id,
            }
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

        await db_manager.create_campaign(
            sender_name=sender_name,
            subject=subject,
            body_template=body_template,
            recipients=recipients,
            attachment_files=attachment_paths,
            user_id=current_user.id,
        )
        return JSONResponse(
            {
                "message": f"Кампания запущена в {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            }
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
