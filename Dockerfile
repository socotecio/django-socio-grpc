FROM --platform=linux/amd64 python:3.8

ENV PYTHONUNBUFFERED 1

WORKDIR /opt/code

RUN apt-get update \
    && apt-get install curl locales gettext -y 

RUN sed -i 's/^# *\(fr_FR.UTF-8\)/\1/' /etc/locale.gen
RUN sed -i 's/^# *\(en_US.UTF-8\)/\1/' /etc/locale.gen
RUN locale-gen

RUN pip install --no-cache-dir psycopg2 poetry

RUN poetry config virtualenvs.create false

COPY pyproject.toml .
COPY poetry.lock .

RUN poetry install
