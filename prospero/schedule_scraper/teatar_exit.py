from datetime import datetime, time
from typing import Generator

from bs4 import BeautifulSoup, Tag

from prospero.db import ScheduleEntry
from prospero.schedule_scraper.base import BaseScheduleScraper


class TeatarExitScheduleScraper(BaseScheduleScraper):
    @classmethod
    def _get_schedule_url(cls) -> str:
        return 'https://teatarexit.hr/raspored-predstava/raspored-sve-nadolazece/'

    @classmethod
    def _croatian_month_to_number(cls, month: str) -> int:
        return {
            'sij': 1,
            'vel': 2,
            'ozu': 3,
            'tra': 4,
            'svi': 5,
            'lip': 6,
            'srp': 7,
            'kol': 8,
            'ruj': 9,
            'lis': 10,
            'stu': 11,
            'pro': 12
        }[month.lower().replace('ž', 'z')[:3]]

    @classmethod
    def get_active_schedule_entries(cls) -> Generator[ScheduleEntry, None, None]:
        schedule_soup: BeautifulSoup = cls._get_schedule_soup()

        event_post_div: Tag
        for event_post_div in schedule_soup.find_all('div', {'class': 'event-post'}):
            date_div: Tag = event_post_div.find('div', {'class': 'date'})
            event_data_div: Tag = event_post_div.find('div', {'class': 'event-data'})

            schedule_main_div: Tag = event_data_div.find('div', {'class': 'schedule_main'})
            bw_buttons_div: Tag = event_data_div.find('div', {'class': 'bw-buttons'})

            day_numeric_span: Tag
            month_string_span: Tag
            _, day_numeric_span, month_string_span = date_div.find_all('span')
            title_a: Tag = schedule_main_div.find('a')
            start_time_div: Tag = schedule_main_div.find('div', {'class': 'clock'})
            location_div: Tag = schedule_main_div.find('div', {'class': 'location'})
            fee_div: Tag = schedule_main_div.find('div', {'class': 'fee'})
            buy_tickets_a: Tag = bw_buttons_div.find('a', {'class': 'botton upcoming'})

            day_str: str = day_numeric_span.text.strip().strip('.')
            month_croatian_str: str = month_string_span.text.strip()
            start_time_str: str = start_time_div.text.strip()
            fee_str: str = fee_div.text.strip() if fee_div else ''

            start_datetime: datetime = cls._assign_year(datetime.strptime(
                f'{day_str}.{cls._croatian_month_to_number(month_croatian_str)}. {start_time_str}',
                '%d.%m. %H:%M'
            ))
            title: str = title_a.text.strip()
            note: str | None = fee_str if len(fee_str) > 0 else None
            location: str = location_div.text.strip()
            buy_tickets_url: str | None = buy_tickets_a['href'] if buy_tickets_a else None

            yield ScheduleEntry(
                start_datetime=start_datetime,
                title=title,
                note=note,
                location=location,
                buy_tickets_url=buy_tickets_url
            )
