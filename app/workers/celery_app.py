from celery import Celery

from common.config.base_config import celery_url

app = Celery('emailer', broker='amqp://rabbitmq:5672')

@app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, user_email, message_data):
    try:

