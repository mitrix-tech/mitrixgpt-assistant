# -----------------------------
# Configuration Variables
# -----------------------------
PROJECT_ID       ?= mitrix-tools
SERVICE_NAME     ?= mitrixgpt-demo
REGION           ?= europe-central2
IMAGE            ?= gcr.io/${PROJECT_ID}/${SERVICE_NAME}

ENV_PROJECT_ID       ?= mitrixgpt-demo
ENV_REGION           ?= europe-central2
OPENAI_API_KEY       ?= ${OPENAI_API_KEY}
LANGSMITH_API_KEY    ?= ${LANGSMITH_API_KEY}
LANGSMITH_PROJECT    ?= mitrixbot-dev
LANGSMITH_TRACING     ?= true
COMMIT_HASH := $(shell git rev-parse --short HEAD)

ENV_VARS = PROJECT_ID=$(ENV_PROJECT_ID),REGION=$(ENV_REGION),OPENAI_API_KEY=$(OPENAI_API_KEY),\
LANGSMITH_API_KEY=$(LANGSMITH_API_KEY),LANGSMITH_PROJECT=$(LANGSMITH_PROJECT),LANGSMITH_TRACING=$(LANGSMITH_TRACING)

# -----------------------------
# Targets
# -----------------------------

init:
	gcloud init
	gcloud services enable containerregistry.googleapis.com
	gcloud services enable artifactregistry.googleapis.com
	gcloud services enable run.googleapis.com

auth:
	gcloud auth login
	gcloud config set project $(PROJECT_ID)

build:
	docker build -t $(IMAGE):$(COMMIT_HASH) .

push:
	docker push $(IMAGE):$(COMMIT_HASH)

deploy: auth build push
	gcloud run deploy $(SERVICE_NAME) \
		--image $(IMAGE) \
		--platform managed \
		--region $(REGION) \
		--set-env-vars $(ENV_VARS) \
		--allow-unauthenticated \
		--min-instances 1 \
		--max-instances 1 \
		--cpu 4 \
		--memory 2Gi \
		--port 8501

	@echo "Service deployed to: $$(gcloud run services describe $(SERVICE_NAME) \
		--region $(REGION) --format 'value(status.url)')"
