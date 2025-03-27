# Build and push image


```bash
# Login to docker
gcloud auth configure-docker europe-west4-docker.pkg.dev

# Biuld image
docker build -t  europe-west4-docker.pkg.dev/mitrix-tools/mitrixgpt-agent/mitrixgpt-agent:latest .

# Push image
docker push  europe-west4-docker.pkg.dev//mitrix-tools/mitrixgpt-agent/mitrixgpt-agent:latest
```

# Restart Deployment

```bash
kubectl rollout restart deployment/agent-mitrixgpt-agent -n mitrix-tools
```