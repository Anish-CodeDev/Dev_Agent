---
name: go-http-server-builder
description: >
  Generates and configures a production-ready HTTP backend using the Go standard library (net/http). 
  Use this skill when a user asks to 'build a Go backend', 'create an API in Golang', 'setup a Go http server', 
  or 'add routes to my Go server'. It provides structure for routing, middleware, and request handling.
compatibility:
  runtime: Go 1.18+
  dependencies: standard library (net/http)
  env_vars: PORT, DB_DSN
---

# Go HTTP Backend Builder

This skill guides the agent in scaffolding and implementing a robust HTTP server in Go, focusing on idiomatic practices like dependency injection and clean routing.

---

## Prerequisites

- Go installed (run `go version` to verify).
- A directory initialized as a Go module (`go mod init <name>`).

```bash
go mod init my-backend
```

---

## Core Concepts

- **ServeMux**: The standard request multiplexer for routing.
- **Handlers**: Functions with signature `func(w http.ResponseWriter, r *http.Request)`.
- **Middleware**: Functions that wrap handlers to inject logic (e.g., logging, auth).
- **Graceful Shutdown**: Essential for production stability to ensure inflight requests complete.

---

## Step-by-Step Instructions

1. **Define the Server Structure**: Use `http.ServeMux` for routing to avoid global state.
2. **Implement Middleware**: Create a function that takes `http.Handler` and returns `http.Handler` for cross-cutting concerns.
3. **Set up the Server Object**: Use `&http.Server` to define timeouts (ReadTimeout/WriteTimeout) to prevent resource exhaustion.
4. **Run the server**: Use `server.ListenAndServe()` and handle errors.

---

## Full Example

```go
package main

import (
	"context"
	"fmt"
	"net/http"
	"time"
)

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, "Hello, World!")
	})

	server := &http.Server{
		Addr:         ":8080",
		Handler:      mux,
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 10 * time.Second,
	}

	fmt.Println("Server starting on :8080")
	server.ListenAndServe()
}
```

---

## Error Handling & Edge Cases

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `address already in use` | Server already running | Kill existing PID using `lsof -i :8080` |
| `404 Not Found` | Route not registered | Ensure path match in ServeMux |
| Timeout errors | Slow processing | Increase server `WriteTimeout` or optimize handler |

---

## Output Format

- Generate a `main.go` file with the server implementation.
- Provide instructions for running it with `go run main.go`.

---

## Test Cases

### Test Case 1 — Happy Path
**Prompt:** 'Create a basic Go HTTP server that returns JSON on the /api/status endpoint.'
**Expected behaviour:** Agent creates a file with a struct and `json.NewEncoder` usage.
**Pass criteria:** Code compiles and curl returns a 200 OK with JSON body.

### Test Case 2 — Edge Case
**Prompt:** 'Make the server handle a POST request with a custom header for authentication.'
**Expected behaviour:** Agent adds a check for `r.Header.Get("X-Auth-Token").`
**Pass criteria:** Request without header returns 401, with header returns 200.

### Test Case 3 — Error Recovery
**Prompt:** 'The server fails to start due to a port conflict, how do I fix it?'
**Expected behaviour:** Agent suggests finding the process using the port and changing the port variable.
**Pass criteria:** Clear explanation of `netstat` or `lsof` commands.