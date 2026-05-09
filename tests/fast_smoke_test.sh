#!/bin/bash
set -e
echo "🚀 Starting Fast Smoke Test (Warm SDK)"

# Fix permissions for the mounted volume
sudo chown -R developer:developer /app

# Install the package
# We remove existing egg-info to avoid permission issues
rm -rf flutter_setup.egg-info
sudo uv pip install -e . --system --break-system-packages

# Run init non-interactively
echo -e "\n\ncom.smoke" | flutter-setup init

# Setup with --flutter-update skip to use the pre-installed SDK
flutter-setup setup smoke_app linux --flutter-update skip --verbose

# Verify Project creation
echo "📂 Verifying Project: smoke_app"
if [ ! -d "smoke_app" ]; then
    echo "❌ Project directory smoke_app not created"
    exit 1
fi

cd smoke_app

# Run make analyze (to check linting)
echo "🧪 Running 'make analyze'..."
make analyze

# Run build (to verify toolchain)
echo "🏗️ Building Linux app..."
flutter build linux --debug

echo "✅ Fast smoke test completed!"
