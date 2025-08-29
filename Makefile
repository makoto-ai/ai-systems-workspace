SHELL := /bin/bash

.PHONY: clean-safe clean-safe-apply rotate-logs

clean-safe:
	./scripts/safe_cleanup.sh

clean-safe-apply:
	./scripts/safe_cleanup.sh --apply

rotate-logs:
	./scripts/safe_cleanup.sh --apply --rotate-logs --keep-logs-days 30 --compress-older-than-days 1


