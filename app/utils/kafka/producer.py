import json
from aiokafka import AIOKafkaProducer

from common.utils.config import base_config
from common.utils.logger import logger

producer: AIOKafkaProducer | None = None

async def init() -> None:
    global producer

    if producer is None:
        try:
            producer = AIOKafkaProducer(
                bootstrap_servers=base_config.KAFKA_BOOTSTRAP_SERVERS,
            )

            await producer.start()

            logger.info(f"✅ Kafka producer started successfully")

        except Exception as e:
            logger.error(f"❌ Failed to start kafka producer: {e}")

            raise

async def send_message(data: dict, key: str) -> None:
    if producer:
        await producer.send(
            base_config.KAFKA_TOPIC,
            json.dumps(data).encode('utf-8'),
            key=str(key).encode('utf-8')
        )
    else:
        raise Exception("No kafka producer available")

async def stop() -> None:
    global producer

    if producer:
        await producer.stop()
