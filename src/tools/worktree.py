#!/usr/bin/env python3
"""
🚀 Git Worktree Manager - Fire Button

Clean launcher for managing Git worktrees with multiple Claude Code sessions.
Run this to get the full interactive interface.
"""

import sys
from pathlib import Path

def main():
    """Launch the worktree manager"""
    
    # Get the script directory 
    script_dir = Path(__file__).parent
    
    # Check if worktree_cli.py exists (should be in same directory now)
    cli_path = script_dir / "worktree_cli.py"
    if not cli_path.exists():
        print("Error: Worktree CLI not found")
        print(f"   Expected: {cli_path}")
        return 1
    
    # Add tools directory to Python path
    sys.path.insert(0, str(script_dir))
    
    try:
        # Import and run the CLI
        from worktree_cli import main as cli_main
        return cli_main()
        
    except ImportError as e:
        print(f"Import Error: {e}")
        print("   Make sure you're in the AGI project directory")
        return 1
    except KeyboardInterrupt:
        print("\nGoodbye!")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == '__main__':
    print("Git Worktree Manager")
    print("=" * 30)
    sys.exit(main())