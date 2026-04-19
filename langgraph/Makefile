IMAGE_NAME := langgraph-example:main

.PHONY: all install-deps test image run run-shell helm-package helm-install helm-uninstall clean

all: install-deps test image helm-package
install-deps:
	uv sync
test:
	uv run pytest -s
image:
	docker build -t $(IMAGE_NAME) .
run:
	docker run -p 8000:8000 -it $(IMAGE_NAME)
run-shell:
	docker run -it $(IMAGE_NAME) /bin/bash
helm-package:
	$(MAKE) -C deployment/helm package
helm-install:
	$(MAKE) -C deployment/helm install
helm-uninstall:
	$(MAKE) -C deployment/helm uninstall
clean:
	find . -name '__pycache__' -type d | xargs rm -rf
	find . -name '*.pyc' -delete
	find . -name '*.log' -delete
