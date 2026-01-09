import json
from aiokafka import AIOKafkaProducer

from app.common.config.base_config import base_settings


class GmailProducer:
    def __init__(self) -> None:
        self._producer = AIOKafkaProducer(
            bootstrap_servers=base_settings.KAFKA_BOOTSTRAP_SERVERS
        )

    async def start_producer(self):
        await self._producer.start()

    async def send_message_to_kafka(
        self,
        data: dict,
        key: str,
    ) -> None:
        await self._producer.send_and_wait(
            base_settings.KAFKA_TOPIC,
            json.dumps(data).encode('utf-8'),
            key=str(key).encode('utf-8')
        )


async def get_gmail_producer() -> GmailProducer:
    return GmailProducer()
