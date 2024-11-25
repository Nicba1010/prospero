from datetime import datetime
from typing import Generator

import requests
from bs4 import BeautifulSoup, Tag
from requests import Response

from prospero.db import ScheduleEntry
from prospero.schedule_scraper.base import BaseScheduleScraper


class KomedijaScheduleScraper(BaseScheduleScraper):
    SCHEDULE_URL: str = 'https://www.komedija.hr/www/wp-admin/admin-ajax.php'

    @classmethod
    def _get_schedule_response(cls) -> Response:
        return requests.post(
            url=cls.SCHEDULE_URL,
            data={
                'limit': 10000,
                'action': 'search_events',
            }
        )

    @classmethod
    def get_active_schedule_entries(cls) -> Generator[ScheduleEntry, None, None]:
        schedule_soup: BeautifulSoup = cls._get_schedule_soup()

        schedule_table: Tag = schedule_soup.find('table')
        schedule_tbody: Tag = schedule_table.find('tbody')

        schedule_entry_tr: Tag
        for schedule_entry_tr in schedule_tbody.find_all('tr'):
            date_time_td: Tag
            title_location_td: Tag
            note_td: Tag
            buy_tickets_td: Tag

            date_time_td, title_location_td, note_td, buy_tickets_td = schedule_entry_tr.find_all('td')

            title_location_a: Tag = title_location_td.find('a')
            location_img: Tag = title_location_td.find('img')
            buy_tickets_a: Tag = buy_tickets_td.find('a')

            date_time_parts: list[str] = list(date_time_td.stripped_strings)

            date_str: str = date_time_parts[0].split(',')[0].strip()
            time_start_str: str = date_time_parts[1].split('-')[0].strip()
            time_end_str: str = date_time_parts[1].split('-')[1].strip()
            note_str: str = note_td.text.strip()

            start_datetime: datetime = cls._assign_year(
                entry_datetime=datetime.strptime(
                    f'{date_str} {time_start_str}',
                    '%d.%m. %H:%M'
                )
            )
            title: str = title_location_a.text.strip()
            note: str | None = note_str if len(note_str) > 0 else None
            duration: int = (
                                    datetime.strptime(time_end_str, '%H:%M') -
                                    datetime.strptime(time_start_str, '%H:%M')
                            ).seconds // 60
            location: str = location_img['alt'].strip() if location_img is not None else 'Komedija'
            buy_tickets_url: str | None = buy_tickets_a['href'] if buy_tickets_a is not None else None

            yield ScheduleEntry(
                start_datetime=start_datetime,
                title=title,
                note=note,
                location=location,
                duration=duration,
                buy_tickets_url=buy_tickets_url
            )
