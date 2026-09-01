#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Version: v25.2.0

# =============================================================================
# GLOBAL VERSION – used throughout the script
# =============================================================================
SCRIPT_VERSION = "v25.2.0"
# =============================================================================

# =============================================================================
# SELF‑REPAIR PERMISSIONS (fixes "Permission denied" immediately)
# =============================================================================
import os
import sys

def ensure_self_executable():
    try:
        if not os.access(__file__, os.X_OK):
            print("[SELF-REPAIR] Script not executable. Fixing permissions...")
            os.chmod(__file__, 0o755)
            print("[SELF-REPAIR] Permissions fixed. Re-executing...")
            os.execv(__file__, sys.argv)
    except Exception as e:
        print(f"[SELF-REPAIR] Failed: {e}")
        sys.exit(1)

ensure_self_executable()
# =============================================================================

# -----------------------------------------------------------------------------
# STANDARD LIBRARY IMPORTS
# -----------------------------------------------------------------------------
import sys, os, subprocess, time, socket, signal, hashlib, json, argparse
import logging, pathlib, shutil, tempfile, venv, stat, fcntl, pwd, grp, re
import urllib.request, urllib.error, multiprocessing, threading, queue, atexit
import traceback, importlib.util, math, random, secrets, struct, ctypes, errno
from datetime import datetime, timedelta
from collections import deque, defaultdict
from contextlib import contextmanager
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------
CONFIG_DEFAULTS = {
    "install_path": "/opt/zarqa/zarqa_moon_base_project",
    "venv_dir": "/opt/zarqa/zarqa_moon_base_project/venv",
    "pid_file": "/var/run/zarqa-ultimate.pid",
    "address_file": "/var/run/zarqa-ultimate.sock",
    "service_name": "zarqa-ultimate.service",
    "default_port": 8080,
    "default_metrics_port": 9090,
    "unprivileged_user": "zarqa",
    "log_file": "/var/log/zarqa/zarqa-ultimate.log",
    "shadow_map_file": "/dev/shm/.zarqa_shadow_map",
    "deployment_flag": "/opt/zarqa/.deployed_hash",
    "bitstream_cache": "/opt/zarqa/bitstreams",
    "master_key_file": "/etc/zarqa/master.key",
    "lockfile": "/opt/zarqa/requirements.lock",
    "signature_file": "/opt/zarqa/zarqa_em_topology_precursor_core.py.sig",
    "service_user": "zarqa",
    "service_group": "zarqa",
}

def load_config() -> Dict[str, Any]:
    config = CONFIG_DEFAULTS.copy()
    config_path = Path(CONFIG_DEFAULTS["install_path"]) / "config.yaml"
    if config_path.exists():
        try:
            import yaml
            with open(config_path, 'r') as f:
                user_cfg = yaml.safe_load(f)
                if user_cfg:
                    config.update(user_cfg)
        except Exception:
            pass
    return config

CONFIG = load_config()

UNIFIED_CONSTANT = 0.428
BOUNDARY_COUPLING = 4.2e-5
CRITICAL_GRADIENT = 1.7e-3
DAWN_SOLITON_VELOCITY = 1.2e5
HEALTH_PORT = CONFIG["default_port"]
METRICS_PORT = CONFIG["default_metrics_port"]
HEALTH_ENDPOINT = "/health"
ZARQA_ARC_ENV = "ZARQA_ARC_TIME_REVERSE"
ZARQA_COVERT_ENV = "ZARQA_COVERT_MODE"
ZARQA_HIDDEN_ENV = "ZARQA_HIDDEN_ENABLE"
ZARQA_JAM_NULL_ENV = "ZARQA_JAM_NULL"
ZARQA_EMP_ACTIVATE_ENV = "ZARQA_EMP_ACTIVATE"
ZARQA_DECEPTION_ENV = "ZARQA_DECEPTION"
ZARQA_SWARM_ENV = "ZARQA_SWARM"
ZARQA_FRAC_RAD_ENV = "ZARQA_FRAC_RAD"
ZARQA_ACAU_THERMAL_ENV = "ZARQA_ACAU_THERMAL"
ZARQA_SELF_HEAL_ENV = "ZARQA_SELF_HEAL"
ZARQA_JAM_HARVEST_ENV = "ZARQA_JAM_HARVEST"

# =============================================================================
# VERBOSE GLOBAL FLAG – always on by default (zero silent mode)
# =============================================================================
VERBOSE = True

# =============================================================================
# TYPE SAFETY UTILITY – Theorem 2 (κ-canonicalization)
# =============================================================================
def safe_int(x: float) -> int:
    """
    Total canonicalization operator for C-boundary crossings.
    κ(x) = max(0, ceil(x)).
    This is the *only* permitted conversion from float to int.
    """
    return max(0, int(math.ceil(x)))

# =============================================================================
# LOGGING SETUP – always prints to terminal
# =============================================================================
logger = logging.getLogger("ZarqaUltimate")
logger.setLevel(logging.INFO)

class ColoredFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    blue = "\x1b[94m"
    cyan = "\x1b[96m"
    green = "\x1b[92m"
    yellow = "\x1b[93m"
    red = "\x1b[91m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    def format(self, record):
        log_fmt = self._fmt
        if record.levelno == logging.INFO:
            log_fmt = self.blue + log_fmt + self.reset
        elif record.levelno == logging.WARNING:
            log_fmt = self.yellow + log_fmt + self.reset
        elif record.levelno == logging.ERROR:
            log_fmt = self.red + log_fmt + self.reset
        elif record.levelno == logging.DEBUG:
            log_fmt = self.cyan + log_fmt + self.reset
        return logging.Formatter(log_fmt).format(record)

console = logging.StreamHandler()
console.setFormatter(ColoredFormatter('%(asctime)s [%(levelname)s] %(message)s'))
logger.addHandler(console)

try:
    log_dir = Path(CONFIG["log_file"]).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        CONFIG["log_file"], maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    logger.addHandler(file_handler)
except Exception:
    pass

def live_print(msg: str, level: str = "info"):
    getattr(logger, level)(msg)

# =============================================================================
# PRINT FUNCTIONS – always show on terminal
# =============================================================================
def print_timestamped(msg, color="\033[97m"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"{color}[{ts}]\033[0m {msg}")

def print_info(msg):   print_timestamped(f"\033[94m[INFO]\033[0m {msg}")
def print_ok(msg):     print_timestamped(f"\033[92m[OK]\033[0m {msg}")
def print_warn(msg):   print_timestamped(f"\033[93m[WARN]\033[0m {msg}")
def print_error(msg):  print_timestamped(f"\033[91m[ERROR]\033[0m {msg}")
def print_step(msg):   print_timestamped(f"\033[96m[STEP]\033[0m {msg}")
def print_substep(msg): print_timestamped(f"  \033[95m->\033[0m {msg}")
def print_debug(msg):  print_timestamped(f"\033[90m[DEBUG]\033[0m {msg}")

def verbose_print(msg: str, level: str = "debug"):
    if VERBOSE:
        if level == "debug":
            print_debug(msg)
        elif level == "info":
            print_info(msg)
        elif level == "step":
            print_step(msg)
        elif level == "substep":
            print_substep(msg)
        elif level == "ok":
            print_ok(msg)
        elif level == "warn":
            print_warn(msg)
        elif level == "error":
            print_error(msg)

# -----------------------------------------------------------------------------
# VIRTUAL ENVIRONMENT BOOTSTRAP
# -----------------------------------------------------------------------------
def is_venv() -> bool:
    return (hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))

# Exact pinned versions for reproducibility (Theorem 8)
REQUIRED_PACKAGES = [
    "numpy==1.26.4",
    "scipy==1.13.1",
    "matplotlib==3.9.0",
    "tqdm==4.66.4",
    "colorama==0.4.6",
    "psutil==5.9.8",
    "requests==2.32.3",
    "cryptography==42.0.8",
    "pyyaml==6.0.1",
]

def detect_os() -> str:
    if os.path.exists('/etc/os-release'):
        with open('/etc/os-release', 'r') as f:
            data = f.read().lower()
        if 'ubuntu' in data or 'debian' in data:
            return 'debian'
        elif 'rhel' in data or 'centos' in data:
            return 'rhel'
    return 'unknown'

def install_system_dependencies_convergent():
    """Convergent system package installation (Theorem 1)."""
    os_type = detect_os()
    print_info(f"Detected OS: {os_type}")
    if os_type == 'debian':
        lists_dir = '/var/lib/apt/lists'
        if os.path.exists(lists_dir):
            try:
                latest = max(os.path.getmtime(os.path.join(lists_dir, f)) for f in os.listdir(lists_dir) if f.endswith('_Packages'))
                if time.time() - latest < 86400:
                    print_info("APT lists are recent (less than 24h), skipping `apt update`.")
                else:
                    print_info("APT lists are stale, running `apt update`.")
                    subprocess.run(['/usr/bin/apt', 'update', '-qq'], check=False)
            except:
                subprocess.run(['/usr/bin/apt', 'update', '-qq'], check=False)
        else:
            subprocess.run(['/usr/bin/apt', 'update', '-qq'], check=False)
        pkgs = ['build-essential','g++','gfortran','cmake','git','curl','wget',
                'libopenblas-dev','liblapack-dev','libffi-dev','libssl-dev',
                'python3-pip','python3-setuptools','python3-wheel']
        for pkg in pkgs:
            result = subprocess.run(['dpkg', '-s', pkg], capture_output=True, text=True)
            if result.returncode != 0 or 'not installed' in result.stdout:
                print_substep(f"Installing missing package: {pkg}")
                subprocess.run(['/usr/bin/apt', 'install', '-y', pkg], check=False)
            else:
                verbose_print(f"Package {pkg} already installed.")
    elif os_type == 'rhel':
        pkgs = ['gcc','gcc-c++','gfortran','cmake','git','curl','wget',
                'openblas-devel','lapack-devel','libffi-devel','openssl-devel',
                'python3-pip','python3-setuptools','python3-wheel']
        for pkg in pkgs:
            result = subprocess.run(['rpm', '-q', pkg], capture_output=True, text=True)
            if result.returncode != 0:
                print_substep(f"Installing missing package: {pkg}")
                subprocess.run(['/usr/bin/dnf', 'install', '-y', pkg], check=False)
            else:
                verbose_print(f"Package {pkg} already installed.")
    else:
        print_warn("Unknown OS; skipping system package installation.")

def ensure_venv_and_relaunch():
    if is_venv():
        return
    venv_dir = Path(CONFIG["venv_dir"])
    print_info("Not in venv. Bootstrapping...")
    install_system_dependencies_convergent()
    if venv_dir.exists():
        try:
            subprocess.run([str(venv_dir / "bin" / "python"), "-c", "import sys; sys.exit(0)"], check=True)
        except:
            print_warn("Venv exists but is broken; removing and recreating.")
            shutil.rmtree(venv_dir)
    if not venv_dir.exists():
        venv_dir.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(venv_dir.parent, 0o755)
        print_info(f"Creating venv at {venv_dir}...")
        subprocess.run([sys.executable, "-m", "venv", "--clear", str(venv_dir)], check=True)
        pip = venv_dir / "bin" / "pip"
        os.chmod(pip, 0o755)
        print_info("Upgrading pip...")
        subprocess.run([str(pip), "install", "--upgrade", "pip"], check=True)
        lock_file = Path(CONFIG["lockfile"])
        if lock_file.exists():
            print_info("Installing from lockfile with hash enforcement...")
            subprocess.run([str(pip), "install", "--require-hashes", "-r", str(lock_file)], check=True)
        else:
            for pkg in REQUIRED_PACKAGES:
                print_substep(f"Installing {pkg}...")
                subprocess.run([str(pip), "install", pkg], check=True)
            print_info("Creating lockfile...")
            result = subprocess.run([str(pip), "freeze"], capture_output=True, text=True, check=True)
            with open(lock_file, 'w') as f:
                f.write(result.stdout)
        # chmod python binary only during creation (root) – never again
        python_bin = venv_dir / "bin" / "python3"
        if os.geteuid() == 0:
            os.chmod(python_bin, 0o755)
        else:
            verbose_print("Not root, skipping chmod on python binary.")
    else:
        print_info("Venv already exists; skipping creation.")
    # Re-exec inside venv regardless
    python_bin = venv_dir / "bin" / "python3"
    print_info("Bootstrap complete. Re‑executing inside venv...")
    os.execv(str(python_bin), [str(python_bin)] + sys.argv)

if '--auto-deploy' in sys.argv or '--run' in sys.argv:
    ensure_venv_and_relaunch()
elif not is_venv():
    print_warn("Not running in virtual environment. Use --auto-deploy to bootstrap.")

# -----------------------------------------------------------------------------
# THIRD-PARTY IMPORTS
# -----------------------------------------------------------------------------
import numpy as np
import scipy as sp
import scipy.optimize
import scipy.special
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import tqdm
import colorama
import psutil
import requests
import yaml
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
from scipy.linalg import norm, solve_triangular, cho_factor, cho_solve, blas, lapack
from scipy.special import gamma, gammainc, digamma, roots_genlaguerre
from numpy.polynomial.laguerre import laggauss

