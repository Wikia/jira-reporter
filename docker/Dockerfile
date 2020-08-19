FROM python:3.8.5-alpine

ENV PIP_INDEX_URL=https://artifactory.wikia-inc.com/artifactory/api/pypi/pypi/simple

ADD . /opt/jira-reporter

WORKDIR /opt/jira-reporter

RUN apk update && \
    apk upgrade && \
    apk add \
        build-base \
        libffi-dev \
        openssl-dev \
        python3-dev && \
    rm -rf /var/cache/apk/* && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --editable . && \
    cp docker/config.py reporter/

USER 65535:65535

ENTRYPOINT [ "make", "check" ]
