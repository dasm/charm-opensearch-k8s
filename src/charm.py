#!/usr/bin/env python3

import logging
from collections import OrderedDict

from charms.nginx_ingress_integrator.v0.ingress import IngressRequires

from ops.charm import CharmBase, ConfigChangedEvent, PebbleReadyEvent, UpdateStatusEvent
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus


logger = logging.getLogger(__name__)


class CharmOpenSearch(CharmBase):
    """Charm the service."""

    stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.opensearch_pebble_ready, self._on_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)

        self.ingress = IngressRequires(
            self,
            {
                "service-hostname": self.config["node_name"],
                "service-name": self.app.name,
                "service-port": 9200,
            },
        )

    def _opensearch_layer(self):
        cluster_name = self.config["cluster_name"]
        node_name = self.config["node_name"]
        seed = self.config["discovery_seed_hosts"]
        cluster_type = self.config["type"]

        cmd = (
            "/usr/share/opensearch/bin/opensearch "
            f"-Ecluster.name={cluster_name} "
            f"-Enode.name={node_name} "
            f"-Ediscovery.seed_hosts={seed} "
            f"-Ediscovery.type={cluster_type}"
        )

        jvm_heap_size = self.config["jvm_heap_size"]

        return {
            "summary": "opensearch layer",
            "description": "pebble config layer for opensearchproject/opensearch",
            "services": {
                "opensearch": {
                    "user": "opensearch",
                    "override": "merge",
                    "environment": {
                        "OPENSEARCH_JAVA_OPTS": f"-Xms{jvm_heap_size} -Xmx{jvm_heap_size}"
                    },
                    "summary": "opensearch",
                    "command": cmd,
                    "startup": "enabled",
                }
            },
        }

    def _on_pebble_ready(self, event: PebbleReadyEvent) -> None:
        container = event.workload

        layer = self._opensearch_layer()
        container.add_layer("opensearch", layer, combine=True)
        container.autostart()
        self.unit.status = ActiveStatus("ready")

    def _on_config_changed(self, event: ConfigChangedEvent) -> None:
        container = self.unit.get_container("opensearch")
        layer = self._opensearch_layer()
        services = container.get_plan().to_dict().get("services", {})

        config_changed = bool(services != layer["services"])

        self.unit.status = ActiveStatus("in progress")
        if config_changed:
            container.add_layer("opensearch", layer, combine=True)
            logging.info("Added updated layer 'opensearch' to Pebble plan")

            if container.get_service("opensearch").is_running():
                container.stop("opensearch")
                container.start("opensearch")
                logging.info("Restarted opensearch service")
        self.unit.status = ActiveStatus("ready")


if __name__ == "__main__":
    main(CharmOpenSearch, use_juju_for_storage=True)
