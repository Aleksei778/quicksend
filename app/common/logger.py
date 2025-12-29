from loguru import logger
from seqlog import SeqLogHandler

from common.config import SEQ_URL, SEQ_API_KEY

handler = SeqLogHandler(
    server_url=SEQ_URL,
    api_key=SEQ_API_KEY,
    batch_size=10,
    auto_flush_timeout=5
)

logger.add(handler)
