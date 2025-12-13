"""
System Information Module

Handles OS detection and shell environment identification
for cross-platform command generation.
"""

import platform
import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class OSType(Enum):
    """Supported operating system types."""
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    UNKNOWN = "unknown"


class ShellType(Enum):
    """Supported shell types."""
    POWERSHELL = "powershell"
    CMD = "cmd"
    BASH = "bash"
    ZSH = "zsh"
    FISH = "fish"
    UNKNOWN = "unknown"


@dataclass
class SystemContext:
    """Container for system environment information."""
    os_type: OSType
    shell_type: ShellType
    os_version: str
    architecture: str
    home_directory: str
    current_directory: str

    def get_shell_name(self) -> str:
        """Returns human-readable shell name."""
        shell_names = {
            ShellType.POWERSHELL: "PowerShell",
            ShellType.CMD: "Command Prompt (CMD)",
            ShellType.BASH: "Bash",
            ShellType.ZSH: "Zsh",
            ShellType.FISH: "Fish",
            ShellType.UNKNOWN: "Unknown Shell"
        }
        return shell_names.get(self.shell_type, "Unknown Shell")
    
    def get_os_name(self) -> str:
        """Returns human-readable OS name."""
        os_names = {
            OSType.WINDOWS: "Windows",
            OSType.LINUX: "Linux",
            OSType.MACOS: "macOS",
            OSType.UNKNOWN: "Unknown OS"
        }
        return os_names.get(self.os_type, "Unknown OS")


def detect_os() -> OSType:
    """Detect the current operating system."""
    system = platform.system().lower()
    
    if system == "windows":
        return OSType.WINDOWS
    elif system == "linux":
        return OSType.LINUX
    elif system == "darwin":
        return OSType.MACOS
    else:
        return OSType.UNKNOWN


def detect_shell() -> ShellType:
    """Detect the current shell environment."""
    os_type = detect_os()
    
    if os_type == OSType.WINDOWS:
        # Check for PowerShell vs CMD
        # PSModulePath is typically set in PowerShell
        if os.environ.get("PSModulePath"):
            return ShellType.POWERSHELL
        # Check parent process name
        comspec = os.environ.get("ComSpec", "").lower()
        if "powershell" in comspec:
            return ShellType.POWERSHELL
        return ShellType.POWERSHELL  # Default to PowerShell on modern Windows
    
    else:
        # Unix-like systems
        shell_path = os.environ.get("SHELL", "")
        shell_name = os.path.basename(shell_path).lower()
        
        if "zsh" in shell_name:
            return ShellType.ZSH
        elif "bash" in shell_name:
            return ShellType.BASH
        elif "fish" in shell_name:
            return ShellType.FISH
        else:
            return ShellType.BASH  # Default to Bash


def get_system_context() -> SystemContext:
    """
    Gather complete system context for command generation.
    
    Returns:
        SystemContext object with all relevant system information.
    """
    os_type = detect_os()
    shell_type = detect_shell()
    
    return SystemContext(
        os_type=os_type,
        shell_type=shell_type,
        os_version=platform.version(),
        architecture=platform.machine(),
        home_directory=os.path.expanduser("~"),
        current_directory=os.getcwd()
    )


def get_shell_for_subprocess() -> tuple[str, list[str]]:
    """
    Get the appropriate shell executable and arguments for subprocess.
    
    Returns:
        Tuple of (shell_executable, shell_args)
    """
    os_type = detect_os()
    
    if os_type == OSType.WINDOWS:
        # Use PowerShell on Windows
        return ("powershell", ["-NoProfile", "-Command"])
    else:
        # Use default shell on Unix-like systems
        shell = os.environ.get("SHELL", "/bin/bash")
        return (shell, ["-c"])

