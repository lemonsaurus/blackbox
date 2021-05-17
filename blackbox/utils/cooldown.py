import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from dateutil.relativedelta import relativedelta

from blackbox.utils.logger import log

_DURATION_REGEX = re.compile(
    r"((?P<years>\d+?) ?(years|year|Y|y) ?)?"
    r"((?P<months>\d+?) ?(months|month|m) ?)?"
    r"((?P<weeks>\d+?) ?(weeks|week|W|w) ?)?"
    r"((?P<days>\d+?) ?(days|day|D|d) ?)?"
    r"((?P<hours>\d+?) ?(hours|hour|H|h) ?)?"
    r"((?P<minutes>\d+?) ?(minutes|minute|M) ?)?"
    r"((?P<seconds>\d+?) ?(seconds|second|S|s))?"
)


def parse_config_cooldown(cooldown) -> Optional[relativedelta]:
    match = _DURATION_REGEX.fullmatch(cooldown)
    if not match:
        return None

    duration_dict = {unit: int(amount) for unit, amount in match.groupdict(default=0).items()}
    delta = relativedelta(**duration_dict)

    return delta


def should_we_send(last_send: datetime, delta: relativedelta) -> bool:
    return True if datetime.now() - delta >= last_send else False


def write_config(**kwargs):
    with open(get_project_root() / 'notify.json', 'w', encoding='utf-8') as f:
        json.dump(kwargs, f, ensure_ascii=False, indent=4)


def read_config() -> dict:
    log.debug('Found json, reading it...')
    with open(get_project_root() / 'notify.json') as infile:
        data = json.load(infile)
    return data


def get_project_root() -> Path:
    """Fancy way to retrieve project root."""
    return Path(__file__).parent.parent


def is_not_cooldown_period(cooldown) -> bool:
    delta = parse_config_cooldown(cooldown)
    if os.path.exists(get_project_root() / 'notify.json'):
        data = read_config()
        last_send = datetime.strptime(data['last_notify'], "%m/%d/%Y, %H:%M:%S")
        return should_we_send(last_send, delta)
    else:
        write_config(last_send=datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
        return True
