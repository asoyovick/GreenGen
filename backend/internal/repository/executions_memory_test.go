package repository

import (
	"context"
	"testing"

	"github.com/asoyovick/GreenGen/backend/internal/domain"
)

func TestMemoryExecutionStore_Idempotency(t *testing.T) {
	s := NewMemoryExecutionStore()
	ex := domain.InvestigationExecution{InvestigationID: "INV-TEST", Status: domain.ExecutionFailed}
	job := &domain.Job{JobType: "analysis", Status: domain.ExecutionFailed}
	payload := map[string]any{"idempotency_key": "k1", "investigation_id": "INV-TEST"}
	a, err := s.Create(context.Background(), ex, job, payload)
	if err != nil {
		t.Fatalf("create: %v", err)
	}
	b, err := s.Create(context.Background(), ex, job, payload)
	if err != nil {
		t.Fatalf("create2: %v", err)
	}
	if a.ID != b.ID {
		t.Fatalf("expected same execution for idempotent create, got %s vs %s", a.ID, b.ID)
	}
	got, ok, _ := s.GetByIdempotencyKey(context.Background(), "k1")
	if !ok || got.ID != a.ID {
		t.Fatalf("expected lookup by idempotency key, ok=%v id=%s", ok, got.ID)
	}
}

func TestMemoryExecutionStore_UpdateStatus(t *testing.T) {
	s := NewMemoryExecutionStore()
	created, _ := s.Create(context.Background(), domain.InvestigationExecution{InvestigationID: "INV-TEST", Status: domain.ExecutionPending}, &domain.Job{JobType: "analysis", Status: domain.ExecutionPending}, map[string]any{})
	if err := s.UpdateStatus(context.Background(), created.ID, domain.ExecutionQueued, "", "", "eng-1"); err != nil {
		t.Fatalf("update: %v", err)
	}
	got, ok, _ := s.Get(context.Background(), created.ID)
	if !ok || got.Status != domain.ExecutionQueued {
		t.Fatalf("expected queued, ok=%v status=%s", ok, got.Status)
	}
}

func TestMemoryExecutionStore_ResultPersistence(t *testing.T) {
	s := NewMemoryExecutionStore()
	created, _ := s.Create(context.Background(), domain.InvestigationExecution{InvestigationID: "INV-TEST", Status: domain.ExecutionRunning}, &domain.Job{JobType: "analysis", Status: domain.ExecutionRunning}, map[string]any{})
	res := domain.ExecutionResult{
		ExecutionID: created.ID,
		Status:      "available",
		Raw:         map[string]any{"status": "completed", "cells": []any{map[string]any{"cell_id": "c1"}}},
		Provenance:  map[string]any{"source": "engine", "synthetic": false},
		Synthetic:   false,
	}
	if err := s.SaveResult(context.Background(), res); err != nil {
		t.Fatalf("save result: %v", err)
	}
	got, ok, err := s.GetResult(context.Background(), created.ID)
	if err != nil || !ok {
		t.Fatalf("get result: ok=%v err=%v", ok, err)
	}
	if got.ExecutionID != created.ID || got.Synthetic {
		t.Fatalf("unexpected result: %#v", got)
	}
	if got.Raw["status"] != "completed" {
		t.Fatalf("expected raw status completed, got %#v", got.Raw["status"])
	}
}
