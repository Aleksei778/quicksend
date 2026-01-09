import asyncio
import json
from aiokafka import AIOKafkaConsumer, ConsumerRecord
from googleapiclient.errors import HttpError

from app.common.db.database import get_db_contextmanager
from app.common.log.logger import logger
from app.common.config.base_config import base_settings
from app.users.models.user import User
from app.users.services.user_service import UserService
from app.google_integration.gmail.services.gmail_service import GoogleGmailService
from app.google_integration.auth.services.google_token_service import GoogleTokenService


class GmailConsumer:
    def __init__(self, consumer: AIOKafkaConsumer) -> None:
        self._consumer = consumer

    async def process_all_kafka_messages(self) -> None:
        await self._consumer.start()

        try:
            async for message in self._consumer:
                await self._process_message(message)
        finally:
            await self._consumer.stop()

    async def _send_message_to_gmail_with_retry(
        self,
        gmail_service: GoogleGmailService,
        user: User,
        message: str
    ) -> None:
        for attempt in range(base_settings.KAFKA_CONSUMER_MAX_RETRIES):
            try:
                await gmail_service.send_email_via_gmail(user, message)

                return

            except HttpError as e:
                status = getattr(e.resp, 'status', None)

                if status in (429, 500, 505):
                    sleep_time = base_settings.KAFKA_CONSUMER_BASE_BACKOFF * (2 ** (attempt - 1))

                    await asyncio.sleep(sleep_time)

                else:
                    raise

        raise RuntimeError('Too many retries')

    async def _process_message(self, message: ConsumerRecord) -> None:
        message_data = json.loads(message.value.decode("utf-8"))
        user_email = message.key.decode("utf-8")

        async with get_db_contextmanager() as db:
            user_service = UserService(db)
            google_token_service = GoogleTokenService(db)
            gmail_service = GoogleGmailService(db, google_token_service)

            user = await user_service.find_by_email(user_email)

            if not user:
                logger.error(f"No user found: {user_email}")
                return

            await self._send_message_to_gmail_with_retry(
                gmail_service=gmail_service,
                user=user,
                message=message_data['message']
            )

            logger.info(f"Email to {message_data['recipient']} sent successfully")


async def main() -> None:
    consumer = AIOKafkaConsumer(
        base_settings.KAFKA_TOPIC,
        bootstrap_servers=base_settings.KAFKA_BOOTSTRAP_SERVERS,
    )

    gmail_consumer = GmailConsumer(consumer)
    await gmail_consumer.process_all_kafka_messages()


if __name__ == "__main__":
    asyncio.run(main())
