package config

import (
	"fmt"
	"os"
	"strconv"
	"time"
)

type Config struct {
	Env         string
	HTTPPort    string
	DatabaseURL string

	ReadTimeout     time.Duration
	WriteTimeout    time.Duration
	ShutdownTimeout time.Duration
	RequestTimeout  time.Duration

	PythonEngineURL     string
	PythonEngineTimeout time.Duration

	CORSAllowedOrigins string
}

func Load() (*Config, error) {
	cfg := &Config{
		Env:                 getEnv("APP_ENV", "development"),
		HTTPPort:            getEnv("HTTP_PORT", "8080"),
		DatabaseURL:         os.Getenv("DATABASE_URL"),
		ReadTimeout:         getDurationEnv("HTTP_READ_TIMEOUT", 15*time.Second),
		WriteTimeout:        getDurationEnv("HTTP_WRITE_TIMEOUT", 60*time.Second),
		ShutdownTimeout:     getDurationEnv("HTTP_SHUTDOWN_TIMEOUT", 20*time.Second),
		RequestTimeout:      getDurationEnv("REQUEST_TIMEOUT", 30*time.Second),
		PythonEngineURL:     os.Getenv("PYTHON_ENGINE_URL"),
		PythonEngineTimeout: getDurationEnv("PYTHON_ENGINE_TIMEOUT", 120*time.Second),
		CORSAllowedOrigins:  getEnv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"),
	}
	if cfg.HTTPPort == "" {
		return nil, fmt.Errorf("HTTP_PORT is required")
	}
	return cfg, nil
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func getDurationEnv(key string, fallback time.Duration) time.Duration {
	v := os.Getenv(key)
	if v == "" {
		return fallback
	}
	// allow seconds as integer for convenience
	if n, err := strconv.Atoi(v); err == nil {
		return time.Duration(n) * time.Second
	}
	d, err := time.ParseDuration(v)
	if err != nil {
		return fallback
	}
	return d
}
