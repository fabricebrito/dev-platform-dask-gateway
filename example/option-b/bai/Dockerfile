FROM docker.io/python:3.10-slim-bullseye

ADD requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm -rf /tmp/requirements.txt

ENV PYTHONPATH=/app

ADD bai.py /app/app.py

ENTRYPOINT []
