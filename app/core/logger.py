import logging
import sys

def setup_logger(name: str = "app") -> logging.Logger:
    # FastAPI/Uvicorn default logger
    logger = logging.getLogger("uvicorn.error")
    
    # Optionally, we can create a custom child logger from uvicorn
    # logger = logging.getLogger(f"uvicorn.error.{name}")
    
    logger.setLevel(logging.DEBUG)
    return logger

logger = setup_logger("atur-uang")
