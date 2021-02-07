import sys

from loguru import logger


# Remove all pre-configured loggers. We just want the ones we're about to add
logger.remove(None)

# Add a simple logger with no fluff.
logger.add(sys.stderr, format="<yellow>{time:HH:mm:ss}</yellow> {message}", colorize=True)

# All other files will import from here.
log = logger.opt(colors=True)
