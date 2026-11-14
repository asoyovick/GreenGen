.PHONY: backend-test backend-build backend-run mock-engine frontend-serve fmt

backend-test:
	cd backend && go test ./...

backend-build:
	cd backend && go build ./...

backend-run:
	cd backend && go run ./cmd/api

mock-engine:
	python3 scripts/mock_engine.py

frontend-serve:
	python3 -m http.server 5174 -d frontend-vanilla

fmt:
	cd backend && gofmt -w .
