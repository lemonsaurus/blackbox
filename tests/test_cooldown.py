from datetime import datetime

import pytest
from dateutil.relativedelta import relativedelta

from blackbox.utils.cooldown import parse_config_cooldown
from blackbox.utils.cooldown import should_we_send


@pytest.fixture
def cooldown_config():
    """Test human view cool down period."""
    return '2h 7M 3s'


def test_regex_cooldown_setting(cooldown_config):
    """Test parsing cool down period."""
    delta = parse_config_cooldown(cooldown_config)
    assert delta == relativedelta(hours=2, minutes=7, seconds=3)


def test_should_we_send_notification(cooldown_config):
    """Test if we allowed to send notification right now."""
    delta = parse_config_cooldown(cooldown_config)
    now = datetime.now()
    last_send_exact = now - delta
    assert should_we_send(last_send_exact, delta) is True
    last_send_long_ago = now - delta - relativedelta(hours=1)
    assert should_we_send(last_send_long_ago, delta) is True
    last_send_recent = now - delta + relativedelta(seconds=10)
    assert should_we_send(last_send_recent, delta) is False