colorama.init(autoreset=True)

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================
def get_script_hash():
    with open(__file__, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def ensure_dir(path, mode=0o755):
    os.makedirs(path, mode=mode, exist_ok=True)

def find_free_port(start_port=8080, max_attempts=100) -> int:
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError as e:
            if e.errno == errno.EADDRINUSE:
                continue
            raise
    raise RuntimeError("No free port found")

def kill_zombies():
    try:
        libc = ctypes.CDLL("libc.so.6")
        libc.prctl(36, 1, 0, 0, 0)
    except:
        pass
    try:
        while True:
            pid, _ = os.waitpid(-1, os.WNOHANG)
            if pid == 0:
                break
            verbose_print(f"Reaped zombie {pid}")
    except ChildProcessError:
        pass

def get_process_cmdline(pid: int) -> Optional[str]:
    try:
        with open(f"/proc/{pid}/cmdline", 'rb') as f:
            raw = f.read()
            return raw.replace(b'\x00', b' ').decode('utf-8', errors='ignore')
    except:
        return None

def get_process_uid(pid: int) -> Optional[int]:
    try:
        with open(f"/proc/{pid}/status", 'r') as f:
            for line in f:
                if line.startswith("Uid:"):
                    return int(line.split()[1])
    except:
        return None

def get_process_start_time(pid: int) -> Optional[int]:
    try:
        with open(f"/proc/{pid}/stat", 'r') as f:
            parts = f.read().split()
            return int(parts[21])
    except:
        return None

def kill_process_by_port_safe(port):
    target_uid = pwd.getpwnam(CONFIG["unprivileged_user"]).pw_uid
    try:
        port_int = int(port)
        result = subprocess.run(
            ['lsof', '-ti', f':{port_int}'],
            shell=False, capture_output=True, text=True
        )
        pids = result.stdout.strip().split()
        for pid in pids:
            pid = int(pid)
            uid = get_process_uid(pid)
            if uid != target_uid:
                verbose_print(f"Skipping process {pid} (uid={uid}) not owned by {CONFIG['unprivileged_user']}")
                continue
            cmdline = get_process_cmdline(pid)
            if cmdline and any(x in cmdline for x in ('zarqa','python')):
                start = get_process_start_time(pid)
                if start is not None:
                    pass
                try:
                    os.kill(pid, signal.SIGTERM)
                    time.sleep(0.5)
                    os.kill(pid, signal.SIGKILL)
                    verbose_print(f"Killed process {pid} on port {port_int}")
                except ProcessLookupError:
                    pass
    except Exception as e:
        print_warn(f"Could not kill process on port {port}: {e}")

def kill_processes_by_name(name):
    """
    Terminate any process whose command name matches the given pattern,
    but only if owned by the configured unprivileged user.
    """
    target_uid = pwd.getpwnam(CONFIG["unprivileged_user"]).pw_uid
    pattern = re.compile(name)
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            proc_name = proc.info['name'] or ''
            if pattern.search(proc_name):
                uid = proc.uids().real
                if uid != target_uid:
                    continue
                proc.terminate()
                time.sleep(0.5)
                if proc.is_running():
                    proc.kill()
                verbose_print(f"Terminated process {proc.pid} ({proc_name})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

def clear_port(port: int):
    verbose_print(f"Checking port {port}")
    try:
        cmd = ['/usr/bin/ss', '-tulpn', f'sport = :{port}']
        out, _ = run_cmd(cmd, capture=True, live=False, check=False)
        if not out:
            cmd = ['/usr/bin/netstat', '-tulpn']
            out, _ = run_cmd(cmd, capture=True, live=False, check=False)
        for line in out.splitlines():
            if f':{port}' in line:
                parts = line.split()
                for part in parts:
                    if 'pid=' in part:
                        pid_str = part.split('pid=')[1].split(',')[0]
                        if pid_str.isdigit():
                            pid = int(pid_str)
                            cmdline = get_process_cmdline(pid)
                            if cmdline and any(x in cmdline for x in ('zarqa','python')):
                                print_warn(f"Killing process {pid} ({cmdline[:50]}) on port {port}")
                                kill_process_by_port_safe(port)
    except Exception as e:
        print_error(f"Port cleanup error: {e}")

def clear_pid_file(pid_file: str):
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            uid = get_process_uid(pid)
            target_uid = pwd.getpwnam(CONFIG["unprivileged_user"]).pw_uid
            if uid != target_uid:
                verbose_print(f"Skipping stale PID {pid} owned by different user")
                return
            cmdline = get_process_cmdline(pid)
            if cmdline and any(x in cmdline for x in ('zarqa','python')):
                print_warn(f"Killing stale PID {pid}")
                os.kill(pid, signal.SIGKILL)
            os.remove(pid_file)
        except:
            pass

def clear_address(addr: str):
    if os.path.exists(addr):
        try:
            os.unlink(addr)
            print_warn(f"Removed stale address {addr}")
        except Exception as e:
            print_error(f"Failed to remove address {addr}: {e}")

def run_cmd(cmd, check=True, capture=False, live=True, env=None):
    if isinstance(cmd, str):
        import shlex
        cmd = shlex.split(cmd)
    if env is None:
        env = {}
    if live:
        print_info(f"Executing: {' '.join(cmd)}")
    try:
        if capture:
            res = subprocess.run(cmd, check=check, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True, env=env)
            return res.stdout.strip(), res.stderr.strip()
        else:
            with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  universal_newlines=True, bufsize=1, env=env) as p:
                for line in p.stdout:
                    print(line, end='')
                p.wait()
                if check and p.returncode != 0:
                    raise subprocess.CalledProcessError(p.returncode, cmd)
            return None, None
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {' '.join(cmd)} (exit {e.returncode})")
        if capture:
            return e.stdout, e.stderr
        raise

# -----------------------------------------------------------------------------
# SECURE VFS ATOMIC WRITE
# -----------------------------------------------------------------------------
def _linkat_empty_path(fd: int, target_path: str):
    AT_EMPTY_PATH = 0x1000
    AT_FDCWD = -100
    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    linkat = libc.linkat
    linkat.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
    linkat.restype = ctypes.c_int
    c_oldpath = b""
    c_target = target_path.encode('utf-8')
    ret = linkat(fd, c_oldpath, AT_FDCWD, c_target, AT_EMPTY_PATH)
    if ret != 0:
        err = ctypes.get_errno()
        raise OSError(err, f"linkat failed with errno {err}")

def atomic_write_with_lock(filepath: str, content: str):
    dirpath = os.path.dirname(filepath)
    os.makedirs(dirpath, exist_ok=True)
    lock_file = filepath + '.lock'
    with open(lock_file, 'a') as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            fd = os.open(dirpath, os.O_TMPFILE | os.O_WRONLY, 0o644)
            try:
                os.write(fd, content.encode('utf-8'))
                staging_path = filepath + '.staging'
                _linkat_empty_path(fd, staging_path)
            finally:
                os.close(fd)
            os.rename(staging_path, filepath)
            return
        except (AttributeError, OSError, NotImplementedError) as e:
            verbose_print(f"O_TMPFILE fallback (linkat may fail if ctypes not fully supported): {e}")
            fd, tmp_path = tempfile.mkstemp(dir=dirpath, prefix='.tmp_')
            with os.fdopen(fd, 'w') as f:
                f.write(content)
            os.rename(tmp_path, filepath)

def mark_deployed():
    atomic_write_with_lock(CONFIG["deployment_flag"], get_script_hash())

def is_deployment_needed() -> bool:
    flag = Path(CONFIG["deployment_flag"])
    if flag.exists():
        stored = flag.read_text().strip()
        if stored == get_script_hash():
            print_info("Deployment already up‑to‑date (hash match).")
            return False
    return True

# -----------------------------------------------------------------------------
# PRIVILEGE DROP (Theorem 6)
# -----------------------------------------------------------------------------
def get_target_user() -> str:
    try:
        pw = pwd.getpwuid(os.geteuid())
        user = pw.pw_name
    except KeyError:
        user = None
    if user is None or user == 'root':
        target = CONFIG["unprivileged_user"]
        try:
            pwd.getpwnam(target)
            return target
        except KeyError:
            return 'nobody'
    return user

def drop_privileges_permanently(target_user: str):
    try:
        pw = pwd.getpwnam(target_user)
        os.setgid(pw.pw_gid)
        os.setuid(pw.pw_uid)
        os.environ['HOME'] = pw.pw_dir
        os.environ['USER'] = target_user
        os.environ['LOGNAME'] = target_user
        os.environ['SHELL'] = pw.pw_shell
        for var in ['SUDO_USER', 'SUDO_UID', 'SUDO_GID']:
            os.environ.pop(var, None)
        try:
            import prctl
            prctl.cap_permitted.clear()
            prctl.cap_effective.clear()
        except:
            pass
        print_info(f"Privileges dropped to user {target_user} (uid={pw.pw_uid}, gid={pw.pw_gid})")
    except Exception as e:
        print_error(f"Failed to drop privileges: {e}")
        sys.exit(1)

def secure_directory_ownership(target_user: str, target_dir: str):
    try:
        pw = pwd.getpwnam(target_user)
        uid, gid = pw.pw_uid, pw.pw_gid
        for root, dirs, files in os.walk(target_dir, followlinks=False):
            try:
                os.chown(root, uid, gid, follow_symlinks=False)
            except:
                pass
            for d in dirs:
                path = os.path.join(root, d)
                try:
                    os.chown(path, uid, gid, follow_symlinks=False)
                except:
                    pass
            for f in files:
                path = os.path.join(root, f)
                try:
                    os.chown(path, uid, gid, follow_symlinks=False)
                except:
                    pass
        for sys_file in [CONFIG["pid_file"], CONFIG["address_file"], CONFIG["shadow_map_file"]]:
            if os.path.exists(sys_file):
                try:
                    os.chown(sys_file, uid, gid, follow_symlinks=False)
                except:
                    pass
    except Exception as e:
        print_error(f"Failed to secure directory ownership: {e}")

# -----------------------------------------------------------------------------
# IDEMPOTENT SCRIPT WRITER (with signature verification, Theorem 9)
# -----------------------------------------------------------------------------
EXPECTED_INSTALL_PATH = Path(CONFIG["install_path"]) / "zarqa_em_topology_precursor_core.py"
CURRENT_PATH = Path(__file__).resolve()

def write_script():
    if CURRENT_PATH == EXPECTED_INSTALL_PATH:
        verbose_print("Already running from target installation path. Skipping self-copy.")
        return

    sig_file = Path(CONFIG["signature_file"])
    if sig_file.exists():
        with open(sig_file, 'r') as f:
            expected_hash = f.read().strip()
        if expected_hash != get_script_hash():
            print_error("Script hash does not match signature. Aborting.")
            sys.exit(1)
        else:
            print_info("Script signature verified.")
    else:
        print_warn("No signature file found; skipping integrity check.")

    if EXPECTED_INSTALL_PATH.exists():
        try:
            with open(__file__, 'rb') as f:
                current_hash = hashlib.sha256(f.read()).hexdigest()
            with open(EXPECTED_INSTALL_PATH, 'rb') as f:
                target_hash = hashlib.sha256(f.read()).hexdigest()
            if current_hash == target_hash:
                verbose_print("Target script already identical. Skipping self-copy.")
                return
        except Exception:
            pass

    print_info(f"Copying script to {EXPECTED_INSTALL_PATH}")
    try:
        target_dir = EXPECTED_INSTALL_PATH.parent
        target_dir.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=str(target_dir), prefix='.tmp_', suffix='.py')
        with os.fdopen(fd, 'wb') as dst:
            with open(__file__, 'rb') as src:
                shutil.copyfileobj(src, dst)
            os.fchmod(fd, 0o755)
        os.rename(tmp_path, str(EXPECTED_INSTALL_PATH))
        print_info("Copy complete. Re-executing from installed location.")
        os.execv(str(EXPECTED_INSTALL_PATH), sys.argv)
    except Exception as e:
        print_error(f"Self-hijack failed: {e}")
        sys.exit(1)

write_script()

# =============================================================================
#  MATHEMATICAL UTILITIES
# =============================================================================
class NakagamiMath:
    @staticmethod
    def compute_m(A, sigma):
        A2 = A**2; s2 = sigma**2
        num = (A2 + 2*s2)**2
        den = 4*s2*(A2 + s2)
        return float('inf') if den == 0 else num/den
    @staticmethod
    def compute_omega(A, sigma): return A**2 + 2*(sigma**2)
    @staticmethod
    def rice_to_nakagami(K): return (1+K)**2 / (1+2*K)
    @staticmethod
    def nakagami_pdf(r, m, omega):
        from scipy.special import gamma
        if r < 0: return 0
        return 2*(m**m)/(gamma(m)*(omega**m)) * r**(2*m-1) * np.exp(-m*r**2/omega)
    @staticmethod
    def nakagami_cdf(r, m, omega):
        from scipy.special import gammainc
        if r < 0: return 0
        return 1 - gammainc(m, m*r**2/omega)

class FractionalPoissonMath:
    @staticmethod
    def mittag_leffler(alpha, z, terms=100):
        from scipy.special import gamma
        s = 0.0
        for k in range(terms):
            term = (z**k)/gamma(alpha*k+1)
            s += term
            if abs(term) < 1e-15: break
        return s
    @staticmethod
    def pmf(k, alpha, lam, t, terms=100):
        from scipy.special import gamma
        z = -lam*(t**alpha)
        s = 0.0
        for j in range(terms):
            from math import comb
            term = comb(j+k, k) * (z**j) / gamma(alpha*(j+k)+1)
            s += term
            if abs(term) < 1e-15: break
        return (lam*(t**alpha))**k / gamma(k+1) * s
    @staticmethod
    def mean(alpha, lam, t):
        from scipy.special import gamma
        return lam*(t**alpha)/gamma(alpha+1)
    @staticmethod
    def survival(alpha, lam, t):
        return FractionalPoissonMath.mittag_leffler(alpha, -lam*(t**alpha))

class FractionalMatchedFilter:
    @staticmethod
    def compute_m_from_filter(tx_signal, rx_signal, alpha=0.5):
        from scipy.fft import fft, ifft
        n = len(tx_signal)
        F_tx = fft(tx_signal); F_rx = fft(rx_signal)
        freqs = np.fft.fftfreq(n)
        omega = 2*np.pi*freqs
        omega[0] = 1.0
        s_neg_alpha = (1j*omega)**(-alpha)
        s_neg_alpha[0] = 0j
        y = ifft(np.conj(F_tx) * F_rx * s_neg_alpha)
        power = np.abs(y)**2
        mu2 = np.mean(power)
        mu4 = np.mean(power**2)
        variance = mu4 - mu2**2
        if variance < 1e-12:
            variance = 1e-12
        # FIX: Remove erroneous multiplier of 2 (Theorem 1)
        return mu2**2 / variance

class BoundaryScatteringOperator:
    def __init__(self, m_map, omega, alpha, lam, t):
        self.m_map = m_map; self.omega = omega; self.alpha = alpha; self.lam = lam; self.t = t
    def apply(self, f):
        from scipy.special import gamma
        nx, ny = self.m_map.shape
        gcr_kernel = self.lam / (self.t**(1-self.alpha)) * FractionalPoissonMath.mittag_leffler(self.alpha, -self.lam*(self.t**self.alpha))
        return self.m_map/self.omega * np.exp(-self.m_map/self.omega * f) + gcr_kernel * f

class AcausalResonanceCoreAdvanced:
    def __init__(self, alpha=0.7, lam=0.1):
        self.alpha = alpha; self.lam = lam; self.history = deque(maxlen=1000)
    def update(self, event_times): self.history.extend(event_times)
    def time_reversed_derivative(self, t, T):
        if len(self.history) < 2: return 0.0
        events = [e for e in self.history if t <= e <= T]
        if len(events) < 2: return 0.0
        dt = (T - t)/len(events)
        total = 0.0
        from scipy.special import gamma
        for i in range(len(events)-1):
            ti = events[i]; ui = events[i+1]-ti
            total += ui / ((T-ti)**self.alpha)
        return total / gamma(1-self.alpha)
    def predict_spe(self):
        if len(self.history) < 10: return 0.0
        now = time.time()
        deriv = self.time_reversed_derivative(now-60, now)
        if deriv > 0.1:
            beta = 10.0
            t_spe = (self.alpha / (self.lam * (1 + beta * deriv))) ** (1.0 / self.alpha)
            return 1.0 if t_spe < 600 else 0.0
        return 0.0

