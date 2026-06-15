"""
SystemInfo model - PRD §📋
"""
from dataclasses import dataclass

@dataclass
class SystemInfo:
    os: str          # ubuntu, macos, windows, etc.
    os_version: str
    arch: str        # x86_64, arm64, AMD64, etc.
    hostname: str
    user: str
    timestamp: str
