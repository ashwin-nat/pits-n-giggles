import logging
import sys
import asyncio
from lib.openf1 import getMostRecentPoleLap
from lib.f1_types import TrackID

async def run_async_stuff():
    logging.basicConfig(
        level=logging.DEBUG,  # capture all levels
        stream=sys.stdout,
        format="%(levelname)s: %(message)s",
    )

    logger = logging.getLogger(__name__)
    lap = await getMostRecentPoleLap(TrackID.Losail, logger)
    print(lap)


if __name__ == "__main__":
    asyncio.run(run_async_stuff())
