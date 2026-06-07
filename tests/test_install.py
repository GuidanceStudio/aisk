import os
import shutil
import subprocess
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _fake_bin(tmp_path: Path) -> tuple[Path, Path]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "uv-args.log"

    (bin_dir / "uv").write_text(
        textwrap.dedent(
            f"""\
            #!/usr/bin/env bash
            set -euo pipefail
            printf '%s\\n' "$*" >> {log}
            if [[ "$1 $2" == "tool list" ]]; then
                echo "aisk 0.1.0"
                exit 0
            fi
            if [[ "$1 $2" == "tool install" ]]; then
                exit 0
            fi
            echo "unexpected uv args: $*" >&2
            exit 1
            """
        )
    )
    (bin_dir / "aisk").write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env bash
            set -euo pipefail
            if [[ "$1" == "init" ]]; then
                exit 0
            fi
            if [[ "$1 $2" == "completions install" ]]; then
                echo "fake completions"
                exit 0
            fi
            echo "unexpected aisk args: $*" >&2
            exit 1
            """
        )
    )
    (bin_dir / "uv").chmod(0o755)
    (bin_dir / "aisk").chmod(0o755)
    return bin_dir, log


def _env(tmp_path: Path, bin_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["HOME"] = str(tmp_path / "home")
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    return env


def test_install_script_uses_local_checkout_when_run_from_file(tmp_path):
    bin_dir, log = _fake_bin(tmp_path)

    subprocess.run(
        ["bash", str(ROOT / "install.sh")],
        cwd=ROOT,
        env=_env(tmp_path, bin_dir),
        check=True,
        text=True,
        capture_output=True,
    )

    assert f"tool install --force --upgrade {ROOT}" in log.read_text()


def test_install_script_uses_git_when_run_from_stdin(tmp_path):
    bin_dir, log = _fake_bin(tmp_path)

    subprocess.run(
        ["bash"],
        cwd=ROOT,
        env=_env(tmp_path, bin_dir),
        input=(ROOT / "install.sh").read_text(),
        check=True,
        text=True,
        capture_output=True,
    )

    assert (
        "tool install --force --upgrade "
        "git+https://github.com/GuidanceStudio/aisk.git"
    ) in log.read_text()


def _powershell() -> str | None:
    return shutil.which("pwsh") or shutil.which("powershell")


def _fake_windows_bin(tmp_path: Path) -> tuple[Path, Path]:
    bin_dir = tmp_path / "ps-bin"
    bin_dir.mkdir()
    log = tmp_path / "ps-args.log"
    ps_log = str(log).replace("'", "''")

    (bin_dir / "uv").write_text(
        textwrap.dedent(
            f"""\
            #!/usr/bin/env bash
            set -euo pipefail
            printf 'uv %s\\n' "$*" >> {log}
            if [[ "$1 $2" == "tool list" ]]; then
                echo "aisk 0.1.0"
                exit 0
            fi
            if [[ "$1 $2" == "tool install" ]]; then
                exit 0
            fi
            echo "unexpected uv args: $*" >&2
            exit 1
            """
        )
    )
    (bin_dir / "uv.ps1").write_text(
        textwrap.dedent(
            f"""\
            Add-Content -LiteralPath '{ps_log}' -Value ('uv ' + ($args -join ' '))
            if ($args.Count -ge 2 -and $args[0] -eq 'tool' -and $args[1] -eq 'list') {{
                Write-Output 'aisk 0.1.0'
                exit 0
            }}
            if ($args.Count -ge 2 -and $args[0] -eq 'tool' -and $args[1] -eq 'install') {{
                exit 0
            }}
            Write-Error ('unexpected uv args: ' + ($args -join ' '))
            exit 1
            """
        )
    )
    (bin_dir / "aisk").write_text(
        textwrap.dedent(
            f"""\
            #!/usr/bin/env bash
            set -euo pipefail
            printf 'aisk %s\\n' "$*" >> {log}
            if [[ "$1" == "init" ]]; then
                exit 0
            fi
            echo "unexpected aisk args: $*" >&2
            exit 1
            """
        )
    )
    (bin_dir / "aisk.ps1").write_text(
        textwrap.dedent(
            f"""\
            Add-Content -LiteralPath '{ps_log}' -Value ('aisk ' + ($args -join ' '))
            if ($args.Count -ge 1 -and $args[0] -eq 'init') {{
                exit 0
            }}
            if ($args.Count -ge 2 -and $args[0] -eq 'completions' -and $args[1] -eq 'install') {{
                Write-Output 'fake completions'
                exit 0
            }}
            Write-Error ('unexpected aisk args: ' + ($args -join ' '))
            exit 1
            """
        )
    )
    (bin_dir / "uv").chmod(0o755)
    (bin_dir / "aisk").chmod(0o755)
    return bin_dir, log


def _ps_env(tmp_path: Path, bin_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["USERPROFILE"] = str(tmp_path / "profile")
    return env


def test_windows_installer_files_and_readme_exist():
    assert (ROOT / "install.ps1").exists()
    assert not (ROOT / "install.bat").exists()

    readme = (ROOT / "README.md").read_text()
    assert "install.ps1" in readme
    assert "irm " in readme


def test_windows_installer_uses_local_checkout_when_run_from_file(tmp_path):
    ps = _powershell()
    if ps is None:
        import pytest
        pytest.skip("PowerShell is not available")
    bin_dir, log = _fake_windows_bin(tmp_path)

    subprocess.run(
        [ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ROOT / "install.ps1")],
        cwd=ROOT,
        env=_ps_env(tmp_path, bin_dir),
        check=True,
        text=True,
        capture_output=True,
    )

    lines = log.read_text()
    assert f"uv tool install --force --upgrade {ROOT}" in lines
    assert "aisk init" in lines
    assert "aisk completions install" in lines


def test_windows_installer_uses_git_when_run_from_stdin(tmp_path):
    ps = _powershell()
    if ps is None:
        import pytest
        pytest.skip("PowerShell is not available")
    bin_dir, log = _fake_windows_bin(tmp_path)

    subprocess.run(
        [ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "-"],
        cwd=ROOT,
        env=_ps_env(tmp_path, bin_dir),
        input=(ROOT / "install.ps1").read_text(),
        check=True,
        text=True,
        capture_output=True,
    )

    assert (
        "uv tool install --force --upgrade "
        "git+https://github.com/GuidanceStudio/aisk.git"
    ) in log.read_text()