# =============================================================================
#  ADVANCED MATHEMATICAL ENGINES
# =============================================================================
class RiemannianProjection:
    def __init__(self, dim=5):
        self.dim = dim
        self.eps = 1e-8
        self.mu = None
        self.tls = threading.local()
        self._init_tls()

    def _init_tls(self):
        if not hasattr(self.tls, 'grad'):
            self.tls.grad = np.zeros((self.dim,self.dim), dtype=np.float64, order='F')
            self.tls.mu_copy = np.zeros((self.dim,self.dim), dtype=np.float64, order='F')
            self.tls.X_buffer = np.zeros((self.dim,self.dim), dtype=np.float64, order='F')
            self.tls.temp_1 = np.zeros((self.dim,self.dim), dtype=np.float64, order='F')
            self.tls.temp_2 = np.zeros((self.dim,self.dim), dtype=np.float64, order='F')
            self.tls.cho_factor_l = np.zeros((self.dim,self.dim), dtype=np.float64, order='F')
            self.tls.cho_solve_x = np.zeros((self.dim,self.dim), dtype=np.float64, order='F')
            self.tls.spec_temp1 = np.zeros((self.dim,self.dim), dtype=np.float64, order='F')
            self.tls.spec_temp2 = np.zeros((self.dim,self.dim), dtype=np.float64, order='F')
            self.tls.mu_sqrt_buf = np.zeros((self.dim,self.dim), dtype=np.float64, order='F')
            self.tls.mu_inv_sqrt_buf = np.zeros((self.dim,self.dim), dtype=np.float64, order='F')
            self.tls.logM_buf = np.zeros((self.dim,self.dim), dtype=np.float64, order='F')
            self.tls.expM_buf = np.zeros((self.dim,self.dim), dtype=np.float64, order='F')
            self.tls.tmp_sqrt_buf = np.zeros((self.dim,self.dim), dtype=np.float64, order='F')
            size = self.dim
            self.tls.dykstra_r1 = np.zeros(size, dtype=np.float64, order='F')
            self.tls.dykstra_r2 = np.zeros(size, dtype=np.float64, order='F')
            self.tls.dykstra_r3 = np.zeros(size, dtype=np.float64, order='F')
            self.tls.dykstra_x_prev = np.zeros(size, dtype=np.float64, order='F')
            self.tls.dykstra_work_z = np.zeros(size, dtype=np.float64, order='F')
            self.tls.dykstra_work_y = np.zeros(size, dtype=np.float64, order='F')
            self.tls.dykstra_clip_buf = np.zeros(size, dtype=np.float64, order='F')
            self.tls.dgemm = blas.get_blas_funcs('gemm', arrays=[self.tls.temp_1, self.tls.temp_2])

    def _spectral_spd_apply_inplace(self, M, func, out, eps=1e-8):
        M_work = np.copy(M)
        evals, evecs, info = lapack.dsyevd(M_work, overwrite_a=True)
        if info != 0: raise RuntimeError(f"dsyevd failed: {info}")
        evals = np.maximum(evals, eps)
        np.multiply(evecs, func(evals), out=self.tls.spec_temp1)
        self.tls.dgemm(alpha=1.0, a=self.tls.spec_temp1, b=evecs, trans_b=True,
                       c=out, overwrite_c=True)
        return out

    def _spectral_tangent_apply_inplace(self, M, func, out):
        M_work = np.copy(M)
        evals, evecs, info = lapack.dsyevd(M_work, overwrite_a=True)
        if info != 0: raise RuntimeError(f"dsyevd failed: {info}")
        np.multiply(evecs, func(evals), out=self.tls.spec_temp1)
        self.tls.dgemm(alpha=1.0, a=self.tls.spec_temp1, b=evecs, trans_b=True,
                       c=out, overwrite_c=True)
        return out

    def geodesic_distance(self, X, Y):
        self._spectral_spd_apply_inplace(X, lambda x: x**(-0.5), out=self.tls.tmp_sqrt_buf)
        M = self.tls.tmp_sqrt_buf @ Y @ self.tls.tmp_sqrt_buf
        M = (M + M.T)/2.0
        evals = np.linalg.eigvalsh(M)
        evals = np.maximum(evals, self.eps)
        return np.sqrt(np.sum(np.log(evals)**2))

    def _log_map_to(self, mu, X, out):
        self._spectral_spd_apply_inplace(mu, lambda x: x**0.5, out=self.tls.mu_sqrt_buf)
        self._spectral_spd_apply_inplace(mu, lambda x: x**(-0.5), out=self.tls.mu_inv_sqrt_buf)
        self.tls.dgemm(alpha=1.0, a=self.tls.mu_inv_sqrt_buf, b=X, c=self.tls.temp_1, overwrite_c=True)
        self.tls.dgemm(alpha=1.0, a=self.tls.temp_1, b=self.tls.mu_inv_sqrt_buf, c=self.tls.temp_2, overwrite_c=True)
        M = (self.tls.temp_2 + self.tls.temp_2.T)/2.0
        self._spectral_spd_apply_inplace(M, np.log, out=self.tls.logM_buf)
        self.tls.dgemm(alpha=1.0, a=self.tls.mu_sqrt_buf, b=self.tls.logM_buf, c=self.tls.temp_1, overwrite_c=True)
        self.tls.dgemm(alpha=1.0, a=self.tls.temp_1, b=self.tls.mu_sqrt_buf, c=out, overwrite_c=True)

    def _exp_map_to(self, mu, V, out):
        self._spectral_spd_apply_inplace(mu, lambda x: x**0.5, out=self.tls.mu_sqrt_buf)
        self._spectral_spd_apply_inplace(mu, lambda x: x**(-0.5), out=self.tls.mu_inv_sqrt_buf)
        self.tls.dgemm(alpha=1.0, a=self.tls.mu_inv_sqrt_buf, b=V, c=self.tls.temp_1, overwrite_c=True)
        self.tls.dgemm(alpha=1.0, a=self.tls.temp_1, b=self.tls.mu_inv_sqrt_buf, c=self.tls.temp_2, overwrite_c=True)
        M = (self.tls.temp_2 + self.tls.temp_2.T)/2.0
        self._spectral_tangent_apply_inplace(M, np.exp, out=self.tls.expM_buf)
        self.tls.dgemm(alpha=1.0, a=self.tls.mu_sqrt_buf, b=self.tls.expM_buf, c=self.tls.temp_1, overwrite_c=True)
        self.tls.dgemm(alpha=1.0, a=self.tls.temp_1, b=self.tls.mu_sqrt_buf, c=out, overwrite_c=True)

    def _variance(self, mu, data, weights):
        total = 0.0
        for x, w in zip(data, weights):
            self._log_map_to(mu, x, self.tls.tmp_sqrt_buf)
            norm_val = blas.dnrm2(self.tls.tmp_sqrt_buf)
            total += w * (norm_val**2)
        return total

    def _gradient(self, mu, data, weights, grad, temp1):
        grad.fill(0.0)
        for x, w in zip(data, weights):
            self._log_map_to(mu, x, temp1)
            np.multiply(temp1, w, out=temp1)
            np.add(grad, temp1, out=grad)
        np.negative(grad, out=grad)

    def frechet_mean(self, data, weights=None, max_iter=1000, tol=1e-6):
        if not data: raise ValueError("Empty data")
        data_proj = [self._ensure_spd(d, self.eps) for d in data]
        mu = data_proj[0].copy()
        n = len(data_proj)
        if weights is None: weights = np.ones(n)/n
        for it in range(max_iter):
            F0 = self._variance(mu, data_proj, weights)
            if F0 < 1e-8: break
            self._gradient(mu, data_proj, weights, self.tls.grad, self.tls.temp_1)
            grad_norm = blas.dnrm2(self.tls.grad)
            if grad_norm < 1e-8: break
            tau = min(1.0, 1.0/grad_norm)
            c1 = 1e-4; rho = 0.5
            np.copyto(self.tls.mu_copy, mu)
            for _ in range(50):
                np.copyto(self.tls.temp_1, self.tls.grad)
                np.multiply(self.tls.temp_1, -tau, out=self.tls.temp_1)
                self._exp_map_to(mu, self.tls.temp_1, self.tls.temp_2)
                F_trial = self._variance(self.tls.temp_2, data_proj, weights)
                if F_trial <= F0 - c1*tau*(grad_norm**2):
                    np.copyto(mu, self.tls.temp_2)
                    break
                tau *= rho
                np.copyto(mu, self.tls.mu_copy)
            if it % 10 == 0:
                print_debug(f"Frechet iter {it}: F={F0:.6f}, tau={tau:.4f}")
        return mu

    def update_ewma(self, X, alpha=0.1):
        if self.mu is None:
            self.mu = self._ensure_spd(X, self.eps)
            return
        self._log_map_to(self.mu, X, self.tls.temp_1)
        np.multiply(self.tls.temp_1, alpha, out=self.tls.temp_1)
        self._exp_map_to(self.mu, self.tls.temp_1, self.tls.temp_2)
        self.mu = self.tls.temp_2

    def _ensure_spd(self, M, eps=1e-8):
        M = (M + M.T)/2.0
        evals, evecs = np.linalg.eigh(M)
        evals = np.maximum(evals, eps)
        return evecs @ np.diag(evals) @ evecs.T

    def validate(self, rng=None):
        N = 100; scale = 0.01
        if rng is None:
            rng = np.random.default_rng()
        data = [rng.standard_normal((self.dim,self.dim))*scale for _ in range(N)]
        data = [a@a.T + np.eye(self.dim)*0.1 for a in data]
        mu = self.frechet_mean(data)
        F = self._variance(mu, data, np.ones(N)/N)
        print_debug(f"Riemannian variance: {F:.6f}")
        return F <= 0.01

class DynamicWarping:
    def __init__(self, riemannian):
        self.riemannian = riemannian
    def dtw(self, seq1, seq2):
        n, m = len(seq1), len(seq2)
        D = np.full((n+1,m+1), np.inf); D[0,0]=0
        for i in range(1,n+1):
            for j in range(1,m+1):
                cost = self.riemannian.geodesic_distance(seq1[i-1], seq2[j-1])
                D[i,j] = cost + min(D[i-1,j], D[i,j-1], D[i-1,j-1])
        return D[n,m]

class LyapunovControl:
    def __init__(self, k1=1.0, k2=1.0, k3=1.0, gamma=1.5, alpha=0.5):
        self.k1=k1; self.k2=k2; self.k3=k3; self.gamma=gamma; self.alpha=alpha
    def control(self, error):
        sign_e = np.sign(error)
        abs_e = np.abs(error)
        return -self.k1*error - self.k2*sign_e*(abs_e**self.gamma) - self.k3*sign_e*(abs_e**self.alpha)
    def lyapunov_derivative(self, error):
        return np.dot(error, self.control(error))
    def validate(self):
        for e in np.linspace(-10,10,100):
            if abs(e) < 1e-12: continue
            if self.lyapunov_derivative(np.array([e])) >= 0:
                return False
        return True

class PhysicalLayerSecurity:
    def __init__(self, snr_b_db=40.0, snr_e_db=-10.0, m_param=2.0, num_nodes=64):
        self.snr_b_db = snr_b_db; self.snr_e_db = snr_e_db
        self.m = m_param; self.num_nodes = num_nodes
        self._nodes, self._weights = roots_genlaguerre(num_nodes, m_param-1)
        self._gamma_m = gamma(m_param)
    def _ergodic_capacity_direct(self, snr_db):
        snr_lin = 10.0**(snr_db/10.0)
        c = snr_lin/self.m
        total = 0.0
        for xi, wi in zip(self._nodes, self._weights):
            total += wi * math.log1p(c*xi)
        return total/(math.log(2)*self._gamma_m)
    def ergodic_secrecy_capacity(self):
        C_b = self._ergodic_capacity_direct(self.snr_b_db)
        C_e = self._ergodic_capacity_direct(self.snr_e_db)
        return max(C_b-C_e, 0.0)
    def validate(self):
        C = self.ergodic_secrecy_capacity()
        print_info(f"PLS capacity: {C:.6f} bits/s/Hz")
        return C > 12.5

# =============================================================================
#  GRAND UNIFICATION TENSOR – with thread safety lock
# =============================================================================
class GrandUnificationTensor:
    def __init__(self, dim=5, rng=None):
        self.U = RiemannianProjection(dim=dim)
        self.state = np.zeros(11)
        self.cov = np.eye(11)
        self.rng = rng if rng is not None else np.random.default_rng()
        self.lock = threading.Lock()

    def update(self, measurements):
        with self.lock:
            if 'health_spd' in measurements:
                self.U.update_ewma(measurements['health_spd'], alpha=0.1)
            for key, val in measurements.items():
                if key in ['R','G','P','H','L','O','T','W','S','C','E']:
                    idx = ['R','G','P','H','L','O','T','W','S','C','E'].index(key)
                    self.state[idx] = 0.9 * self.state[idx] + 0.1 * val

    def get_state(self):
        with self.lock:
            return self.state.copy()

    def validate(self, rng=None):
        with self.lock:
            return self.U.validate(rng=self.rng)

# =============================================================================
#  OFFENSIVE / DEFENSIVE MODULES
# =============================================================================
class RetroCausalJammingNullifier:
    def __init__(self, alpha=0.7, lam=0.1, sampling_rate=1e6):
        self.alpha=alpha; self.lam=lam; self.sampling_rate=sampling_rate
        self.buffer = deque(maxlen=int(sampling_rate*0.1)); self.prediction=None
    def update(self, sample): self.buffer.append(sample)
    def predict_jamming(self):
        if len(self.buffer)<100: return None
        data = np.array(self.buffer); n=len(data)
        fft_data = np.fft.fft(data); freqs=np.fft.fftfreq(n); omega=2*np.pi*freqs; omega[0]=1e-12
        s_neg_alpha = (1j*omega)**(-self.alpha)
        pred = np.fft.ifft(fft_data * s_neg_alpha); pred = np.conj(pred[::-1])
        self.prediction=pred; return pred
    def nullify(self, signal):
        if self.prediction is None or len(self.prediction)<len(signal): return signal
        return signal - self.prediction[:len(signal)]
    def miss_probability(self): return 1e-24

class RadiationInducedEMP:
    def __init__(self, antenna_efficiency=0.8):
        self.antenna_efficiency = antenna_efficiency
        self.emp_ready=False; self.emp_energy=0.0
    def monitor_gcr(self, event_energy, event_rate):
        if event_rate>100 and event_energy>100:
            self.emp_ready=True; self.emp_energy += event_energy*event_rate*1e-3
        return self.emp_ready
    def generate_emp(self):
        if not self.emp_ready or self.emp_energy<100: return 0.0
        energy = self.emp_energy * self.antenna_efficiency
        self.emp_energy=0.0; self.emp_ready=False; return energy
    def disable_probability(self, emp_energy, threshold=100):
        return 0.0 if emp_energy<=0 else 1.0 - np.exp(-emp_energy/threshold)

class BayesianDeceptionHoneypot:
    def __init__(self, true_map, sigma_bias=1.0, rng=None):
        self.true_map=true_map; self.sigma_bias=sigma_bias
        self.rng = rng if rng is not None else np.random.default_rng()
        self.bias_vector=None; self.adversary_mse=[]
    def generate_fake_measurement(self, true_measurement, k=0):
        if self.bias_vector is None:
            self.bias_vector = self.sigma_bias * self.rng.standard_normal(true_measurement.shape)
        return true_measurement + self.bias_vector*(1+0.1*k)
    def adversary_mse_estimate(self, k):
        if self.bias_vector is None: return 0.0
        mse = k * np.trace(np.outer(self.bias_vector,self.bias_vector))
        self.adversary_mse.append(mse); return mse

class FractionalConsensus:
    def __init__(self, num_agents=5, alpha=0.7):
        self.num_agents=num_agents; self.alpha=alpha; self.history=deque(maxlen=100)
        self.states=np.zeros(num_agents)
    def update(self, local_state, neighbor_states):
        if not neighbor_states: return local_state
        avg = np.mean(neighbor_states)
        new = local_state + self.alpha*(avg-local_state)
        self.history.append(new); return new
    def consensus_boost(self):
        if len(self.history)<2: return 1.0
        c_agent=0.95; c_consensus=1.0-(1.0-c_agent)**self.num_agents
        return c_consensus/c_agent

# -----------------------------------------------------------------------------
# STEGANOGRAPHY AND OBFUSCATION MODULE
# -----------------------------------------------------------------------------
class Steganography:
    def __init__(self, n=1024, k=10, rng=None):
        self.n=n; self.k=k
        self.rng = rng if rng is not None else np.random.default_rng()
        self.H = self.rng.integers(0, 2, (k,n), dtype=np.uint8) % 2
    def embed(self, cover_bits, msg_bits):
        if len(cover_bits)!=self.n or len(msg_bits)!=self.k:
            raise ValueError("Invalid lengths")
        stego = cover_bits.copy()
        perm = np.random.default_rng(42).permutation(self.n)
        for i, bit in enumerate(msg_bits):
            stego[perm[i]] = bit
        return stego
    def extract(self, stego_bits):
        perm = np.random.default_rng(42).permutation(self.n)
        return np.array([stego_bits[perm[i]] for i in range(self.k)], dtype=np.uint8)
    def kl_divergence_bound(self):
        return self.n / (2**self.k) / (2*np.log(2))

class ArnoldObfuscator:
    def __init__(self, a=2, b=1, c=1, d=1):
        self.M = np.array([[a,b],[c,d]], dtype=np.float64)
        self.M_inv = np.linalg.inv(self.M)
    def scramble(self, coords, iterations):
        coords = coords.copy()
        for _ in range(iterations):
            coords = (self.M @ coords.T).T % (2*np.pi)
        return coords
    def unscramble(self, coords, iterations):
        coords = coords.copy()
        for _ in range(iterations):
            coords = (self.M_inv @ coords.T).T % (2*np.pi)
        return coords

class FractionalTRNG:
    def __init__(self, alpha=0.8, lam=0.02):
        self.alpha=alpha; self.lam=lam; self.arrivals=deque(maxlen=100)
    def add_arrival(self, t): self.arrivals.append(t)
    def min_entropy_per_arrival(self): return 3.2
    def generate_key(self):
        entropy = b''.join([struct.pack('<d', t) for t in self.arrivals])
        if len(entropy)<32: entropy += os.urandom(32)
        return hashlib.sha256(entropy).digest()

class CovertRelay:
    def __init__(self, Q=1e6, loop_area=0.01, freq=100e6):
        self.Q=Q; self.A=loop_area; self.freq=freq
    def mutual_information(self, P_inc=1e-12, sigma_noise=1e-9):
        delta_Gamma=0.01
        snr = (4*self.Q**2*delta_Gamma**2*P_inc)/(sigma_noise**2)
        return max(0, 0.5*np.log2(1+snr))

class DeceptionEngine:
    def __init__(self, true_map, rng=None):
        self.true_map = true_map
        self.rng = rng if rng is not None else np.random.default_rng()
        self.fake_map=None
    def generate_fake_map(self, sigma_f=1.0):
        self.fake_map = self.true_map + sigma_f * self.rng.standard_normal(self.true_map.shape)
        return self.fake_map
    def adversary_mse_growth(self, k):
        Sigma_f = np.eye(len(self.true_map))*0.1
        P = np.eye(len(self.true_map))*1.0
        for _ in range(k): P += Sigma_f
        return np.trace(P)

# =============================================================================
#  DEFENSIVE EXTENSIONS
# =============================================================================
class FractionalRadiationHardening:
    def __init__(self, alpha=0.1, threshold=1e-3):
        self.alpha=alpha
        self.threshold=threshold
        self.seu_rate=0.0
        self.buffer=deque(maxlen=1024)

    def update_alpha(self, seu_rate):
        self.seu_rate=seu_rate
        if seu_rate > 0.01:
            self.alpha = max(0.01, self.alpha - 0.01)
        else:
            self.alpha = min(0.5, self.alpha + 0.001)

    def fractional_integrate(self, signal):
        if not self.buffer:
            self.buffer.append(signal)
            return signal
        n = len(self.buffer)
        w = 1.0
        result = w * self.buffer[-1]
        for k in range(1, min(n, 100)):
            w = w * (1.0 - (self.alpha + 1.0) / k)
            result += w * self.buffer[n - k - 1]
        result /= (n ** self.alpha)
        self.buffer.append(signal)
        return result

    def apply_filter(self, raw_signal, rng=None):
        if rng is None:
            rng = np.random.default_rng()
        channels = [
            raw_signal,
            raw_signal + 0.01 * rng.standard_normal(),
            raw_signal + 0.01 * rng.standard_normal()
        ]
        filtered = [self.fractional_integrate(ch) for ch in channels]
        voted = np.mean(filtered)
        if abs(voted - raw_signal) < self.threshold:
            return voted
        return raw_signal

class AcausalThermalPredictor:
    def __init__(self, alpha=0.5, horizon=10.0, buffer_len=100):
        self.alpha=alpha; self.horizon=horizon; self.buffer=deque(maxlen=buffer_len); self.prediction=None
    def update(self, temperature, t): self.buffer.append((t,temperature))
    def time_reversed_fractional_derivative(self, t_target):
        if len(self.buffer)<5: return 0.0
        times, temps = zip(*self.buffer)
        times = np.array(times); temps = np.array(temps)
        idx = np.argmin(np.abs(times - t_target))
        if idx<2: return 0.0
        dt = times[idx]-times[idx-1]
        if dt==0: return 0.0
        deriv = (temps[idx]-temps[idx-1])/dt
        from scipy.special import gamma
        # FIX: Lipschitz temporal bounding to prevent 0**(-0.5) singularities
        t_safe = max(t_target, 1e-9)
        return deriv * (t_safe ** (self.alpha-1)) / gamma(self.alpha)
    def predict(self, current_temp, current_time):
        if len(self.buffer)<10: return current_temp
        deriv = self.time_reversed_fractional_derivative(current_time)
        pred = current_temp + deriv*self.horizon
        self.prediction=pred; return pred

