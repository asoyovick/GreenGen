.PHONY: help backend-test backend-build backend-run backend-vet backend-tidy backend-fmt backend-fmt-check frontend-serve frontend-check check test fmt

help:
	@echo "Targets:"
	@echo "  backend-test       Run Go backend tests"
	@echo "  backend-build      Build Go backend packages"
	@echo "  backend-run        Run Go backend API locally (configure env as needed)"
	@echo "  backend-vet        Run go vet on backend"
	@echo "  backend-tidy       Run go mod tidy in backend"
	@echo "  backend-fmt        Format backend Go code (gofmt -w)"
	@echo "  backend-fmt-check  Check backend Go formatting"
	@echo "  frontend-serve     Serve frontend-vanilla at http://127.0.0.1:5174"
	@echo "  frontend-check     Syntax-check frontend JavaScript (node --check)"
	@echo "  check              Run backend build/vet/fmt-check and frontend checks"
	@echo "  test               Run backend tests"
	@echo "  fmt                Alias for backend-fmt"

backend-test:
	cd backend && go test ./...

backend-build:
	cd backend && go build ./...

backend-run:
	cd backend && go run ./cmd/api

backend-vet:
	cd backend && go vet ./...

backend-tidy:
	cd backend && go mod tidy

backend-fmt:
	cd backend && gofmt -w .

backend-fmt-check:
	@cd backend && test -z "$$(gofmt -l .)" || (echo "gofmt needed:"; gofmt -l .; exit 1)

frontend-serve:
	python3 -m http.server 5174 --directory frontend-vanilla

frontend-check:
	@node --check frontend-vanilla/js/config.js frontend-vanilla/js/main.js && \
	find frontend-vanilla/js -type f -name '*.js' -print0 | xargs -0 -n1 node --check

check: backend-build backend-vet backend-fmt-check frontend-check

test: backend-test

fmt: backend-fmt

