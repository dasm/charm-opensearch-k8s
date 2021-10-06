# Introduction
## What is OpenSearch?
[OpenSearch] is a community-driven, open source search and analytics suite derived from Apache 2.0 licensed Elasticsearch 7.10.2 & Kibana 7.10.2. It consists of a search engine daemon, OpenSearch, and a visualization and user interface, OpenSearch Dashboards. OpenSearch enables people to easily ingest, secure, search, aggregate, view, and analyze data. These capabilities are popular for use cases such as application search, log analytics, and more. With OpenSearch people benefit from having an open source product they can use, modify, extend, monetize, and resell how they want. At the same time, OpenSearch will continue to provide a secure, high-quality search and analytics suite with a rich roadmap of new and innovative functionality.

## What is Charm?
[Charms] are sets of scripts for deploying and operating software. With event handling built in, they can declare interfaces that fit charms for other services, so relationships can be formed.

## Charm OpenSearch for Kubernetes
This is an implementation of OpenSearch for Kubernetes with use of a charm.

# Deployment
Deploy the app with an attached container resource.

```bash
juju deploy opensearch-k8s
juju deploy nginx-ingress-integrator
juju relate nginx-ingress-integrator opensearch-k8s
juju run-action opensearch-k8s/0 reveal-admin-password --wait
curl --insecure -u admin:<password> -k https://<ingress_ip>:9200
```

Road Map
---------

### Relations
* [x] define relations to use ingress controller
* [ ] define app relations for HA deployments (password share)

### Configuration
* [X] Autogeneration of secure password during a startup.
* [ ] Support for license file as well as license URL
* [ ] Add option to upload custom `internal_users.yml`
* [ ] Configure upload of cacert files

[OpenSearch]: https://www.opensearch.org/
[Charms]: https://jaas.ai/how-it-works
