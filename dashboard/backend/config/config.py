from .settings import settings

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": settings.DEFAULT_LOG_FORMAT,
        },
        "minimal": {
            "format": settings.MINIMAL_LOG_FORMAT,
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "minimal",
            "level": settings.LOG_LEVEL,
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "default",
            "filename": settings.LOG_DIR / settings.LOG_FILE,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "level": settings.LOG_LEVEL,
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": settings.LOG_LEVEL,
    },
    "loggers": {
        "uvicorn": {
            "handlers": ["console"],
            "level": settings.LOG_LEVEL,
            "propagate": False,
        },
        "fastapi": {
            "handlers": ["console", "file"],
            "level": settings.LOG_LEVEL,
            "propagate": False,
        },
        "archfl": {
            "handlers": ["console", "file"],
            "level": settings.LOG_LEVEL,
            "propagate": False,
        },
        "opacus.optimizers.optimizer": {
            "handlers": ["console"],
            "level": settings.LOG_LEVEL,
            "propagate": False,
        },
    },
}
