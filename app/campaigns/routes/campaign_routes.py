import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from starlette import status

from subscriptions.services.subscription_service import SubscriptionService
from users.dependencies.get_current_user import get_current_user
from users.models.user import User

campaign_router = APIRouter(name="/campaigns", tags=["Campaigns"])

@campaign_router.post("/start")
async def start_campaign(
    body: Annotated[str, Form(..., min_length=10)],
    files: Annotated[list[UploadFile], File([])],
    current_user: Annotated[User, Depends(get_current_user)],
    subscription_service: Annotated[SubscriptionService, Depends()],
) -> None:
    campaign_data = json.loads(body) if body else {}
    recipients = campaign_data.get("recipients", [])

    can_send, message = await subscription_service.check_if_user_can_send_emails(current_user, len(recipients))

    if not can_send:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message
        )

    attachments = []
    if files:
        for file in files:
            attachment_data = await prepare_attachment_for_gmail(file)
            attachments.append(attachment_data)

    print("Hello, run_campaign")
    print(f"current_user: {current_user}")

    sender_email = current_user.email
    sender_name = f"{current_user.first_name} {current_user.last_name}"
    subject = campaign_data.get("subject", "")  # Добавляем значение по умолчанию
    body_template = campaign_data.get("body", "")  # Добавляем значение по умолчанию

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

@send_router.get("/all-campaigns")
async def get_all_campaigns(
    request: Request,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    db_manager = DBManager(session=db)

    campaigns = await db_manager.get_all_campaigns(user_id=current_user.id)

    new_campaigns = []
    total_recipients = 0

    for camp in campaigns:
        new_camp = {}

        recipients_list = camp.recipients.split(",")
        attachment_files_list = camp.attachment_files.split(",")
        date_str = camp.campaign_time.date().isoformat()
        recipients_cnt = len(recipients_list)

        total_recipients += recipients_cnt

        new_camp["name"] = camp.subject
        new_camp["date"] = date_str
        new_camp["recipients_cnt"] = recipients_cnt
        new_camp["attachments"] = attachment_files_list

        new_campaigns.append(new_camp)

    return {"campaigns": new_campaigns}


@send_router.get("/campaigns-stat")
async def get_camps_stat(
    request: Request,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    db_manager = DBManager(session=db)

    campaigns = await db_manager.get_all_campaigns(user_id=current_user.id)

    total_camps = len(campaigns)
    total_resips = 0

    for camp in campaigns:
        recipients_list = camp.recipients.split(",")
        recipients_cnt = len(recipients_list)

        total_resips += recipients_cnt

    return {"campaigns_count": total_camps, "recipients_count": total_resips}

