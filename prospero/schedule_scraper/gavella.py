from datetime import datetime, time
from typing import Generator

from bs4 import BeautifulSoup, Tag

from prospero.db import ScheduleEntry
from prospero.schedule_scraper.base import BaseScheduleScraper


class GavellaScheduleScraper(BaseScheduleScraper):
    @classmethod
    def _get_schedule_url(cls) -> str:
        return 'https://www.gavella.hr/raspored-izvedbi/'

    @classmethod
    def get_active_schedule_entries(cls) -> Generator[ScheduleEntry, None, None]:
        schedule_soup: BeautifulSoup = cls._get_schedule_soup()

        schedule_table: Tag = schedule_soup.find('table', {'class': 'table'})
        schedule_tbody: Tag = schedule_table.find('tbody')

        schedule_entry_tr: Tag
        for schedule_entry_tr in list(schedule_tbody.find_all('tr'))[1:]:
            date_div: Tag = schedule_entry_tr.find('div', {'class': 'date'})
            time_div: Tag = schedule_entry_tr.find('div', {'class': 'time'})
            note_div: Tag | None = schedule_entry_tr.find('div', {'class': 'playcomment'})
            place_div: Tag = schedule_entry_tr.find('div', {'class': 'place'})
            buy_tickets_a: Tag | None = schedule_entry_tr.find('a', {'class': 'btn btn-small btn-primary'})

            title_a: Tag = schedule_entry_tr.find('a')

            date_str: str = date_div.text.strip()
            date_str_no_day: str = date_str.split(',')[1].strip()
            time_str: str = time_div.text.strip()

            start_datetime: datetime = datetime.strptime(
                f'{date_str_no_day} {time_str}',
                '%d.%m.%Y. %H:%M'
            )
            title: str = title_a.text.strip()
            note: str | None = note_div.text.strip() if note_div else None
            location: str = place_div.text.strip()
            if location.lower() in [
                'velika scena', 'mala gavella'
            ]:
                location = f'Gavella ({location})'
            buy_tickets_url: str | None = buy_tickets_a['href'] if buy_tickets_a else None

            yield ScheduleEntry(
                start_datetime=start_datetime,
                title=title,
                note=note,
                location=location,
                buy_tickets_url=buy_tickets_url
            )
