#!/bin/bash
set -e

echo "🚀 Starting Flutter Setup Smoke Test (Full E2E)"

# Install the package
sudo uv pip install -e . --system --break-system-packages

# Run init non-interactively: location, channel, org, architecture, local DB,
# testing starter, auth, cloud database, notifications.
printf "\n\ncom.smoke\nbasic\nnone\nstandard\nnone\nnone\nnone\n" | flutter-setup init

# Create project — installs prerequisites (using sudo) and Flutter SDK
flutter-setup create smoke_app linux --verbose

# Verify Flutter installation
FLUTTER_PATH="$HOME/development/flutter/bin"
export PATH="$FLUTTER_PATH:$PATH"

echo "🔍 Verifying Flutter installation..."
if ! command -v flutter &> /dev/null; then
    echo "❌ Flutter not found in PATH"
    exit 1
fi

flutter --version

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
# We use --debug for a faster check
echo "🏗️ Building Linux app..."
flutter build linux --debug

echo "✅ Smoke test completed successfully!"
