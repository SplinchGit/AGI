#!/usr/bin/env python3
"""
Git Worktree Manager with Rich CLI Interface

A comprehensive tool for managing Git worktrees with multiple Claude Code sessions.
Features interactive UI, status monitoring, and session management.
"""

import subprocess
import argparse
import json
import os
import sys
import time
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import re

# Color constants for rich terminal output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Standard colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    
    # Background colors
    BG_RED = '\033[101m'
    BG_GREEN = '\033[102m'
    BG_YELLOW = '\033[103m'

@dataclass
class WorktreeInfo:
    """Information about a Git worktree"""
    path: Path
    branch: str
    commit: str
    is_bare: bool = False
    is_detached: bool = False
    is_main: bool = False
    has_changes: bool = False
    claude_sessions: List[Dict] = None
    last_activity: Optional[datetime] = None
    
    def __post_init__(self):
        if self.claude_sessions is None:
            self.claude_sessions = []

class WorktreeUI:
    """Handles rich terminal UI display"""
    
    @staticmethod
    def print_header(title: str):
        """Print a styled header"""
        width = max(60, len(title) + 20)
        print(f"\n{Colors.CYAN}{'=' * width}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.WHITE}{title.center(width)}{Colors.RESET}")
        print(f"{Colors.CYAN}{'=' * width}{Colors.RESET}\n")
    
    @staticmethod
    def print_success(message: str):
        """Print success message"""
        print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")
    
    @staticmethod
    def print_error(message: str):
        """Print error message"""
        print(f"{Colors.RED}✗ {message}{Colors.RESET}")
    
    @staticmethod
    def print_warning(message: str):
        """Print warning message"""
        print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")
    
    @staticmethod
    def print_info(message: str):
        """Print info message"""
        print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")
    
    @staticmethod
    def print_table(headers: List[str], rows: List[List[str]], widths: List[int] = None):
        """Print a formatted table"""
        if not rows:
            WorktreeUI.print_info("No data to display")
            return
        
        # Calculate column widths if not provided
        if widths is None:
            widths = []
            for i, header in enumerate(headers):
                max_width = len(header)
                for row in rows:
                    if i < len(row):
                        max_width = max(max_width, len(str(row[i])))
                widths.append(max_width + 2)
        
        # Print header
        header_line = "│".join(f" {header:<{width-1}}" for header, width in zip(headers, widths))
        separator = "─" * (sum(widths) + len(headers) - 1)
        
        print(f"{Colors.BOLD}{header_line}{Colors.RESET}")
        print(f"{Colors.DIM}{separator}{Colors.RESET}")
        
        # Print rows
        for row in rows:
            padded_row = row + [''] * (len(headers) - len(row))  # Pad short rows
            row_line = "│".join(f" {str(cell):<{width-1}}" for cell, width in zip(padded_row, widths))
            print(row_line)
    
    @staticmethod
    def confirm(message: str, default: bool = False) -> bool:
        """Ask for user confirmation"""
        suffix = "[Y/n]" if default else "[y/N]"
        response = input(f"{Colors.YELLOW}? {message} {suffix}: {Colors.RESET}").strip().lower()
        
        if not response:
            return default
        return response in ['y', 'yes', 'true', '1']
    
    @staticmethod
    def select_option(prompt: str, options: List[str]) -> int:
        """Select from a list of options"""
        print(f"\n{Colors.BOLD}{prompt}{Colors.RESET}")
        for i, option in enumerate(options, 1):
            print(f"  {Colors.CYAN}{i}.{Colors.RESET} {option}")
        
        while True:
            try:
                choice = input(f"\n{Colors.YELLOW}Enter choice (1-{len(options)}): {Colors.RESET}")
                index = int(choice) - 1
                if 0 <= index < len(options):
                    return index
                else:
                    WorktreeUI.print_error(f"Please enter a number between 1 and {len(options)}")
            except ValueError:
                WorktreeUI.print_error("Please enter a valid number")
            except KeyboardInterrupt:
                print()  # New line after ^C
                return -1

