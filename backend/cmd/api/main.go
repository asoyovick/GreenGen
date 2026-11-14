package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"
	"time"

	"github.com/asoyovick/GreenGen/backend/internal/config"
	"github.com/asoyovick/GreenGen/backend/internal/db"
	"github.com/asoyovick/GreenGen/backend/internal/repository"
	"github.com/asoyovick/GreenGen/backend/internal/routes"
	"github.com/asoyovick/GreenGen/backend/internal/service"
)

func main() {
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("load config: %v", err)
	}

	ctx := context.Background()
	var database *db.DB
	if cfg.DatabaseURL != "" {
		database, err = db.Connect(ctx, cfg.DatabaseURL)
		if err != nil {
			log.Printf("database connection failed (continuing without DB): %v", err)
		} else {
			log.Printf("database connected")
			if os.Getenv("AUTO_MIGRATE") == "true" {
				migrationsPath := os.Getenv("MIGRATIONS_PATH")
				if migrationsPath == "" {
					migrationsPath = "migrations"
				}
				// resolve relative to working directory
				if !filepath.IsAbs(migrationsPath) {
					if wd, err := os.Getwd(); err == nil {
						migrationsPath = filepath.Join(wd, migrationsPath)
					}
				}
				res, err := database.ApplyMigrationsFromFS(ctx, os.DirFS(migrationsPath), ".")
				if err != nil {
					log.Printf("auto-migrate failed: %v", err)
				} else {
					log.Printf("migrations applied=%v skipped=%v", res.Applied, res.Skipped)
				}
			}
		}
	} else {
		log.Printf("DATABASE_URL not set; running in seed-only mode (no persistence)")
	}

	var invRepo *repository.InvestigationRepository
	if database != nil {
		invRepo = repository.NewInvestigationRepository(database.SQL)
		if err := invRepo.EnsureSeeded(ctx); err != nil {
			log.Printf("ensure seeded investigations failed: %v", err)
		}
	} else {
		invRepo = repository.NewInvestigationRepository(nil)
	}
	invSvc := service.NewInvestigationService(invRepo)

	srv := &http.Server{
		Addr:         ":" + cfg.HTTPPort,
		Handler:      routes.NewRouter(routes.Services{Investigations: invSvc}),
		ReadTimeout:  cfg.ReadTimeout,
		WriteTimeout: cfg.WriteTimeout,
	}

	go func() {
		log.Printf("greengen backend listening on %s", srv.Addr)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("server error: %v", err)
		}
	}()

	stop := make(chan os.Signal, 1)
	signal.Notify(stop, syscall.SIGINT, syscall.SIGTERM)
	<-stop

	shutdownCtx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	log.Println("shutting down server...")
	if err := srv.Shutdown(shutdownCtx); err != nil {
		log.Printf("graceful shutdown failed: %v", err)
	}
	if database != nil {
		_ = database.Close()
	}
}
