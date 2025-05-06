# Build and push image


```bash
# Login to docker
gcloud auth configure-docker europe-west4-docker.pkg.dev

# Biuld image
docker build -t  europe-west4-docker.pkg.dev/company-tools/companygpt-assistant/companygpt-assistant:latest .

# Push image
docker push  europe-west4-docker.pkg.dev/company-tools/companygpt-assistant/companygpt-assistant:latest
```

# Restart Deployment

```bash
kubectl rollout restart deployment/assistant-companygpt-assistant -n company-tools
```