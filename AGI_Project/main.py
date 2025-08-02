#!/usr/bin/env python3
"""
AGI Chat System - Main Entry Point
A multi-agent chat system featuring you, Claude, and a Qwen-based clone of you
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Chat.chat_manager import ChatManager
from UI.chat_cli import ChatCLI
from UI.chat_gui import ChatGUI
from UI.web_chat import WebChat


def load_config():
    """Load configuration from config.json"""
    config_path = Path(__file__).parent / "config.json"
    with open(config_path, 'r') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="AGI Chat System")
    parser.add_argument(
        "--ui", 
        choices=["cli", "gui", "web"], 
        default="cli",
        help="Choose the user interface (default: cli)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Initialize chat manager
    chat_manager = ChatManager(config, debug=args.debug)
    
    # Start the appropriate UI
    if args.ui == "cli":
        ui = ChatCLI(chat_manager)
    elif args.ui == "gui":
        ui = ChatGUI(chat_manager)
    elif args.ui == "web":
        ui = WebChat(chat_manager)
    
    try:
        ui.run()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        chat_manager.save_session()
    except Exception as e:
        print(f"\nError: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()