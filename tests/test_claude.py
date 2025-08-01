#!/usr/bin/env python3
"""
Quick test script to verify Claude CLI integration works
"""
import subprocess
import os
from pathlib import Path

WORKSPACE_PATH = r"C:\Users\jf358\Documents\AGI"

def find_claude_command():
    """Find Claude CLI command"""
    npm_path = os.path.expanduser(r"~\AppData\Roaming\npm\claude.cmd")
    if os.path.exists(npm_path):
        return npm_path
    return "claude"  # Hope it's in PATH

def test_claude_cli():
    """Test Claude CLI with a simple prompt"""
    claude_cmd = find_claude_command()
    prompt = "Say 'Hello from the test script!' and nothing else."
    
    print(f"Testing Claude CLI: {claude_cmd}")
    print(f"Prompt: {prompt}")
    print("-" * 50)
    
    try:
        # Test the improved method
        cmd = [claude_cmd, "-p", prompt]
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(Path(WORKSPACE_PATH))
        )
        
        print(f"Return code: {process.returncode}")
        print(f"STDOUT: {process.stdout}")
        print(f"STDERR: {process.stderr}")
        
        if process.returncode == 0 and process.stdout:
            print("SUCCESS: Claude CLI is working!")
            return True
        else:
            print("FAILED: Claude CLI didn't respond properly")
            
            # Try the echo method as fallback
            print("Trying echo method...")
            cmd_string = f'echo "Hello from test!" | "{claude_cmd}"'
            process2 = subprocess.run(
                cmd_string,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(Path(WORKSPACE_PATH))
            )
            
            print(f"Echo method - Return code: {process2.returncode}")
            print(f"Echo method - STDOUT: {process2.stdout}")
            
            if process2.stdout and len(process2.stdout.strip()) > 5:
                print("SUCCESS: Echo method works!")
                return True
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    test_claude_cli()