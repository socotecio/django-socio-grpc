FROM --platform=linux/amd64 python:3.10 AS builder

ENV PYTHONUNBUFFERED 1

WORKDIR /opt/code

RUN apt update \
    && apt install curl locales gettext -y \
    && apt clean

RUN sed -i 's/^# *\(fr_FR.UTF-8\)/\1/' /etc/locale.gen
RUN sed -i 's/^# *\(en_US.UTF-8\)/\1/' /etc/locale.gen
RUN locale-gen

RUN pip install --no-cache-dir psycopg2 poetry

RUN poetry config virtualenvs.create false

COPY pyproject.toml .
COPY poetry.lock .


FROM builder AS server

RUN poetry install

FROM builder AS docs

RUN apt update \
  && apt -y install enchant-2 entr \
  && apt clean

COPY docs docs
RUN poetry install --with docs
RUN cd docs && make html
