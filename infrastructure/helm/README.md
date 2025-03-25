# Get cluster credentials

```bash
gcloud container clusters get-credentials mitrix-tools-dev-cluster \
  --region europe-west4 \
  --project mitrix-tools
```

# install postgres

```bash
helm upgrade --install postgres oci://registry-1.docker.io/bitnamicharts/postgresql  --values ./infrastructure/helm/postgres/values.yaml --namespace mitrix-tools --create-namespace
```


# install qdrant
```bash
helm repo add qdrant https://qdrant.github.io/qdrant-helm
helm repo update
helm upgrade --install qdrant qdrant/qdrant --values ./infrastructure/helm/qdrant/values.yaml --namespace mitrix-tools --create-namespace
```


# install application itself

```bash
helm upgrade -i agent . --values values.traefik.yaml --namespace mitrix-tools
```