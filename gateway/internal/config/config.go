package config

import (
	"os"
)

// Config holds application configuration
type Config struct {
	Environment string
	RAGServiceURL string
	PlannerServiceURL string
	QuizServiceURL string
}

// Load loads configuration from environment variables
func Load() *Config {
	return &Config{
		Environment:       getEnv("ENVIRONMENT", "development"),
		RAGServiceURL:     getEnv("RAG_SERVICE_URL", "http://localhost:8001"),
		PlannerServiceURL: getEnv("PLANNER_SERVICE_URL", "http://localhost:8002"),
		QuizServiceURL:    getEnv("QUIZ_SERVICE_URL", "http://localhost:8003"),
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
