import logging
import sys


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


def get_logger(name: str = "ARCH-FL") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    silenceLoggers()
    return logger


logger = get_logger()
