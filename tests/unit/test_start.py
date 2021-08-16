from unittest.mock import MagicMock, patch

import charm

from ops.charm import ActionEvent

import pytest

import requests_mock


@pytest.mark.parametrize(
    "config_expected",
    [
        (200, True),
        (404, False),
    ],
    ids=[
        "success",
        "failure",
    ],
)
def test_updated_password(harness, config_expected):
    url = "https://localhost:9200/_plugins/_security/api/account"

    status_code, expected = config_expected

    with patch(
        "charm.generate_random_password", return_value="random_password"
    ), requests_mock.Mocker() as m:
        m.put(url, status_code=status_code)

        updated, new_password = charm.updated_admin_password("")

        assert updated == expected
        assert new_password == "random_password"


@pytest.mark.parametrize(
    "config_expected",
    [
        (True, "new_password"),
        (False, "new_password"),
    ],
    ids=[
        "success",
        "failure",
    ],
)
def test_regenerate_admin_password_action(harness, config_expected):
    updated, new_password = config_expected

    old_password = "default_password"
    harness.charm._state.admin_password = old_password

    with patch("charm.updated_admin_password", return_value=(updated, new_password)):
        harness.charm._on_regenerate_admin_password_action(None)
        if updated:
            assert harness.charm._state.admin_password == new_password
        else:
            assert harness.charm._state.admin_password == old_password


def test_reveal_password(harness):
    act = MagicMock(spec=ActionEvent)
    harness.charm._state.admin_password = "testing"
    harness.charm._on_reveal_admin_password_action(act)
    act.set_results.assert_called_with({"username": "admin", "password": "testing"})
