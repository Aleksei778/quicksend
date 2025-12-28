import sys
import os
import asyncio
import logging
from aiokafka import AIOKafkaConsumer
from googleapiclient.errors import HttpError
import json
from sqlalchemy.future import select

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from common.database import get_db2
from google_token_file import get_gmail_service
from common.database import UserOrm
from consumer_config import KAFKA_CONSUMER_CONFIG, KAFKA_TOPIC

# Логирование
logger = logging.getLogger(__name__)


async def process_kafka_messages():
    consumer = AIOKafkaConsumer(KAFKA_TOPIC, **KAFKA_CONSUMER_CONFIG)
    await consumer.start()

    try:
        async for msg in consumer:
            message_data = json.loads(msg.value.decode("utf-8"))
            # Проверяем, что сообщение пришло от пользователя
            user_id = msg.key.decode("utf-8")
            print(user_id)
            logger.info(f"Processing message for user {user_id}")

            await send_email_via_gmail(user_id, message_data)

            await consumer.commit()
    finally:
        await consumer.stop()


async def send_email_via_gmail(user_id, message_data):
    # Используем контекстный менеджер для работы с сессией
    async with get_db2() as db:
        try:
            stmt_user = select(UserOrm).where(UserOrm.email == user_id)
            result_user = await db.execute(stmt_user)
            user = result_user.scalar_one_or_none()

            if not user:
                logger.error(f"UserOrm with ID {user_id} not found")
                return
            print("нет ошибки1")
            gmail_service = await get_gmail_service(user, db)
            print("нет ошибки2")
            response = await asyncio.to_thread(
                lambda: gmail_service.users()
                .messages()
                .send(userId="me", body=message_data["message"])
                .execute()
            )
            logger.info(f"Email to {message_data['recipient']} sent successfully")
        except HttpError as e:
            logger.error(f"Failed to send email to {message_data['recipient']}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error for {message_data['recipient']}: {e}")


if __name__ == "__main__":
    asyncio.run(process_kafka_messages())
