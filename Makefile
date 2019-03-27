dev-infra:
	docker-compose -f ./env/dev/docker-compose.yml up -d

dev-run:
	solo run --solocfg ./test_config.yml

dev-boot: dev-infra dev-run

dev-stop:
	docker-compose -f ./env/dev/docker-compose.yml down

typecheck:
	python -m mypy --config-file setup.cfg --package solo
