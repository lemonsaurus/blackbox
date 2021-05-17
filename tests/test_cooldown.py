from datetime import datetime

import pytest
from dateutil.relativedelta import relativedelta

from blackbox.utils.cooldown import parse_config_cooldown, should_we_send


@pytest.fixture
def cooldown_config():
    return '2h 7M 3s'


def test_regex_cooldown_setting(cooldown_config):
    delta = parse_config_cooldown(cooldown_config)
    assert delta == relativedelta(hours=2, minutes=7, seconds=3)


def test_should_we_send_notification(cooldown_config):
    delta = parse_config_cooldown(cooldown_config)
    now = datetime.now()
    last_send_exact = now - delta
    assert should_we_send(last_send_exact, delta) is True
    last_send_long_ago = now - delta - relativedelta(hours=1)
    assert should_we_send(last_send_long_ago, delta) is True
    last_send_recent = now - delta + relativedelta(seconds=10)
    assert should_we_send(last_send_recent, delta) is False
