FROM python:3.12.3-slim

ENV PORT 3000
EXPOSE $PORT

WORKDIR /app

COPY ./src/default.configuration.json /app/configurations/config.json
COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY ./src /app

ENV PYTHONPATH "${PYTHONPATH}:/app"

ENTRYPOINT ["python", "-B", "app.py"]