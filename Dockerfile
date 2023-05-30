FROM python:3.10-buster

ENV LANG C.UTF-8
ENV TZ UTC
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /backend/app:/backend
ENV TEAM xterm-256color

RUN apt-get update && apt-get install -y \
    git \
    gcc \
    libmariadb-dev \
    curl
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

WORKDIR /backend
COPY ./pyproject.toml ./poetry.lock /backend/

RUN poetry install --no-root
RUN poe _bash_completion >> /root/.bashrc