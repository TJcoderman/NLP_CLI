"""
Command Templates Module

Maps intents to OS-specific shell command templates.
Templates use placeholders that get filled with extracted entities.

Placeholders:
- {filename} - Specific file name
- {pattern} - File pattern like *.txt
- {directory} - Directory/folder name
- {destination} - Destination path
- {source} - Source path
- {path} - Generic path
- {text} - Search text
- {new_name} - New name for rename
- {url} - URL for downloads
- {hostname} - Hostname/IP for network commands
- {process} - Process name
"""

from dataclasses import dataclass
from typing import Dict, Optional

from .system_info import OSType, ShellType, SystemContext
from .entity_extractor import ExtractedEntities


@dataclass
class CommandTemplate:
    """A command template with OS-specific variations."""
    windows_powershell: str
    windows_cmd: str
    unix: str  # Works for Linux and macOS (bash/zsh)
    
    # Description for the user
    description: str
    
    # Whether this command is potentially dangerous
    is_dangerous: bool = False


# Map intents to command templates
COMMAND_TEMPLATES: Dict[str, CommandTemplate] = {
    
    # ============== FILE LISTING ==============
    "list_files": CommandTemplate(
        windows_powershell="Get-ChildItem",
        windows_cmd="dir",
        unix="ls",
        description="List files in current directory",
    ),
    
    "list_files_detailed": CommandTemplate(
        windows_powershell="Get-ChildItem -Force | Format-Table Mode, LastWriteTime, Length, Name",
        windows_cmd="dir /a",
        unix="ls -la",
        description="List files with detailed information",
    ),
    
    # ============== DIRECTORY OPERATIONS ==============
    "create_directory": CommandTemplate(
        windows_powershell="New-Item -ItemType Directory -Name \"{directory}\"",
        windows_cmd="mkdir \"{directory}\"",
        unix="mkdir -p \"{directory}\"",
        description="Create a new directory",
    ),
    
    "delete_directory": CommandTemplate(
        windows_powershell="Remove-Item -Recurse -Force \"{directory}\"",
        windows_cmd="rmdir /s /q \"{directory}\"",
        unix="rm -rf \"{directory}\"",
        description="Delete a directory and its contents",
        is_dangerous=True,
    ),
    
    "current_directory": CommandTemplate(
        windows_powershell="Get-Location",
        windows_cmd="cd",
        unix="pwd",
        description="Show current working directory",
    ),
    
    "change_directory": CommandTemplate(
        windows_powershell="Set-Location \"{directory}\"",
        windows_cmd="cd \"{directory}\"",
        unix="cd \"{directory}\"",
        description="Change to a different directory",
    ),
    
    # ============== FILE OPERATIONS ==============
    "delete_files": CommandTemplate(
        windows_powershell="Remove-Item {target}",
        windows_cmd="del {target}",
        unix="rm {target}",
        description="Delete files",
        is_dangerous=True,
    ),
    
    "copy_files": CommandTemplate(
        windows_powershell="Copy-Item \"{source}\" -Destination \"{destination}\"",
        windows_cmd="copy \"{source}\" \"{destination}\"",
        unix="cp \"{source}\" \"{destination}\"",
        description="Copy files from source to destination",
    ),
    
    "move_files": CommandTemplate(
        windows_powershell="Move-Item \"{source}\" -Destination \"{destination}\"",
        windows_cmd="move \"{source}\" \"{destination}\"",
        unix="mv \"{source}\" \"{destination}\"",
        description="Move files from source to destination",
    ),
    
    "rename": CommandTemplate(
        windows_powershell="Rename-Item \"{filename}\" -NewName \"{new_name}\"",
        windows_cmd="ren \"{filename}\" \"{new_name}\"",
        unix="mv \"{filename}\" \"{new_name}\"",
        description="Rename a file or directory",
    ),
    
    "view_file": CommandTemplate(
        windows_powershell="Get-Content \"{filename}\"",
        windows_cmd="type \"{filename}\"",
        unix="cat \"{filename}\"",
        description="Display file contents",
    ),
    
    "create_file": CommandTemplate(
        windows_powershell="New-Item -ItemType File -Name \"{filename}\"",
        windows_cmd="type nul > \"{filename}\"",
        unix="touch \"{filename}\"",
        description="Create an empty file",
    ),
    
    # ============== SEARCH OPERATIONS ==============
    "find_files": CommandTemplate(
        windows_powershell="Get-ChildItem -Recurse -Filter \"{pattern}\"",
        windows_cmd="dir /s /b {pattern}",
        unix="find . -name \"{pattern}\"",
        description="Find files matching a pattern",
    ),
    
    "search_in_files": CommandTemplate(
        windows_powershell="Select-String -Pattern \"{text}\" -Path {target}",
        windows_cmd="findstr /s \"{text}\" {target}",
        unix="grep -r \"{text}\" {target}",
        description="Search for text within files",
    ),
    
    # ============== SYSTEM INFO ==============
    "system_info": CommandTemplate(
        windows_powershell="Get-ComputerInfo | Select-Object WindowsProductName, OsVersion, CsProcessors",
        windows_cmd="systeminfo",
        unix="uname -a",
        description="Display system information",
    ),
    
    "disk_usage": CommandTemplate(
        windows_powershell="Get-PSDrive -PSProvider FileSystem | Select-Object Name, Used, Free",
        windows_cmd="wmic logicaldisk get size,freespace,caption",
        unix="df -h",
        description="Show disk usage",
    ),
    
    "file_size": CommandTemplate(
        windows_powershell="Get-ChildItem \"{path}\" -Recurse | Measure-Object -Property Length -Sum",
        windows_cmd="dir /s \"{path}\"",
        unix="du -sh \"{path}\"",
        description="Show file or folder size",
    ),
    
    # ============== PROCESS OPERATIONS ==============
    "list_processes": CommandTemplate(
        windows_powershell="Get-Process | Sort-Object CPU -Descending | Select-Object -First 20",
        windows_cmd="tasklist",
        unix="ps aux | head -20",
        description="List running processes",
    ),
    
    "kill_process": CommandTemplate(
        windows_powershell="Stop-Process -Name \"{process}\" -Force",
        windows_cmd="taskkill /IM \"{process}\" /F",
        unix="pkill -f \"{process}\"",
        description="Kill a process by name",
        is_dangerous=True,
    ),
    
    # ============== NETWORK ==============
    "network_info": CommandTemplate(
        windows_powershell="Get-NetIPAddress | Where-Object {$_.AddressFamily -eq 'IPv4'}",
        windows_cmd="ipconfig",
        unix="ip addr show 2>/dev/null || ifconfig",
        description="Show network configuration",
    ),
    
    "ping": CommandTemplate(
        windows_powershell="Test-Connection -ComputerName \"{hostname}\" -Count 4",
        windows_cmd="ping -n 4 \"{hostname}\"",
        unix="ping -c 4 \"{hostname}\"",
        description="Ping a host",
    ),
    
    # ============== DATE/TIME ==============
    "datetime": CommandTemplate(
        windows_powershell="Get-Date",
        windows_cmd="date /t & time /t",
        unix="date",
        description="Show current date and time",
    ),
    
    # ============== MISC ==============
    "clear_screen": CommandTemplate(
        windows_powershell="Clear-Host",
        windows_cmd="cls",
        unix="clear",
        description="Clear the terminal screen",
    ),
    
    "env_vars": CommandTemplate(
        windows_powershell="Get-ChildItem Env:",
        windows_cmd="set",
        unix="env",
        description="Show environment variables",
    ),
    
    "history": CommandTemplate(
        windows_powershell="Get-History",
        windows_cmd="doskey /history",
        unix="history",
        description="Show command history",
    ),
    
    "count_files": CommandTemplate(
        windows_powershell="(Get-ChildItem {target} | Measure-Object).Count",
        windows_cmd="dir /a-d {target} | find /c \":\"",
        unix="ls -1 {target} | wc -l",
        description="Count files in directory",
    ),
    
    "count_lines": CommandTemplate(
        windows_powershell="Get-Content \"{filename}\" | Measure-Object -Line",
        windows_cmd="find /c /v \"\" \"{filename}\"",
        unix="wc -l \"{filename}\"",
        description="Count lines in a file",
    ),
    
    "compare_files": CommandTemplate(
        windows_powershell="Compare-Object (Get-Content \"{source}\") (Get-Content \"{destination}\")",
        windows_cmd="fc \"{source}\" \"{destination}\"",
        unix="diff \"{source}\" \"{destination}\"",
        description="Compare two files",
    ),
    
    "echo": CommandTemplate(
        windows_powershell="Write-Output \"{text}\"",
        windows_cmd="echo {text}",
        unix="echo \"{text}\"",
        description="Print text to terminal",
    ),
    
    "compress": CommandTemplate(
        windows_powershell="Compress-Archive -Path \"{source}\" -DestinationPath \"{destination}.zip\"",
        windows_cmd="tar -cvf \"{destination}.tar\" \"{source}\"",
        unix="zip -r \"{destination}.zip\" \"{source}\"",
        description="Compress files or folders",
    ),
    
    "extract": CommandTemplate(
        windows_powershell="Expand-Archive -Path \"{source}\" -DestinationPath \"{destination}\"",
        windows_cmd="tar -xvf \"{source}\"",
        unix="unzip \"{source}\" -d \"{destination}\"",
        description="Extract compressed files",
    ),
    
    "permissions": CommandTemplate(
        windows_powershell="icacls \"{filename}\"",
        windows_cmd="icacls \"{filename}\"",
        unix="chmod +x \"{filename}\"",
        description="Change file permissions",
    ),
    
    "download": CommandTemplate(
        windows_powershell="Invoke-WebRequest -Uri \"{url}\" -OutFile \"{filename}\"",
        windows_cmd="curl -o \"{filename}\" \"{url}\"",
        unix="wget \"{url}\" -O \"{filename}\"",
        description="Download a file from URL",
    ),
    
    "help": CommandTemplate(
        windows_powershell="Get-Help {command}",
        windows_cmd="help {command}",
        unix="man {command}",
        description="Show help for a command",
    ),
    
    "shutdown": CommandTemplate(
        windows_powershell="Stop-Computer -Force",
        windows_cmd="shutdown /s /t 0",
        unix="sudo shutdown -h now",
        description="Shutdown the computer",
        is_dangerous=True,
    ),
    
    "restart": CommandTemplate(
        windows_powershell="Restart-Computer -Force",
        windows_cmd="shutdown /r /t 0",
        unix="sudo reboot",
        description="Restart the computer",
        is_dangerous=True,
    ),

    # ============== CYBER / ADVANCED NETWORKING ==============
    "port_scan": CommandTemplate(
        windows_powershell="Test-NetConnection -ComputerName \"{hostname}\" -Port 80",
        windows_cmd="nmap \"{hostname}\"", # Assumes nmap is installed
        unix="nmap \"{hostname}\"",
        description="Scan ports on a host",
        is_dangerous=True,
    ),

    "trace_route": CommandTemplate(
        windows_powershell="Test-NetConnection -ComputerName \"{hostname}\" -TraceRoute",
        windows_cmd="tracert \"{hostname}\"",
        unix="traceroute \"{hostname}\"",
        description="Trace route to host",
    ),

    "dns_lookup": CommandTemplate(
        windows_powershell="Resolve-DnsName -Name \"{hostname}\"",
        windows_cmd="nslookup \"{hostname}\"",
        unix="nslookup \"{hostname}\" || dig \"{hostname}\"",
        description="Lookup DNS records",
    ),

    "check_ports": CommandTemplate(
        windows_powershell="Get-NetTCPConnection | Where-Object State -eq Listen",
        windows_cmd="netstat -an | findstr LISTENING",
        unix="netstat -tuln || ss -tuln",
        description="Check open ports",
    ),

    "ssh_connect": CommandTemplate(
        windows_powershell="ssh {hostname}",
        windows_cmd="ssh {hostname}",
        unix="ssh {hostname}",
        description="Connect via SSH",
    ),

    # ============== PACKAGE / SYSTEM MAINTENANCE ==============
    "update_system": CommandTemplate(
        windows_powershell="winget upgrade --all",
        windows_cmd="winget upgrade --all",
        unix="sudo apt update && sudo apt upgrade -y",
        description="Update system packages",
        is_dangerous=True,
    ),

    "install_package": CommandTemplate(
        windows_powershell="winget install \"{process}\"",
        windows_cmd="winget install \"{process}\"",
        unix="sudo apt install \"{process}\"",
        description="Install a package",
        is_dangerous=True,
    ),

    "system_monitor": CommandTemplate(
        windows_powershell="Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 | Format-Table",
        windows_cmd="tasklist",
        unix="htop || top",
        description="Monitor system resources",
    ),

    # ============== ADVANCED FILE OPS ==============
    "make_symlink": CommandTemplate(
        windows_powershell="New-Item -ItemType SymbolicLink -Path \"{destination}\" -Target \"{source}\"",
        windows_cmd="mklink \"{destination}\" \"{source}\"",
        unix="ln -s \"{source}\" \"{destination}\"",
        description="Create symbolic link",
    ),

    "change_owner": CommandTemplate(
        windows_powershell="icacls \"{filename}\" /setowner \"{process}\"", # Using process placeholder for user/owner
        windows_cmd="icacls \"{filename}\" /setowner \"{process}\"",
        unix="sudo chown \"{process}\" \"{filename}\"",
        description="Change file owner",
        is_dangerous=True,
    ),

    "write_file": CommandTemplate(
        windows_powershell="Set-Content -Path \"{filename}\" -Value \"{text}\"",
        windows_cmd="echo {text} > \"{filename}\"",
        unix="echo \"{text}\" > \"{filename}\"",
        description="Write text to a file",
        is_dangerous=True,
    ),

    "firewall_allow": CommandTemplate(
        windows_powershell="New-NetFirewallRule -DisplayName \"Allow {process}\" -Direction Inbound -Program \"{process}\" -Action Allow",
        windows_cmd="netsh advfirewall firewall add rule name=\"Allow {process}\" dir=in action=allow program=\"{process}\"",
        unix="sudo ufw allow {process}",
        description="Allow app through firewall",
        is_dangerous=True,
    ),

    "get_wifi_pass": CommandTemplate(
        windows_powershell="netsh wlan show profile name=\"{text}\" key=clear",
        windows_cmd="netsh wlan show profile name=\"{text}\" key=clear",
        unix="sudo cat /etc/NetworkManager/system-connections/{text} | grep psk=",
        description="Get Wi-Fi password",
        is_dangerous=True,
    ),

    "check_service": CommandTemplate(
        windows_powershell="Get-Service -Name \"{process}\"",
        windows_cmd="sc query \"{process}\"",
        unix="systemctl status {process}",
        description="Check service status",
    ),

    # ============== GIT / VERSION CONTROL ==============
    "git_status": CommandTemplate(
        windows_powershell="git status",
        windows_cmd="git status",
        unix="git status",
        description="Show git repository status",
    ),

    "git_log": CommandTemplate(
        windows_powershell="git log --oneline --graph --decorate -n 10",
        windows_cmd="git log --oneline -n 10",
        unix="git log --oneline --graph --decorate -n 10",
        description="Show git commit log",
    ),

    "git_pull": CommandTemplate(
        windows_powershell="git pull",
        windows_cmd="git pull",
        unix="git pull",
        description="Pull latest changes from git",
    ),

    "git_push": CommandTemplate(
        windows_powershell="git push",
        windows_cmd="git push",
        unix="git push",
        description="Push changes to remote",
    ),

    # ============== DOCKER / CONTAINERS ==============
    "docker_ps": CommandTemplate(
        windows_powershell="docker ps -a",
        windows_cmd="docker ps -a",
        unix="docker ps -a",
        description="List docker containers",
    ),

    "docker_images": CommandTemplate(
        windows_powershell="docker images",
        windows_cmd="docker images",
        unix="docker images",
        description="List docker images",
    ),
}


