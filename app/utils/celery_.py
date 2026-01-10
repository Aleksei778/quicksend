from celery import Celery
from kombu import Exchange, Queue

from common.utils.logger import logger
from common.utils.config import base_config


celery_app = Celery(broker=base_config.RABBITMQ_URL, backend=base_config.REDIS_URL)

campaigns_exchange = Exchange(name="campaigns", type="direct")
campaigns_queue = Queue(
    name="campaigns", exchange=campaigns_exchange, routing_key="campaigns"
)

subscriptions_exchange = Exchange(name="subscriptions", type="direct")
subscriptions_queue = Queue(
    name="subscriptions",
    exchange=subscriptions_exchange,
    routing_key="subscriptions",
)

celery_app.conf.update(
    task_queues=(campaigns_queue, subscriptions_queue),
    task_routes={
        "send_emails_task": {"queue": "campaigns"},
        # "update_subscriptions_task": {"queue": "subscriptions"},
    },
    task_track_started=True,
    timezone="UTC",
    enable_utc=True,
    worker_log_format="[%(asctime)s: %(levelname)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s][%(task_name)s(%(task_id)s)] %(message)s",
    task_default_retry_delay=300,
    task_max_retries=3,
)

# celery_app.conf.beat_schedule = {
#     "update-subscriptions": {
#         "task": "update_subscriptions_task",
#         "schedule": crontab(hour=9, minute=0),
#         "options": {"queue": "subscriptions"},
#     }
# }


@celery_app.task(name="test_connection")
def test_connection():
    logger.info("Test connection task executed successfully")
