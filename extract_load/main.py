from logging import getLogger
from dotenv import load_dotenv
load_dotenv()

from pipeline import Pipeline

logger = getLogger(__name__)


def main() -> None:

    logger.info("_" * 30)
    logger.info("Portfolio loading started")
    pipeline = Pipeline()
    pipeline.run()
    logger.info("Portfolio loading finished")
    logger.info("_" * 30)


if __name__ == "__main__":
    main()