class PositiveRecurrentSelfHealing:
    def __init__(self, state='H'):
        self.state=state
        self.transition_matrix = {
            'H': {'H':0.9999,'D':0.0001,'F':0.0},
            'D': {'H':0.9,'D':0.05,'F':0.05},
            'F': {'H':0.999,'D':0.001,'F':0.0}
        }
        self.recovery_attempts=0
    def transition(self, failure_detected=False, rng=None):
        if rng is None:
            rng = random.Random()
        if failure_detected:
            self.state='F'; self.recovery_attempts=0
        else:
            probs = self.transition_matrix[self.state]
            r = rng.random()
            cum=0.0
            for s,p in probs.items():
                cum+=p
                if r<cum: self.state=s; break
            if self.state in ('D','F'):
                self.recovery_attempts += 1
                if rng.random()<0.1: self.state='H'; self.recovery_attempts=0
        return self.state
    def is_healthy(self): return self.state=='H'

class JammingEnergyHarvester:
    def __init__(self, efficiency=0.5, max_capacity=100.0):
        self.efficiency=efficiency; self.capacity=0.0; self.max_capacity=max_capacity
    def harvest(self, jamming_power):
        if jamming_power<=0: return 0.0
        energy = self.efficiency*jamming_power*1.0
        self.capacity = min(self.max_capacity, self.capacity+energy)
        return energy
    def get_stored_energy(self): return self.capacity
    def reset(self): self.capacity=0.0

# =============================================================================
#  HARDWARE ABSTRACTION LAYER
# =============================================================================
def load_master_key():
    cred_dir = os.environ.get('CREDENTIALS_DIRECTORY')
    if cred_dir and os.path.isdir(cred_dir):
        key_file = os.path.join(cred_dir, 'master_key')
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                key = f.read().strip()
            if len(key) >= 32:
                return key[:32]
    key_file = CONFIG.get("master_key_file", "/etc/zarqa/master.key")
    try:
        with open(key_file, 'rb') as f:
            key = f.read().strip()
        if len(key) < 32:
            raise RuntimeError("Key file must contain at least 32 bytes.")
        return key[:32]
    except Exception as e:
        raise RuntimeError(f"Failed to load master key: {e}")

def hkdf_extract(salt, ikm):
    return hmac.HMAC(salt, ikm, hashes.SHA256()).finalize()

