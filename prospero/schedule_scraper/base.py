from datetime import datetime
from typing import Generator

import requests
from bs4 import BeautifulSoup
from loguru import logger
from requests import Response

from prospero.db import ScheduleEntry


class BaseScheduleScraper(object):
    @classmethod
    def _assign_year(cls, entry_datetime: datetime) -> datetime:
        # Get current date
        current_date: datetime = datetime.now()

        # Get the years we're dealing with
        current_year: int = current_date.year
        next_year: int = current_year + 1

        # Get months for comparison
        entry_month: int = entry_datetime.month
        current_month: int = current_date.month

        # Logic for assigning the correct year
        assigned_year: int
        if entry_month < current_month:
            # If the entry month is less than current month, it must be next year
            assigned_year = next_year
        elif entry_month == current_month:
            # If same month, compare days to determine year
            if entry_datetime.day >= current_date.day:
                assigned_year = current_year
            else:
                assigned_year = next_year
        else:
            # If entry month is greater than current month, it's current year
            assigned_year = current_year

        # Return new datetime with assigned year
        return entry_datetime.replace(year=assigned_year)

    @classmethod
    def _get_schedule_url(cls) -> str:
        raise NotImplementedError

    @classmethod
    def _get_schedule_response(cls) -> Response:
        return requests.get(cls._get_schedule_url())

    @classmethod
    def _get_schedule_soup(cls) -> BeautifulSoup:
        response: Response = cls._get_schedule_response()
        response.raise_for_status()
        return BeautifulSoup(
            response.content,
            features='html5lib',
            from_encoding=response.encoding
        )

    @classmethod
    def get_active_schedule_entries(cls) -> Generator[ScheduleEntry, None, None]:
        raise NotImplementedError

    @classmethod
    def try_get_active_schedule_entries(cls) ->  Generator[ScheduleEntry, None, None]:
        try:
            yield from cls.get_active_schedule_entries()
        except Exception as e:
            logger.exception(f'Exception occurred while running {cls}', e)
