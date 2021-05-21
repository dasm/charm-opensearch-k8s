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

from charms.nginx_ingress_integrator.v0.ingress import IngressRequires

from ops.charm import CharmBase, ConfigChangedEvent, PebbleReadyEvent
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, ModelError
from ops.pebble import ConnectionError, ServiceStatus, ChangeError

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
        self.framework.observe(self.on.opensearch_pebble_ready, self._on_opensearch_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)

        self.state.set_default(auto_start=True)
        self.state.set_default(jvm_heap_size="512m")
        self.state.set_default(cluster_name="opensearch-cluster")
        self.state.set_default(node_name="opensearch-node1")
        self.state.set_default(discovery_seed_hosts="opensearch-node1")
        self.state.set_default(cluster_initial_master_nodes="opensearch-node1")

        self.ingress = IngressRequires(
            self,
            {
                "service-hostname": "opensearch.juju",
                "service-name": self.app.name,
                "service-port": 9200,
            },
        )


    def _opensearch_layer(self):
        environment = {
            "OPENSEARCH_JAVA_OPTS": f"-Xms{self.state.jvm_heap_size} -Xmx{self.state.jvm_heap_size}",
        }

        # Install missing "su"

        cmd = (
            'su -p opensearch -c "/usr/share/opensearch/bin/opensearch '
            f'-Ecluster.name={self.state.cluster_name} '
            f'-Enode.name={self.state.node_name} '
            f'-Ediscovery.seed_hosts={self.state.discovery_seed_hosts} '
            f'-Ecluster.initial_master_nodes={self.state.cluster_initial_master_nodes}"'
        )

        return {
            "summary": "opensearch layer",
            "description": "pebble config layer for opensearchproject/opensearch",
            "services": {
                "p": {
                    "override": "merge",
                    "command": "yum install -y procps",
                    "startup": "enabled",
                    "summary": "procps",
                },
                "opensearch": {
                    "requires": "p",
                    "override": "merge",
                    "environment": environment,
                    "summary": "opensearch",
                    "command": cmd,
                    "startup": "disabled",
                }
            }
        }


    def _on_opensearch_pebble_ready(self, event: PebbleReadyEvent) -> None:
        container = event.workload
        layer = self._opensearch_layer()
        container.add_layer("opensearch", layer, combine=True)
        container.autostart()

        if container.get_service("p").is_running():
            self.unit.status = BlockedStatus("Waiting for procps")
            return

        container.start("opensearch")
        self.unit.status = ActiveStatus()

    def _on_config_changed(self, event: ConfigChangedEvent) -> None:
        container = self.unit.get_container("opensearch")
        try:
            service = container.get_service("opensearch")
        except ConnectionError:
            logger.info("Pebble API not yet ready, waiting...")
            return
        except ModelError:
            logger.info("Service 'opensearch' not yet defined, waiting...")
            return


        environment = {}
        for env_name, config in OPENSEARCH_ARGS.items():
            cfg = self.config[config]
            if cfg:
                environment[env_name] = cfg

        layer = self._opensearch_layer()
        plan = container.get_plan()
        if plan.services["environment"] != layer["services"]["environment"]:
            container.add_layer("opensearch", layer, combine=True)
            logging.debug("Added config layer to Pebble plan")

            if service.is_running():
                container.stop("opensearch")
            container.start("opensearch")
            logging.info("Restarted 'opensearch' service")
        self.unit.status = ActiveStatus()


if __name__ == "__main__":
    main(CharmOpenSearch)
