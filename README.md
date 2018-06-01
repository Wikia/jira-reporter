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
