# Introduction
This charm is used to configure OpenSearch into a kubernetes cloud.

# Deployment
Deploy the app with an attached container resource

```bash
juju deploy opensearch-k8s --resource image=opensearch-project/opensearch:latest
```

# Development
```bash
# Clone the charm code
git clone https://github.com/dasm/charm-opensearch-k8s && cd charm-opensearch-k8s

# Build the charm package
charmcraft build

# Deploy!
juju deploy opensearch-k8s --resource image=opensearch-project/opensearch:latest ./charm-opensearch-k8s.charm
```

## Debugging
```bash
watch -n1 -c juju status --color
juju debug-log

microk8s kubectl logs pod/opensearch-k8s-0 -c opensearch -n development
microk8s kubectl logs pod/opensearch-k8s-0 -c charm -n development

k exec -it pod/opensearch-k8s-0 -c opensearch -n development -- ash
k exec -it pod/opensearch-k8s-0 -c opensearch -n development -- /charm/bin/pebble plan
k exec -it pod/opensearch-k8s-0 -c opensearch -n development -- /charm/bin/pebble services
```
