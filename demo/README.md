# MitrixGPT Demo
[![Python version](https://img.shields.io/badge/streamlit-v1.43.0-blue)](#)
---

A simple Streamlit application that interacts with the MitrixGPT REST API. The app allows you to:

- Create and manage chats
- Upload files or links to generate embeddings
- Send messages and retrieve responses from the MitrixGPT service

## Features

- **Create & Delete Chats**  
  Create a new chat instance, or remove existing ones, managed by the MitrixGPT backend.
  
- **Upload Documents**  
  Upload txt, PDF, Markdown to generate embeddings in Knowledge Base. Batch upload supported as .zip, gzip and .tar archives.

- **Link Embeddings**  
  Provide a URL to parse text content and produce embeddings, with link-based crawling support.

- **Chat Interface**  
  A conversation-like interface, showing user and assistant messages.

- **Error Handling**  
  The app catches and displays any HTTP errors from the MitrixGPT API (e.g., invalid file types, concurrent embedding tasks, etc.).


## Requirements

- **Python 3.12**
- [Poetry](https://python-poetry.org/) or `pip` for installing dependencies
- Access to a MitrixGPT API endpoint, defined by the environment variable `MITRIX_GPT_API_URL`
- Docker (if you plan to build and deploy the container image)
- Google Cloud SDK (if deploying to Google Cloud Run)

## Local Development

1. **Clone the Repo**  
   ```bash
   git clone https://github.com/mitrix-tech/mitrixgpt-agent.git
   cd mitrixgpt-agent/demo
   ```

2. **Install Dependencies**  
   If using `pip`:
   ```bash
   pip install -r requirements.txt
   ```
   Or using Poetry:
   ```bash
   poetry install
   ```

3. **Set the API URL**  
   By default, the app uses `MITRIX_GPT_API_URL` from your environment`.  
   Example:
   ```bash
   export MITRIX_GPT_API_URL="https://my-custom-gpt-agent.com/"
   ```

4. **Run the Streamlit App**  
   ```bash
   streamlit run app.py --server.port=8501 --server.address=0.0.0.0
   ```
   Then open [http://localhost:8501](http://localhost:8501) in your browser to interact with the app.

## Deploying to Google Cloud Run

A sample `deploy.sh` script is provided for building and deploying to Google Cloud Run. Steps:

### Configuration
```bash
PROJECT_ID="<YOUR_GCP_PROJECT_ID>"
SERVICE_NAME="<YOUR_GCP_SERIVCE_NAME>"
REGION="<YOUR_GCP_REGION>"
IMAGE="gcr.io/$PROJECT_ID/$SERVICE_NAME"
```

1. **Set up Google Cloud**  
   Ensure you have the Google Cloud SDK installed and are logged in:
   ```bash
   gcloud auth login
   gcloud config set project <YOUR_GCP_PROJECT_ID>
   ```

2. **Define environment variables**  
   Make sure `MITRIX_GPT_API_URL` is set in your current shell or passed into the script. If you are using a different variable name, update `deploy.sh` accordingly.

3. **Build and Deploy**  
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```
   - This script builds the Docker image, pushes it to Google Container Registry, and deploys to Cloud Run.
   - The script also sets environment variables (e.g. `MITRIX_GPT_API_URL`) in the Cloud Run service.

4. **Check Deployment**  
   After the script completes, it prints a service URL. Open that URL to view the running Streamlit demo.
