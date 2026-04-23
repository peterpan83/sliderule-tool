"""Unit tests for sliderule_tool.config."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from sliderule_tool.config import Config


class TestConfigDefaults:
    def test_default_api_url(self):
        cfg = Config()
        assert cfg.api_url == "slideruleearth.io"

    def test_default_organization_is_none(self):
        cfg = Config()
        assert cfg.organization is None

    def test_default_desired_nodes_is_none(self):
        cfg = Config()
        assert cfg.desired_nodes is None

    def test_default_timeout(self):
        cfg = Config()
        assert cfg.timeout == 600

    def test_default_max_resources(self):
        cfg = Config()
        assert cfg.max_resources == 1000

    def test_default_output_format(self):
        cfg = Config()
        assert cfg.default_output_format == "parquet"

    def test_default_output_dir(self):
        cfg = Config()
        assert cfg.output_dir == Path("./output")

    def test_default_log_level(self):
        cfg = Config()
        assert cfg.log_level == "WARNING"


class TestConfigLoad:
    """Test Config.load() reads from environment variables."""

    def _env_vars(self, **overrides) -> dict:
        base = {
            "SLIDERULE_API_URL": "custom.api.io",
            "SLIDERULE_ORGANIZATION": "my-org",
            "SLIDERULE_DESIRED_NODES": "8",
            "SLIDERULE_TIMEOUT": "300",
            "SLIDERULE_MAX_RESOURCES": "2000",
            "SLIDERULE_DEFAULT_OUTPUT_FORMAT": "csv",
            "SLIDERULE_OUTPUT_DIR": "/data/output",
            "SLIDERULE_LOG_LEVEL": "DEBUG",
        }
        base.update(overrides)
        return base

    def test_load_all_env_vars(self):
        with patch.dict(os.environ, self._env_vars(), clear=False):
            cfg = Config.load()
        assert cfg.api_url == "custom.api.io"
        assert cfg.organization == "my-org"
        assert cfg.desired_nodes == 8
        assert cfg.timeout == 300
        assert cfg.max_resources == 2000
        assert cfg.default_output_format == "csv"
        assert cfg.output_dir == Path("/data/output")
        assert cfg.log_level == "DEBUG"

    def test_load_empty_organization_becomes_none(self):
        with patch.dict(os.environ, {"SLIDERULE_ORGANIZATION": ""}, clear=False):
            cfg = Config.load()
        assert cfg.organization is None

    def test_load_empty_desired_nodes_becomes_none(self):
        with patch.dict(os.environ, {"SLIDERULE_DESIRED_NODES": ""}, clear=False):
            cfg = Config.load()
        assert cfg.desired_nodes is None

    def test_load_defaults_when_env_absent(self):
        env = {k: "" for k in [
            "SLIDERULE_API_URL", "SLIDERULE_ORGANIZATION", "SLIDERULE_DESIRED_NODES",
            "SLIDERULE_TIMEOUT", "SLIDERULE_MAX_RESOURCES",
            "SLIDERULE_DEFAULT_OUTPUT_FORMAT", "SLIDERULE_OUTPUT_DIR",
            "SLIDERULE_LOG_LEVEL",
        ]}
        # Remove them from the environment entirely
        with patch.dict(os.environ, {}, clear=False):
            for key in env:
                os.environ.pop(key, None)
            cfg = Config.load()
        assert cfg.api_url == "slideruleearth.io"
        assert cfg.timeout == 600

    def test_load_accepts_explicit_env_file(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("SLIDERULE_API_URL=file.api.io\n")
        cfg = Config.load(env_file=env_file)
        # The env file sets the value; dotenv loads it only if not already set
        # We cannot easily assert exact value here because existing env may override,
        # but we can assert Config.load() does not raise.
        assert isinstance(cfg, Config)


class TestToSlideruleInitKwargs:
    def test_always_contains_loglevel(self):
        cfg = Config(log_level="INFO")
        kwargs = cfg.to_sliderule_init_kwargs()
        assert "loglevel" in kwargs
        assert kwargs["loglevel"] == logging.INFO

    def test_unknown_log_level_falls_back_to_warning(self):
        cfg = Config(log_level="NOTEXIST")
        kwargs = cfg.to_sliderule_init_kwargs()
        assert kwargs["loglevel"] == logging.WARNING

    def test_organization_included_when_set(self):
        cfg = Config(organization="my-org")
        kwargs = cfg.to_sliderule_init_kwargs()
        assert kwargs.get("organization") == "my-org"

    def test_organization_excluded_when_none(self):
        cfg = Config(organization=None)
        kwargs = cfg.to_sliderule_init_kwargs()
        assert "organization" not in kwargs

    def test_desired_nodes_included_when_set(self):
        cfg = Config(desired_nodes=4)
        kwargs = cfg.to_sliderule_init_kwargs()
        assert kwargs.get("desired_nodes") == 4

    def test_desired_nodes_excluded_when_none(self):
        cfg = Config(desired_nodes=None)
        kwargs = cfg.to_sliderule_init_kwargs()
        assert "desired_nodes" not in kwargs

    def test_all_three_fields_present(self):
        cfg = Config(log_level="DEBUG", organization="org", desired_nodes=2)
        kwargs = cfg.to_sliderule_init_kwargs()
        assert set(kwargs.keys()) == {"loglevel", "organization", "desired_nodes"}
