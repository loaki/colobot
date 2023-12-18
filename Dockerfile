# syntax = docker/dockerfile:1.4
FROM python:3.11-slim-bookworm

WORKDIR /app

COPY . /app

ENV PYTHONPATH /python

RUN python3 -m pip install -r requirements.txt

CMD ["/usr/bin/env", "python3", "-m", "bot"]
