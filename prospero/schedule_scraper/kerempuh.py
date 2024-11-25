from datetime import datetime
from typing import Generator

import requests
from bs4 import BeautifulSoup, Tag
from requests import Response

from prospero.db import ScheduleEntry
from prospero.schedule_scraper.base import BaseScheduleScraper


class KerempuhScheduleScraper(BaseScheduleScraper):
    @classmethod
    def _get_schedule_url(cls) -> str:
        return 'https://kazalistekerempuh.hr/raspored-predstava/'

    @classmethod
    def _get_schedule_response(cls) -> Response:
        return requests.post(
            url=cls._get_schedule_url(),
            data={
                'limit': 10000,
                'action': 'search_events',
            }
        )

    @classmethod
    def get_active_schedule_entries(cls) -> Generator[ScheduleEntry, None, None]:
        schedule_soup: BeautifulSoup = cls._get_schedule_soup()

        timetable_row_div: Tag
        for timetable_row_div in schedule_soup.find_all(
                'div',
                {
                    'class': 'timetable-rows col span_12'
                }
        ):
            event_date_div: Tag = timetable_row_div.find('div', {'class': 'event-date'})
            event_time_div: Tag = timetable_row_div.find('div', {'class': 'event-time'})
            event_title_div_div: Tag = timetable_row_div.find('div', {'class': 'event-title'}).find('div')
            event_location_div: Tag = timetable_row_div.find('div', {'class': 'event-location'})
            event_buy_ticket_div: Tag = timetable_row_div.find('div', {'class': 'event-buy-ticket'})

            date_b: Tag = event_date_div.find('b')
            time_span: Tag = event_time_div.find('span')
            title_a: Tag = event_title_div_div.find('a')
            note_div: Tag | None = event_title_div_div.find('div')
            duration_span: Tag = event_location_div.find('span')
            buy_tickets_a: Tag | None = event_buy_ticket_div.find('a') if event_buy_ticket_div else None

            date_str: str = date_b.text.strip()
            time_str: str = time_span.text.strip()
            duration_str: str = duration_span.text.strip()

            duration_str_split: list[str] = duration_str.split(' ')

            start_datetime: datetime = cls._assign_year(
                entry_datetime=datetime.strptime(
                    f'{date_str} {time_str}',
                    '%d.%m. %H:%M'
                )
            )
            title: str = title_a.text.strip()
            note: str | None = note_div.text.strip() if note_div else None
            duration: int | None
            try:
                duration = int(duration_str_split[0])
            except ValueError or IndexError:
                duration = None
            includes_break: bool
            try:
                includes_break = 'pauz' in duration_str_split[-1]
            except IndexError:
                includes_break = False
            buy_tickets_url: str | None = buy_tickets_a['href'] if buy_tickets_a else None

            yield ScheduleEntry(
                start_datetime=start_datetime,
                title=title,
                note=note,
                location='Kerempuh',
                duration=duration,
                includes_break=includes_break,
                buy_tickets_url=buy_tickets_url
            )
