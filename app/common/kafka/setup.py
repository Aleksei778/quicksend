from aiokafka.admin import AIOKafkaAdminClient, NewTopic

from app.common.log.logger import logger
from app.common.config.base_config import base_settings


async def create_kafka_topic_if_not_exists():
    admin = AIOKafkaAdminClient(bootstrap_servers=base_settings.KAFKA_BOOTSTRAP_SERVERS)

    await admin.start()

    try:
        topics = await admin.list_topics()

        if base_settings.KAFKA_TOPIC in topics:
            logger.info(f"Topic {base_settings.KAFKA_TOPIC} already exists")
            return

        topic = NewTopic(
            name=base_settings.KAFKA_TOPIC,
            num_partitions=base_settings.KAFKA_NUM_PARTITIONS,
            replication_factor=base_settings.KAFKA_REPLICATION_FACTOR,
        )

        await admin.create_topics([topic])

        logger.info(f"Created kafka topic {base_settings.KAFKA_TOPIC}")

    except Exception as e:
        logger.error(f"Failed to create topic {base_settings.KAFKA_TOPIC}: {e}")
    finally:
        await admin.close()
