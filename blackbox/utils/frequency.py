import json
import os
from datetime import datetime
from pathlib import Path

from blackbox.config import Blackbox as CONFIG
from blackbox.utils.logger import log


def get_project_root() -> Path:
    return Path(__file__).parent.parent


def can_we_notify_now() -> (bool, int):
    """Check if we allowed to send notification to user."""
    now = datetime.now()
    frequency = CONFIG['notifier_frequency']
    period = int(24 * 60 * 60 / frequency)
    attempts = 0

    if os.path.exists(get_project_root() / 'notify.json'):
        # Load data from JSON
        log.debug('Found json, reading it...')
        with open(get_project_root() / 'notify.json') as infile:
            data = json.load(infile)

        # Assign it to variables
        last_notify = datetime.strptime(data['last_notify'], "%m/%d/%Y, %H:%M:%S")
        attempts = int(data['attempts'])
        frequency_in_json = int(data['frequency'])

        # If frequency in config changed restarting our process
        if frequency != frequency_in_json:
            log.debug(f'Frequency changed. Recreating json with period: {period}')
            write_down_last_notification(attempts=0, frequency=frequency)
            return True, 0

        # Calculate passed time from last notification
        delta = now - last_notify
        if delta.seconds < period:
            log.debug(f"Can't send notification, {delta.seconds} < {period}.")
            attempts += 1
            write_down_last_notification(attempts, frequency, last_notify)
            return False, 0

    # Creating or recreating json settings file
    log.debug(f'Recreating json with period: {period}')
    write_down_last_notification(attempts=0, frequency=frequency)
    return True, attempts


def write_down_last_notification(attempts, frequency, last_notify=None):
    """Write down info about last attempt to send notification."""
    # No datetime means it was successful attempt
    if last_notify is None:
        last_notify = datetime.now()

    data = {
        'attempts': attempts,
        'frequency': frequency,
        'last_notify': last_notify.strftime("%m/%d/%Y, %H:%M:%S"),
    }
    with open(get_project_root() / 'notify.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
