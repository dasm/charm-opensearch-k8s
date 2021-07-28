from charm import CharmOpenSearch

from ops.testing import Harness

import pytest


@pytest.fixture
def harness():
    _harness = Harness(CharmOpenSearch)
    _harness.set_model_name("testing")
    _harness.begin()
    yield _harness
    _harness.cleanup()
