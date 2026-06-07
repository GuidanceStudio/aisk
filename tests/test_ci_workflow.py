from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def test_ci_workflow_runs_pytest_on_ubuntu_and_windows():
    assert WORKFLOW.exists()
    text = WORKFLOW.read_text()

    assert "ubuntu-latest" in text
    assert "windows-latest" in text
    assert "astral-sh/setup-uv" in text
    assert "uv run pytest -q" in text


def test_ci_workflow_checks_windows_installer_with_powershell():
    assert WORKFLOW.exists()
    text = WORKFLOW.read_text()

    assert "install.ps1" in text
    assert "pwsh" in text
    assert "tests/test_install.py" in text
