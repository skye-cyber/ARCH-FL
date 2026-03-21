import logging
import logging.config
from backend.config.config import LOGGING_CONFIG


def silenceLoggers():
    logging.getLogger("opacus").setLevel(logging.WARNING)

    logging.getLogger("opacus.privacy_engine").setLevel(
        logging.WARNING
    )  # Common submodule
    logging.getLogger("opacus.optimizers.optimizer").setLevel(logging.WARNING)
    # For torch.optim (PyTorch optimizers; may use root or 'torch.optim')
    logging.getLogger("torch.optim").setLevel(logging.WARNING)
    logging.getLogger("numexpr.utils").setLevel(logging.WARNING)
    logging.getLogger("matplotlib.font_manager").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("pydot").setLevel(logging.WARNING)
    logging.getLogger("pydot.core").setLevel(logging.WARNING)

    # logging.getLogger().setLevel(logging.WARNING) For root logger

    # Alternative: Silence all except yours (use post-import)
    # for name in logging.root.manager.loggerDict:
    #     if name not in ("ARCH-FL", "archfl"):
    #         logging.getLogger(name).disabled = True


# Configure logging
logging.config.dictConfig(LOGGING_CONFIG)
silenceLoggers()
logger = logging.getLogger("archfl")
