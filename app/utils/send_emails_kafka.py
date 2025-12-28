from email.mime import text, image, multipart, base
from email.header import Header
from email.utils import make_msgid
import base64
import os
from datetime import datetime
import logging
from aiokafka import AIOKafkaProducer
import json
from email.encoders import encode_base64
from fastapi import UploadFile

from common.config import KAFKA_TOPIC, KAFKA_PRODUCER_CONFIG


def setup_logging():
    log_directory = "logs"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_directory, f"email_campaign_{timestamp}.log")

    logger = logging.getLogger("email_campaign")
    logger.setLevel(logging.INFO)

    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5
    )

    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger


logger = setup_logging()


# ---- ТЕСТОВАЯ ЧАСТЬ ДЛЯ РАССЫЛКИ ---
async def get_kafka_producer():
    print("hello get_kafka_producer")
    producer = AIOKafkaProducer(**KAFKA_PRODUCER_CONFIG)
    await producer.start()
    return producer


async def prepare_attachment_for_gmail(file: UploadFile) -> dict:
    content = await file.read()

    filename = file.filename
    encoded_filename = None

    if not all(ord(c) < 128 for c in filename):
        filename_encoded = filename.encode("utf-8")
        encoded_filename = "".join(["%{:02x}".format(b) for b in filename_encoded])

    mime_part = base.MIMEBase("application", "octet-stream")
    mime_part.set_payload(content)
    encode_base64(mime_part)

    mime_part.add_header("Content-Disposition", f'attachment; filename="{filename}"')

    return {
        "filename": filename,
        "encoded_filename": encoded_filename,
        "content_type": file.content_type,
        "mime_part": mime_part,
        "size": len(content),
        # Сохраняем закодированное содержимое для Gmail API
        "encoded_content": base64.urlsafe_b64encode(content).decode("utf-8"),
    }


async def send_message_to_kafka(producer, user_id, message_data):
    print("hello send_message_to_kafka")
    print(type(message_data))
    await producer.send_and_wait(
        KAFKA_TOPIC,
        json.dumps(message_data).encode("utf-8"),
        key=str(user_id).encode("utf-8"),
    )


async def create_message_with_attachment(
    sender, recipient, subject, body, sender_name, attachments=None, inline_images=None
):
    msg = multipart.MIMEMultipart()
    msg["From"] = f"{sender_name} <{sender}>"
    msg["To"] = recipient
    msg["Subject"] = Header(f"{subject}", "utf-8")
    msg["Message-ID"] = make_msgid()

    msg.attach(
        text.MIMEText(body, "html")
    )  # можно 'html' вместо 'plain' , чтобы поддерживать форматироание текста

    total_size = 0
    max_size = 25 * 1024 * 1024

    if inline_images:
        for img_id, img_path in inline_images.items():
            with open(img_path, "rb") as img:
                img_data = img.read()
                total_size += len(img_data)
                if total_size > max_size:
                    logger.warning(f"Skipping inline image {img_id} due to size limit")
                    continue
                img_part = image.MIMEImage(img_data)
                img_part.add_header("Content-ID", f"<{img_id}>")
                img_part.add_header("Content-Disposition", "inline")
                msg.attach(img_part)

    if attachments:
        for attachment in attachments:
            part = base.MIMEBase("application", "octet-stream")
            # Используем уже закодированные данные
            part.set_payload(base64.urlsafe_b64decode(attachment["data"]))
            encode_base64(part)

            if attachment.get("encoded_filename"):
                disposition_str = (
                    f"attachment; filename*=UTF-8''{attachment['encoded_filename']}"
                )
                part.add_header("Content-Disposition", disposition_str)
            else:
                # Для ASCII имён используем обычный формат
                part.add_header(
                    "Content-Disposition", "attachment", filename=attachment["filename"]
                )

            msg.attach(part)

    raw_msg = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    return {"raw": raw_msg}


async def mass_email_campaign(
    sender, recipients, subject, body_template, attachments, sender_name
):
    user_id = sender
    print("Hello, mass email_campaign")

    producer = await get_kafka_producer()

    print("producer is started")

    successful_count = 0
    failed_count = 0

    for i, recipient in enumerate(recipients):
        raw = await create_message_with_attachment(
            sender=sender,
            recipient=recipient,
            subject=subject,
            body=body_template,
            attachments=attachments,
            sender_name=sender_name,
        )

        print(
            f"user_id: {type(user_id)}, message: {type(raw)}, message_num: {type(i)}, recipient: {type(recipient)}"
        )
        print(str(user_id))

        message_data = {
            "user_id": user_id,
            "message": raw,
            "message_num": i,
            "recipient": recipient,
        }
        print("message_data is ready")
        print(type(message_data))

        await send_message_to_kafka(producer, user_id, message_data)
        print("send_message_to_kafka")

    await producer.stop()
    logger.info(
        f"Campaign completed. Sent {successful_count} emails successfully. Failed to send {failed_count} emails."
    )