class ClaudeSessionManager:
    """Manages Claude Code sessions in worktrees (simplified without psutil)"""
    
    @staticmethod
    def find_claude_sessions() -> List[Dict]:
        """Find running Claude Code sessions using basic process detection"""
        sessions = []
        
        try:
            # Use tasklist on Windows to find Claude processes
            if os.name == 'nt':
                result = subprocess.run(['tasklist', '/fo', 'csv'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines[1:]:  # Skip header
                        if 'claude' in line.lower():
                            parts = line.split(',')
                            if len(parts) >= 2:
                                name = parts[0].strip('"')
                                pid = parts[1].strip('"')
                                sessions.append({
                                    'pid': pid,
                                    'name': name,
                                    'cwd': 'unknown',
                                    'started': datetime.now(),
                                    'cmdline': name
                                })
            else:
                # Use ps on Unix-like systems
                result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines[1:]:  # Skip header
                        if 'claude' in line.lower():
                            parts = line.split()
                            if len(parts) >= 2:
                                sessions.append({
                                    'pid': parts[1],
                                    'name': 'claude',
                                    'cwd': 'unknown',
                                    'started': datetime.now(),
                                    'cmdline': ' '.join(parts[10:]) if len(parts) > 10 else 'claude'
                                })
        except Exception as e:
            # Silently fail - session detection is optional
            pass
        
        return sessions
    
    @staticmethod
    def get_sessions_for_path(path: Path) -> List[Dict]:
        """Get Claude sessions (simplified - just return found sessions)"""
        # Without psutil, we can't easily determine working directory
        # Just return all found Claude sessions
        return ClaudeSessionManager.find_claude_sessions()

class EnhancedWorktreeManager:
    """Enhanced Git worktree manager with rich UI and session management"""
    
    def __init__(self, base_path: Optional[str] = None):
        """Initialize the enhanced worktree manager"""
        self.repo_root = self._find_git_root()
        if not self.repo_root:
            raise RuntimeError("Not in a Git repository. Run 'git init' first.")
        
        self.base_path = Path(base_path) if base_path else self.repo_root.parent
        self.project_name = self.repo_root.name
        self.ui = WorktreeUI()
        self.session_manager = ClaudeSessionManager()
        
        # Configuration
        self.config_file = self.repo_root / '.worktree-config.json'
        self.config = self._load_config()
    
    def _find_git_root(self) -> Optional[Path]:
        """Find the root of the current Git repository"""
        current = Path.cwd()
        while current.parent != current:
            if (current / '.git').exists():
                return current
            current = current.parent
        return None
    
    def _load_config(self) -> Dict:
        """Load worktree configuration"""
        default_config = {
            'auto_setup_env': True,
            'default_base_branch': 'main',
            'confirm_destructive_actions': True,
            'show_session_info': True,
            'cleanup_on_merge': False
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    default_config.update(config_data)
            except Exception as e:
                self.ui.print_warning(f"Could not load config: {e}")
        
        return default_config
    
    def _save_config(self):
        """Save worktree configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.ui.print_warning(f"Could not save config: {e}")
    
    def _run_git_command(self, cmd: List[str], cwd: Optional[Path] = None) -> Tuple[bool, str, str]:
        """Run a Git command and return success status and output"""
        try:
            result = subprocess.run(
                ['git'] + cmd,
                cwd=cwd or self.repo_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def _check_for_changes(self, path: Path) -> bool:
        """Check if worktree has uncommitted changes"""
        success, stdout, _ = self._run_git_command(['status', '--porcelain'], cwd=path)
        return success and bool(stdout.strip())
    
    def _get_branch_info(self, path: Path) -> Tuple[str, str]:
        """Get current branch and commit info"""
        # Get branch
        success, branch, _ = self._run_git_command(['branch', '--show-current'], cwd=path)
        if not success or not branch:
            branch = "detached"
        
        # Get commit
        success, commit, _ = self._run_git_command(['rev-parse', '--short', 'HEAD'], cwd=path)
        if not success:
            commit = "unknown"
        
        return branch, commit
    
    def get_worktree_info(self, path: Path) -> WorktreeInfo:
        """Get detailed information about a worktree"""
        branch, commit = self._get_branch_info(path)
        
        info = WorktreeInfo(
            path=path,
            branch=branch,
            commit=commit,
            is_main=(path == self.repo_root),
            has_changes=self._check_for_changes(path)
        )
        
        # Get Claude sessions
        info.claude_sessions = self.session_manager.get_sessions_for_path(path)
        
        # Get last activity (last modified file time)
        try:
            latest_time = None
            for item in path.rglob('*'):
                if item.is_file() and not any(part.startswith('.') for part in item.parts):
                    mtime = datetime.fromtimestamp(item.stat().st_mtime)
                    if latest_time is None or mtime > latest_time:
                        latest_time = mtime
            info.last_activity = latest_time
        except Exception:
            pass
        
        return info
    
    def list_worktrees(self) -> List[WorktreeInfo]:
        """Get detailed information about all worktrees"""
        success, stdout, stderr = self._run_git_command(['worktree', 'list', '--porcelain'])
        
        if not success:
            self.ui.print_error(f"Failed to list worktrees: {stderr}")
            return []
        
        worktrees = []
        current_path = None
        
        for line in stdout.split('\n'):
            if line.startswith('worktree '):
                current_path = Path(line[9:])  # Remove 'worktree ' prefix
        
        # If we have worktrees from git, get their info
        if current_path:
            # Get all worktree paths
            success, stdout, _ = self._run_git_command(['worktree', 'list'])
            if success:
                for line in stdout.split('\n'):
                    if line.strip():
                        parts = line.split()
                        if parts:
                            path = Path(parts[0])
                            if path.exists():
                                worktrees.append(self.get_worktree_info(path))
        
        return sorted(worktrees, key=lambda x: (not x.is_main, str(x.path)))
    
    def create_worktree_interactive(self):
        """Interactive worktree creation with all options"""
        self.ui.print_header("Create New Worktree")
        
        # Get branch name
        branch_name = input(f"{Colors.YELLOW}Branch name: {Colors.RESET}").strip()
        if not branch_name:
            self.ui.print_error("Branch name is required")
            return False
        
        # Check if branch exists
        success, stdout, _ = self._run_git_command(['branch', '--list', branch_name])
        branch_exists = bool(stdout.strip())
        
        # Determine creation mode
        if branch_exists:
            print(f"\n{Colors.INFO}Branch '{branch_name}' already exists{Colors.RESET}")
            create_new = False
        else:
            create_new = self.ui.confirm("Create new branch?", default=True)
        
        base_branch = self.config['default_base_branch']
        if create_new:
            base_input = input(f"{Colors.YELLOW}Base branch [{base_branch}]: {Colors.RESET}").strip()
            if base_input:
                base_branch = base_input
        
        # Choose worktree location
        default_path = self.base_path / f"{self.project_name}-{branch_name}"
        path_input = input(f"{Colors.YELLOW}Worktree path [{default_path}]: {Colors.RESET}").strip()
        worktree_path = Path(path_input) if path_input else default_path
        
        # Environment setup
        setup_env = self.ui.confirm("Setup development environment?", default=self.config['auto_setup_env'])
        
        # Create the worktree
        return self.create_worktree(branch_name, worktree_path, create_new, base_branch, setup_env)
    
    def create_worktree(self, branch_name: str, worktree_path: Path = None, 
                       new_branch: bool = True, base_branch: str = None, 
                       setup_env: bool = True) -> bool:
        """Create a new worktree with specified options"""
        
        if worktree_path is None:
            worktree_path = self.base_path / f"{self.project_name}-{branch_name}"
        
        if base_branch is None:
            base_branch = self.config['default_base_branch']
        
        # Check if worktree already exists
        if worktree_path.exists():
            self.ui.print_error(f"Directory {worktree_path} already exists")
            return False
        
        print(f"\n{Colors.BOLD}Creating worktree...{Colors.RESET}")
        print(f"  Branch: {Colors.CYAN}{branch_name}{Colors.RESET}")
        print(f"  Path: {Colors.CYAN}{worktree_path}{Colors.RESET}")
        if new_branch:
            print(f"  Base: {Colors.CYAN}{base_branch}{Colors.RESET}")
        print()
        
        # Prepare Git command
        if new_branch:
            cmd = ['worktree', 'add', str(worktree_path), '-b', branch_name, base_branch]
        else:
            cmd = ['worktree', 'add', str(worktree_path), branch_name]
        
        # Create the worktree
        success, stdout, stderr = self._run_git_command(cmd)
        
        if success:
            self.ui.print_success(f"Created worktree: {worktree_path}")
            
            # Setup development environment
            if setup_env:
                if self._setup_environment(worktree_path):
                    self.ui.print_success("Development environment setup complete")
                else:
                    self.ui.print_warning("Could not setup development environment")
            
            # Show next steps
            print(f"\n{Colors.BOLD}Next steps:{Colors.RESET}")
            print(f"  {Colors.GREEN}cd {worktree_path}{Colors.RESET}")
            print(f"  {Colors.GREEN}claude{Colors.RESET}")
            
            return True
        else:
            self.ui.print_error(f"Failed to create worktree: {stderr}")
            return False
    
    def _setup_environment(self, worktree_path: Path) -> bool:
        """Setup development environment in the new worktree"""
        try:
            original_cwd = Path.cwd()
            os.chdir(worktree_path)
            
            setup_commands = []
            
            # Python project
            if (worktree_path / 'pyproject.toml').exists():
                print(f"  {Colors.BLUE}📦 Python project detected{Colors.RESET}")
                if (worktree_path / 'requirements.txt').exists():
                    setup_commands.append(('pip install -r requirements.txt', 'Installing Python dependencies'))
                
            # Node.js project  
            elif (worktree_path / 'package.json').exists():
                print(f"  {Colors.BLUE}📦 Node.js project detected{Colors.RESET}")
                setup_commands.append(('npm install', 'Installing Node.js dependencies'))
                
            # Rust project
            elif (worktree_path / 'Cargo.toml').exists():
                print(f"  {Colors.BLUE}📦 Rust project detected{Colors.RESET}")
                setup_commands.append(('cargo check', 'Checking Rust dependencies'))
                
            # Go project
            elif (worktree_path / 'go.mod').exists():
                print(f"  {Colors.BLUE}📦 Go project detected{Colors.RESET}")
                setup_commands.append(('go mod download', 'Downloading Go dependencies'))
            
            # Run setup commands
            for cmd, description in setup_commands:
                print(f"    {description}...")
                result = subprocess.run(cmd, shell=True, cwd=worktree_path, 
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    self.ui.print_warning(f"Setup command failed: {cmd}")
                    return False
            
            return True
            
        except Exception as e:
            self.ui.print_warning(f"Environment setup error: {e}")
            return False
        finally:
            os.chdir(original_cwd)
    
    def display_worktrees(self, show_sessions: bool = True):
        """Display detailed worktree information"""
        worktrees = self.list_worktrees()
        
        if not worktrees:
            self.ui.print_info("No worktrees found")
            return
        
        self.ui.print_header(f"Git Worktrees for {self.project_name}")
        
        # Prepare table data
        headers = ['Path', 'Branch', 'Status', 'Last Activity']
        if show_sessions:
            headers.append('Claude Sessions')
        
        rows = []
        for wt in worktrees:
            # Format path (shorten if too long)
            path_str = str(wt.path)
            if len(path_str) > 35:
                path_str = "..." + path_str[-32:]
            
            # Status indicators
            status_parts = []
            if wt.is_main:
                status_parts.append(f"{Colors.BOLD}MAIN{Colors.RESET}")
            if wt.has_changes:
                status_parts.append(f"{Colors.YELLOW}MODIFIED{Colors.RESET}")
            if wt.is_detached:
                status_parts.append(f"{Colors.RED}DETACHED{Colors.RESET}")
            if not status_parts:
                status_parts.append(f"{Colors.GREEN}CLEAN{Colors.RESET}")
            
            status = " ".join(status_parts)
            
            # Last activity
            if wt.last_activity:
                time_diff = datetime.now() - wt.last_activity
                if time_diff.days > 0:
                    activity = f"{time_diff.days}d ago"
                elif time_diff.seconds > 3600:
                    activity = f"{time_diff.seconds // 3600}h ago"
                elif time_diff.seconds > 60:
                    activity = f"{time_diff.seconds // 60}m ago"
                else:
                    activity = "now"
            else:
                activity = "unknown"
            
            row = [path_str, wt.branch, status, activity]
            
            # Claude sessions
            if show_sessions:
                if wt.claude_sessions:
                    session_info = f"{Colors.GREEN}{len(wt.claude_sessions)} active{Colors.RESET}"
                else:
                    session_info = f"{Colors.DIM}none{Colors.RESET}"
                row.append(session_info)
            
            rows.append(row)
        
        self.ui.print_table(headers, rows)
        
        # Show session details if requested
        if show_sessions and self.config['show_session_info']:
            active_sessions = [wt for wt in worktrees if wt.claude_sessions]
            if active_sessions:
                print(f"\n{Colors.BOLD}Active Claude Sessions:{Colors.RESET}")
                for wt in active_sessions:
                    print(f"\n  {Colors.CYAN}{wt.path.name}{Colors.RESET}:")
                    for session in wt.claude_sessions:
                        duration = datetime.now() - session['started']
                        duration_str = f"{duration.seconds // 60}m" if duration.seconds > 60 else f"{duration.seconds}s"
                        print(f"    • PID {session['pid']} (running {duration_str})")
    
    def remove_worktree_interactive(self):
        """Interactive worktree removal"""
        worktrees = [wt for wt in self.list_worktrees() if not wt.is_main]
        
        if not worktrees:
            self.ui.print_info("No worktrees to remove")
            return False
        
        self.ui.print_header("Remove Worktree")
        
        # Select worktree to remove
        options = [f"{wt.path.name} ({wt.branch})" for wt in worktrees]
        selected = self.ui.select_option("Select worktree to remove:", options)
        
        if selected == -1:  # Cancelled
            return False
        
        worktree = worktrees[selected]
        
        # Show warnings
        print(f"\n{Colors.BOLD}Worktree to remove:{Colors.RESET}")
        print(f"  Path: {Colors.CYAN}{worktree.path}{Colors.RESET}")
        print(f"  Branch: {Colors.CYAN}{worktree.branch}{Colors.RESET}")
        
        if worktree.has_changes:
            self.ui.print_warning("Worktree has uncommitted changes!")
        
        if worktree.claude_sessions:
            self.ui.print_warning(f"Worktree has {len(worktree.claude_sessions)} active Claude sessions!")
        
        # Confirm removal
        if self.config['confirm_destructive_actions']:
            if not self.ui.confirm("Are you sure you want to remove this worktree?"):
                return False
        
        force = False
        if worktree.has_changes:
            force = self.ui.confirm("Force removal despite uncommitted changes?")
            if not force:
                self.ui.print_info("Removal cancelled")
                return False
        
        return self.remove_worktree(worktree.path, force)
    
    def remove_worktree(self, worktree_path: Path, force: bool = False) -> bool:
        """Remove a worktree"""
        # Warn about Claude sessions but don't try to kill them
        info = self.get_worktree_info(worktree_path)
        if info.claude_sessions:
            self.ui.print_warning("Note: There may be Claude sessions running in this worktree")
            self.ui.print_info("Please close Claude sessions manually before removal")
        
        # Remove the worktree
        cmd = ['worktree', 'remove', str(worktree_path)]
        if force:
            cmd.append('--force')
        
        success, stdout, stderr = self._run_git_command(cmd)
        
        if success:
            self.ui.print_success(f"Removed worktree: {worktree_path}")
            return True
        else:
            self.ui.print_error(f"Failed to remove worktree: {stderr}")
            return False
    
    def configure_interactive(self):
        """Interactive configuration"""
        self.ui.print_header("Worktree Configuration")
        
        print(f"Current configuration:")
        for key, value in self.config.items():
            print(f"  {key}: {Colors.CYAN}{value}{Colors.RESET}")
        
        print(f"\n{Colors.BOLD}Available settings:{Colors.RESET}")
        settings = [
            ("auto_setup_env", "Automatically setup development environment"),
            ("default_base_branch", "Default base branch for new branches"),
            ("confirm_destructive_actions", "Confirm before removing worktrees"),
            ("show_session_info", "Show Claude session information"),
            ("cleanup_on_merge", "Auto-cleanup merged branches")
        ]
        
        for key, description in settings:
            print(f"  {Colors.YELLOW}{key}{Colors.RESET}: {description}")
        
        print()
        setting = input(f"{Colors.YELLOW}Setting to change (or Enter to skip): {Colors.RESET}").strip()
        
        if setting and setting in self.config:
            current = self.config[setting]
            new_value = input(f"{Colors.YELLOW}New value for {setting} [{current}]: {Colors.RESET}").strip()
            
            if new_value:
                # Type conversion
                if isinstance(current, bool):
                    new_value = new_value.lower() in ['true', 'yes', '1', 'on']
                elif isinstance(current, int):
                    try:
                        new_value = int(new_value)
                    except ValueError:
                        self.ui.print_error("Invalid integer value")
                        return
                
                self.config[setting] = new_value
                self._save_config()
                self.ui.print_success(f"Updated {setting} to {new_value}")

def main():
    """Main CLI entry point with rich interface"""
    parser = argparse.ArgumentParser(
        description="Enhanced Git Worktree Manager for Claude Code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{Colors.BOLD}Examples:{Colors.RESET}
  # Interactive mode
  %(prog)s

  # Create worktree with new branch
  %(prog)s create feature-auth --new

  # List all worktrees with sessions
  %(prog)s list --sessions

  # Remove worktree interactively
  %(prog)s remove

  # Configure settings
  %(prog)s config
        """
    )
    
    parser.add_argument('--no-color', action='store_true', help='Disable colored output')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new worktree')
    create_parser.add_argument('branch', nargs='?', help='Branch name for the worktree')
    create_parser.add_argument('--new', action='store_true', help='Create a new branch')
    create_parser.add_argument('--base', help='Base branch for new branch')
    create_parser.add_argument('--path', help='Custom path for worktree')
    create_parser.add_argument('--no-setup', action='store_true', help='Skip environment setup')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all worktrees')
    list_parser.add_argument('--sessions', action='store_true', help='Show Claude session info')
    list_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a worktree')
    remove_parser.add_argument('branch', nargs='?', help='Branch name of worktree to remove')
    remove_parser.add_argument('--force', action='store_true', help='Force removal')
    
    # Switch command
    switch_parser = subparsers.add_parser('switch', help='Switch to a worktree')
    switch_parser.add_argument('branch', nargs='?', help='Branch name to switch to')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Configure worktree settings')
    
    # Sessions command
    sessions_parser = subparsers.add_parser('sessions', help='Manage Claude sessions')
    sessions_parser.add_argument('--kill', help='Kill sessions in specific worktree')
    
    args = parser.parse_args()
    
    # Disable colors if requested
    if args.no_color:
        for attr in dir(Colors):
            if not attr.startswith('_'):
                setattr(Colors, attr, '')
    
    try:
        manager = EnhancedWorktreeManager()
        
        if not args.command:
            # Interactive mode
            manager.ui.print_header("Git Worktree Manager")
            
            while True:
                print(f"\n{Colors.BOLD}Available actions:{Colors.RESET}")
                actions = [
                    "List worktrees",
                    "Create worktree", 
                    "Remove worktree",
                    "Configure settings",
                    "Manage Claude sessions",
                    "Exit"
                ]
                
                choice = manager.ui.select_option("What would you like to do?", actions)
                
                if choice == -1 or choice == 5:  # Exit
                    break
                elif choice == 0:  # List
                    manager.display_worktrees()
                elif choice == 1:  # Create
                    manager.create_worktree_interactive()
                elif choice == 2:  # Remove
                    manager.remove_worktree_interactive()
                elif choice == 3:  # Configure
                    manager.configure_interactive()
                elif choice == 4:  # Sessions
                    manager.display_worktrees(show_sessions=True)
        
        elif args.command == 'create':
            if args.branch:
                manager.create_worktree(
                    args.branch,
                    Path(args.path) if args.path else None,
                    args.new,
                    args.base,
                    not args.no_setup
                )
            else:
                manager.create_worktree_interactive()
        
        elif args.command == 'list':
            if args.json:
                worktrees = manager.list_worktrees()
                data = []
                for wt in worktrees:
                    data.append({
                        'path': str(wt.path),
                        'branch': wt.branch,
                        'commit': wt.commit,
                        'is_main': wt.is_main,
                        'has_changes': wt.has_changes,
                        'sessions': len(wt.claude_sessions),
                        'last_activity': wt.last_activity.isoformat() if wt.last_activity else None
                    })
                print(json.dumps(data, indent=2))
            else:
                manager.display_worktrees(show_sessions=args.sessions)
        
        elif args.command == 'remove':
            if args.branch:
                worktree_path = manager.base_path / f"{manager.project_name}-{args.branch}"
                manager.remove_worktree(worktree_path, args.force)
            else:
                manager.remove_worktree_interactive()
        
        elif args.command == 'config':
            manager.configure_interactive()
        
        elif args.command == 'sessions':
            manager.display_worktrees(show_sessions=True)
        
        return 0
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Operation cancelled{Colors.RESET}")
        return 1
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")
        return 1

if __name__ == '__main__':
    sys.exit(main())