#!/bin/bash

# Script to uninstall and reinstall all packages in the monorepo
# This helps refresh dependencies and resolve installation issues

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PACKAGES_DIR="$PROJECT_ROOT/packages"
APPS_DIR="$PROJECT_ROOT/apps"

echo "=================================="
echo "Uninstalling all local packages..."
echo "=================================="

# List of packages in dependency order (dependencies first)
# Note: Directory names use underscores, pip package names use hyphens
PACKAGES=(
    "config"
    "domain_orderbook"
    "domain_imbalance"
    "signal_engine"
    "connector_binance"
    "notifier_telegram"
    "observability"
    "testkit"
)

# List of apps
APPS=(
    "orderbook_watcher"
)

# Uninstall all packages
for package in "${PACKAGES[@]}"; do
    echo ""
    echo "Uninstalling: $package"
    pip uninstall -y "$package" 2>/dev/null || echo "  (not installed, skipping)"
done

# Uninstall all apps
for app in "${APPS[@]}"; do
    echo ""
    echo "Uninstalling: $app"
    pip uninstall -y "$app" 2>/dev/null || echo "  (not installed, skipping)"
done

echo ""
echo "=================================="
echo "Reinstalling all local packages..."
echo "=================================="

# Reinstall all packages in editable mode with dev dependencies
for package in "${PACKAGES[@]}"; do
    package_path="$PACKAGES_DIR/$package"
    if [ -d "$package_path" ]; then
        echo ""
        echo "Installing: $package"
        pip install -e "$package_path[dev]"
    else
        echo "  Warning: Package directory not found: $package_path"
    fi
done

echo ""
echo "=================================="
echo "Reinstalling all apps..."
echo "=================================="

# Reinstall all apps in editable mode with dev dependencies
for app in "${APPS[@]}"; do
    app_path="$APPS_DIR/$app"
    if [ -d "$app_path" ]; then
        echo ""
        echo "Installing: $app"
        pip install -e "$app_path[dev]"
    else
        echo "  Warning: App directory not found: $app_path"
    fi
done

echo ""
echo "=================================="
echo "Done! All packages reinstalled."
echo "=================================="
