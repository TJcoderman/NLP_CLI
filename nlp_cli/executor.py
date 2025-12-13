"""
Command Executor Module

Handles safe execution of shell commands with proper
subprocess management and output handling.
"""

import subprocess
import shlex
from dataclasses import dataclass
from typing import Optional
from enum import Enum

from .system_info import get_shell_for_subprocess, OSType, detect_os


class RiskLevel(Enum):
    """Risk levels for command operations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ExecutionResult:
    """Container for command execution results."""
    stdout: str
    stderr: str
    return_code: int
    success: bool
    
    @property
    def output(self) -> str:
        """Combined output preferring stdout."""
        if self.stdout:
            return self.stdout
        return self.stderr


class CommandExecutor:
    """
    Safely executes shell commands with risk assessment.
    
    This class provides a layer of safety between the AI-generated
    commands and actual system execution.
    """
    
    # Keywords that indicate dangerous operations
    DANGEROUS_KEYWORDS = {
        RiskLevel.CRITICAL: [
            "rm -rf /",
            "rm -rf /*",
            ":(){ :|:& };:",  # Fork bomb
            "mkfs",
            "dd if=",
            "> /dev/sda",
            "chmod -R 777 /",
            "format c:",
            "del /f /s /q c:\\",
            "Remove-Item -Recurse -Force C:\\",
        ],
        RiskLevel.HIGH: [
            "rm -rf",
            "rm -r",
            "rmdir /s",
            "del /s",
            "Remove-Item -Recurse",
            "sudo rm",
            "chmod -R",
            "chown -R",
            "shutdown",
            "reboot",
            "init 0",
            "init 6",
            "kill -9",
            "pkill",
            "killall",
            "> /dev/null",
            "truncate",
        ],
        RiskLevel.MEDIUM: [
            "sudo",
            "rm ",
            "del ",
            "Remove-Item",
            "mv ",
            "move ",
            "Move-Item",
            "chmod",
            "chown",
            "curl | bash",
            "wget | bash",
            "pip install",
            "npm install -g",
        ],
    }
    
    def __init__(self, timeout: int = 30):
        """
        Initialize the executor.
        
        Args:
            timeout: Maximum seconds to wait for command completion.
        """
        self.timeout = timeout
        self.os_type = detect_os()
    
    def assess_risk(self, command: str) -> tuple[RiskLevel, list[str]]:
        """
        Assess the risk level of a command.
        
        Args:
            command: The command to assess.
            
        Returns:
            Tuple of (RiskLevel, list of reasons).
        """
        command_lower = command.lower()
        reasons = []
        highest_risk = RiskLevel.LOW
        
        for risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.MEDIUM]:
            for keyword in self.DANGEROUS_KEYWORDS[risk_level]:
                if keyword.lower() in command_lower:
                    reasons.append(f"Contains '{keyword}'")
                    if risk_level.value > highest_risk.value or (
                        risk_level == RiskLevel.CRITICAL
                    ):
                        highest_risk = risk_level
        
        return highest_risk, reasons
    
    def execute(
        self, 
        command: str, 
        capture_output: bool = True,
        timeout: Optional[int] = None
    ) -> ExecutionResult:
        """
        Execute a shell command.
        
        Args:
            command: The command to execute.
            capture_output: Whether to capture stdout/stderr.
            timeout: Override default timeout.
            
        Returns:
            ExecutionResult with output and status.
        """
        shell_exe, shell_args = get_shell_for_subprocess()
        effective_timeout = timeout or self.timeout
        
        try:
            if self.os_type == OSType.WINDOWS:
                # Windows: Use PowerShell
                result = subprocess.run(
                    [shell_exe] + shell_args + [command],
                    capture_output=capture_output,
                    text=True,
                    timeout=effective_timeout,
                    shell=False,
                )
            else:
                # Unix: Use shell directly
                result = subprocess.run(
                    command,
                    shell=True,
                    executable=shell_exe,
                    capture_output=capture_output,
                    text=True,
                    timeout=effective_timeout,
                )
            
            return ExecutionResult(
                stdout=result.stdout.strip() if result.stdout else "",
                stderr=result.stderr.strip() if result.stderr else "",
                return_code=result.returncode,
                success=result.returncode == 0
            )
            
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                stdout="",
                stderr=f"Command timed out after {effective_timeout} seconds",
                return_code=-1,
                success=False
            )
        except Exception as e:
            return ExecutionResult(
                stdout="",
                stderr=str(e),
                return_code=-1,
                success=False
            )
    
    def dry_run(self, command: str) -> str:
        """
        Show what would be executed without actually running it.
        
        Args:
            command: The command to analyze.
            
        Returns:
            Description of what would happen.
        """
        shell_exe, shell_args = get_shell_for_subprocess()
        risk_level, reasons = self.assess_risk(command)
        
        output = f"Shell: {shell_exe}\n"
        output += f"Command: {command}\n"
        output += f"Risk Level: {risk_level.value.upper()}\n"
        
        if reasons:
            output += "Warnings:\n"
            for reason in reasons:
                output += f"  - {reason}\n"
        
        return output


def create_executor(timeout: int = 30) -> CommandExecutor:
    """
    Factory function to create a CommandExecutor instance.
    
    Args:
        timeout: Maximum seconds for command execution.
        
    Returns:
        Configured CommandExecutor instance.
    """
    return CommandExecutor(timeout=timeout)

