#!/bin/bash
set -e
echo "🚀 Starting Fast Smoke Test (Warm SDK)"

# Fix permissions safely
# Instead of recursive chown of /app (which could be the whole host repo),
# we ensure the developer user can write to the current directory for build artifacts
sudo chown developer:developer .
rm -rf flutter_setup.egg-info
sudo uv pip install -e . --system --break-system-packages

# Run init non-interactively: location, channel, org, architecture, local DB,
# testing starter, auth, cloud database, notifications.
printf "\n\ncom.smoke\nbasic\nnone\nstandard\nnone\nnone\nnone\n" | flutter-setup init

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
