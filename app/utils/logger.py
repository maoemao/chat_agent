import logging
import os
from datetime import datetime
from typing import Optional

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if logger.handlers:
        logger.handlers.clear()
    
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)
    
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
    
    logger.propagate = False
    return logger

current_time = datetime.now().strftime("%Y%m%d")
LOG_DIR = "logs"

telegram_logger = setup_logger("telegram", os.path.join(LOG_DIR, f"telegram_{current_time}.log"))
agent_logger = setup_logger("agent", os.path.join(LOG_DIR, f"agent_{current_time}.log"))
rag_logger = setup_logger("rag", os.path.join(LOG_DIR, f"rag_{current_time}.log"))
plan_logger = setup_logger("plan", os.path.join(LOG_DIR, f"plan_{current_time}.log"))
mcp_logger = setup_logger("mcp", os.path.join(LOG_DIR, f"mcp_{current_time}.log"))
router_logger = setup_logger("router", os.path.join(LOG_DIR, f"router_{current_time}.log"))