"""Tests for CLI commands."""

import tempfile
from pathlib import Path
from unittest import mock

from click.testing import CliRunner

from tokencost.cli.main import cli


def _isolated_runner():
    """Create a CLI runner with isolated home dir to avoid polluting real data."""
    tmp = tempfile.mkdtemp()
    tmp_dir = Path(tmp) / ".tokencost"
    tmp_dir.mkdir()
    patch_dir = mock.patch("tokencost.config.settings.DEFAULT_DIR", tmp_dir)
    patch_cfg = mock.patch("tokencost.config.settings.DEFAULT_CONFIG_PATH", tmp_dir / "config.yaml")
    patch_db = mock.patch("tokencost.config.settings.DEFAULT_DB_PATH", tmp_dir / "tokencost.db")
    patch_db2 = mock.patch("tokencost.tracker.database.DEFAULT_DB_PATH", tmp_dir / "tokencost.db")
    return patch_dir, patch_cfg, patch_db, patch_db2


def test_version():
    """Test version command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["version"])
    assert result.exit_code == 0
    assert "tokencost" in result.output


def test_models():
    """Test models command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["models"])
    assert result.exit_code == 0
    assert "gpt-4o" in result.output


def test_models_filtered():
    """Test models command with provider filter."""
    runner = CliRunner()
    result = runner.invoke(cli, ["models", "--provider", "anthropic"])
    assert result.exit_code == 0
    assert "claude" in result.output
    assert "gpt" not in result.output


def test_summary():
    """Test summary command."""
    patches = _isolated_runner()
    with patches[0], patches[1], patches[2], patches[3]:
        runner = CliRunner()
        result = runner.invoke(cli, ["summary", "--period", "all"])
        assert result.exit_code == 0
        assert "Summary" in result.output


def test_summary_json():
    """Test summary command with JSON output."""
    patches = _isolated_runner()
    with patches[0], patches[1], patches[2], patches[3]:
        runner = CliRunner()
        result = runner.invoke(cli, ["summary", "--period", "all", "--json"])
        assert result.exit_code == 0
        assert "total_cost" in result.output


def test_estimate():
    """Test estimate command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["estimate", "Hello world test text", "--model", "gpt-4o"])
    assert result.exit_code == 0
    assert "Tokens" in result.output


def test_log_command():
    """Test log command with isolated DB."""
    patches = _isolated_runner()
    with patches[0], patches[1], patches[2], patches[3]:
        runner = CliRunner()
        result = runner.invoke(cli, ["log", "--model", "gpt-4o", "--input", "100", "--output", "50"])
        assert result.exit_code == 0
        assert "Logged" in result.output


def test_budget_status():
    """Test budget status command."""
    patches = _isolated_runner()
    with patches[0], patches[1], patches[2], patches[3]:
        runner = CliRunner()
        result = runner.invoke(cli, ["budget", "status"])
        assert result.exit_code == 0
