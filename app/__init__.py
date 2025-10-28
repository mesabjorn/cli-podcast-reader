import logging


def setup_logger():
    FORMAT = "%(asctime)s::::%(filename)s::::%(levelname)s::::%(message)s::::"
    logging.basicConfig(format=FORMAT)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    return logger


LOGGER = setup_logger()
