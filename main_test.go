package main

import (
	"fmt"
	"log/slog"
	"os"
	"testing"
)

// Setup for all of the tests
func TestMain(m *testing.M) {
	slog.Info("deploying new version of ak")
	// Setup
	if err := DeployAK(); err != nil {
		fmt.Fprintf(os.Stderr, "error: deploy ak - %s\n", err)
		os.Exit(1)
	}

	val := m.Run() // Runs tests

	// Teardown, currently nothing to do

	status := "OK"
	if val != 0 {
		status = "ERROR"
	}
	slog.Info("testing done", "status", status)
	os.Exit(val)
}
