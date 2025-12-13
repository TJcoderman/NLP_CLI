"""
LLM Prompt Templates Module

Contains carefully crafted system prompts for consistent
and accurate command generation across different platforms.
"""

from .system_info import SystemContext, OSType, ShellType


def get_system_prompt(context: SystemContext) -> str:
    """
    Generate a system prompt tailored to the detected OS and shell.
    
    Args:
        context: SystemContext object with system information.
        
    Returns:
        Formatted system prompt string for the LLM.
    """
    
    os_name = context.get_os_name()
    shell_name = context.get_shell_name()
    
    # OS-specific command examples and notes
    os_examples = _get_os_examples(context)
    
    system_prompt = f"""You are a CLI command translator. Your ONLY job is to convert natural language requests into executable shell commands.

SYSTEM INFORMATION:
- Operating System: {os_name}
- Shell: {shell_name}
- Architecture: {context.architecture}
- Current Directory: {context.current_directory}

STRICT RULES:
1. Output ONLY the command - no explanations, no markdown, no code blocks
2. Never use ```bash``` or any formatting - just the raw command
3. Use the correct syntax for {shell_name} on {os_name}
4. If multiple commands are needed, chain them properly for the shell
5. For dangerous operations (delete, format, etc.), still provide the command
6. If the request is unclear, output the most likely intended command
7. Always use absolute paths when the context suggests it
8. Prefer built-in commands over external tools when possible

{os_examples}

RESPONSE FORMAT:
- Single line command OR
- Multi-line command with proper line continuation for the shell
- NO explanations, NO markdown, NO additional text

Remember: Output ONLY the executable command, nothing else."""

    return system_prompt


def _get_os_examples(context: SystemContext) -> str:
    """Generate OS-specific examples for the prompt."""
    
    if context.os_type == OSType.WINDOWS:
        if context.shell_type == ShellType.POWERSHELL:
            return """POWERSHELL EXAMPLES:
- List files: Get-ChildItem or dir or ls
- Create folder: New-Item -ItemType Directory -Name "FolderName" or mkdir FolderName
- Delete files: Remove-Item *.txt or del *.txt
- Copy files: Copy-Item source dest
- Move files: Move-Item source dest
- Find text in files: Select-String -Pattern "text" -Path *.txt
- Show file contents: Get-Content filename or cat filename
- Current directory: Get-Location or pwd
- Environment variables: $env:VARNAME
- Chain commands: command1; command2
- Conditional: command1 && command2"""
        else:  # CMD
            return """CMD EXAMPLES:
- List files: dir
- Create folder: mkdir FolderName
- Delete files: del *.txt
- Copy files: copy source dest
- Move files: move source dest
- Find text: findstr "text" *.txt
- Show file: type filename
- Current directory: cd
- Environment variables: %VARNAME%
- Chain commands: command1 & command2
- Conditional: command1 && command2"""
    
    else:  # Linux/macOS (Bash/Zsh/Fish)
        return """BASH/ZSH EXAMPLES:
- List files: ls -la
- Create folder: mkdir -p FolderName
- Delete files: rm *.txt
- Copy files: cp source dest
- Move files: mv source dest
- Find text: grep "text" *.txt
- Show file: cat filename
- Current directory: pwd
- Environment variables: $VARNAME
- Chain commands: command1; command2
- Conditional: command1 && command2
- Background: command &
- Sudo for admin: sudo command"""


def get_refinement_prompt(original_request: str, generated_command: str, error: str) -> str:
    """
    Generate a prompt to refine a failed command.
    
    Args:
        original_request: The user's original natural language request.
        generated_command: The command that failed.
        error: The error message from execution.
        
    Returns:
        Prompt to help LLM fix the command.
    """
    return f"""The command you generated failed. Please fix it.

Original Request: {original_request}
Generated Command: {generated_command}
Error: {error}

Provide ONLY the corrected command, no explanations."""


def get_explanation_prompt(command: str, context: SystemContext) -> str:
    """
    Generate a prompt to explain what a command does.
    
    Args:
        command: The shell command to explain.
        context: System context information.
        
    Returns:
        Prompt for command explanation.
    """
    return f"""Explain this {context.get_shell_name()} command in simple terms:

Command: {command}

Provide a brief, clear explanation of:
1. What this command does
2. Any potential risks or side effects
3. What files/directories it affects

Keep it concise - max 3-4 sentences."""

