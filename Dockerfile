FROM python:3.10 AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED 1

WORKDIR /opt/code

RUN apt update \
    && apt install curl locales gettext -y \
    && apt clean

RUN sed -i 's/^# *\(fr_FR.UTF-8\)/\1/' /etc/locale.gen
RUN sed -i 's/^# *\(en_US.UTF-8\)/\1/' /etc/locale.gen
RUN locale-gen

COPY pyproject.toml .
COPY uv.lock .

FROM builder AS server

COPY ./django_socio_grpc /opt/code/django_socio_grpc
ENV UV_PROJECT_ENVIRONMENT /opt/venv
RUN uv sync

FROM builder AS docs

RUN apt update \
&& apt -y install enchant-2 entr \
&& apt clean

COPY docs docs
COPY ./django_socio_grpc /opt/code/django_socio_grpc
RUN uv sync --group docs
WORKDIR /opt/code/docs
RUN uv run make html
WORKDIR /opt/code