def get_command_for_intent(
    intent: str,
    entities: ExtractedEntities,
    context: SystemContext
) -> tuple[str, str, bool]:
    """
    Get the appropriate command for an intent and system context.
    
    Args:
        intent: The classified intent.
        entities: Extracted entities from the query.
        context: System context (OS, shell type).
        
    Returns:
        Tuple of (command, description, is_dangerous)
    """
    template = COMMAND_TEMPLATES.get(intent)
    
    if template is None:
        return (
            "# Unknown intent - could not generate command",
            "Unknown operation",
            False
        )
    
    # Get OS-specific template
    if context.os_type == OSType.WINDOWS:
        if context.shell_type == ShellType.POWERSHELL:
            cmd_template = template.windows_powershell
        else:
            cmd_template = template.windows_cmd
    else:
        cmd_template = template.unix
    
    # Build substitution dictionary
    substitutions = _build_substitutions(entities)
    
    # Apply substitutions
    command = cmd_template
    for key, value in substitutions.items():
        placeholder = "{" + key + "}"
        if placeholder in command:
            command = command.replace(placeholder, value)
    
    # Handle generic {target} placeholder
    target = _get_target(entities)
    command = command.replace("{target}", target)
    
    # Clean up any remaining placeholders with defaults
    command = _apply_defaults(command, intent)
    
    return (command, template.description, template.is_dangerous)


