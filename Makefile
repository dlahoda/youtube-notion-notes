-include .local.mk

.PHONY: test ingest-sample notion-sample require-sample-url require-notion-env

test:
	@bash ./scripts/test.sh

require-sample-url:
	@test -n "$(YNN_SAMPLE_URL)" || (echo "Missing YNN_SAMPLE_URL. Create .local.mk from .local.mk.example"; exit 1)

ingest-sample: require-sample-url
	@python ./ingest.py "$(YNN_SAMPLE_URL)"

require-notion-env:
	@test -n "$(NOTION_API_KEY)" || (echo "Missing NOTION_API_KEY"; exit 1)
	@test -n "$(NOTION_DATABASE_ID)" || (echo "Missing NOTION_DATABASE_ID"; exit 1)

notion-sample: require-sample-url require-notion-env
	@python ./ingest.py "$(YNN_SAMPLE_URL)" --export notion