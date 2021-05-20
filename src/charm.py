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
from collections import OrderedDict

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus

logger = logging.getLogger(__name__)

OPENSEARCH_ARGS = OrderedDict(
    JVM_HEAP_SIZE="jvm-heap-size",
    CLUSTER_NAME="cluster-name",
)


class CharmOpenSearch(CharmBase):
    """Charm the service."""

    state = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.resume_action, self._on_resume_action)

        self.state.set_default(auto_start=True)
        self.state.set_default(jvm_heap_size="512m")


    def _on_update_status(self, _):
        container = self.unit.get_container("opensearch")
        if not self.state.auto_start:
            self.unit.status = MaintenanceStatus("opensearch service is paused")
        elif not container.get_service("opensearch").is_running():
            self.unit.status = BlockedStatus("opensearch service isn't running")
        else:
            self.unit.status = ActiveStatus("ready")

    def _on_config_changed(self, _):
        container = self.unit.get_container("opensearch")
        layer = self._layer()

        services = container.get_plan().to_dict().get("services", {})
        if services != layer["services"]:
            container.add_layer("opensearch", layer, combine=True)
            logging.info("Added updated layer 'opensearch' to Pebble plan")

        if container.get_service("opensearch").is_running():
            container.stop("opensearch")

        if self.state.auto_start and not container.get_service("opensearch").is_running():
            container.start("opensearch")
            logging.info("Restarted opensearch service")

        self._on_update_status(None)

    def _on_resume_action(self, _):
        self.state.auto_start = True
        self._do_config_change()

    def _on_pause_action(self, _):
        self.state.auto_start = False
        self._do_config_change()

    def _layer(self):
        jvm_heap_size = self.state.jvm_heap_size
        environment = {
            "OPENSEARCH_JAVA_OPTS": f"-Xms{jvm_heap_size} -Xmx{jvm_heap_size}",
        }

        for env_name, config in OPENSEARCH_ARGS.items():
            cfg = self.config[config]
            if cfg:
                environment[env_name] = cfg

        cmd = "bash -c '/sbin/entrypoint.sh start > /var/log/opensearch.log 2>&1'"
        return {
            "summary": "opensearch layer",
            "description": "pebble config layer for opensearch",
            "services": {
                "opensearch": {
                    "override": "replace",
                    "summary": "opensearch",
                    "command": cmd,
                    "startup": "enabled" if self.state.auto_start else "disabled",
                    "environment": environment,
                    },
                },
            }


if __name__ == "__main__":
    main(CharmOpenSearch)
