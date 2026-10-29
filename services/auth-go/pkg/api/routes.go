package api

import (
	"net/http"
	"strings"

	"auth-go/internal/tenant"
)

// Route represents a single HTTP route with its handler.
type Route struct {
	Method  string
	Path    string
	Handler http.HandlerFunc
}

// Router dispatches requests to registered handlers.
type Router struct {
	routes []Route
}

// NewRouter creates a router with the given routes.
func NewRouter(routes ...Route) *Router {
	return &Router{routes: routes}
}

// ServeHTTP implements http.Handler.
func (r *Router) ServeHTTP(w http.ResponseWriter, req *http.Request) {
	// Inject correlation ID into context.
	cid := tenant.NewCorrelationID()
	ctx := tenant.WithCorrelationID(req.Context(), cid)
	req = req.WithContext(ctx)

	for _, route := range r.routes {
		if route.Method == req.Method && matchPath(route.Path, req.URL.Path) {
			route.Handler(w, req)
			return
		}
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusNotFound)
	json.NewEncoder(w).Encode(map[string]string{"error": "not found"})
}

// matchPath performs simple prefix matching for path parameters.
func matchPath(pattern, path string) bool {
	if pattern == path {
		return true
	}
	// Support path parameters like /api/v1/business/{id}
	patternParts := strings.Split(pattern, "/")
	pathParts := strings.Split(path, "/")

	if len(patternParts) != len(pathParts) {
		return false
	}

	for i, pp := range patternParts {
		if strings.HasPrefix(pp, "{") && strings.HasSuffix(pp, "}") {
			continue // path parameter
		}
		if pp != pathParts[i] {
			return false
		}
	}
	return true
}