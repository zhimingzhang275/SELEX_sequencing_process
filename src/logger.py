"""日志系统：同时输出到终端和日志文件"""
import logging
import os
import sys
from paths import get_base_dir

LOG_DIR = os.path.join(get_base_dir(), "logs")


def setup_logger(name: str = "selex", round_name: str = "") -> logging.Logger:
    """初始化并返回 logger，pipeline.log + error.log + 终端三路输出"""
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    fmt = "%(asctime)s [%(levelname)s]" + (f"[{round_name}]" if round_name else "") + " %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt=datefmt)

    # 终端输出（INFO+）
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # pipeline.log（DEBUG+）
    pipeline_path = os.path.join(LOG_DIR, "pipeline.log")
    file_handler = logging.FileHandler(pipeline_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # error.log（WARNING+）
    error_path = os.path.join(LOG_DIR, "error.log")
    error_handler = logging.FileHandler(error_path, encoding="utf-8")
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    return logger


def get_logger(name: str = "selex") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger
