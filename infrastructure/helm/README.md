# Get cluster credentials

```bash
gcloud container clusters get-credentials company-tools-dev-cluster \
  --region europe-west4 \
  --project company-tools
```

# install postgres

```bash
helm upgrade --install postgres oci://registry-1.docker.io/bitnamicharts/postgresql  --values ./infrastructure/helm/postgres/values.yaml --namespace company-tools --create-namespace
```


# install qdrant
```bash
helm repo add qdrant https://qdrant.github.io/qdrant-helm
helm repo update
helm upgrade --install qdrant qdrant/qdrant --values ./infrastructure/helm/qdrant/values.yaml --namespace company-tools --create-namespace
```


# install application itself

```bash
helm upgrade -i assistant . --values values.traefik.yaml --namespace company-tools
```