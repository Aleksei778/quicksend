from loguru import logger
from seqlog import SeqLogHandler

from common.config.base_config import base_settings

handler = SeqLogHandler(
    server_url=base_settings.SEQ_URL,
    api_key=base_settings.SEQ_API_KEY,
    batch_size=10,
    auto_flush_timeout=5,
)

logger.add(handler)
