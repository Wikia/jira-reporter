jira-reporter
-------------

[![Build Status](https://travis-ci.org/Wikia/jira-reporter.svg?branch=master)](https://travis-ci.org/Wikia/jira-reporter)

Automated JIRA reporting of issue from various sources (PHP fatal errors, exceptions, SQL queries errors, CSRF issues, ...) also known as **[Norsk skogkatt](https://no.wikipedia.org/wiki/Norsk_skogkatt)**.

![](https://user-images.githubusercontent.com/1929317/40851261-2ba2d2f2-65c7-11e8-9f01-8a6e6b5302c3.jpg)

## Installation

* clone the repository
* run

```
virtualenv env
source env/bin/activate
pip install -e .
```

## Make sure to test cover your changes

```
make test
```

## CronJob: `jira-reporter`

### Synopsis

* script: `make check`
* schedule: five minutes after every hour

### Workflow

Every time you make changes to any of the files in this repository, a new Docker
image has to be built and pushed to Artifactory. `make cronjob-deploy` will do
it for you. Refer to the `Makefile` for details.

**IMPORTANT: Changes will affect production environment. If you want to work on `dev`,
make sure to examime the files and make required changes.**

### Useful Commands

* `$ kubectl --context=kube-sjc-prod --namespace=prod get cronjob jira-reporter`:
  display cronjob metadata

* `kubectl --context=kube-sjc-prod --namespace=prod get pods | grep jira-reporter`:
  list all pods associated with the cronjob

* `kubectl --context=kube-sjc-prod --namespace=prod logs -f jira-reporter-1549370100-p7mmr`:
  monitor the output of your script; remember to check the pod name with `get pods` command.

