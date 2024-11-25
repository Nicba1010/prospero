from datetime import datetime
from typing import Generator

from bs4 import BeautifulSoup, Tag

from prospero.db import ScheduleEntry
from prospero.schedule_scraper.base import BaseScheduleScraper


class LudaKucaScheduleScraper(BaseScheduleScraper):
    @classmethod
    def _get_schedule_url(cls) -> str:
        return 'https://www.ludakuca.hr/raspored/'

    @classmethod
    def get_active_schedule_entries(cls) -> Generator[ScheduleEntry, None, None]:
        schedule_soup: BeautifulSoup = cls._get_schedule_soup()

        kd_photobox_div: Tag
        for kd_photobox_div in schedule_soup.find_all(
                'div',
                {
                    'class': 'kd-photobox'
                }
        ):
            phb_content_div: Tag = kd_photobox_div.find('div', {'class': 'phb-content'})

            date_h5: Tag = phb_content_div.find('h5')
            title_time_p: Tag = phb_content_div.find('p')
            buy_tickets_a: Tag | None = phb_content_div.find('a')

            date_with_day_str: str = date_h5.text.strip()
            title_time_str: str = title_time_p.text.strip()
            title_time_str_split: list[str] = title_time_str.rsplit(' ', 1)

            date_str: str = date_with_day_str.split(' ')[0].strip()
            time_str: str = title_time_str_split[-1].strip()

            start_datetime: datetime = cls._assign_year(
                entry_datetime=datetime.strptime(
                    f'{date_str} {time_str}',
                    '%d.%m. %H:%M'
                )
            )
            title: str = title_time_str_split[0]
            buy_tickets_url: str = buy_tickets_a['href'] if buy_tickets_a else None

            yield ScheduleEntry(
                start_datetime=start_datetime,
                title=title,
                location='Luda Kuća',
                buy_tickets_url=buy_tickets_url
            )
