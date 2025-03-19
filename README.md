# mitrixgpt-agent

[![Python version](https://img.shields.io/badge/python-v3.12.3-blue)](#)
[![FastAPI version](https://img.shields.io/badge/fastapi-v0.115.6-blue)](#)

---

**mitrixgpt-agent** is a Retrieval Augmented Generation (RAG) system, providing a RESTful API server that integrates a Qdrant vector database for embeddings storage and PostgreSQL for chat history storage. The service uses [LangChain](https://python.langchain.com/) to orchestrate advanced workflows with Large Language Models (LLMs) and is built with the [FastAPI](https://fastapi.tiangolo.com/) framework.

## Table of Contents

1. [Overview](#overview)
2. [Endpoints](#endpoints)
   - [Chat Completions](#chat-completions-endpoint)
   - [Chat Management](#chat-management)
   - [Embeddings](#embedding-endpoints)
   - [Metrics](#metrics-endpoint)
3. [Local Development](#local-development)
4. [Docker Usage](#docker-usage)
5. [Configuration](#configuration)
6. [Architecture Overview](#architecture-overview)

---

## Overview

`mitrixgpt-agent` exposes endpoints to:
- **Chat Completions**: Converse with a knowledge-augmented assistant.
- **Chat Management**: Store/retrieve messages from PostgreSQL using a UUID-based chat identifier.  
- **Embeddings**: Generate embeddings from URLs or uploaded files for subsequent retrieval in Qdrant.
- **Metrics**: Observe usage metrics in Prometheus format.

When running the service, you can explore all the endpoints via **Swagger UI** at `http://localhost:3000/docs`.

---

## Endpoints

### Chat Completions Endpoint

Generates a response to user queries, optionally referencing relevant data from the Qdrant vector store. For ephemeral chat, you supply a `chat_history` array. Or specify a `chat_id` to load and store messages from your PostgreSQL database.

**Example**:

<details>
<summary>Request</summary>

```bash
curl -X POST 'http://localhost:3000/chat/completions' \
  -H 'Content-Type: application/json' \
  --data-raw '{
    "chat_query": "Hello, how can you help me?",
    "chat_history": ["Hi there!", "Hello!"],
    "chat_id": null
  }'
````
</details>

<details>
<summary>Response</summary>

```json
{
  "message": "I'm here to assist you with your questions about <some topic>.",
  "references": []
}
```
</details>

### Chat Management

#### Create a new chat (`POST /chat`)

Creates a new chat session and returns a UUID `chat_id`.

**Example**:
```bash
curl -X POST 'http://localhost:3000/chat'
```

**Response**:
```json
{
  "chat_id": "97f5483e-22b8-4781-bf2a-67176d6c7f45"
}
```

#### List all chats (`GET /chat`)

Returns an array of all chats, each with `id`, `title`, and a `created_at` timestamp.

#### Get a single chat (`GET /chat/{chat_id}`)

Retrieves a single chat by `chat_id`.

#### Remove a chat (`DELETE /chat/{chat_id}`)

Removes a chat, cascading deletions of associated messages.

#### List chat messages (`GET /chat/{chat_id}/messages`)

Returns messages (in chronological order) for a given `chat_id`. Optionally takes a `limit` query parameter.

---

### Embedding Endpoints

#### Generate from website (`POST /embeddings/generate`)

Given an initial `url` (and optional `filterPath`), crawls the domain for text, chunking and storing embeddings into Qdrant. Only one embedding process can run at a time—subsequent calls return a `409 Conflict` until the current process finishes.

**Example**:
```bash
curl -X POST 'http://localhost:3000/embeddings/generate' \
  -H 'Content-Type: application/json' \
  --data-raw '{"url":"https://docs.mia-platform.eu/"}'
```

**Response** (on success):
```json
{
  "statusOk": true
}
```

#### Generate from file (`POST /embeddings/generateFromFile`)

Uploads a file (PDF, text, markdown, or archived files containing those formats) to generate embeddings. Also locked to a single running process.

#### Generation status (`GET /embeddings/status`)

Returns `"running"` or `"idle"` to indicate whether an embedding generation process is currently active.

---

### Metrics Endpoint

The `/-/metrics` endpoint exposes Prometheus-format metrics about token usage (requests, replies, embeddings, ingestion) and more.  

**Example**:
```bash
curl 'http://localhost:3000/-/metrics'
```

---

## Local Development

1. **Clone the Repo & Setup**  
   ```bash
   git clone https://github.com/mitrix-tech/mitrixgpt-agent.git
   cd mitrixgpt-agent
   ```

2. **Create `.env` File**  
   Copy the sample environment file and update your credentials:
   ```bash
   cp src/default.env src/.env
   ```
   Adjust `DB_URI`, `VECTOR_DB_CLUSTER_URI`, `LLM_API_KEY`, and so on.

3. **Install Dependencies**  
   - Create and activate a Python virtual environment:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
   - Install from `requirements.txt`:
     ```bash
     pip install -r requirements.txt
     ```

4. **Run the Service**
   - Checkout sources directory:
   ```bash
   cd src
   ```
   - Run the service with
   ```bash
   # Option A: Using python
   dotenv -f .env run python -m app
   
   # Option B: Using uvicorn
   dotenv -f .env run uvicorn app:app --host 0.0.0.0 --port 3000
   ```
   
5. **Explore**  
   Go to `http://localhost:3000/docs` to see the Swagger UI.

---

## Docker Usage

1. **Build your image**  
   ```bash
   docker build . -t mitrixgpt-agent
   ```

2. **Run with Docker**  
   ```bash
   docker run \
     -p 3000:3000 \
     --env-file ./src/.env \
     -d mitrixgpt-agent
   ```
   This starts the container on port **3000**. 

**(Optional)** If you have a `docker-compose.yml`, you can also run:
```bash
docker-compose up --build
```
which spins up the service alongside Postgres/Qdrant containers defined in `docker-compose.yml`.

---

## Configuration

The service uses a JSON configuration file (default path specified by `CONFIGURATION_PATH` in your `.env`). For example:

```json
{
  "llm": {
    "name": "gpt-4o"
  },
  "embeddings": {
    "name": "text-embedding-3-small"
  },
  "vectorStore": {
    "dbName": "mitrixgpt",
    "collectionName": "mitrix-data",
    "indexName": "vector_index",
    "relevanceScoreFn": "Cosine",
    "embeddingKey": "embedding",
    "textKey": "text",
    "maxDocumentsToRetrieve": 4
  }
}
```

In your `.env` file, you might have lines such as:

```
PORT=3000
LOG_LEVEL=DEBUG
CONFIGURATION_PATH=default.configuration.json
VECTOR_DB_CLUSTER_URI=http://localhost:6333
DB_URI=postgres://postgres:postgres@localhost:5432/mitrixgpt
LLM_API_KEY="<YOUR LLM API KEY>"
EMBEDDINGS_API_KEY="<YOUR EMBEDDINGS API KEY>"
```

**Key config fields**:
- **llm**: The name/type of OpenAI language model used for chat completions (e.g., `gpt-4o`, `gpt-4o-mini`, etc.).  
- **embeddings**: OpenAI embedding model name (e.g., `text-embedding-3-small`, `text-embedding-3-large`).  
- **vectorStore**: Qdrant-based store details: the `collectionName`, `indexName`, similarity function, etc.
---

## Architecture Overview

```mermaid
flowchart LR
    user([User]) -->|#1 REST requests| server[FastAPI + LangChain]
    server -->|#2 Create or query embeddings| qdrant[(Qdrant)]
    server -->|#3 Store or retrieve chat<br>history as needed| postgres[(PostgreSQL)]
    server -->|#4 Send prompt<br>with context| openai[OpenAI / LLM]
    openai -->|#5 Return completion| server
    server -->|#6 Return response| user
```

This diagram illustrates the typical flow:
1. The client issues a request (either a new chat or a chat completion).  
2. The system retrieves or creates embeddings in Qdrant.  
3. Chat states (messages) are stored in Postgres if a `chat_id` is used.  
4. A prompt is sent to the configured LLM (OpenAI, Azure, etc.).  
5. The response is returned to the server, then to the user.  

---
