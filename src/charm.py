#!/usr/bin/env python3
# Copyright 2021 dasm
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Charm the service.

Refer to the following post for a quick-start guide that will help you
develop a new k8s charm using the Operator Framework:

    https://discourse.charmhub.io/t/4208
"""

import logging

from charms.nginx_ingress_integrator.v0.ingress import IngressRequires

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus

logger = logging.getLogger(__name__)

class CharmOpensearchK8SCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self._on_config_changed)

        self.ingress = IngressRequires(
            self, {
                "service-hostname": self.config["external-hostname"],
                "service-name": self.app.name,
                "service-port": 9200,
            }
        )

    def _on_config_changed(self, _):
        pass


if __name__ == "__main__":
    main(CharmOpensearchK8SCharm)
