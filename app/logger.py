from loguru import logger
import sys
import os


LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logger.remove()

logger.add(
    sys.stdout,
    colorize=True,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: 8}</level>"
            "<cyan>{name}</cyan>:<cyan>function</cyan>:<cyan>{line}</cyan> -"
            "<level>{message}</level>"
)

logger.add(
    f"{LOG_DIR}/app.log",
    rotation="10 MB",
    retention="7 days",
    compression="zip",
    encoding="utf-8",
    level="INFO",
)

logger.add(
    f"{LOG_DIR}/error.log",
    rotation="5 MB",
    retention="14 days",
    compression="zip",
    encoding="utf-8",
    level="ERROR",
)

logger.add(
    f"{LOG_DIR}/structured.json",
    rotation="10 MB",
    serialize=True,
    level="INFO",
)

logger.info("Logger initialized ✅")
