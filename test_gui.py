#!/usr/bin/env python3
"""
Test script to verify GUI functionality
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent / "AGI_Project"
sys.path.insert(0, str(project_root))

try:
    from Chat.chat_manager import ChatManager
    from UI.chat_gui import ChatGUI
    import json
    
    print("Imports successful!")
    
    # Load config
    config_path = project_root / "config.json"
    with open(config_path, 'r') as f:
        config = json.load(f)
    print("Config loaded!")
    
    # Create chat manager
    chat_manager = ChatManager(config, debug=True)
    print("Chat manager created!")
    
    # Create GUI
    gui = ChatGUI(chat_manager)
    print("GUI created! Starting...")
    
    # Run GUI
    gui.run()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()