# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
import urllib.error
import urllib.request

from PyQt6.QtCore import QThread, pyqtSignal

from config import BASE_DIR, CONTROL_PORT


def kill_process_on_port(port: int) -> bool:
    if sys.platform != "win32":
        return False
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        target_pid = None
        for line in result.stdout.split("\n"):
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                if len(parts) >= 5:
                    target_pid = parts[-1]
                    break
        if target_pid and target_pid.isdigit():
            subprocess.run(
                ["taskkill", "/F", "/PID", target_pid],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            import time

            time.sleep(1)
            return True
    except Exception:
        pass
    return False


class ServerThread(QThread):
    log_signal = pyqtSignal(str)
    stats_signal = pyqtSignal(dict)

    def __init__(self, host="0.0.0.0", port=5000, use_https=False):
        super().__init__()
        self.host = host
        self.port = port
        self.use_https = use_https
        self.running = True
        self.process = None
        self.last_log_id = 0
        self.control_port = CONTROL_PORT
        self._control_token = None

    def _load_control_token(self):
        if self._control_token is not None:
            return self._control_token
        candidates = []
        try:
            candidates.append(os.path.join(BASE_DIR, ".control_token"))
        except Exception:
            pass
        try:
            candidates.append(os.path.join(os.path.dirname(sys.executable), ".control_token"))
        except Exception:
            pass
        try:
            repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            candidates.append(os.path.join(repo_root, ".control_token"))
        except Exception:
            pass
        for candidate in candidates:
            try:
                if candidate and os.path.exists(candidate):
                    with open(candidate, "r", encoding="utf-8", errors="replace") as handle:
                        token = (handle.read() or "").strip()
                        if token:
                            self._control_token = token
                            return token
            except Exception:
                continue
        self._control_token = ""
        return self._control_token

    def _control_base_urls(self):
        return [
            f"http://127.0.0.1:{self.control_port}/control",
            f"http://127.0.0.1:{self.port}/control",
        ]

    def _request_control(self, path: str, method: str = "GET", data: bytes | None = None, timeout: int = 3):
        token = self._load_control_token()
        last_err = None
        for base in self._control_base_urls():
            try:
                url = f"{base}{path}"
                req = urllib.request.Request(url, method=method, data=data)
                if token:
                    req.add_header("X-Control-Token", token)
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return resp.read()
            except Exception as exc:
                last_err = exc
                continue
        raise last_err if last_err else RuntimeError("Control request failed")

    def run(self):
        try:
            if kill_process_on_port(self.port):
                self.log_signal.emit(f"Port {self.port} process terminated")
            if kill_process_on_port(self.control_port):
                self.log_signal.emit(f"Port {self.control_port} process terminated")

            if getattr(sys, "frozen", False):
                cmd = [sys.executable, "--worker", "--port", str(self.port)]
            else:
                launcher_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "app",
                    "server_launcher.py",
                )
                python_exe = sys.executable
                if python_exe.endswith("pythonw.exe"):
                    python_exe = python_exe.replace("pythonw.exe", "python.exe")
                cmd = [python_exe, launcher_path, "--port", str(self.port)]
            if self.use_https:
                cmd.append("--https")

            self.log_signal.emit(f"서버 시작 중: {' '.join(cmd)}")
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )

            log_thread = threading.Thread(target=self.read_output, daemon=True)
            log_thread.start()

            self.log_signal.emit("서버 프로세스 시작됨 (gevent 고성능 모드)")
            import time

            time.sleep(2)
            consecutive_errors = 0
            while self.running and self.process.poll() is None:
                try:
                    try:
                        raw = self._request_control("/stats", method="GET", timeout=3)
                        stats = json.loads(raw.decode("utf-8", errors="replace"))
                        self.stats_signal.emit(stats)
                        consecutive_errors = 0
                    except (urllib.error.URLError, socket.timeout):
                        pass

                    time.sleep(1)
                except Exception:
                    consecutive_errors += 1
                    if consecutive_errors >= 10:
                        self.log_signal.emit("모니터링 연결 지연...")
                        consecutive_errors = 0
                    time.sleep(2)
        except Exception as exc:
            self.log_signal.emit(f"서버 프로세스 시작 오류: {exc}")
        finally:
            self.cleanup()

    def read_output(self):
        if not self.process:
            return
        stdout = self.process.stdout
        if stdout is None:
            return
        try:
            for line in iter(stdout.readline, ""):
                if not line:
                    break
                line = line.strip()
                if line and "/control/stats" not in line and "/control/logs" not in line:
                    self.log_signal.emit(line)
        except Exception:
            pass

    def stop(self):
        self.running = False
        try:
            self._request_control("/shutdown", method="POST", data=b"", timeout=2)
        except Exception:
            pass
        self.cleanup()

    def cleanup(self):
        if self.process and self.process.poll() is None:
            self.log_signal.emit("서버 프로세스 종료 중...")
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        kill_process_on_port(self.port)
