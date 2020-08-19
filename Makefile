.PHONY: test coverage lint vault docker-image docker-push cronjob-delete cronjob-apply

project_name = reporter
coverage_options = --include='$(project_name)/*' --omit='$(project_name)/test/*,$(project_name)/config.py,*__init__.py'
pwd = $(shell pwd)
k8s_context = kube-sjc-prod
k8s_namespace = prod

test:
	py.test -x $(project_name) -vv

coverage:
	rm -f .coverage*
	rm -rf htmlcov/*
	coverage run -p -m py.test -x $(project_name)
	coverage combine
	coverage html -d htmlcov $(coverage_options)
	coverage xml -i
	coverage report $(coverage_options)

lint:
	pylint $(project_name)/ --ignore=test

check:
	python $(project_name)/bin/check.py

sandbox:
	python $(project_name)/bin/sandbox.py 2>&1 | less

update_classifier_config:
	python ${project_name}/bin/update_classifier_config.py

vault:
	rm -rf docker/vault docker/secrets
	mkdir -p docker/vault
	docker run --interactive --tty --rm \
		--volume "${pwd}/docker/vault:/var/lib/secrets" \
		--env USER=${$USER} \
		artifactory.wikia-inc.com/ops/init-vault:0.0.42 \
		--ldap \
		"secret/app/prod/jira-reporter"
	mkdir -p docker/secrets
	cp docker/vault/secrets.json docker/secrets/
	rm -rf docker/vault

docker-image:
	docker build --no-cache --rm \
		--tag artifactory.wikia-inc.com/sus/jira-reporter:latest \
		--file docker/Dockerfile .

docker-push:
	docker push artifactory.wikia-inc.com/sus/jira-reporter:latest

cronjob-delete:
	kubectl --context=${k8s_context} --namespace=${k8s_namespace} delete cronjob --ignore-not-found=true jira-reporter

cronjob-apply:
	kubectl --context=${k8s_context} --namespace=${k8s_namespace} apply --filename=docker/cronjob.yaml

cronjob-deploy: docker-image docker-push cronjob-delete cronjob-apply
