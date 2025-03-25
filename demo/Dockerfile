FROM python:3.12.3-slim

ENV PORT 8501

WORKDIR /app

COPY requirements.txt /app

RUN pip install -U pip setuptools
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app.py /app

EXPOSE $PORT

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]