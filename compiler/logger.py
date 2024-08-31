import logging


formatter = logging.Formatter("[%(asctime)s] - [%(levelname)s] - %(message)s")
handler = logging.StreamHandler()
handler.setFormatter(formatter)

LOGGER = logging.getLogger("compiler")
LOGGER.setLevel(logging.INFO)
LOGGER.addHandler(handler)
