#!/usr/bin/env python3
"""
AGI System GUI Launcher
A simple launcher for the AGI chat system with GUI interface
"""

import sys
import os
from pathlib import Path
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading

class AGILauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AGI System Launcher")
        self.root.geometry("600x500")
        self.root.minsize(500, 400)
        
        # Set icon and styling
        self.root.configure(bg='#2b2b2b')
        
        # Variables
        self.process = None
        self.is_running = False
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="AGI Chat System", 
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="System Status", padding="10")
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        ttk.Label(status_frame, text="Status:").grid(row=0, column=0, sticky=tk.W)
        self.status_label = ttk.Label(status_frame, text="Ready", foreground="green")
        self.status_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # Launch options frame
        options_frame = ttk.LabelFrame(main_frame, text="Launch Options", padding="10")
        options_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        options_frame.columnconfigure(0, weight=1)
        
        # Interface selection
        ttk.Label(options_frame, text="Select Interface:").grid(row=0, column=0, sticky=tk.W)
        
        self.interface_var = tk.StringVar(value="gui")
        interface_frame = ttk.Frame(options_frame)
        interface_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 10))
        
        ttk.Radiobutton(
            interface_frame, 
            text="GUI (Kivy)", 
            variable=self.interface_var, 
            value="gui"
        ).pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Radiobutton(
            interface_frame, 
            text="CLI", 
            variable=self.interface_var, 
            value="cli"
        ).pack(side=tk.LEFT)
        
        # Debug mode
        self.debug_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame,
            text="Enable Debug Mode",
            variable=self.debug_var
        ).grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        
        # Control buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, pady=(0, 10))
        
        self.launch_button = ttk.Button(
            button_frame,
            text="Launch AGI System",
            command=self.launch_system,
            style="Accent.TButton"
        )
        self.launch_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(
            button_frame,
            text="Stop System",
            command=self.stop_system,
            state="disabled"
        )
        self.stop_button.pack(side=tk.LEFT)
        
        # Log output frame
        log_frame = ttk.LabelFrame(main_frame, text="System Log", padding="10")
        log_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=10,
            wrap=tk.WORD,
            state="disabled",
            bg="#1e1e1e",
            fg="#ffffff",
            font=("Consolas", 9)
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Info panel
        info_frame = ttk.LabelFrame(main_frame, text="System Info", padding="10")
        info_frame.grid(row=5, column=0, sticky=(tk.W, tk.E))
        info_frame.columnconfigure(1, weight=1)
        
        # Project path
        ttk.Label(info_frame, text="Project:").grid(row=0, column=0, sticky=tk.W)
        project_path = str(Path(__file__).parent)
        ttk.Label(info_frame, text=project_path, foreground="blue").grid(
            row=0, column=1, sticky=tk.W, padx=(10, 0)
        )
        
        # Python version
        ttk.Label(info_frame, text="Python:").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(info_frame, text=f"{sys.version.split()[0]}", foreground="blue").grid(
            row=1, column=1, sticky=tk.W, padx=(10, 0)
        )
        
        self.log("AGI System Launcher initialized")
        
    def log(self, message):
        """Add message to log output"""
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.config(state="disabled")
        self.log_text.see(tk.END)
        
    def update_status(self, status, color="black"):
        """Update status label"""
        self.status_label.config(text=status, foreground=color)
        
    def launch_system(self):
        """Launch the AGI system"""
        if self.is_running:
            messagebox.showwarning("Already Running", "System is already running!")
            return
            
        try:
            cmd = self._build_launch_command()
            self._start_process(cmd)
            
        except Exception as e:
            self._handle_launch_error(e)
            
    def _build_launch_command(self):
        """Build launch command based on options"""
        interface = self.interface_var.get()
        debug = self.debug_var.get()
        
        if interface == "gui":
            cmd = [sys.executable, "src/interfaces/gui.py"]
            self.log("Starting GUI interface...")
        else:
            cmd = [sys.executable, "src/interfaces/cli.py"]
            self.log("Starting CLI interface...")
        
        if debug:
            cmd.append("--debug")
            self.log("Debug mode enabled")
            
        return cmd
        
    def _start_process(self, cmd):
        """Start the subprocess"""
        project_dir = Path(__file__).parent
        os.chdir(project_dir)
        
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        self.is_running = True
        self.update_status("Running", "green")
        self.launch_button.config(state="disabled")
        self.stop_button.config(state="normal")
        
        threading.Thread(target=self.monitor_output, daemon=True).start()
        
    def _handle_launch_error(self, error):
        """Handle launch errors"""
        self.log(f"Error launching system: {str(error)}")
        self.update_status("Error", "red")
        messagebox.showerror("Launch Error", f"Failed to launch system:\n{str(error)}")
    
    def monitor_output(self):
        """Monitor subprocess output"""
        try:
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.root.after(0, lambda msg=line.strip(): self.log(f"System: {msg}"))
                    
            # Process ended
            self.process.wait()
            self.root.after(0, self.on_process_end)
            
        except Exception as e:
            self.root.after(0, lambda: self.log(f"Output monitoring error: {str(e)}"))
    
    def on_process_end(self):
        """Handle process termination"""
        self.is_running = False
        self.update_status("Stopped", "red")
        self.launch_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.log("System stopped")
    
    def stop_system(self):
        """Stop the running system"""
        if not self.is_running or not self.process:
            return
            
        try:
            self._terminate_process()
        except Exception as e:
            self.log(f"Error stopping system: {str(e)}")
            
    def _terminate_process(self):
        """Terminate the process gracefully"""
        self.process.terminate()
        self.log("Stopping system...")
        
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.log("Force stopped system")
    
    def run(self):
        """Run the launcher"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except KeyboardInterrupt:
            self.stop_system()
    
    def on_closing(self):
        """Handle window closing"""
        if self.is_running:
            if messagebox.askokcancel("Quit", "System is running. Stop and quit?"):
                self.stop_system()
                self.root.destroy()
        else:
            self.root.destroy()

if __name__ == "__main__":
    launcher = AGILauncher()
    launcher.run()