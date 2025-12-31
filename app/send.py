from fastapi import APIRouter, Request, Depends, File, UploadFile, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import List
import json
from celery_conf import send_campaign
from pytz import timezone

from utils.send_emails_kafka import mass_email_campaign, prepare_attachment_for_gmail
from common.db.database import get_db
from common.db.database import DBManager
from auth.dependencies import get_current_user

# --- MOSCOW TIMEZONE ---
moscow_tz = timezone("Europe/Moscow")

# --- РОУТЕР ОТПРАВКИ ---
send_router = APIRouter()


@send_router.post("/start-campaign1")
async def run_campaign2(
    files: List[UploadFile] = File(default=None),  # Делаем files необязательным
    body: str = Form(...),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    db_manager = DBManager(session=db)
    print("нет ошибки в start_camp")

    # Проверяем, есть ли тело запроса
    campaign_data = json.loads(body) if body else {}
    recipients = campaign_data.get("recipients", [])

    can_send, message = await db_manager.can_send_emails(current_user, len(recipients))
    print("нет ошибки в start_camp")
    print(f"can_send: {can_send}, message: {message}")
    if not can_send:
        raise HTTPException(status_code=403, detail=message)
    print(campaign_data)

    # Обработка вложений, только если они есть
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


# --- ЗАПУСК РАССЫЛКИ
@send_router.post("/start-campaign")
async def run_campaign1(
    files: List[UploadFile] = File(...),
    body: str = Form(...),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Получаем тело запроса в виде JSON-данных
    db_manager = DBManager(session=db)
    print("нет ошибки в start_camp")
    campaign_data = json.loads(body)
    recipients = campaign_data.get("recipients")

    can_send, message = await db_manager.can_send_emails(current_user, len(recipients))
    print("нет ошибки в start_camp")
    print(f"can_send: {can_send}, message: {message}")
    if not can_send:
        raise HTTPException(status_code=403, detail=message)

    print(campaign_data)
    attachments = []
    for file in files:
        attachment_data = await prepare_attachment_for_gmail(file)
        attachments.append(attachment_data)

    print("Hello, run_campaign")

    # Получаем пользователя из базы данных по user_id
    # Выполняем асинхронный запрос для получения пользователя из базы данных
    print(f"current_user: {current_user}")

    sender_email = current_user.email
    sender_name = f"{current_user.first_name} {current_user.last_name}"
    subject = campaign_data.get("subject")
    body_template = campaign_data.get("body")

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

        # Добавляем кампанию в бд
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
                "message": f"Кампания запланирована на {scheduled_datetime}",
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

        print(f"Рассылка начата в {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.")

        # Добавляем кампанию в бд
        await db_manager.create_campaing(
            sender_name=sender_name,
            subject=subject,
            body_template=body_template,
            recipients=recipients,
            attachment_files=attachment_paths,
            user_id=current_user.id,
        )

        return JSONResponse(
            {
                "message": f"Кампания запущена в {datetime.now()}",
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
