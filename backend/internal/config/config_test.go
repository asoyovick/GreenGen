package config

import (
	"os"
	"testing"
	"time"
)

func TestLoadDefaults(t *testing.T) {
	os.Unsetenv("HTTP_PORT")
	os.Unsetenv("APP_ENV")
	os.Unsetenv("DATABASE_URL")
	cfg, err := Load()
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if cfg.HTTPPort != "8080" {
		t.Fatalf("expected 8080, got %s", cfg.HTTPPort)
	}
	if cfg.Env != "development" {
		t.Fatalf("expected development, got %s", cfg.Env)
	}
	if cfg.ReadTimeout != 15*time.Second {
		t.Fatalf("unexpected read timeout: %v", cfg.ReadTimeout)
	}
}

func TestLoadEnvOverrides(t *testing.T) {
	t.Setenv("HTTP_PORT", "9090")
	t.Setenv("APP_ENV", "test")
	t.Setenv("DATABASE_URL", "postgres://x")
	t.Setenv("HTTP_READ_TIMEOUT", "5s")
	t.Setenv("PYTHON_ENGINE_URL", "http://engine:8000")
	cfg, err := Load()
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if cfg.HTTPPort != "9090" || cfg.Env != "test" || cfg.DatabaseURL != "postgres://x" {
		t.Fatalf("unexpected cfg: %+v", cfg)
	}
	if cfg.ReadTimeout != 5*time.Second {
		t.Fatalf("unexpected read timeout: %v", cfg.ReadTimeout)
	}
	if cfg.PythonEngineURL != "http://engine:8000" {
		t.Fatalf("unexpected engine url: %s", cfg.PythonEngineURL)
	}
}
