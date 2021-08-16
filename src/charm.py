#!/usr/bin/env python3

import json
import logging
import secrets
import string
from collections import OrderedDict
from io import StringIO

from charms.nginx_ingress_integrator.v0.ingress import IngressRequires

from ops.charm import CharmBase, ConfigChangedEvent, PebbleReadyEvent
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus

import requests

import yaml

logger = logging.getLogger(__name__)


def random_password(length=32):
    alphabet = string.ascii_letters + string.digits
    password = "".join(secrets.choice(alphabet) for i in range(length))
    return password


def unblock_users(container):
    path = (
        "/usr/share/opensearch/"
        "plugins/opensearch-security/securityconfig/internal_users.yml"
    )

    users_file = container.pull(path)
    internal_users = yaml.safe_load(users_file)

    for user in ("admin", "kibanaserver"):
        internal_users[user]["reserved"] = False

    logger.debug(internal_users)

    users_file = StringIO(yaml.safe_dump(internal_users))
    container.push(path, users_file)
    logger.info("Users unreserved")


def updated_admin_password(current_password):
    new_password = random_password()

    url = "https://localhost:9200/_plugins/_security/api/account"
    headers = {"Content-Type": "application/json"}
    data = {"current_password": current_password, "password": new_password}
    auth = requests.auth.HTTPBasicAuth("admin", current_password)
    # root_ca_path = "/usr/share/opensearch/config/root-ca.pem"
    # root_ca_file = container.pull(root_ca_path)
    # root_ca = root_ca_file.read()

    r = requests.put(
        url, data=json.dumps(data), headers=headers, verify=False, auth=auth
    )

    logger.debug(r)
    return r.status_code == requests.codes.ok, new_password


class CharmOpenSearch(CharmBase):
    """Charm the service."""

    _state = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.opensearch_pebble_ready, self._on_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(
            self.on.reveal_admin_password_action, self._on_reveal_admin_password_action
        )
        self.framework.observe(
            self.on.regenerate_admin_password_action,
            self._on_regenerate_admin_password_action,
        )

        self._state.set_default(admin_password="admin")

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
                        "OPENSEARCH_JAVA_OPTS": f"-Xms{jvm_heap_size} -Xmx{jvm_heap_size}",  # noqa: E501
                        "JAVA_HOME": "/usr/share/opensearch/jdk",
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

        unblock_users(container)

        container.autostart()
        self.unit.status = ActiveStatus("ready")

    def _on_reveal_admin_password_action(self, event):
        return event.set_results(
            OrderedDict(username="admin", password=self._state.admin_password)
        )

    def _on_regenerate_admin_password_action(self, event):
        updated, new_password = updated_admin_password(self._state.admin_password)
        if updated:
            self._state.admin_password = new_password
            logger.info("Admin password changed")
        else:
            logger.error("Password not updated")

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
