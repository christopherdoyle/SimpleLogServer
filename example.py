import logging.handlers


logger = logging.getLogger("example")
logger.setLevel(logging.DEBUG)
handler = logging.handlers.SocketHandler(host="127.0.0.1", port=18001)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

logger.debug("One")
logger.info("Two")
logger.warning("Three")
logger.error("Four")
logger.critical("Five")
