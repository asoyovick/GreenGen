package db

import (
	"context"
	"fmt"
	"io/fs"
	"sort"
	"strings"
)

// ApplyMigrationsFromFS applies *.up.sql files in lexical order and records them in schema_migrations.
// dir is the directory within filesystem containing migration SQL files (e.g. ".").

type MigrationResult struct {
	Applied []string `json:"applied"`
	Skipped []string `json:"skipped"`
}

func (d *DB) EnsureMigrationsTable(ctx context.Context) error {
	_, err := d.SQL.ExecContext(ctx, `
CREATE TABLE IF NOT EXISTS schema_migrations (
	version TEXT PRIMARY KEY,
	applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)`)
	return err
}

func (d *DB) AppliedMigrations(ctx context.Context) (map[string]bool, error) {
	if err := d.EnsureMigrationsTable(ctx); err != nil {
		return nil, err
	}
	rows, err := d.SQL.QueryContext(ctx, `SELECT version FROM schema_migrations`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := map[string]bool{}
	for rows.Next() {
		var v string
		if err := rows.Scan(&v); err != nil {
			return nil, err
		}
		out[v] = true
	}
	return out, rows.Err()
}

func (d *DB) ApplyMigrationsFromFS(ctx context.Context, filesystem fs.FS, dir string) (*MigrationResult, error) {
	appliedSet, err := d.AppliedMigrations(ctx)
	if err != nil {
		return nil, err
	}
	entries, err := fs.ReadDir(filesystem, dir)
	if err != nil {
		return nil, fmt.Errorf("read migrations dir: %w", err)
	}
	var ups []string
	for _, e := range entries {
		if e.IsDir() {
			continue
		}
		name := e.Name()
		if strings.HasSuffix(name, ".up.sql") {
			ups = append(ups, name)
		}
	}
	sort.Strings(ups)
	res := &MigrationResult{}
	for _, name := range ups {
		version := strings.TrimSuffix(name, ".up.sql")
		if appliedSet[version] {
			res.Skipped = append(res.Skipped, version)
			continue
		}
		filePath := name
		if dir != "" && dir != "." {
			filePath = dir + "/" + name
		}
		b, err := fs.ReadFile(filesystem, filePath)
		if err != nil {
			return res, fmt.Errorf("read migration %s: %w", name, err)
		}
		tx, err := d.SQL.BeginTx(ctx, nil)
		if err != nil {
			return res, fmt.Errorf("begin tx for %s: %w", name, err)
		}
		if _, err := tx.ExecContext(ctx, string(b)); err != nil {
			_ = tx.Rollback()
			return res, fmt.Errorf("apply migration %s: %w", name, err)
		}
		if _, err := tx.ExecContext(ctx, `INSERT INTO schema_migrations(version) VALUES ($1)`, version); err != nil {
			_ = tx.Rollback()
			return res, fmt.Errorf("record migration %s: %w", name, err)
		}
		if err := tx.Commit(); err != nil {
			return res, fmt.Errorf("commit migration %s: %w", name, err)
		}
		res.Applied = append(res.Applied, version)
	}
	return res, nil
}
