FROM python:2-alpine

ENV PIP_INDEX_URL=https://artifactory.wikia-inc.com/artifactory/api/pypi/pypi/simple

ADD . /opt/jira-reporter

WORKDIR /opt/jira-reporter

RUN apk update && \
    apk upgrade && \
    apk add \
        build-base \
        libffi-dev \
        openssl-dev \
        python-dev && \
    rm -rf /var/cache/apk/* && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --editable . && \
    cp docker/config.py reporter/ && \
    adduser -D -g '' -s /bin/ash wikia

USER wikia

ENTRYPOINT [ "make", "check" ]
