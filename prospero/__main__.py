import itertools
import time

import schedule
from apprise.apprise import Apprise
from loguru import logger

from prospero.config import TELEGRAM_BOT_TOKEN, SCHEDULE_CHECK_INTERVAL, TELEGRAM_CHAT_IDS
from prospero.db import ScheduleDatabase
from prospero.schedule_scraper.base import BaseScheduleScraper
from prospero.schedule_scraper.gavella import GavellaScheduleScraper
from prospero.schedule_scraper.kerempuh import KerempuhScheduleScraper
from prospero.schedule_scraper.komedija import KomedijaScheduleScraper
from prospero.schedule_scraper.luda_kuca import LudaKucaScheduleScraper
from prospero.schedule_scraper.teatar_exit import TeatarExitScheduleScraper

ALL_SCHEDULE_SCRAPERS: list[type[BaseScheduleScraper]] = [
    KerempuhScheduleScraper,
    KomedijaScheduleScraper,
    GavellaScheduleScraper,
    LudaKucaScheduleScraper,
    TeatarExitScheduleScraper
    # Add new scrapers here
]


def schedule_check():
    apprise: Apprise = Apprise(
        servers=[
            f'tgram://{TELEGRAM_BOT_TOKEN}/{telegram_chat_id}/?format=markdown'
            for telegram_chat_id
            in TELEGRAM_CHAT_IDS
        ]
    )

    with ScheduleDatabase() as db:
        for entry in sorted(
                itertools.chain.from_iterable(
                    schedule_scraper.try_get_active_schedule_entries()
                    for schedule_scraper
                    in ALL_SCHEDULE_SCRAPERS
                ),
                key=lambda e: e.start_datetime
        ):
            if not db.contains_entry(entry):
                db.add_entry(entry)
                logger.debug(f'Added new entry: {entry}')
                logger.debug(f'Notifying users...')

                apprise.notify(body=entry.to_markdown())
                time.sleep(0.5)
            else:
                logger.debug(f'Entry already exists: {entry}')


def main():
    schedule_check()
    schedule.every(SCHEDULE_CHECK_INTERVAL).seconds.do(schedule_check)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    main()
