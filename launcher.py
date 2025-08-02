#!/usr/bin/env python3
"""
AGI Chat System Direct Launcher
Directly launches the AGI chat GUI interface
"""

import sys
import os
from pathlib import Path
import subprocess


def launch_gui():
    """Launch the GUI chat interface directly"""
    try:
        # Get the path to the AGI_Project directory
        launcher_dir = Path(__file__).parent
        project_dir = launcher_dir / "AGI_Project"
        
        # Change to project directory
        os.chdir(project_dir)
        
        # Launch the main.py with GUI option
        cmd = [sys.executable, "main.py", "--ui", "gui"]
        
        # Run the command
        result = subprocess.run(cmd, capture_output=False)
        
        if result.returncode != 0:
            raise Exception(f"Process exited with code {result.returncode}")
            
    except Exception as e:
        import tkinter as tk
        from tkinter import messagebox
        
        # Show error in GUI
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Launch Error",
            f"Failed to launch AGI Chat:\n\n{str(e)}\n\nPlease check your configuration."
        )
        root.destroy()
        
        # Also print to console
        print(f"Error launching AGI Chat: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

        

if __name__ == "__main__":
    launch_gui()