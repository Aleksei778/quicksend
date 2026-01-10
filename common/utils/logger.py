from loguru import logger
from seqlog import SeqLogHandler

from common.utils.config import base_config

handler = SeqLogHandler(
    server_url=base_config.SEQ_URL,
    api_key=base_config.SEQ_API_KEY,
    batch_size=10,
    auto_flush_timeout=5,
)

logger.add(handler)
