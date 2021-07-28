# Introduction
This charm is used to configure OpenSearch into a kubernetes cloud.
After successful deployment, the OpenSearch is configured with default `admin:admin`
credentials. To change that, you need to run `juju run-action opensearck-k8s/0 regenerate-admin-password --wait` to change that and make it more secure.

# Deployment
Deploy the app with an attached container resource

```bash
juju deploy opensearch-k8s --resource image=opensearchproject/opensearch:1.0.0-rc1
juju deploy nginx-ingress-integrator
juju relate nginx-ingress-integrator opensearch-k8s
curl -u admin:admin -k https://<ingress_ip>:9200 -u
```

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
sudo snap alias microk8s.kubectl k

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
k get all -n controller-micro
k get all -n testing

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

k exec -it pod/opensearch-k8s-0 -c opensearch -n development -- bash
k exec -it pod/opensearch-k8s-0 -c opensearch -n development -- /charm/bin/pebble plan
k exec -it pod/opensearch-k8s-0 -c opensearch -n development -- /charm/bin/pebble services
```

Road Map
---------

### Relations
* [x] define relations to use ingress controller
* [ ] define app relations for HA deployments (password share)

### Configuration
* [ ] Support for license file as well as license URL
* [ ] Add option to upload custom `internal_users.yml`
* [ ] Configure upload of cacert files
