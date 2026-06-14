"""Tests for the cleaner module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from macos_cleanup.cleaner import (
    CleanupStats,
    estimate_size,
    human_size,
    is_within,
)


def test_human_size_bytes():
    """Test human_size with bytes."""
    assert human_size(0) == "0.00 B"
    assert human_size(100) == "100.00 B"
    assert human_size(1023) == "1023.00 B"


def test_human_size_kilobytes():
    """Test human_size with kilobytes."""
    assert human_size(1024) == "1.00 KB"
    assert human_size(1536) == "1.50 KB"
    assert human_size(1024 * 1023) == "1023.00 KB"


def test_human_size_megabytes():
    """Test human_size with megabytes."""
    assert human_size(1024 * 1024) == "1.00 MB"
    assert human_size(1024 * 1024 * 1.5) == "1.50 MB"


def test_human_size_gigabytes():
    """Test human_size with gigabytes."""
    assert human_size(1024 * 1024 * 1024) == "1.00 GB"
    assert human_size(1024 * 1024 * 1024 * 2.5) == "2.50 GB"


def test_is_within_true():
    """Test is_within returns True for valid paths."""
    parent = Path("/home/user")
    child = Path("/home/user/documents/file.txt")
    assert is_within(parent, child) is True


def test_is_within_false():
    """Test is_within returns False for invalid paths."""
    parent = Path("/home/user")
    child = Path("/home/other/file.txt")
    assert is_within(parent, child) is False


def test_is_within_same_path():
    """Test is_within with same path."""
    path = Path("/home/user")
    assert is_within(path, path) is True


def test_estimate_size_nonexistent():
    """Test estimate_size with non-existent path."""
    path = Path("/nonexistent/path")
    assert estimate_size(path) == 0


def test_estimate_size_file():
    """Test estimate_size with a file."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test content")
        f.flush()
        path = Path(f.name)
        
        try:
            size = estimate_size(path)
            assert size == len(b"test content")
        finally:
            path.unlink()


def test_estimate_size_directory():
    """Test estimate_size with a directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create some files
        (tmpdir_path / "file1.txt").write_text("content1")
        (tmpdir_path / "file2.txt").write_text("content2")
        
        # Create a subdirectory with a file
        subdir = tmpdir_path / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content3")
        
        size = estimate_size(tmpdir_path)
        expected = len(b"content1") + len(b"content2") + len(b"content3")
        assert size == expected


def test_cleanup_stats_default():
    """Test CleanupStats default values."""
    stats = CleanupStats()
    assert stats.files_deleted == 0
    assert stats.dirs_deleted == 0
    assert stats.bytes_deleted == 0
    assert stats.bytes_would_delete == 0
    assert stats.target_bytes_would_delete == {}
    assert stats.errors == 0


def test_cleanup_stats_custom():
    """Test CleanupStats with custom values."""
    stats = CleanupStats(
        files_deleted=5,
        dirs_deleted=2,
        bytes_deleted=1024,
        errors=1
    )
    assert stats.files_deleted == 5
    assert stats.dirs_deleted == 2
    assert stats.bytes_deleted == 1024
    assert stats.errors == 1


def test_cleanup_stats_post_init():
    """Test CleanupStats __post_init__ method."""
    stats = CleanupStats()
    assert stats.target_bytes_would_delete == {}
    
    stats2 = CleanupStats(target_bytes_would_delete={"/path": 100})
    assert stats2.target_bytes_would_delete == {"/path": 100}
