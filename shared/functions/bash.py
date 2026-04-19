import logging
import re
import subprocess

logger = logging.getLogger(__name__)

_BLOCKED_COMMANDS = [
    r"rm\s+-rf\s+/",
    r"\bmkfs\b",
    r"\bdd\b.+\bif=",
    r"\bshutdown\b",
    r"\breboot\b",
    r"\bhalt\b",
    r":\(\)\s*\{.*\}",  # fork bomb
    r"\bchmod\s+777\s+/",
    r"\bsudo\s+rm\b",
]


def run_bash(command: str) -> str:
    """Executes an arbitrary bash command and returns its output.

    Available commands include:
    File and directory:
      ls, cp, mv, rm, mkdir, rmdir, touch, ln, chmod, chown, chgrp, find, locate, stat, file, du, df

    Text processing:
      cat, echo, head, tail, grep, sed, awk, cut, sort, uniq, wc, tr, diff, patch, tee, xargs

    Networking:
      ping, curl, wget, ssh, scp, rsync, netstat, ifconfig, ip, nslookup, dig, traceroute, nc, telnet

    Process management:
      ps, top, kill, killall, pkill, pgrep, nice, nohup, jobs, bg, fg, wait

    System info:
      uname, hostname, uptime, whoami, id, date, cal, env, printenv, lsof, dmesg, sysctl

    Archive and compression:
      tar, gzip, gunzip, zip, unzip, bzip2, xz

    Package management:
      apt, apt-get, brew, pip, npm, yum, dnf

    Disk and filesystem:
      mount, umount, fdisk, mkfs, fsck, lsblk, blkid

    Shell utilities:
      echo, printf, read, export, source, alias, history, which, type, man, help, test, expr
    """

    for pattern in _BLOCKED_COMMANDS:
        if re.search(pattern, command, re.IGNORECASE):
            logger.warning("Blocked dangerous bash command: %s", command)
            return f"Blocked: command matches disallowed pattern '{pattern}'."

    logger.info("Running bash command: %s", command)
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout
        if result.returncode != 0:
            output += result.stderr
        return output or f"Command exited with code {result.returncode}"
    except subprocess.TimeoutExpired:
        return f"Command timed out after 30 seconds: {command}"
    except Exception as e:
        return f"Failed to run command '{command}': {e}"
