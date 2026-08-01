"""Tests for the config_manager module."""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import yaml

from flutter_setup.config_manager import ConfigManager


class TestConfigManager:
    """Test cases for ConfigManager class."""

    def test_init(self) -> None:
        """Test ConfigManager initialization."""
        manager = ConfigManager()
        assert manager.config_dir is not None
        assert manager.config_file is not None
        assert manager.config_file.name == "config.yaml"

    def test_get_config_dir_default(self) -> None:
        """Test getting default config directory."""
        with patch.dict(os.environ, {}, clear=True):
            manager = ConfigManager()
            expected = Path.home() / ".config" / "flutter-setup"
            assert manager.config_dir == expected

    def test_get_config_dir_xdg(self) -> None:
        """Test getting config directory from XDG_CONFIG_HOME."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": tmpdir}):
                manager = ConfigManager()
                expected = Path(tmpdir) / "flutter-setup"
                assert manager.config_dir == expected

    def test_ensure_config_dir(self) -> None:
        """Test ensuring config directory exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": tmpdir}):
                manager = ConfigManager()
                manager.ensure_config_dir()
                assert manager.config_dir.exists()

    def test_get_default_config(self) -> None:
        """Test getting default configuration."""
        manager = ConfigManager()
        config = manager.get_default_config()
        assert "flutter" in config
        assert "project" in config
        assert config["flutter"]["channel"] == "stable"
        assert config["project"]["org"] == "com.example"
        assert config["project"]["e2e_testing"] == "integration_test"

    def test_create_default_config(self) -> None:
        """Test creating default config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": tmpdir}):
                manager = ConfigManager()
                manager.create_default_config()
                assert manager.config_file.exists()

    def test_create_default_config_already_exists(self) -> None:
        """Test creating default config when it already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": tmpdir}):
                manager = ConfigManager()
                manager.config_file.parent.mkdir(parents=True, exist_ok=True)
                manager.config_file.write_text("existing: config")
                manager.create_default_config()
                # Should not overwrite
                assert manager.config_file.read_text() == "existing: config"

    def test_load_config_file_exists(self) -> None:
        """Test loading config from existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": tmpdir}):
                manager = ConfigManager()
                manager.config_file.parent.mkdir(parents=True, exist_ok=True)
                test_config = {"flutter": {"channel": "beta"}}
                with open(manager.config_file, "w") as f:
                    yaml.dump(test_config, f)
                config = manager.load_config()
                assert config["flutter"]["channel"] == "beta"

    def test_load_config_file_not_exists(self) -> None:
        """Test loading config when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": tmpdir}):
                manager = ConfigManager()
                config = manager.load_config()
                # Should return default config
                assert "flutter" in config
                assert "project" in config

    def test_save_config(self) -> None:
        """Test saving configuration to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": tmpdir}):
                manager = ConfigManager()
                test_config = {"flutter": {"channel": "beta"}}
                manager.save_config(test_config)
                assert manager.config_file.exists()
                loaded = yaml.safe_load(manager.config_file.read_text())
                assert loaded["flutter"]["channel"] == "beta"

    def test_get_flutter_location(self) -> None:
        """Test getting Flutter location from config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": tmpdir}):
                manager = ConfigManager()
                test_config = {
                    "flutter": {"location": "/path/to/flutter"},
                    "project": {},
                }
                manager.save_config(test_config)
                location = manager.get_flutter_location()
                assert location == Path("/path/to/flutter")

    def test_get_flutter_location_not_set(self) -> None:
        """Test getting Flutter location when not set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": tmpdir}):
                manager = ConfigManager()
                test_config: Dict[str, Any] = {"flutter": {}, "project": {}}
                manager.save_config(test_config)
                location = manager.get_flutter_location()
                assert location is None

    def test_set_flutter_location(self) -> None:
        """Test setting Flutter location in config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": tmpdir}):
                manager = ConfigManager()
                manager.set_flutter_location(Path("/custom/flutter/path"))
                location = manager.get_flutter_location()
                assert location == Path("/custom/flutter/path")

    def test_detect_flutter_location_from_env(self) -> None:
        """Test detecting Flutter location from FLUTTER_ROOT environment variable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flutter_path = Path(tmpdir) / "flutter"
            flutter_path.mkdir()
            (flutter_path / "bin").mkdir()
            (flutter_path / "bin" / "flutter").touch()
            with patch.dict(os.environ, {"FLUTTER_ROOT": str(flutter_path)}):
                manager = ConfigManager()
                location = manager.detect_flutter_location()
                assert location == flutter_path

    def test_detect_flutter_location_from_path(self) -> None:
        """Test detecting Flutter location from PATH."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flutter_path = Path(tmpdir) / "flutter"
            flutter_path.mkdir()
            (flutter_path / "bin").mkdir()
            (flutter_path / "bin" / "flutter").touch()
            (flutter_path / ".git").touch()
            with patch(
                "shutil.which", return_value=str(flutter_path / "bin" / "flutter")
            ):
                manager = ConfigManager()
                location = manager.detect_flutter_location()
                assert location == flutter_path

    def test_detect_flutter_location_common_paths(self) -> None:
        """Test detecting Flutter location from common paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flutter_path = Path(tmpdir) / "development" / "flutter"
            flutter_path.mkdir(parents=True)
            (flutter_path / "bin").mkdir()
            (flutter_path / "bin" / "flutter").touch()
            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                with patch.dict(os.environ, {}, clear=True):
                    with patch("shutil.which", return_value=None):
                        manager = ConfigManager()
                        location = manager.detect_flutter_location()
                        assert location == flutter_path

    def test_detect_flutter_location_not_found(self) -> None:
        """Test detecting Flutter location when not found."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("shutil.which", return_value=None):
                with patch("pathlib.Path.home", return_value=Path("/nonexistent")):
                    with patch("pathlib.Path.exists", return_value=False):
                        manager = ConfigManager()
                        location = manager.detect_flutter_location()
                        assert location is None
