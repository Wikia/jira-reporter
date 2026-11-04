FROM artifactory.wikia-inc.com/platform/fandom-python:3.14-202611040642

ENV PIP_INDEX_URL=https://artifactory.wikia-inc.com/artifactory/api/pypi/pypi/simple

ADD . /opt/jira-reporter

WORKDIR /opt/jira-reporter

USER 0

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
        libssl-dev \
        python3-dev && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --editable . && \
    cp docker/config.py reporter/

USER 65535:65535

ENTRYPOINT [ "make", "check" ]
