import os
from typing import List

TELEGRAM_BOT_TOKEN: str = os.environ['TELEGRAM_BOT_TOKEN']
TELEGRAM_CHAT_IDS: List[str] = os.environ['TELEGRAM_CHAT_IDS'].split(',')
assert len(TELEGRAM_CHAT_IDS) > 0, 'TELEGRAM_CHAT_IDS must contain at least one chat ID'
SCHEDULE_CHECK_INTERVAL: int = int(os.environ.get('SCHEDULE_CHECK_INTERVAL', 60 * 5))
