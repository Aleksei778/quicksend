from aiokafka.admin import AIOKafkaAdminClient, NewTopic

from common.utils.logger import logger
from common.utils.config import base_config


async def create_kafka_topic_if_not_exists():
    admin = AIOKafkaAdminClient(bootstrap_servers=base_config.KAFKA_BOOTSTRAP_SERVERS)

    await admin.start()

    try:
        topics = await admin.list_topics()

        if base_config.KAFKA_TOPIC in topics:
            logger.info(f"Topic {base_config.KAFKA_TOPIC} already exists")
            return

        topic = NewTopic(
            name=base_config.KAFKA_TOPIC,
            num_partitions=base_config.KAFKA_NUM_PARTITIONS,
            replication_factor=base_config.KAFKA_REPLICATION_FACTOR,
        )

        await admin.create_topics([topic])

        logger.info(f"Created kafka topic {base_config.KAFKA_TOPIC}")

    except Exception as e:
        logger.error(f"Failed to create topic {base_config.KAFKA_TOPIC}: {e}")
    finally:
        await admin.close()
