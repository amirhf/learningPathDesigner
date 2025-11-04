# Gateway Service

Go-based API gateway that handles:
- Authentication (JWT verification)
- Rate limiting
- Request routing to backend services
- Request/response transformation

## Development

```bash
cd gateway
go mod download
go run main.go
```

## Testing

```bash
go test ./...
```

## Building

```bash
go build -o gateway main.go
```
