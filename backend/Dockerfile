FROM golang:1.22-alpine AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /out/greengen-api ./cmd/api

FROM alpine:3.20
WORKDIR /app
RUN apk add --no-cache ca-certificates tzdata
COPY --from=build /out/greengen-api /usr/local/bin/greengen-api
COPY migrations ./migrations
COPY docs ./docs
ENV HTTP_PORT=8080
EXPOSE 8080
CMD ["greengen-api"]
