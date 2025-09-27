.PHONY: install
install:
	@echo "Installing libraries..."
	@poetry config installer.parallel false
	@poetry config installer.max-workers 1
	@if command -v gcloud >/dev/null 2>&1; then \
			echo "Configuring authentication for gen-ai repository..."; \
			poetry config http-basic.gen-ai-internal oauth2accesstoken "$$(gcloud auth print-access-token)"; \
	else \
			echo "WARNING: gcloud CLI not found. Authentication for gen-ai repository may fail."; \
			echo "Please install Google Cloud SDK (https://cloud.google.com/sdk/docs/install) and authenticate."; \
	fi
	@poetry install

.PHONY: update
update:
	@echo "Updating libraries..."
	@poetry config installer.parallel false
	@poetry config installer.max-workers 1
	@if command -v gcloud >/dev/null 2>&1; then \
			echo "Configuring authentication for gen-ai repository..."; \
			poetry config http-basic.gen-ai oauth2accesstoken "$$(gcloud auth print-access-token)"; \
	else \
			echo "WARNING: gcloud CLI not found. Authentication for gen-ai repository may fail."; \
			echo "Please install Google Cloud SDK (https://cloud.google.com/sdk/docs/install) and authenticate."; \
	fi
	@poetry update

.PHONY: test
test:
	@echo "Running tests..."
	@poetry run python -m pytest tests/ -v

inspector:
	DANGEROUSLY_OMIT_AUTH=true npx @modelcontextprotocol/inspector
