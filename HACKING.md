# Development
## Configure dependencies

```bash
sudo usermod -a -G microk8s $USER
newgrp microk8s  # or relogin

sudo snap install microk8s --classic --channel=1.18/stable
sudo snap install juju
sudo snap install charmcraft

# Create an alias to kubectl
sudo snap alias microk8s.kubectl kubectl

# Enable firewall for traffic from and to k8s
sudo ufw allow in on cni0 && sudo ufw allow out on cni0
sudo ufw default allow routed

microk8s enable dashboard dns ingress storage
microk8s status --wait-ready
```

## Deploying
```bash
# Bootstrap juju
juju bootstrap microk8s micro
juju add-model testing

# Check deployment
kubectl get all -n controller-micro
kubectl get all -n testing

# Clone the charm code
git clone https://github.com/dasm/charm-opensearch-k8s && cd charm-opensearch-k8s

# Build the charm package
charmcraft build

# Deploy!
juju deploy ./opensearch-k8s.charm --resource image=opensearchproject/opensearch:1.0.0-rc1

# When done, you can stop microk8s
microk8s stop
```

## Debugging
```bash
watch -n1 -c juju status --color

# Change verbositoy
juju model-config logging-config="<root>=INFO;unit=DEBUG"
juju debug-log


microk8s kubectl logs pod/opensearch-k8s-0 -c opensearch -n development
microk8s kubectl logs pod/opensearch-k8s-0 -c charm -n development

kubectl exec -it pod/opensearch-k8s-0 -c opensearch -n development -- bash
kubectl exec -it pod/opensearch-k8s-0 -c opensearch -n development -- /charm/bin/pebble plan
kubectl exec -it pod/opensearch-k8s-0 -c opensearch -n development -- /charm/bin/pebble services
```
