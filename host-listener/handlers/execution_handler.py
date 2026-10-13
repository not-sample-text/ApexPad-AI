import os
import re
import shlex
import subprocess
import sys
import webbrowser
import time
from typing import Any
from utils.logger import get_logger

logger = get_logger("ExecutionHandler")

EXE_SPLIT_RE = re.compile(r"^(.*?\.exe)(?:\s+(.*))?$", re.IGNORECASE)


class ExecutionHandler:
    _last_executed: dict[str, float] = {}
    
    @staticmethod
    def _get_popen_kwargs(run_headless: bool, work_dir: str | None = None) -> dict[str, Any]:
        """
        Builds subprocess.Popen kwargs that work reliably inside a PyInstaller
        console=False executable for both headless and visible launches.
        """
        kwargs: dict[str, Any] = {
            "stdin": subprocess.DEVNULL,
        }

        if work_dir and os.path.isdir(work_dir):
            kwargs["cwd"] = work_dir

        if sys.platform == "win32":
            if run_headless:
                kwargs["stdout"] = subprocess.DEVNULL
                kwargs["stderr"] = subprocess.DEVNULL
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # SW_HIDE
                kwargs["startupinfo"] = startupinfo
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            else:
                # Allocate a dedicated visible console window so scripts can be seen
                # even when ApexPad itself runs as a background tray app (console=False)
                kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE
        else:
            if run_headless:
                kwargs["stdout"] = subprocess.DEVNULL
                kwargs["stderr"] = subprocess.DEVNULL
                kwargs["start_new_session"] = True

        return kwargs

    @staticmethod
    def _split_executable_and_args(raw_value: str) -> tuple[str, list[str]]:
        """
        Safely separates an executable path from trailing CLI flags
        (e.g. 'C:\\...\\Bloxstrap.exe -player' -> ('C:\\...\\Bloxstrap.exe', ['-player'])).
        """
        cleaned = raw_value.strip()

        # 1. If the entire string is a valid file path as-is
        unquoted = cleaned.strip('"').strip("'")
        if os.path.isfile(unquoted):
            return unquoted, []

        # 2. Match up to '.exe' followed by optional arguments
        match = EXE_SPLIT_RE.match(unquoted)
        if match:
            exe_part = match.group(1).strip('"').strip("'")
            args_part = (match.group(2) or "").strip()
            args_list = shlex.split(args_part, posix=(sys.platform != "win32")) if args_part else []
            return exe_part, args_list

        # 3. Fallback to standard shell splitting
        parts = shlex.split(cleaned, posix=(sys.platform != "win32"))
        if parts:
            return parts[0].strip('"').strip("'"), parts[1:]
        return unquoted, []

    @staticmethod
    def _run_elevated_windows(
        executable: str,
        args_list: list[str],
        work_dir: str | None,
        run_headless: bool
    ) -> None:
        """Executes a process with Windows UAC elevation ('runas') via ShellExecuteW."""
        import ctypes

        show_cmd = 0 if run_headless else 1  # 0 = SW_HIDE, 1 = SW_SHOWNORMAL
        arg_str = subprocess.list2cmdline(args_list) if args_list else ""
        lp_dir = work_dir if (work_dir and os.path.isdir(work_dir)) else None

        result = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            executable,
            arg_str,
            lp_dir,
            show_cmd
        )
        # ShellExecuteW returns a value > 32 on success
        if result <= 32:
            raise RuntimeError(f"ShellExecuteW failed with error code {result}")

    @staticmethod
    def execute(action: dict[str, Any] | None) -> None:
        if not action or not isinstance(action, dict):
            return

        action_type = action.get("type")
        value = action.get("value")
        label = action.get("label", "Unknown")
        run_admin = bool(action.get("runAsAdmin", False))
        run_headless = bool(action.get("runHeadless", False))

        if not value:
            return

        raw_val_str = str(value).strip()
        
        # FIX: Debounce execution by 500ms to prevent duplicate launches
        now = time.time()
        if raw_val_str in ExecutionHandler._last_executed:
            if now - ExecutionHandler._last_executed[raw_val_str] < 0.5:
                logger.debug(f"Debounced duplicate execution for: {label}")
                return
        ExecutionHandler._last_executed[raw_val_str] = now

        if action_type == "APP":
            ExecutionHandler._launch_app(raw_val_str, str(label), run_admin, run_headless)
        elif action_type == "SCRIPT":
            ExecutionHandler._run_script(raw_val_str, str(label), run_admin, run_headless)
        elif action_type in ("KEY", "SHORTCUT"):
            pass
        else:
            logger.warning(f"Unknown action type '{action_type}' for '{label}'")

    @staticmethod
    def _launch_app(
        raw_path: str,
        label: str,
        run_admin: bool = False,
        run_headless: bool = False
    ) -> None:
        exe_path, args_list = ExecutionHandler._split_executable_and_args(raw_path)
        work_dir = os.path.dirname(exe_path) if os.path.isabs(exe_path) else None

        logger.info(
            f"Launching APP [{label}]: {exe_path} "
            f"(Args: {args_list}, Admin: {run_admin}, Headless: {run_headless})"
        )

        try:
            if sys.platform == "win32":
                if run_admin:
                    ExecutionHandler._run_elevated_windows(
                        exe_path, args_list, work_dir, run_headless
                    )
                else:
                    kwargs = ExecutionHandler._get_popen_kwargs(run_headless, work_dir)
                    # For GUI apps when run_headless=False, don't force CREATE_NEW_CONSOLE
                    if not run_headless:
                        kwargs.pop("creationflags", None)
                    subprocess.Popen([exe_path, *args_list], **kwargs)
            else:
                kwargs = ExecutionHandler._get_popen_kwargs(run_headless, work_dir)
                subprocess.Popen([exe_path, *args_list], **kwargs)
        except Exception as e:
            logger.error(f"Failed to launch APP '{raw_path}': {e}")

    @staticmethod
    def _run_script(
        raw_path: str,
        label: str,
        run_admin: bool = False,
        run_headless: bool = False
    ) -> None:
        path = raw_path.strip().strip('"').strip("'")
        logger.info(
            f"Running SCRIPT [{label}]: {path} (Admin: {run_admin}, Headless: {run_headless})"
        )

        if path.startswith("http://") or path.startswith("https://"):
            webbrowser.open(path)
            return

        if not os.path.exists(path):
            logger.error(f"Script path does not exist: {path}")
            return

        script_dir = os.path.dirname(os.path.abspath(path))
        ext = os.path.splitext(path)[1].lower()
        cmd: list[str] = []

        if ext == ".py":
            venv_exe = None
            py_binary = "pythonw.exe" if (sys.platform == "win32" and run_headless) else "python.exe"

            for venv_name in ["venv", ".venv", "env", ".env"]:
                if sys.platform == "win32":
                    candidate = os.path.join(script_dir, venv_name, "Scripts", py_binary)
                    if not os.path.exists(candidate):
                        candidate = os.path.join(script_dir, venv_name, "Scripts", "python.exe")
                else:
                    candidate = os.path.join(script_dir, venv_name, "bin", "python3")

                if os.path.exists(candidate):
                    venv_exe = candidate
                    break

            if venv_exe:
                logger.info(f"Detected local venv. Routing through: {venv_exe}")
                cmd = [venv_exe, path]
            else:
                if sys.platform == "win32":
                    global_py = "pythonw" if run_headless else "python"
                    cmd = [global_py, path]
                else:
                    cmd = ["python3", path]

        elif ext in (".sh", ".bash"):
            cmd = ["bash", path]
        elif ext in (".bat", ".cmd"):
            cmd = ["cmd.exe", "/c", path]
        elif ext == ".ps1":
            if run_headless:
                cmd = [
                    "powershell.exe",
                    "-NoProfile",
                    "-NonInteractive",
                    "-WindowStyle",
                    "Hidden",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    path
                ]
            else:
                cmd = [
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    path
                ]
        elif ext == ".js":
            cmd = ["node", path]
        elif ext == ".ahk":
            cmd = ["AutoHotkey.exe", path]
        elif ext == ".scpt":
            cmd = ["osascript", path]
        else:
            if sys.platform == "win32":
                cmd = ["cmd.exe", "/c", path]
            elif sys.platform == "darwin":
                cmd = ["open", path]
            else:
                cmd = ["xdg-open", path]

        try:
            if sys.platform == "win32":
                if run_admin:
                    ExecutionHandler._run_elevated_windows(
                        cmd[0], cmd[1:], script_dir, run_headless
                    )
                else:
                    kwargs = ExecutionHandler._get_popen_kwargs(run_headless, script_dir)
                    subprocess.Popen(cmd, **kwargs)
            else:
                kwargs = ExecutionHandler._get_popen_kwargs(run_headless, script_dir)
                subprocess.Popen(cmd, **kwargs)
        except Exception as e:
            logger.error(f"Failed to run SCRIPT '{path}': {e}")