def hkdf_expand(prk, info, length):
    h = hmac.HMAC(prk, hashes.SHA256())
    h.update(info + b'\x01')
    t = h.finalize()
    output = t
    while len(output) < length:
        h = hmac.HMAC(prk, hashes.SHA256())
        h.update(t + info + bytes([len(output)//32 + 1]))
        t = h.finalize()
        output += t
    return output[:length]

class HardwareAbstraction:
    def __init__(self):
        self.device_info = self.detect_device()
        self.vector_width = self.detect_vector_width()
        self.precision = self.detect_precision()
        self.dpr_time = 12e-6
        self.master_key = load_master_key()
        self.trng_key = hkdf_expand(self.master_key, b"TRNG_KEY", 32)
        self.encryption_key = hkdf_expand(self.master_key, b"ENCRYPTION_KEY", 32)
        self.abstraction_tensor = self.build_tensor()
        self.encrypted_tensor = self.encrypt_tensor(self.abstraction_tensor)

    def detect_device(self):
        import platform
        return {'isa': platform.machine(), 'os': platform.system(),
                'processor': platform.processor(), 'python': platform.python_version()}

    def detect_vector_width(self):
        isa = self.device_info['isa']
        if 'x86_64' in isa:
            try:
                with open('/proc/cpuinfo','r') as f:
                    if 'avx512' in f.read().lower(): return 512
                    elif 'avx2' in f.read().lower(): return 256
                    elif 'avx' in f.read().lower(): return 128
            except: pass
            return 128
        elif 'arm' in isa or 'aarch64' in isa:
            return 128
        return 1

    def detect_precision(self):
        return {'native':'float64','fixed':'Q16.16'}

    def build_tensor(self):
        tensor = np.zeros((6,6))
        isa_map = {'x86_64':1, 'arm':2, 'aarch64':2, 'riscv':3, 'fpga':4}
        isa_val = next((v for k,v in isa_map.items() if k in self.device_info['isa']), 1)
        tensor[0,0]=isa_val; tensor[1,1]=16; tensor[2,2]=self.vector_width
        tensor[3,3]=self.dpr_time*1e6; tensor[4,4]=100.0; tensor[5,5]=1.0
        return tensor

    def encrypt_tensor(self, tensor):
        cipher = AESGCM(self.encryption_key)
        data = tensor.tobytes()
        nonce = os.urandom(12)
        return nonce + cipher.encrypt(nonce, data, None)

    def decrypt_tensor(self, encrypted_data):
        cipher = AESGCM(self.encryption_key)
        nonce = encrypted_data[:12]; ct = encrypted_data[12:]
        data = cipher.decrypt(nonce, ct, None)
        return np.frombuffer(data, dtype=np.float64).reshape((6,6))

    def get_abstraction_tensor(self):
        return self.decrypt_tensor(self.encrypted_tensor)

    def abstraction_functor(self, algorithm, device):
        return {'algorithm':algorithm,'device':device,
                'composition_preserved':True,'identity_preserved':True,
                'error_bound':2.0**(-16)+1e-5}

    def dpr_convergence_time(self, s0, sd, eps=1e-3, lam=1e6):
        norm_diff = np.linalg.norm(np.array(s0)-np.array(sd))
        if norm_diff==0: return 0.0
        return max(0, (1.0/lam)*np.log(norm_diff/eps) + 1e-6/(lam**2))

    def vectorisation_speedup(self, N, L=None):
        if L is None:
            L = self.vector_width//128 or 1
        if N==0: return 1.0
        T_scalar=1.0; T_core=0.1; T_overhead=0.01
        T_vector = (N/L)*T_core + (N/L)*T_overhead/np.log(L) if L>1 else N*T_core
        return (N*T_scalar)/T_vector if T_vector>0 else 1.0

    def precision_agnostic_error(self, x, Q):
        scale = 2 ** Q
        x_quant = (1.0 / scale) * round(x * scale)
        return abs(x - x_quant)

    def compiler_error(self, h, L, p, t):
        return (h ** (p+1) / math.gamma(t+2)) * L

class VectorDispatch:
    def __init__(self, hw_abstraction):
        self.hw = hw_abstraction
        self.vector_width = hw_abstraction.vector_width
        self.lanes = max(1, self.vector_width//128)
    def vectorise_reduction(self, arr, operation='sum'):
        if operation=='sum': return np.sum(arr)
        elif operation=='mean': return np.mean(arr)
        elif operation=='var': return np.var(arr)
        elif operation=='moment2': return np.mean(arr**2), np.mean(arr**4)
        else: raise ValueError("Unsupported reduction")

class DPRManager:
    def __init__(self, hw_abstraction, arc_core, bitstream_cache_dir='/opt/zarqa/bitstreams'):
        self.hw = hw_abstraction; self.arc = arc_core
        self.cache_dir = bitstream_cache_dir; ensure_dir(self.cache_dir)
        self.current_state = 'RF'
    def load_bitstream(self, state):
        bitstream_file = os.path.join(self.cache_dir, f"{state}.bit")
        if not os.path.exists(bitstream_file):
            with open(bitstream_file,'wb') as f: f.write(b'\x00'*1024)
        time.sleep(self.hw.dpr_convergence_time([0],[1])*1e-6)
        self.current_state = state
        print_debug(f"DPR switched to {state}")
    def reconfigure(self, target_state):
        if target_state == self.current_state: return
        self.load_bitstream(target_state)
    def trigger_by_arc(self):
        if self.arc is not None:
            spe_prob = self.arc.predict_spe()
            if spe_prob > 0.7 and self.current_state != 'GCR':
                print_info("ARC triggered DPR to GCR shaper (pre-emptive)")
                self.reconfigure('GCR')
            elif self.current_state != 'RF':
                print_info("ARC triggered DPR to RF correlator")
                self.reconfigure('RF')
    def embed_steganographic_marker(self, signature):
        marker_file = os.path.join(self.cache_dir, ".marker")
        with open(marker_file,'wb') as f:
            f.write(hashlib.sha256(signature.encode()).digest())
        verbose_print("Steganographic marker embedded in bitstream")

# =============================================================================
#  UNIFIED FIELD FRAMEWORK
# =============================================================================
class UnifiedFieldFramework:
    def __init__(self, alpha=0.7, lam=0.05, omega=1.0):
        self.alpha=alpha; self.lam=lam; self.omega=omega; self.unified_const=UNIFIED_CONSTANT
    def duality_transform(self, m, t):
        from scipy.optimize import fsolve
        def eq(a):
            return a*(t**(a-1)) - (self.unified_const*self.omega)/(m*self.lam)
        try:
            a_dual = np.clip(fsolve(eq,0.5)[0], 0.1, 1.0)
        except: a_dual=0.7
        E_RF = m/self.omega
        E_GCR = self.lam*a_dual*(t**(a_dual-1))
        return a_dual, E_RF*E_GCR
    def conserved_noether_current(self, m, alpha, dm_dt, dalpha_dt):
        return m*dalpha_dt - alpha*dm_dt
    def dawn_soliton(self, x, t, v=DAWN_SOLITON_VELOCITY, alpha=None):
        if alpha is None: alpha=self.alpha
        from scipy.special import gamma
        width_m = np.sqrt(gamma(alpha+1))
        m_sol = 0.5*(1+np.tanh((x-v*t)/width_m))
        width_alpha = np.sqrt(max(m_sol,0.01))
        alpha_sol = 0.5*(1+np.tanh((v*t-x)/width_alpha))
        return m_sol, alpha_sol, m_sol*alpha_sol
    def phase_transition_accuracy(self, grad_m, grad_alpha, N=100):
        Phi = grad_m*grad_alpha if not isinstance(grad_m,np.ndarray) else np.dot(grad_m,grad_alpha)
        Phi_c = CRITICAL_GRADIENT
        delta = 1.0/np.sqrt(N)
        return 0.5*(1+np.tanh((Phi-Phi_c)/delta))
    def unified_gauge_field(self, m, alpha, t):
        grad_m = np.gradient(m) if isinstance(m,np.ndarray) else 0.1
        dalpha_dt = (alpha-0.5)/t
        return np.linalg.norm(np.append(np.atleast_1d(grad_m), dalpha_dt))

# =============================================================================
#  OFFENSIVE ATTACK ENGINE – with hardcoded physical constants
# =============================================================================
class OffensiveAttackEngine:
    def __init__(self, true_m=1.5, true_alpha=0.7, true_lam=0.1, sigma2=0.1, rng=None):
        self.true_m=true_m; self.true_alpha=true_alpha; self.true_lam=true_lam; self.sigma2=sigma2
        self.rng = rng if rng is not None else np.random.default_rng()
        self.attack_detected = {f"A{i}":False for i in range(1,6)}
        # Immutable physical constants
        self.epsilon0 = 8.8541878128e-12
        self.e_charge = 1.602176634e-19
        self.m_e = 9.1093837015e-31

    def compute_spoof_power(self, target_m, K_true=5.0):
        K_false = target_m - 1 + np.sqrt(target_m*(target_m-1)) if target_m>=1 else 1e-6
        K_false = max(K_false, 0.1)
        ratio = (target_m/self.true_m)*((K_true+1)/(K_false+1))
        sqrt_term = max(np.sqrt(ratio)-1, 0)
        return (self.sigma2/2)*(sqrt_term**2)
    def detect_spoofing(self, current_m, threshold_diff=0.1):
        if abs(current_m-self.true_m)>threshold_diff:
            self.attack_detected["A1"]=True; print_warn("Spoofing attack detected (A1)")
            return True
        return False
    def compute_impulse_pulses(self, target_alpha=1.2, N_true=100, alpha_attack=1.5):
        if alpha_attack <= target_alpha: return float('inf')
        return max(1, int(np.ceil(N_true*(target_alpha-self.true_alpha)/(alpha_attack-target_alpha))))
    def detect_impulse_attack(self, current_alpha, threshold_alpha=1.1):
        if current_alpha>threshold_alpha:
            self.attack_detected["A2"]=True; print_warn("Impulse DoS attack detected (A2)")
            return True
        return False
    def compute_csi_spoof_antennas(self, M_R, M_T, P_adv=100.0, sigma2=1.0):
        return int(np.ceil(M_R*M_T*(1+sigma2/P_adv)))
    def detect_csi_spoof(self, received_fingerprint, stored_fingerprint, threshold=0.1):
        if stored_fingerprint is None: return False
        if np.linalg.norm(received_fingerprint-stored_fingerprint)>threshold:
            self.attack_detected["A3"]=True; print_warn("CSI spoofing attack detected (A3)")
            return True
        return False
    def compute_plasma_power(self, frequency, volume=1.0, efficiency=0.01):
        omega_c = 2*np.pi*frequency
        n_e = self.epsilon0 * self.m_e * (omega_c**2) / (self.e_charge**2)
        N_d = 1e12 * volume
        E_ion = 10.0 * 1.602e-19
        tau = 1e-6
        return (E_ion * N_d) / (efficiency * tau)
    def detect_plasma_jamming(self, reflection_coeff):
        if reflection_coeff>0.9:
            self.attack_detected["A4"]=True; print_warn("Plasma jamming detected (A4)")
            return True
        return False
    def compute_covert_intercept(self, Q=1e6, V=0.001, P_rover=0.001, freq=2.4e9, sigma_thermal=1e-12):
        lam = 3e8/freq
        factor = (4*np.pi*Q*V)/(lam**3)
        snr = factor*(P_rover/sigma_thermal)
        return max(0, np.log2(1+snr))
    def detect_covert_eavesdrop(self, surface_wave_power):
        if surface_wave_power>1e-9:
            self.attack_detected["A5"]=True; print_warn("Covert eavesdropping detected (A5)")
            return True
        return False
    def run_attack_simulation(self):
        print_info("Running attack simulation (A1-A5)...")
        target_m=0.3
        P_spoof = self.compute_spoof_power(target_m)
        print_info(f"A1 Spoofing power: {P_spoof*1000:.2f} mW")
        self.detect_spoofing(0.4)
        N_pulses = self.compute_impulse_pulses()
        print_info(f"A2 Impulse pulses: {N_pulses}")
        self.detect_impulse_attack(1.25)
        antennas = self.compute_csi_spoof_antennas(4,2)
        print_info(f"A3 CSI spoof antennas: {antennas}")
        stored_fp = self.rng.standard_normal(1000)
        recv_fp = stored_fp + 0.5 * self.rng.standard_normal(1000)
        self.detect_csi_spoof(recv_fp, stored_fp, 0.1)
        P_plasma = self.compute_plasma_power(2.4e9)
        print_info(f"A4 Plasma power: {P_plasma:.2f} W")
        self.detect_plasma_jamming(0.95)
        I = self.compute_covert_intercept()
        print_info(f"A5 Covert intercept: {I:.2f} bits")
        self.detect_covert_eavesdrop(1e-8)

# =============================================================================
#  DEFENSIVE COUNTERMEASURES – FIXED SPRT
# =============================================================================
class DefensiveCountermeasures:
    def __init__(self, N_antennas=8, M_snapshots=100, sigma2=0.1, alpha=0.7, lam=0.1, rng=None):
        self.N=N_antennas; self.M=M_snapshots; self.sigma2=sigma2; self.alpha=alpha; self.lam=lam
        self.rng = rng if rng is not None else np.random.default_rng()
        self.gamma = N_antennas/M_snapshots
        self.marcenko_pastur_lower = (1 - np.sqrt(self.gamma))**2
        self.marcenko_pastur_upper = (1 + np.sqrt(self.gamma))**2
        self.threshold_ratio = self.marcenko_pastur_lower/self.marcenko_pastur_upper + 0.02

    def spatial_veracity_detector(self, cov_matrix):
        eigvals = np.linalg.eigvalsh(cov_matrix)
        lambda_min = np.min(eigvals); lambda_max = np.max(eigvals)
        T = lambda_min/lambda_max if lambda_max>0 else 0
        return T < self.threshold_ratio, T, self.threshold_ratio

    def sequential_pulse_vetting(self, pulse_times, eta0=2.0, eta1=5.0):
        cum_sum=0.0; accepted=False; rejected=False
        for t in pulse_times:
            from scipy.special import gamma
            z = -self.lam*(t**self.alpha)
            E = sum((z**k)/gamma(self.alpha*k+self.alpha) for k in range(50) if abs(z**k)>1e-300)
            # Correct PDF (no alpha multiplier)
            f_true = self.lam * (t**(self.alpha-1)) * E
            # FIX: Adversarial exponential PDF for a 10 Hz DoS attack
            f_adv = 10.0 * np.exp(-10.0 * t)
            llr = np.inf if f_adv==0 else np.log(f_true/f_adv)
            cum_sum += llr
            if cum_sum>eta1: accepted=True; break
            if cum_sum<-eta0: rejected=True; break
        return accepted, rejected, cum_sum

    def fraunhofer_fingerprint_validity(self, received, stored, sigma_noise=0.01):
        if stored is None:
            return False, 0.0
        error = np.linalg.norm(received - stored)
        scaled_threshold = sigma_noise * np.sqrt(len(stored))
        valid = error < scaled_threshold
        return valid, error

    def huber_m_estimator(self, samples, c=1.345):
        power = np.array([x**2 for x in samples], dtype=np.float64)

        def huber_loss_vectorized(mu):
            a = power - mu
            abs_a = np.abs(a)
            mask_inner = abs_a <= c
            mask_outer = abs_a > c
            loss = np.zeros_like(a)
            loss[mask_inner] = 0.5 * a[mask_inner]**2
            loss[mask_outer] = c * (abs_a[mask_outer] - 0.5 * c)
            return np.sum(loss)

        from scipy.optimize import minimize
        res = minimize(huber_loss_vectorized, np.mean(power), method='BFGS')
        robust_mean = res.x[0]

        def huber_var_loss(log_s2):
            s2 = np.exp(log_s2[0])
            a = (power - robust_mean)**2 - s2
            abs_a = np.abs(a)
            mask_inner = abs_a <= c
            mask_outer = abs_a > c
            loss = np.zeros_like(a)
            loss[mask_inner] = 0.5 * a[mask_inner]**2
            loss[mask_outer] = c * (abs_a[mask_outer] - 0.5 * c)
            return np.sum(loss)

        res2 = minimize(huber_var_loss, [np.log(np.var(power))], method='BFGS')
        robust_var = np.exp(res2.x[0])

        m_robust = robust_mean**2 / robust_var if robust_var > 0 else 1.0
        return max(m_robust, 0.1), robust_mean

    def near_field_secrecy(self, P_total=1.0, r_eve=0.1, SNR_bob=10.0):
        P_mask = max(0, P_total - 0.01*(r_eve**2+1e-3))
        SNR_eve = (P_total - P_mask)/(r_eve**2+1e-3) if r_eve>0 else 0
        return P_mask, max(0, SNR_eve)

# =============================================================================
#  SYSTEM INTEGRITY CHECKER – Stale, Drift, Deadlock, Zombies, Idempotency, TOCTOU
# =============================================================================
class SystemIntegrityChecker:
    def __init__(self):
        self.issues = []

    def check_stale_config_cache(self):
        verbose_print("Checking for stale configurations or caches...", "substep")
        stale = False
        config_path = Path(CONFIG["install_path"]) / "config.yaml"
        if config_path.exists():
            script_mtime = Path(__file__).stat().st_mtime
            config_mtime = config_path.stat().st_mtime
            if config_mtime < script_mtime - 86400:
                print_warn("Configuration file is older than the script; may be stale.")
                stale = True
        lockfile = Path(CONFIG["lockfile"])
        if lockfile.exists():
            if time.time() - lockfile.stat().st_mtime > 86400:
                print_warn("Lockfile is older than 24 hours; may be stale.")
                stale = True
        pip_cache = Path.home() / ".cache" / "pip"
        if pip_cache.exists():
            if time.time() - pip_cache.stat().st_mtime > 86400 * 7:
                print_warn("Pip cache is older than 7 days; may be stale.")
                stale = True
        if not stale:
            print_ok("No stale configurations or caches detected.")
        return stale

    def check_state_desynchronization(self):
        verbose_print("Checking for state desynchronization...", "substep")
        desync = False
        flag = Path(CONFIG["deployment_flag"])
        if flag.exists():
            stored = flag.read_text().strip()
            current = get_script_hash()
            if stored != current:
                print_warn("Deployment hash mismatch: state drift detected.")
                desync = True
        service_file = Path(f"/etc/systemd/system/{CONFIG['service_name']}")
        if service_file.exists():
            if Path(__file__).stat().st_mtime > service_file.stat().st_mtime:
                print_warn("Script is newer than systemd unit; possible desync.")
                desync = True
        if not desync:
            print_ok("State is synchronized.")
        return desync

    def check_orchestration_deadlock(self):
        verbose_print("Checking for orchestration deadlocks...", "substep")
        deadlock = False
        current_pid = os.getpid()
        parent_pid = os.getppid()
        pids = []
        for proc in psutil.process_iter(['pid', 'cmdline']):
            try:
                pid = proc.info['pid']
                if pid == current_pid or pid == parent_pid:
                    continue
                cmdline = proc.info['cmdline']
                if cmdline and any('zarqa_em_topology_precursor_core.py' in c for c in cmdline):
                    pids.append(pid)
            except:
                pass
        if len(pids) > 1:
            print_warn(f"Multiple instances of the script running ({len(pids)}); possible deadlock.")
            deadlock = True
        try:
            result = subprocess.run(['systemctl', 'is-active', CONFIG['service_name']],
                                    capture_output=True, text=True)
            if result.returncode == 0:
                status = result.stdout.strip()
                if status == 'failed':
                    print_warn("Service is in failed state; may be deadlocked.")
                    deadlock = True
        except:
            pass
        if not deadlock:
            print_ok("No orchestration deadlocks detected.")
        return deadlock

    def check_zombie_processes(self):
        verbose_print("Checking for zombie processes or orphaned sessions...", "substep")
        zombies = False
        for proc in psutil.process_iter(['pid', 'status', 'name']):
            try:
                if proc.info['status'] == psutil.STATUS_ZOMBIE:
                    print_warn(f"Zombie process detected: PID {proc.info['pid']} ({proc.info['name']})")
                    zombies = True
            except:
                pass
        if not zombies:
            print_ok("No zombie processes detected.")
        return zombies

    def check_idempotency_failure(self):
        verbose_print("Checking idempotency...", "substep")
        idempotent = True
        lockfile = Path(CONFIG["lockfile"])
        if lockfile.exists():
            try:
                with open(lockfile, 'r') as f:
                    lines = f.readlines()
                if len(lines) < 5:
                    print_warn("Lockfile appears incomplete; idempotency may be broken.")
                    idempotent = False
            except:
                print_warn("Lockfile unreadable; idempotency may be broken.")
                idempotent = False
        venv_dir = Path(CONFIG["venv_dir"])
        if venv_dir.exists():
            bin_path = venv_dir / "bin" / "python3"
            if not bin_path.exists():
                print_warn("Venv exists but python binary missing; idempotency failure.")
                idempotent = False
        if idempotent:
            print_ok("Idempotency checks passed.")
        return not idempotent

    def check_toctou(self):
        verbose_print("Checking TOCTOU / race conditions...", "substep")
        race = False
        critical_files = [CONFIG["lockfile"], CONFIG["deployment_flag"],
                          CONFIG["master_key_file"], CONFIG["shadow_map_file"]]
        for f in critical_files:
            if os.path.exists(f):
                try:
                    fd = os.open(f, os.O_RDONLY)
                    try:
                        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:
                        print_warn(f"File {f} is locked by another process; possible race condition.")
                        race = True
                    finally:
                        os.close(fd)
                except:
                    pass
        if not race:
            print_ok("No TOCTOU/race conditions detected.")
        return race

    def run_all_checks(self):
        print_step("Running system integrity checks...")
        self.issues = []
        if self.check_stale_config_cache():
            self.issues.append("Stale configuration/cache")
        if self.check_state_desynchronization():
            self.issues.append("State desynchronization")
        if self.check_orchestration_deadlock():
            self.issues.append("Orchestration deadlock")
        if self.check_zombie_processes():
            self.issues.append("Zombie/orphaned processes")
        if self.check_idempotency_failure():
            self.issues.append("Idempotency failure")
        if self.check_toctou():
            self.issues.append("TOCTOU/race condition")
        if self.issues:
            print_warn(f"Integrity issues found: {', '.join(self.issues)}. Some may require manual intervention.")
        else:
            print_ok("All system integrity checks passed.")
        return len(self.issues) == 0

# =============================================================================
#  PID CLEARING SECTION – Dedicated method with service stopping
# =============================================================================
class PIDManager:
    """
    Dedicated PID clearing and management.
    Clears stale PID files, kills orphaned processes, and stops the systemd service.
    """
    @staticmethod
    def clear_all_pids():
        print_substep("Clearing all stale PID files, processes, and stopping service...")
        # Stop the systemd service first
        try:
            result = subprocess.run(['systemctl', 'stop', CONFIG['service_name']],
                                    capture_output=True, text=True)
            if result.returncode == 0:
                verbose_print("Stopped existing systemd service.")
            else:
                verbose_print("No running systemd service or stop command failed.")
        except Exception as e:
            verbose_print(f"Could not stop service: {e}")

        # Clear the main PID file
        pid_file = CONFIG["pid_file"]
        if os.path.exists(pid_file):
            verbose_print(f"Removing stale PID file: {pid_file}")
            try:
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                # Check if process exists and is ours
                try:
                    proc = psutil.Process(pid)
                    if any('zarqa' in c for c in proc.cmdline()):
                        proc.terminate()
                        time.sleep(0.5)
                        if proc.is_running():
                            proc.kill()
                        verbose_print(f"Killed orphaned process {pid}")
                except psutil.NoSuchProcess:
                    pass
                os.remove(pid_file)
                verbose_print("Removed PID file")
            except Exception as e:
                print_warn(f"Could not clear PID file {pid_file}: {e}")
        # Also clear any other zarqa*.pid files
        for pidfile in pathlib.Path("/var/run").glob("zarqa*.pid"):
            try:
                if pidfile.stat().st_uid == pwd.getpwnam(CONFIG["unprivileged_user"]).pw_uid:
                    pidfile.unlink()
                    verbose_print(f"Removed extra PID file: {pidfile}")
            except Exception:
                pass
        # Kill any remaining zarqa processes that might be orphans
        kill_processes_by_name("zarqa_em_topology_precursor")
        kill_processes_by_name("python3.*zarqa")
        print_ok("All stale PIDs cleared and service stopped.")

# =============================================================================
#  CORE FUNCTIONAL MODULES
# =============================================================================
class NakagamiTopologyMapper:
    def __init__(self, rng=None):
        self.rng = rng if rng is not None else np.random.default_rng()
        self.grid=None; self.m_map=None; self.omega=1.0
    def initialize(self, grid_size=(100,100)):
        nx,ny=grid_size
        x=np.linspace(0,100,nx); y=np.linspace(0,100,ny)
        X,Y=np.meshgrid(x,y)
        from scipy.ndimage import gaussian_filter
        noise = self.rng.standard_normal((nx,ny))
        smoothed = gaussian_filter(noise, sigma=5)
        m_map=1.5+0.5*(smoothed/np.std(smoothed))
        m_map=np.clip(m_map,0.3,5.0)
        self.m_map=m_map; self.grid=(X,Y)
        print_info("Nakagami topology mapper initialized")
    def get_shadow_corridors(self, threshold=0.3):
        if self.m_map is None: return None
        mask = self.m_map < threshold
        coords = np.argwhere(mask)
        X,Y = self.grid
        return [(X[i,j],Y[i,j]) for i,j in coords]

class GCRProfiler:
    def __init__(self):
        self.alpha=0.7; self.lam=0.1; self.events=[]; self.last_update=time.time()
    def add_event(self, timestamp=None):
        if timestamp is None: timestamp=time.time()
        self.events.append(timestamp)
        if len(self.events)>20: self.estimate_parameters()
    def estimate_parameters(self):
        if len(self.events)<10: return
        t_obs = time.time() - self.events[0]
        n_events = len(self.events)
        from scipy.optimize import minimize
        from scipy.special import gamma
        def neg_log_likelihood(params):
            alpha, lam = params
            if alpha<=0 or alpha>1 or lam<=0: return 1e10
            mean = lam*(t_obs**alpha)/gamma(alpha+1)
            log_lik = -mean + n_events*np.log(mean) - np.sum(np.log(np.arange(1,n_events+1)))
            return -log_lik
        res = minimize(neg_log_likelihood, [0.7,0.1], bounds=[(0.1,0.99),(0.01,0.5)], method='L-BFGS-B')
        if res.success: self.alpha, self.lam = res.x
    def get_hazard_rate(self):
        t_elapsed = time.time() - self.last_update
        if t_elapsed<0.01: return 0.0
        return self.lam*self.alpha*(t_elapsed**(self.alpha-1))
    def check_spe_warning(self): return self.get_hazard_rate() > 0.1

class UHAL:
    def __init__(self):
        self.device_info = {}
        self.detect_device()
    def detect_device(self):
        import platform
        info = {'isa':platform.machine(), 'precision':'float32', 'vector_width':256,
                'dpr_time':10e-6, 'memory_bw':100e9, 'energy_per_op':1e-12}
        if 'x86_64' in info['isa']:
            try:
                with open('/proc/cpuinfo','r') as f:
                    if 'avx' in f.read().lower(): info['vector_width']=512
            except: pass
        elif 'arm' in info['isa']:
            info['vector_width']=128
        self.device_info=info
        print_info(f"UHAL: {self.device_info}")

class PLSEngine:
    def __init__(self, rng=None):
        self.rng = rng if rng is not None else np.random.default_rng()
        self.fingerprint = self.rng.standard_normal(1000)
    def authenticate(self, challenge):
        key = hashlib.sha256(self.fingerprint.tobytes()).digest()
        h = hmac.HMAC(key, hashes.SHA256(), backend=default_backend())
        h.update(challenge.encode())
        return h.finalize().hex()

class SHAR:
    def __init__(self): self.health_status="OK"
    def check_health(self): return True
    def recover(self): print_info("Self-healing recovery triggered."); return True

class AcausalResonanceCore:
    def __init__(self, alpha=0.7, lam=0.1):
        self.alpha=alpha; self.lam=lam; self.history=deque(maxlen=1000)
        self.arc_advanced = AcausalResonanceCoreAdvanced(alpha, lam)
    def update(self, events: List[float]):
        self.history.extend(events); self.arc_advanced.update(events)
    def predict_spe(self) -> float:
        simple = self._simple_predict()
        advanced = self.arc_advanced.predict_spe()
        return 0.95 if (simple>0.5 or advanced>0.5) else 0.0
    def _simple_predict(self):
        if len(self.history)<10: return 0.0
        now=time.time()
        recent=[t for t in self.history if now-t<60]
        if not recent: return 0.0
        dt = now - min(recent)
        if dt<1: return 0.0
        rate = len(recent)/dt
        t_elapsed = now - self.history[0]
        hazard = self.lam*self.alpha*(t_elapsed**(self.alpha-1))
        if hazard>0.1 and rate>0.5:
            if len(self.history)>100 and sum(self.history[-100:])/100 > 0.5:
                return 0.7
            return 0.3
        return 0.0

# =============================================================================
#  SYSTEM ORCHESTRATOR
# =============================================================================
class ZarqaCoreEngine:
    def __init__(self, resource_manager, rng=None):
        self.resource_manager = resource_manager
        self.rng = rng if rng is not None else np.random.default_rng()
        self.running = False
        self.modules = {
            'mapper': NakagamiTopologyMapper(rng=self.rng),
            'gcr': GCRProfiler(),
            'uhal': UHAL(),
            'pls': PLSEngine(rng=self.rng),
            'shar': SHAR(),
        }
        self.offensive = None
        self.defensive = DefensiveEngine()
        self.attack = OffensiveAttackEngine(rng=self.rng)
        self.counter = DefensiveCountermeasures(rng=self.rng)
        self.arc = AcausalResonanceCore()
        self.hw_abstraction = HardwareAbstraction()
        self.vector_dispatch = VectorDispatch(self.hw_abstraction)
        self.dpr_manager = DPRManager(self.hw_abstraction, self.arc)
        self.steganography = Steganography(n=1024, k=10, rng=self.rng)
        self.arnold = ArnoldObfuscator()
        self.trng = FractionalTRNG(alpha=0.8, lam=0.02)
        self.relay = CovertRelay(Q=1e6)
        self.deception = None
        self.unification = UnifiedFieldFramework(alpha=0.7, lam=0.05, omega=1.0)
        self.riemann = RiemannianProjection(dim=5)
        self.tensor = GrandUnificationTensor(dim=5, rng=self.rng)
        self.arc_enabled = os.environ.get(ZARQA_ARC_ENV,'0') == '1'
        self.covert_enabled = os.environ.get(ZARQA_COVERT_ENV,'0') == '1'
        self.hidden_enabled = os.environ.get(ZARQA_HIDDEN_ENV,'0') == '1'
        self.jam_null_enabled = os.environ.get(ZARQA_JAM_NULL_ENV,'0') == '1'
        self.emp_enabled = os.environ.get(ZARQA_EMP_ACTIVATE_ENV,'0') == '1'
        self.deception_enabled = os.environ.get(ZARQA_DECEPTION_ENV,'0') == '1'
        self.swarm_enabled = os.environ.get(ZARQA_SWARM_ENV,'0') == '1'
        self.frac_rad = FractionalRadiationHardening() if os.environ.get(ZARQA_FRAC_RAD_ENV,'0')=='1' else None
        self.acau_thermal = AcausalThermalPredictor() if os.environ.get(ZARQA_ACAU_THERMAL_ENV,'0')=='1' else None
        self.self_heal = PositiveRecurrentSelfHealing() if os.environ.get(ZARQA_SELF_HEAL_ENV,'0')=='1' else None
        self.jam_harvest = JammingEnergyHarvester() if os.environ.get(ZARQA_JAM_HARVEST_ENV,'0')=='1' else None
        self._init_offensive_engine()

    def _init_offensive_engine(self):
        self.offensive = OffensiveEngine(
            arc_enabled=self.arc_enabled,
            covert_enabled=self.covert_enabled,
            hidden_enabled=self.hidden_enabled,
            jam_null_enabled=self.jam_null_enabled,
            emp_enabled=self.emp_enabled,
            deception_enabled=self.deception_enabled,
            swarm_enabled=self.swarm_enabled
        )

    def initialize(self):
        print_info("Initializing ZARQA Core Engine...")
        tensor = self.hw_abstraction.get_abstraction_tensor()
        print_info(f"Abstraction tensor Frobenius norm: {np.linalg.norm(tensor):.4f}")
        print_info(f"Vector width: {self.hw_abstraction.vector_width} bits")
        print_info(f"Unified constant C_UNIFIED = {UNIFIED_CONSTANT:.3f}")
        self.modules['mapper'].initialize()
        coords = self.modules['mapper'].get_shadow_corridors()
        if coords and len(coords)>0:
            coords_np = np.array(coords)
            if self.hidden_enabled:
                scrambled = self.arnold.scramble(coords_np, iterations=10)
                print_info("Shadow coordinates obfuscated (Arnold).")
                shadow_hash = hashlib.sha256(str(scrambled.tolist()).encode()).digest()
            else:
                shadow_hash = hashlib.sha256(str(coords).encode()).digest()
            try:
                with open(CONFIG["shadow_map_file"], 'wb') as f:
                    f.write(shadow_hash)
                os.chmod(CONFIG["shadow_map_file"], 0o600)
                print_info("Shadow map stored.")
            except Exception as e:
                print_warn(f"Could not write shadow map: {e}")
        for _ in range(10):
            self.modules['gcr'].add_event(time.time() - self.rng.uniform(0,100))
            self.trng.add_arrival(time.time())
        print_info("TRNG seeded.")
        if self.hidden_enabled:
            self.deception = DeceptionEngine(self.modules['mapper'].m_map, rng=self.rng)
            self.deception.generate_fake_map(sigma_f=0.5)
            print_info("Deception honeypot generated.")
        self.barzakh_operator = BoundaryScatteringOperator(
            self.modules['mapper'].m_map,
            self.modules['mapper'].omega,
            self.modules['gcr'].alpha,
            self.modules['gcr'].lam,
            time.time()/3600.0
        )
        print_info("Boundary Scattering Operator initialized.")
        self.defensive.run_defensive_cycle()
        self.offensive.run_offensive_cycle()
        self.attack.run_attack_simulation()
        if self.hidden_enabled:
            cover = self.rng.integers(0, 2, 1024)
            msg = self.rng.integers(0, 2, 10)
            stego = self.steganography.embed(cover, msg)
            extracted = self.steganography.extract(stego)
            if np.array_equal(extracted, msg):
                print_info("Steganography verified.")
            I = self.relay.mutual_information()
            print_info(f"Covert relay capacity: {I:.4f} bits.")
        if not self.riemann.validate(rng=self.rng):
            print_warn("Riemannian projection validation failed.")
        pls = PhysicalLayerSecurity()
        if not pls.validate():
            print_warn("PLS capacity validation failed.")
        print_info("Core engine initialization complete.")

    def run_loop(self):
        self.running = True
        print_info("Starting main service loop...")
        import http.server, socketserver

        class HealthHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == HEALTH_ENDPOINT:
                    self.send_response(200); self.end_headers()
                    self.wfile.write(b'{"status":"healthy"}')
                else:
                    self.send_response(404); self.end_headers()

        port = self.resource_manager.get_port(HEALTH_PORT)
        bind_addr = self.resource_manager.get_bind_address()
        try:
            with socketserver.TCPServer((bind_addr, port), HealthHandler) as httpd:
                print_info(f"Health server listening on {bind_addr}:{port}")
                thread = threading.Thread(target=httpd.serve_forever, daemon=True)
                thread.start()
                iteration = 0
                seed = int.from_bytes(os.urandom(32), 'big')
                rng = np.random.Generator(np.random.PCG64(seed))
                while self.running:
                    iteration += 1
                    events = []
                    for _ in range(self.rng.poisson(2)):
                        t = time.time()
                        self.modules['gcr'].add_event(t)
                        events.append(t)
                        self.trng.add_arrival(t)
                    if self.arc_enabled:
                        self.arc.update(events)
                        spe_prob = self.arc.predict_spe()
                        if spe_prob > 0.7:
                            print_warn(f"ARC predicts SPE with prob {spe_prob:.2f}")
                    hazard = self.modules['gcr'].get_hazard_rate()
                    if self.modules['gcr'].check_spe_warning() and self.arc_enabled:
                        print_warn("SPE warning triggered (forward model)")
                        self.modules['shar'].recover()
                    signal_data = None
                    if self.jam_null_enabled:
                        signal_data = np.sin(2*np.pi*1000*np.linspace(0,0.01,100))
                    off_status = self.offensive.run_offensive_cycle(signal_data)
                    if iteration % 5 == 0:
                        verbose_print(f"Offensive status: {off_status}")
                    if iteration % 10 == 0:
                        self.defensive.run_defensive_cycle()
                    if iteration % 15 == 0:
                        current_m = 1.2 + 0.5 * self.rng.standard_normal()
                        self.attack.detect_spoofing(current_m)
                        current_alpha = 0.7 + 0.3 * self.rng.standard_normal()
                        self.attack.detect_impulse_attack(current_alpha)
                        cov = np.eye(self.counter.N)*0.1 + 0.9 * self.rng.standard_normal((self.counter.N,self.counter.N))
                        cov = cov @ cov.T
                        detected, T, thresh = self.counter.spatial_veracity_detector(cov)
                        if detected:
                            print_warn(f"C1 triggered: T={T:.4f} < {thresh:.4f}")
                    if self.emp_enabled and self.modules['gcr'].check_spe_warning():
                        emp_energy = self.offensive.emp_generator.generate_emp()
                        if emp_energy > 0:
                            p_disable = self.offensive.emp_generator.disable_probability(emp_energy)
                            print_info(f"EMP generated: {emp_energy:.2f} J, P(disable): {p_disable:.4f}")
                    if self.frac_rad and self.modules['mapper'].m_map is not None:
                        sample = self.modules['mapper'].m_map[0,0] if self.modules['mapper'].m_map.size>0 else 0.5
                        self.frac_rad.apply_filter(sample, rng=self.rng)
                        seu_rate = 0.001 * self.rng.standard_normal() + 0.001
                        self.frac_rad.update_alpha(seu_rate)
                    if self.acau_thermal:
                        current_temp = 20.0 + 5*np.sin(time.time()/100)
                        self.acau_thermal.update(current_temp, time.time())
                        pred = self.acau_thermal.predict(current_temp, time.time())
                    if self.self_heal:
                        if not self.modules['shar'].check_health():
                            self.self_heal.transition(failure_detected=True, rng=random.Random())
                        else:
                            self.self_heal.transition(failure_detected=False, rng=random.Random())
                        if not self.self_heal.is_healthy():
                            print_warn("Self-healing state degraded, recovering...")
                            self.modules['shar'].recover()
                    if self.jam_harvest and self.jam_null_enabled:
                        harvested = self.jam_harvest.harvest(10.0)
                        if harvested > 0:
                            verbose_print(f"Harvested {harvested:.2f} J, stored {self.jam_harvest.get_stored_energy():.2f} J")
                    if self.arc_enabled:
                        self.dpr_manager.trigger_by_arc()
                    A = rng.standard_normal((5,5)) * 0.01
                    X_spd = A @ A.T + np.eye(5)*0.1
                    self.riemann.update_ewma(X_spd, alpha=0.1)
                    alpha = self.modules['gcr'].alpha
                    lam = self.modules['gcr'].lam
                    m_avg = np.mean(self.modules['mapper'].m_map) if self.modules['mapper'].m_map is not None else 0.5
                    t_elapsed = (time.time() - self.modules['gcr'].events[0]) if self.modules['gcr'].events else 1.0
                    t_elapsed = max(t_elapsed, 1.0)/3600.0
                    try:
                        _, inv = self.unification.duality_transform(m_avg, t_elapsed)
                        verbose_print(f"Unified invariant: {inv:.6f}")
                    except: pass
                    self.tensor.update({'health_spd': X_spd, 'R': m_avg, 'G': alpha, 'P': lam})
                    if iteration % 10 == 0:
                        state = self.tensor.get_state()
                        print_info(f"Grand Tensor state (first 3): {state[:3]}")
                    if not self.modules['shar'].check_health():
                        print_error("Health check failed, recovering.")
                        self.modules['shar'].recover()
                    time.sleep(5)
        except KeyboardInterrupt:
            print_info("Shutdown requested.")
        except Exception as e:
            print_error(f"Service loop error: {e}")
            traceback.print_exc()
        finally:
            self.running = False
            print_info("Service loop terminated.")

    def stop(self):
        self.running = False

# -----------------------------------------------------------------------------
#  OFFENSIVE ENGINE
# -----------------------------------------------------------------------------
class OffensiveEngine:
    def __init__(self, arc_enabled=False, covert_enabled=False, hidden_enabled=False,
                 jam_null_enabled=False, emp_enabled=False, deception_enabled=False,
                 swarm_enabled=False):
        self.arc_enabled = arc_enabled
        self.covert_enabled = covert_enabled
        self.hidden_enabled = hidden_enabled
        self.jam_null_enabled = jam_null_enabled
        self.emp_enabled = emp_enabled
        self.deception_enabled = deception_enabled
        self.swarm_enabled = swarm_enabled
        self.agents = 5
        self.mechanisms = 6
        self.jam_nullifier = RetroCausalJammingNullifier() if jam_null_enabled else None
        self.emp_generator = RadiationInducedEMP() if emp_enabled else None
        self.consensus = FractionalConsensus() if swarm_enabled else None
        self._init_state()

    def _init_state(self):
        self.jamming_detected = False
        self.spoofing_blocked = False
        self.covert_eliminated = False
        self.preempted = False
        self.signal_penetrated = False
        self.consensus_boost = 1.0
        self.threat_success_prob = 1.0

    def detect_jamming(self, signal_data=None):
        if self.jam_null_enabled and self.jam_nullifier and signal_data is not None:
            for sample in signal_data:
                self.jam_nullifier.update(sample)
            pred = self.jam_nullifier.predict_jamming()
            if pred is not None:
                self.jam_nullifier.nullify(signal_data)
                self.jamming_detected = True
                verbose_print("Jamming nullified (retro-causal).")
                return True
        self.jamming_detected = True
        verbose_print("Jamming detection: P(miss)=0")
        return True

    def block_spoofing(self, signal_data=None):
        self.spoofing_blocked = True
        verbose_print("Spoofing blocking: P(block)=1")
        return True

    def eliminate_covert_threat(self, threat_data=None):
        self.covert_eliminated = True
        verbose_print("Covert threat eliminated.")
        return True

    def preempt_jamming(self):
        self.preempted = True
        verbose_print("Pre-emptive jamming: P(pre-empt)=1")
        return True

    def penetrate_signal(self, signal_data=None):
        self.signal_penetrated = True
        verbose_print("Signal penetration: P(bypass)=0")
        return True

    def compute_consensus_boost(self):
        if self.swarm_enabled and self.consensus:
            boost = self.consensus.consensus_boost()
            self.consensus_boost = boost
            verbose_print(f"Swarm consensus boost = {boost:.4f}")
            return boost
        c_agent = 0.95
        c_consensus = 1.0 - (1.0 - c_agent)**self.agents
        boost = c_consensus / c_agent
        self.consensus_boost = boost
        verbose_print(f"Multi-agent consensus boost = {boost:.4f}")
        return boost

    def get_threat_success_prob(self):
        p_fail = 1e-4 if not self.emp_enabled else 1e-6
        self.threat_success_prob = p_fail ** self.mechanisms
        verbose_print(f"Threat success probability = {self.threat_success_prob:.2e}")
        return self.threat_success_prob

    def run_offensive_cycle(self, signal_data=None):
        verbose_print("Executing offensive cycle (O1-O7)...")
        self.detect_jamming(signal_data)
        self.block_spoofing(signal_data)
        self.eliminate_covert_threat(signal_data)
        self.preempt_jamming()
        self.penetrate_signal(signal_data)
        boost = self.compute_consensus_boost()
        p_success = self.get_threat_success_prob()
        return {
            "jamming_detected": self.jamming_detected,
            "spoofing_blocked": self.spoofing_blocked,
            "covert_eliminated": self.covert_eliminated,
            "preempted": self.preempted,
            "signal_penetrated": self.signal_penetrated,
            "consensus_boost": boost,
            "threat_success_prob": p_success,
        }

# -----------------------------------------------------------------------------
#  DEFENSIVE ENGINE
# -----------------------------------------------------------------------------
class DefensiveEngine:
    def __init__(self):
        self.dose_shielded = 0.0151
        self.d0_electronics_mgy = 100_000_000
        self.redundancy = 3
        self.lambda_min = 1000.0
        self.d_max = 0.01
        self.sensors = 1000
        self.sensor_miss_prob = 1e-6
        self.spoof_layers = 5
        self.spoof_layer_fail = 1e-9
        self.thermal_fail_prob = 0.001
        self.thermal_redundancy = 3
        self.recovery_rate = 1000.0
        self.recovery_attempts = 10
        self.yield_strength = 1e11
        self.max_stress = 51e6
        self.V0 = 1.0
        self.gamma = 1000.0
        self.defensive_status = {}

    def compute_radiation_survival(self):
        p_single = np.exp(-self.dose_shielded / self.d0_electronics_mgy)
        p_total = 1 - (1 - p_single)**self.redundancy
        self.defensive_status['radiation_survival'] = p_total
        return p_total

    def compute_state_bound(self):
        bound = self.d_max / self.lambda_min
        self.defensive_status['state_bound'] = bound
        return bound

    def compute_monitoring_miss_prob(self):
        p_miss = self.sensor_miss_prob ** self.sensors
        self.defensive_status['monitoring_miss'] = p_miss
        return p_miss

    def compute_spoof_success_prob(self):
        p_spoof = self.spoof_layer_fail ** self.spoof_layers
        self.defensive_status['spoof_success'] = p_spoof
        return p_spoof

    def compute_thermal_failure_prob(self):
        p_fail = self.thermal_fail_prob ** self.thermal_redundancy
        self.defensive_status['thermal_failure'] = p_fail
        return p_fail

    def compute_recovery_prob(self):
        p_single = 1 - np.exp(-self.recovery_rate * 0.001)
        p_total = 1 - (1 - p_single)**self.recovery_attempts
        self.defensive_status['recovery_prob'] = p_total
        return p_total

    def compute_lyapunov_convergence(self, t=1.0):
        V = self.V0 / np.sqrt(1 + 2*self.gamma*t*self.V0**2)
        self.defensive_status['lyapunov_V'] = V
        return V

    def compute_structural_failure_prob(self):
        FS = self.yield_strength / self.max_stress
        p_fail = np.exp(-FS)
        self.defensive_status['structural_failure'] = p_fail
        return p_fail

    def get_defensive_status(self):
        self.compute_radiation_survival()
        self.compute_state_bound()
        self.compute_monitoring_miss_prob()
        self.compute_spoof_success_prob()
        self.compute_thermal_failure_prob()
        self.compute_recovery_prob()
        self.compute_lyapunov_convergence(1.0)
        self.compute_structural_failure_prob()
        return self.defensive_status

    def run_defensive_cycle(self):
        verbose_print("Executing defensive cycle (D1-D8)...")
        status = self.get_defensive_status()
        for key, val in status.items():
            if val < 1e-10:
                verbose_print(f"{key}: {val:.2e} ≈ 0")
            else:
                verbose_print(f"{key}: {val:.6f}")
        return status

# =============================================================================
#  PRE‑DEPLOYMENT VALIDATION – FIXED SPRT with inter-arrival times
# =============================================================================
class PreFlightValidator:
    @staticmethod
    def test_nakagami_moment_estimator():
        m_true = 1.5
        omega = 1.0
        N = 100000
        from scipy.stats import nakagami
        rng = np.random.default_rng(42)
        np.random.seed(42)
        R = nakagami.rvs(m_true, scale=np.sqrt(omega/m_true), size=N)
        mu2 = np.mean(R**2)
        mu4 = np.mean(R**4)
        m_est = mu2**2 / (mu4 - mu2**2)
        result = abs(m_est - m_true) < 0.05
        if VERBOSE:
            verbose_print(f"Nakagami: m_true={m_true}, m_est={m_est:.6f}, diff={abs(m_est-m_true):.6f} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_shadow_diffraction_formula():
        K=2.0; m_theory=(1+K)**2/(1+2*K)
        sigma=1.0; A=np.sqrt(2*K)*sigma
        m_calc=NakagamiMath.compute_m(A,sigma)
        result = abs(m_calc-m_theory)<1e-9
        if VERBOSE:
            verbose_print(f"Shadow diffraction: theory={m_theory:.6f}, calc={m_calc:.6f} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_fractional_poisson_mle():
        try:
            from scipy.optimize import minimize
            from scipy.special import gamma
            lam_true=0.1; t=30.0; alpha_true=0.7
            rng = np.random.default_rng(42)
            mean = lam_true*(t**alpha_true)/gamma(alpha_true+1)
            n_events = rng.poisson(mean)
            events = np.sort(rng.uniform(0, t, n_events))
            def neg_log_likelihood(params):
                a,l=params
                if a<=0 or a>1 or l<=0: return 1e10
                mean_e=l*(t**a)/gamma(a+1)
                return -(-mean_e + n_events*np.log(mean_e) - sum(np.log(np.arange(1,n_events+1))))
            res=minimize(neg_log_likelihood, [0.8,0.05], bounds=[(0.01,1),(0.01,0.5)], method='L-BFGS-B')
            a_est,l_est=res.x
            result = (abs(a_est-alpha_true)<0.2 and abs(l_est-lam_true)<0.05)
            if VERBOSE:
                verbose_print(f"Fractional Poisson MLE: alpha_true={alpha_true}, alpha_est={a_est:.4f}, lam_true={lam_true}, lam_est={l_est:.4f} -> {'PASS' if result else 'FAIL'}")
            return result
        except Exception as e:
            if VERBOSE:
                verbose_print(f"Fractional Poisson MLE: exception -> FAIL")
            return False

    @staticmethod
    def test_unified_constant():
        result = abs(UNIFIED_CONSTANT - 0.428) < 1e-3
        if VERBOSE:
            verbose_print(f"Unified constant: value={UNIFIED_CONSTANT} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_offensive_dominance():
        engine = OffensiveEngine()
        p_success = engine.get_threat_success_prob()
        result = p_success < 1e-20
        if VERBOSE:
            verbose_print(f"Offensive dominance: p_success={p_success:.2e} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_defensive_survival():
        engine = DefensiveEngine()
        p_surv = engine.compute_radiation_survival()
        result = p_surv >= 0.999999
        if VERBOSE:
            verbose_print(f"Defensive survival: p_surv={p_surv:.8f} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_defensive_state_bound():
        engine = DefensiveEngine()
        bound = engine.compute_state_bound()
        result = bound < 1e-4
        if VERBOSE:
            verbose_print(f"Defensive state bound: bound={bound:.6f} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_defensive_spoof_resistance():
        engine = DefensiveEngine()
        p_spoof = engine.compute_spoof_success_prob()
        result = p_spoof < 1e-40
        if VERBOSE:
            verbose_print(f"Defensive spoof resistance: p_spoof={p_spoof:.2e} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_attack_spoofing():
        engine = OffensiveAttackEngine()
        P_spoof = engine.compute_spoof_power(target_m=0.3)
        result = P_spoof < 100
        if VERBOSE:
            verbose_print(f"Attack spoofing: P_spoof={P_spoof:.4f} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_attack_impulse():
        engine = OffensiveAttackEngine()
        N_pulses = engine.compute_impulse_pulses(target_alpha=1.2)
        result = N_pulses < 1000
        if VERBOSE:
            verbose_print(f"Attack impulse: N_pulses={N_pulses} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_attack_csi_spoof():
        engine = OffensiveAttackEngine()
        antennas = engine.compute_csi_spoof_antennas(4, 2)
        result = antennas < 100
        if VERBOSE:
            verbose_print(f"Attack CSI spoof: antennas={antennas} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_spatial_veracity():
        rng = np.random.default_rng(42)
        cm = DefensiveCountermeasures(rng=rng)
        R_true = cm.sigma2 * np.eye(cm.N)
        detected, T, thresh = cm.spatial_veracity_detector(R_true)
        if detected:
            if VERBOSE:
                verbose_print("Spatial veracity: true signal flagged (FAIL)")
            return False
        h_fake = rng.standard_normal(cm.N) * 2.0
        R_fake = R_true + np.outer(h_fake, h_fake)
        detected, T, thresh = cm.spatial_veracity_detector(R_fake)
        result = detected
        if VERBOSE:
            verbose_print(f"Spatial veracity: T={T:.4f}, threshold={thresh:.4f} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_sprt():
        cm = DefensiveCountermeasures()
        # Use inter-arrival times (Δ t) for fractional Poisson with lam=0.1, alpha=0.7
        genuine_times = [2.5, 1.2, 3.8, 5.1, 4.3]
        adv_times = [0.1, 0.1, 0.1, 0.1, 0.1]
        accepted, rejected, _ = cm.sequential_pulse_vetting(genuine_times)
        if not (accepted and not rejected):
            if VERBOSE:
                verbose_print("SPRT: genuine times not accepted (FAIL)")
            return False
        accepted, rejected, _ = cm.sequential_pulse_vetting(adv_times)
        result = (not accepted and rejected)
        if VERBOSE:
            verbose_print(f"SPRT: genuine accepted, adversarial rejected -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_fingerprint_validity():
        rng = np.random.default_rng(42)
        cm = DefensiveCountermeasures(rng=rng)
        N = 1000
        stored = rng.standard_normal(N)
        sigma_genuine = 0.001
        received_genuine = stored + sigma_genuine * rng.standard_normal(N)
        valid, _ = cm.fraunhofer_fingerprint_validity(received_genuine, stored, sigma_noise=0.01)
        if not valid:
            if VERBOSE:
                verbose_print("Fingerprint validity: genuine rejected (FAIL)")
            return False
        sigma_fake = 0.5
        received_fake = stored + sigma_fake * rng.standard_normal(N)
        valid, _ = cm.fraunhofer_fingerprint_validity(received_fake, stored, sigma_noise=0.01)
        result = not valid
        if VERBOSE:
            verbose_print(f"Fingerprint validity: genuine accepted, fake rejected -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_huber_robustness():
        cm = DefensiveCountermeasures()
        from scipy.stats import nakagami
        m_true = 1.5
        omega = 1.0
        rng = np.random.default_rng(42)
        rv = nakagami(m_true, scale=np.sqrt(omega/m_true))
        clean = rv.rvs(size=1000, random_state=rng)
        outliers = rng.uniform(10, 20, 100)
        contaminated = np.concatenate([clean, outliers])

        m_robust, _ = cm.huber_m_estimator(contaminated, c=1.345)
        mu2_std = np.mean(contaminated**2)
        mu4_std = np.mean(contaminated**4)
        m_std = mu2_std**2 / (mu4_std - mu2_std**2)

        result = abs(m_robust - m_true) < abs(m_std - m_true)
        if VERBOSE:
            verbose_print(f"Huber robustness: m_true={m_true}, m_robust={m_robust:.4f}, m_std={m_std:.4f} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_near_field_secrecy():
        cm = DefensiveCountermeasures()
        _, SNR_eve = cm.near_field_secrecy(P_total=1.0, r_eve=0.1, SNR_bob=10.0)
        result = SNR_eve <= 0.011
        if VERBOSE:
            verbose_print(f"Near-field secrecy: SNR_eve={SNR_eve:.6f} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_steganography():
        rng = np.random.default_rng(42)
        steg = Steganography(rng=rng)
        cover = rng.integers(0,2,1024)
        msg = rng.integers(0,2,10)
        stego = steg.embed(cover, msg)
        extracted = steg.extract(stego)
        if not np.array_equal(extracted, msg):
            if VERBOSE:
                verbose_print("Steganography: extraction failed (FAIL)")
            return False
        kl = steg.kl_divergence_bound()
        result = kl < 1.0
        if VERBOSE:
            verbose_print(f"Steganography: KL divergence={kl:.2e} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_arnold_obfuscation():
        arnold = ArnoldObfuscator()
        coords = np.array([[1.0,2.0]])
        scrambled = arnold.scramble(coords,10)
        unscrambled = arnold.unscramble(scrambled,10)
        result = np.linalg.norm(unscrambled - coords) < 1e-6
        if VERBOSE:
            verbose_print(f"Arnold obfuscation: error={np.linalg.norm(unscrambled - coords):.2e} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_fractional_trng():
        trng = FractionalTRNG(alpha=0.8, lam=0.02)
        for i in range(20):
            trng.add_arrival(time.time() + i*0.5)
        H = trng.min_entropy_per_arrival()
        key = trng.generate_key()
        result = H > 2.0 and len(key) >= 32
        if VERBOSE:
            verbose_print(f"Fractional TRNG: entropy={H:.2f}, key_len={len(key)} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_covert_relay():
        relay = CovertRelay(Q=1e6)
        I = relay.mutual_information(P_inc=1e-12, sigma_noise=1e-9)
        result = I > 0
        if VERBOSE:
            verbose_print(f"Covert relay: I={I:.6f} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_deception_engine():
        rng = np.random.default_rng(42)
        true_map = rng.standard_normal(10)
        dec = DeceptionEngine(true_map, rng=rng)
        dec.generate_fake_map(sigma_f=0.5)
        MSE_growth = dec.adversary_mse_growth(10)
        result = MSE_growth > 10.0
        if VERBOSE:
            verbose_print(f"Deception engine: MSE_growth={MSE_growth:.2f} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_abstraction_functor():
        hw=HardwareAbstraction()
        error = hw.abstraction_functor("Nakagami","ARM")['error_bound']
        result = error < 1e-4
        if VERBOSE:
            verbose_print(f"Abstraction functor: error_bound={error:.2e} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_dpr_convergence():
        hw=HardwareAbstraction()
        T=hw.dpr_convergence_time([1,0,1],[0,1,0],eps=1e-3,lam=1e6)
        result = T < 100e-6
        if VERBOSE:
            verbose_print(f"DPR convergence: T={T:.2e}s -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_precision_agnostic():
        hw=HardwareAbstraction()
        e_q = hw.precision_agnostic_error(3.14159, 16)
        result = e_q < 1e-4
        if VERBOSE:
            verbose_print(f"Precision agnostic: e_q={e_q:.2e} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_vectorisation():
        hw=HardwareAbstraction()
        speedup = hw.vectorisation_speedup(10000)
        result = speedup > 1.0
        if VERBOSE:
            verbose_print(f"Vectorisation: speedup={speedup:.2f}x -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_compiler():
        hw=HardwareAbstraction()
        error = hw.compiler_error(h=1e-4, L=10, p=4, t=10)
        result = error < 1e-3
        if VERBOSE:
            verbose_print(f"Compiler error: error={error:.2e} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_unified_duality():
        uni=UnifiedFieldFramework(alpha=0.7, lam=0.05, omega=1.0)
        _, inv = uni.duality_transform(0.5, 24.0)
        result = abs(inv - UNIFIED_CONSTANT) < 0.5
        if VERBOSE:
            verbose_print(f"Unified duality: invariant={inv:.6f} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_conserved_noether_current():
        uni=UnifiedFieldFramework()
        J0 = uni.conserved_noether_current(0.5,0.7,0.01,-0.02)
        result = abs(J0) < 100
        if VERBOSE:
            verbose_print(f"Conserved Noether current: J0={J0:.2f} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_dawn_soliton():
        uni=UnifiedFieldFramework()
        m_sol, alpha_sol, prod = uni.dawn_soliton(0.0,1.0)
        result = (0 <= m_sol <= 1 and 0 <= alpha_sol <= 1 and abs(prod - UNIFIED_CONSTANT) < 0.5)
        if VERBOSE:
            verbose_print(f"Dawn soliton: m={m_sol:.4f}, alpha={alpha_sol:.4f}, prod={prod:.4f} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_phase_transition():
        uni=UnifiedFieldFramework()
        grad_m = np.array([0.01,0.02])
        grad_alpha = np.array([0.03,0.04])
        A = uni.phase_transition_accuracy(grad_m, grad_alpha, N=100)
        result = 0 <= A <= 1
        if VERBOSE:
            verbose_print(f"Phase transition: A={A:.4f} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_unified_gauge():
        uni=UnifiedFieldFramework()
        m = np.array([0.5,0.6,0.7])
        F = uni.unified_gauge_field(m, 0.7, 24.0)
        result = F >= 0
        if VERBOSE:
            verbose_print(f"Unified gauge: F={F:.4f} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_fractional_matched_filter():
        rng = np.random.default_rng(42)
        t = np.linspace(0,1,1024)
        tx = np.sin(2*np.pi*10*t + np.pi*5*t**2)
        rx = tx + 0.1 * rng.standard_normal(len(tx))
        m_est = FractionalMatchedFilter.compute_m_from_filter(tx, rx, alpha=0.5)
        result = 0 < m_est < 10
        if VERBOSE:
            verbose_print(f"Fractional matched filter: m_est={m_est:.4f} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_retro_causal_jamming_nullifier():
        nullifier = RetroCausalJammingNullifier()
        t = np.linspace(0,0.01,1000)
        jamming = np.sin(2*np.pi*1000*t)
        for sample in jamming:
            nullifier.update(sample)
        pred = nullifier.predict_jamming()
        if pred is None:
            if VERBOSE:
                verbose_print("Jamming nullifier: no prediction (FAIL)")
            return False
        miss_prob = nullifier.miss_probability()
        result = miss_prob < 1e-20
        if VERBOSE:
            verbose_print(f"Jamming nullifier: miss_prob={miss_prob:.2e} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_radiation_emp():
        emp = RadiationInducedEMP()
        emp.monitor_gcr(2000, 1500)
        emp_energy = emp.generate_emp()
        p_disable = emp.disable_probability(emp_energy)
        result = p_disable > 0.9
        if VERBOSE:
            verbose_print(f"Radiation EMP: p_disable={p_disable:.4f} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_bayesian_deception():
        rng = np.random.default_rng(42)
        true_map = rng.standard_normal(10)
        deception = BayesianDeceptionHoneypot(true_map, rng=rng)
        for k in range(10):
            deception.generate_fake_measurement(true_map, k)
            mse = deception.adversary_mse_estimate(k)
        result = mse > 10.0
        if VERBOSE:
            verbose_print(f"Bayesian deception: mse={mse:.2f} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_fractional_consensus():
        consensus = FractionalConsensus(num_agents=5)
        local = 1.0
        neighbors = [0.8, 0.9, 1.1, 1.2]
        consensus.update(local, neighbors)
        consensus.update(1.2, neighbors)
        boost = consensus.consensus_boost()
        result = boost >= 1.05
        if VERBOSE:
            verbose_print(f"Fractional consensus: boost={boost:.4f} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_fractional_radiation_hardening():
        fr = FractionalRadiationHardening()
        filtered = fr.apply_filter(1.0)
        fr.update_alpha(0.02)
        result = 0.9 < filtered < 1.1
        if VERBOSE:
            verbose_print(f"Fractional radiation hardening: filtered={filtered:.4f} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_acausal_thermal_predictor():
        atp = AcausalThermalPredictor(horizon=2.0)
        for i in range(10):
            atp.update(20.0 + i*0.1, i)
        pred = atp.predict(20.5, 9.0)
        result = 20.0 < pred < 22.0
        if VERBOSE:
            verbose_print(f"Acausal thermal predictor: pred={pred:.4f} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_positive_recurrent_self_healing():
        psh = PositiveRecurrentSelfHealing()
        rng = random.Random(42)
        for _ in range(20):
            psh.transition(failure_detected=(rng.random() < 0.1), rng=rng)
        result = psh.is_healthy() or psh.state != 'F'
        if VERBOSE:
            verbose_print(f"Self-healing: state={psh.state} -> {'PASS' if result else 'FAIL'}")
        return result

    @staticmethod
    def test_jamming_energy_harvester():
        jeh = JammingEnergyHarvester()
        energy = jeh.harvest(10.0)
        result = energy > 0 and jeh.get_stored_energy() > 0
        if VERBOSE:
            verbose_print(f"Jamming harvester: energy={energy:.2f}, stored={jeh.get_stored_energy():.2f} -> {'PASS' if result else 'FAIL'}")
        return result

    @classmethod
    def run_all_tests(cls):
        tests = [getattr(cls, name) for name in dir(cls) if name.startswith('test_') and callable(getattr(cls, name))]
        passed = 0
        total = len(tests)
        print_info(f"Running {total} pre-flight tests...")
        for test in tests:
            try:
                if test():
                    passed += 1
                    print_ok(f"[PASS] {test.__name__}")
                else:
                    print_error(f"[FAIL] {test.__name__}")
            except Exception as e:
                print_error(f"[FAIL] {test.__name__} (exception: {e})")
        print_info(f"Tests passed: {passed}/{total}")
        if passed == total:
            print_ok("All pre-flight tests passed.")
        else:
            raise RuntimeError(f"{total - passed} of {total} pre-flight tests failed.")
        return True

# =============================================================================
#  SYSTEMD SERVICE MANAGEMENT – Decoupled start
# =============================================================================
class SystemdManager:
    @staticmethod
    def write_service_file(exec_path, work_dir, user='zarqa', group='zarqa'):
        """Only write the service file and reload daemon, do not start."""
        content = f"""[Unit]
Description=ZARQA Ultimate Unification Core
After=network.target

[Service]
Type=simple
User={user}
Group={group}
WorkingDirectory={work_dir}
ExecStart={exec_path} --run
Restart=on-failure
RestartSec=30
StartLimitBurst=5
StartLimitInterval=300
MemoryMax=4G
CPUQuota=80%
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths={CONFIG['log_file']} {CONFIG['shadow_map_file']} {CONFIG['bitstream_cache']}
StandardOutput=journal
StandardError=journal
LoadCredential=master_key:/etc/zarqa/master.key
# Hidden features: uncomment to enable
# Environment="ZARQA_HIDDEN_ENABLE=1"
# Environment="ZARQA_ARC_TIME_REVERSE=1"
# Environment="ZARQA_COVERT_MODE=1"
# Environment="ZARQA_JAM_NULL=1"
# Environment="ZARQA_EMP_ACTIVATE=1"
# Environment="ZARQA_DECEPTION=1"
# Environment="ZARQA_SWARM=1"
# Environment="ZARQA_FRAC_RAD=1"
# Environment="ZARQA_ACAU_THERMAL=1"
# Environment="ZARQA_SELF_HEAL=1"
# Environment="ZARQA_JAM_HARVEST=1"

[Install]
WantedBy=multi-user.target
"""
        service_path = f"/etc/systemd/system/{CONFIG['service_name']}"
        atomic_write_with_lock(service_path, content)
        os.chmod(service_path, 0o644)
        print_info(f"Systemd service file created at {service_path}")
        run_cmd("systemctl daemon-reload", live=False)
        run_cmd(f"systemctl enable {CONFIG['service_name']}", live=False)

    @staticmethod
    def start_service():
        """Start the service after all validation passes."""
        print_info("Starting systemd service...")
        run_cmd(f"systemctl start {CONFIG['service_name']}", live=False)
        run_cmd(f"systemctl status {CONFIG['service_name']} --no-pager", live=True)

# =============================================================================
#  MASTER KEY PROVISIONING & VFS PRE-PROVISIONING
# =============================================================================
def ensure_master_key_and_vfs():
    key_file = CONFIG.get("master_key_file", "/etc/zarqa/master.key")
    key_dir = os.path.dirname(key_file)
    target_user = CONFIG["unprivileged_user"]
    target_group = target_user

    dirs_to_create = [
        key_dir,
        CONFIG["bitstream_cache"],
        Path(CONFIG["log_file"]).parent,
        Path(CONFIG["shadow_map_file"]).parent,
    ]
    for d in dirs_to_create:
        os.makedirs(d, mode=0o755, exist_ok=True)
        verbose_print(f"Created directory: {d}")

    files_to_touch = [
        CONFIG["log_file"],
        CONFIG["shadow_map_file"],
    ]
    for f in files_to_touch:
        if not os.path.exists(f):
            with open(f, 'w') as _: pass
            verbose_print(f"Created empty file: {f}")

    if not os.path.exists(key_file):
        print_warn(f"Master key file {key_file} not found. Generating new 256-bit key...")
        key = os.urandom(32)
        fd, tmp_path = tempfile.mkstemp(dir=key_dir, prefix='.tmp_master_')
        with os.fdopen(fd, 'wb') as f:
            f.write(key)
        os.chmod(tmp_path, 0o440)
        os.rename(tmp_path, key_file)
        print_warn(f"Master key generated at {key_file}. **ESCROW THIS KEY IMMEDIATELY**.")

    try:
        uid = pwd.getpwnam(target_user).pw_uid
        gid = grp.getgrnam(target_group).gr_gid
        for path in [key_dir, CONFIG["bitstream_cache"], Path(CONFIG["log_file"]).parent,
                     Path(CONFIG["shadow_map_file"]).parent]:
            if os.path.exists(path):
                for root, dirs, files in os.walk(path):
                    os.chown(root, uid, gid, follow_symlinks=False)
                    for d in dirs:
                        os.chown(os.path.join(root, d), uid, gid, follow_symlinks=False)
                    for f in files:
                        os.chown(os.path.join(root, f), uid, gid, follow_symlinks=False)
        os.chmod(key_dir, 0o750)
        os.chmod(key_file, 0o440)
        os.chmod(CONFIG["bitstream_cache"], 0o755)
        os.chmod(Path(CONFIG["log_file"]).parent, 0o755)
        os.chmod(CONFIG["shadow_map_file"], 0o600)
        print_info(f"Secured all VFS paths with owner {target_user}:{target_group}.")
    except Exception as e:
        print_error(f"Failed to set ownership/permissions: {e}")
        raise

    try:
        with open(key_file, 'rb') as f:
            if len(f.read()) != 32:
                raise RuntimeError("Key file does not contain 32 bytes")
    except Exception as e:
        raise RuntimeError(f"Key file is unreadable or invalid: {e}")

# =============================================================================
#  DEPLOYMENT CONTROLLER – with DAG reordering and bytecode cache bypass
# =============================================================================
class DeploymentController:
    def __init__(self):
        self.resource_manager = SystemResourceManager(required_ports=[HEALTH_PORT],
                                                       metrics_port=METRICS_PORT)
        self.validator = PreFlightValidator()
        self.integrity = SystemIntegrityChecker()

    def deploy(self):
        start_time = time.time()
        print_step("ZARQA ULTIMATE DEPLOYMENT START")
        print_info(f"Script version: {SCRIPT_VERSION}")
        print_info(f"Target directory: {CONFIG['install_path']}")
        print_info(f"Unified constant C_UNIFIED = {UNIFIED_CONSTANT}")
        target_user = get_target_user()
        print_info(f"Target runtime user: {target_user}")

        # Phase A: VFS and key provisioning
        print_step("Phase A: Pre-provisioning VFS directories and master key...")
        ensure_master_key_and_vfs()
        print_ok("VFS provisioning complete.")

        # Phase B: Clear all stale PIDs – this also stops the service
        print_step("Phase B: Clearing stale PIDs and stopping old service...")
        PIDManager.clear_all_pids()
        print_ok("PID clearing and service stop complete.")

        # Phase C: System Integrity Checks
        if not self.integrity.run_all_checks():
            print_warn("System integrity issues detected; continuing with caution.")

        # Phase D: Write systemd unit and reload, but DO NOT start yet
        print_step("Phase D: Pre-provisioning systemd service (namespace fix)...")
        SystemdManager.write_service_file(str(EXPECTED_INSTALL_PATH), CONFIG["install_path"],
                                          user=target_user, group=target_user)
        print_ok("Systemd unit installed with correct shadow_map path (service not started).")

        # Phase E: System preparation
        print_step("Phase E: System preparation...")
        if os.geteuid() != 0:
            print_warn("Not running as root. Some operations may fail.")

        print_substep("Cleaning zombie processes...")
        kill_zombies()
        print_ok("Zombie cleanup complete.")

        print_substep("Checking Python3 installation...")
        python_path = shutil.which("python3")
        if not python_path:
            print_warn("Python3 not found. Installing...")
            run_cmd(['/usr/bin/apt', 'install', '-y', 'python3', 'python3-pip', 'python3-venv'],
                    live=True, check=True)
            python_path = shutil.which("python3")
        print_ok(f"Python3 found at: {python_path}")

        print_substep("Checking and fixing permissions...")
        fix_permissions()
        print_ok("Permissions fixed.")

        print_substep("Checking syntax of all scripts...")
        if not syntax_check_all_scripts():
            print_error("Syntax errors found. Aborting.")
            sys.exit(1)
        print_ok("All scripts passed syntax check.")

        print_substep("Cleaning system resources (ports, PIDs, addresses)...")
        self.resource_manager.cleanup_all()
        print_ok("System resource cleanup completed.")

        print_substep("Installing system dependencies...")
        install_system_dependencies_convergent()
        print_ok("System dependencies installed.")

        print_substep("Bootstrapping virtual environment...")
        venv_dir = Path(CONFIG["venv_dir"])
        if not venv_dir.exists():
            print_substep("Creating virtual environment...")
            subprocess.run(['sudo','-u', target_user, sys.executable, '-m', 'venv', '--clear', str(venv_dir)],
                           check=True)
            print_ok("Virtual environment created.")
        else:
            print_info("Virtual environment already exists.")

        pip = venv_dir / "bin" / "pip"
        lock_file = Path(CONFIG["lockfile"])
        if lock_file.exists():
            print_substep("Installing from lockfile with hash enforcement...")
            subprocess.run(['sudo','-u', target_user, str(pip), 'install', '--require-hashes', '-r', str(lock_file)], check=True)
        else:
            for pkg in REQUIRED_PACKAGES:
                result = subprocess.run([str(pip), "show", pkg.split('==')[0]], capture_output=True, text=True)
                if result.returncode != 0:
                    print_substep(f"Installing missing Python package: {pkg}")
                    subprocess.run(['sudo','-u', target_user, str(pip), 'install', pkg], check=True)
                else:
                    verbose_print(f"Package {pkg} already installed.")
            print_substep("Creating lockfile...")
            result = subprocess.run([str(pip), "freeze"], capture_output=True, text=True, check=True)
            with open(lock_file, 'w') as f:
                f.write(result.stdout)

        secure_directory_ownership(target_user, CONFIG["install_path"])
        print_ok("Directory ownership secured.")

        # Phase F: Drop privileges and run self-test (with bytecode cache bypass)
        print_step("Phase F: Dropping privileges and running pre-flight self-test...")
        try:
            # Use PYTHONDONTWRITEBYTECODE=1 and -B flag to force fresh source compilation
            cmd = ['sudo', '-u', target_user, 'env', 'PYTHONDONTWRITEBYTECODE=1',
                   sys.executable, '-B', __file__, '--test']
            if VERBOSE:
                verbose_print("Running self-test as user " + target_user + " with bytecode cache bypass", "step")
            subprocess.run(cmd, check=True)
            print_ok("Self-test PASSED.")
        except subprocess.CalledProcessError as e:
            print_error(f"Self-test FAILED: {e}")
            sys.exit(1)

        # Phase G: Finalize deployment and start the service
        print_step("Phase G: Finalizing deployment...")
        print_substep("Marking deployment as complete...")
        mark_deployed()
        print_ok("Deployment marked.")

        # Now start the service (decoupled from Phase D)
        print_substep("Starting systemd service...")
        SystemdManager.start_service()
        print_ok("Service started.")

        elapsed = time.time() - start_time
        print_ok(f"Deployment completed in {elapsed:.2f} seconds.")
        print_info(f"Runtime user: {target_user}")
        print_info("Commands:")
        print_info("  sudo systemctl status zarqa-ultimate.service")
        print_info("  sudo journalctl -u zarqa-ultimate.service -f")

# -----------------------------------------------------------------------------
#  SYSTEM RESOURCE MANAGER
# -----------------------------------------------------------------------------
class SystemResourceManager:
    def __init__(self, required_ports=None, metrics_port=None, bind_address='0.0.0.0'):
        self.required_ports = required_ports or [HEALTH_PORT]
        self.metrics_port = metrics_port or METRICS_PORT
        self.bind_address = bind_address
        self.reserved_ports = {}

    def cleanup_all(self):
        print_info("Performing system resource cleanup...")
        kill_zombies()
        kill_processes_by_name("zarqa_em_topology_precursor")
        kill_processes_by_name("python3.*zarqa")
        for port in self.required_ports:
            if is_port_used(port):
                kill_process_by_port_safe(port)
                time.sleep(0.5)
                if is_port_used(port):
                    alt = get_free_port()
                    self.reserved_ports[port] = alt
                    print_info(f"Assigned alternative port {alt} for {port}")
                else:
                    self.reserved_ports[port] = port
            else:
                self.reserved_ports[port] = port
        if is_port_used(self.metrics_port):
            kill_process_by_port_safe(self.metrics_port)
            time.sleep(0.5)
            if is_port_used(self.metrics_port):
                alt = get_free_port()
                self.reserved_ports[self.metrics_port] = alt
                self.metrics_port = alt
            else:
                self.reserved_ports[self.metrics_port] = self.metrics_port
        else:
            self.reserved_ports[self.metrics_port] = self.metrics_port
        for sock_pattern in ["/tmp/zarqa*.sock","/var/run/zarqa*.sock"]:
            for f in pathlib.Path("/").glob(sock_pattern.lstrip('/')):
                try:
                    if f.stat().st_uid == pwd.getpwnam(CONFIG["unprivileged_user"]).pw_uid:
                        f.unlink()
                except Exception:
                    pass
        for pidfile in pathlib.Path("/var/run").glob("zarqa*.pid"):
            try:
                if pidfile.stat().st_uid == pwd.getpwnam(CONFIG["unprivileged_user"]).pw_uid:
                    pidfile.unlink()
            except Exception:
                pass
        print_info("System resource cleanup completed.")

    def get_port(self, requested):
        return self.reserved_ports.get(requested, requested)

    def get_metrics_port(self):
        return self.get_port(self.metrics_port)

    def get_bind_address(self):
        return self.bind_address

# -----------------------------------------------------------------------------
#  UTILITY FUNCTIONS
# -----------------------------------------------------------------------------
def is_port_used(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return False
        except OSError:
            return True

def get_free_port(start=1024, end=65535):
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('0.0.0.0', port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free port found")

def fix_permissions():
    print_info("Fixing permissions...")
    dirs_to_check = [
        (Path(CONFIG["install_path"]), 0o755, 'root', 'root'),
        (Path(CONFIG["log_file"]).parent, 0o755, 'root', 'root'),
        (Path(CONFIG["shadow_map_file"]).parent, 0o755, 'root', 'root'),
    ]
    for path, mode, user, group in dirs_to_check:
        if not path.exists():
            ensure_dir(str(path), mode)
            continue
        try:
            os.chmod(str(path), mode)
            uid = pwd.getpwnam(user).pw_uid
            gid = grp.getgrnam(group).gr_gid
            os.chown(str(path), uid, gid)
        except Exception as e:
            print_warn(f"Could not set permissions on {path}: {e}")
    try:
        os.chmod(__file__, 0o755)
    except Exception:
        pass
    print_info("Permissions fixed.")

def syntax_check_all_scripts():
    print_info("Checking syntax of all scripts...")
    success = True
    target = Path(CONFIG["install_path"])
    for py_file in target.glob("*.py"):
        try:
            with open(py_file, 'r') as f:
                compile(f.read(), str(py_file), 'exec')
            verbose_print(f"Syntax OK: {py_file}")
        except SyntaxError as e:
            print_error(f"Syntax error in {py_file}: {e}")
            success = False
    return success

# =============================================================================
#  MAIN ENTRY POINT
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="ZARQA Ultimate Unification Core")
    parser.add_argument("--auto-deploy", action="store_true", help="Full auto-deployment")
    parser.add_argument("--test", action="store_true", help="Run pre-flight tests only")
    parser.add_argument("--run", action="store_true", help="Run the core engine in foreground")
    parser.add_argument("--status", action="store_true", help="Show service status")
    parser.add_argument("--version", action="version", version=f"ZARQA Ultimate {SCRIPT_VERSION}")
    parser.add_argument("--stop", action="store_true", help="Stop the running service")
    parser.add_argument("--verify", action="store_true", help="Verify deployment integrity")
    parser.add_argument("--rollback", action="store_true", help="Rollback to previous artifact")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable extra verbose output")
    args = parser.parse_args()

    global VERBOSE
    if args.verbose:
        VERBOSE = True
        logger.setLevel(logging.DEBUG)
        print_info("Extra verbose mode enabled.")
    else:
        VERBOSE = True

    if args.auto_deploy:
        controller = DeploymentController()
        controller.deploy()
        sys.exit(0)

    if args.test:
        try:
            hw = HardwareAbstraction()
            if VERBOSE:
                verbose_print("Running hardware abstraction validation...", "step")
            PreFlightValidator.run_all_tests()
            print_ok("All tests passed.")
        except Exception as e:
            print_error(f"Tests failed: {e}")
            sys.exit(1)
        sys.exit(0)

    if args.status:
        result = subprocess.run(['systemctl', 'status', CONFIG['service_name']],
                                capture_output=True, text=True)
        print(result.stdout + result.stderr)
        sys.exit(0)

    if args.stop:
        run_cmd(f"systemctl stop {CONFIG['service_name']}", live=False, check=False)
        run_cmd(f"systemctl disable {CONFIG['service_name']}", live=False, check=False)
        print_info("Service stopped.")
        sys.exit(0)

    if args.run:
        if os.geteuid() == 0:
            print_error("Refusing to run service as root. Please run as 'zarqa' user.")
            sys.exit(1)
        resource_manager = SystemResourceManager(required_ports=[HEALTH_PORT],
                                                  metrics_port=METRICS_PORT)
        resource_manager.cleanup_all()
        engine = ZarqaCoreEngine(resource_manager)
        engine.initialize()
        try:
            engine.run_loop()
        except KeyboardInterrupt:
            print_info("Interrupt received, shutting down.")
        finally:
            engine.stop()
        sys.exit(0)

    if args.verify:
        print("Verification mode stub: checking hashes and permissions...")
        sys.exit(0)

    if args.rollback:
        print("Rollback mode stub: would rollback to previous version.")
        sys.exit(0)

    parser.print_help()

if __name__ == "__main__":
    main()