def _build_substitutions(entities: ExtractedEntities) -> dict:
    """Build substitution dictionary from entities."""
    subs = {}
    
    if entities.filename:
        subs['filename'] = entities.filename
    
    if entities.file_pattern:
        subs['pattern'] = entities.file_pattern
    
    if entities.directory:
        subs['directory'] = entities.directory
    
    if entities.destination:
        subs['destination'] = entities.destination
    
    if entities.source:
        subs['source'] = entities.source
    
    if entities.path:
        subs['path'] = entities.path
    
    if entities.search_text:
        subs['text'] = entities.search_text
    
    if entities.new_name:
        subs['new_name'] = entities.new_name
    
    if entities.url:
        subs['url'] = entities.url
    
    if entities.hostname:
        subs['hostname'] = entities.hostname
    
    if entities.process_name:
        subs['process'] = entities.process_name
    
    return subs


def _get_target(entities: ExtractedEntities) -> str:
    """Get the most appropriate target from entities."""
    if entities.filename:
        return entities.filename
    if entities.file_pattern:
        return entities.file_pattern
    if entities.path:
        return entities.path
    if entities.directory:
        return entities.directory
    return "."  # Current directory as fallback


def _apply_defaults(command: str, intent: str) -> str:
    """Apply sensible defaults for missing placeholders."""
    defaults = {
        '{filename}': 'file.txt',
        '{pattern}': '*',
        '{directory}': 'NewFolder',
        '{destination}': '.',
        '{source}': '.',
        '{path}': '.',
        '{text}': 'search_term',
        '{new_name}': 'new_name',
        '{url}': 'https://example.com/file',
        '{hostname}': 'localhost',
        '{process}': 'process_name',
        '{command}': 'command_name',
    }
    
    for placeholder, default in defaults.items():
        if placeholder in command:
            command = command.replace(placeholder, default)
    
    return command


def get_all_intents() -> list:
    """Get list of all supported intents."""
    return list(COMMAND_TEMPLATES.keys())


def get_template_info(intent: str) -> Optional[CommandTemplate]:
    """Get template info for an intent."""
    return COMMAND_TEMPLATES.get(intent)

