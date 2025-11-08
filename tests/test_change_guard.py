import subprocess
from pathlib import Path

import pytest

from ob1.change_guard import ChangeGuardError, ensure_changes_within_scope, list_changed_files


def run_git(args, cwd):
    subprocess.check_call(["git", *args], cwd=cwd)


def setup_repo(tmp_path: Path) -> Path:
    run_git(["init", "-b", "main"], tmp_path)
    run_git(["config", "user.email", "test@example.com"], tmp_path)
    run_git(["config", "user.name", "Test"], tmp_path)
    (tmp_path / "frontend").mkdir()
    file_path = tmp_path / "frontend" / "App.jsx"
    file_path.write_text("console.log('hi')\n")
    run_git(["add", "-A"], tmp_path)
    run_git(["commit", "-m", "init"], tmp_path)
    return tmp_path


def test_list_changed_and_guard(tmp_path):
    repo = setup_repo(tmp_path)
    changed = repo / "frontend" / "App.jsx"
    changed.write_text("console.log('bye')\n")
    files = list_changed_files(repo)
    assert files == ["frontend/App.jsx"]
    ensure_changes_within_scope(files, ["frontend/**"])
    with pytest.raises(ChangeGuardError):
        ensure_changes_within_scope(files, ["backend/**"])
