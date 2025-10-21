import logging

from src.util import env

LOG_LEVEL = env.require_any_env("LOGLEVEL") or "INFO"

root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

handler = logging.StreamHandler()
handler.setLevel(LOG_LEVEL)


class ColorFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[41m",  # Red background
    }
    GREY = "\033[90m"
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        record.name = f"{self.GREY}{record.name}{self.RESET}"
        record.link = f"\033[34m{record.pathname}:{record.lineno}\033[0m"
        return super().format(record)


formatter = ColorFormatter("%(asctime)s %(levelname)-16s %(name)-32s [%(link)s] \n%(message)s\n")
handler.setFormatter(formatter)
root_logger.addHandler(handler)
root_logger.setLevel(LOG_LEVEL)

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

logger.info(f"Package logger initialized with level: {logging.getLevelName(logger.level)}")
