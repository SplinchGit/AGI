#!/usr/bin/env python3
"""
AGI System - Main Entry Point
Provides multiple interface options for the AGI system
"""

import sys
import argparse
from pathlib import Path

# Add the src directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Main entry point with interface selection"""
    parser = argparse.ArgumentParser(
        description='AGI System - Advanced AI Agent Framework',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available Interfaces:
  cli     - Command Line Interface (enhanced chat)
  gui     - Graphical User Interface (Kivy-based)
  api     - REST API Service (CasCasA)
  
Examples:
  python src/main.py cli                    # Start CLI interface
  python src/main.py gui                    # Start GUI interface  
  python src/main.py api --port 8080        # Start API service on port 8080
        """
    )
    
    parser.add_argument(
        'interface',
        choices=['cli', 'gui', 'api'],
        help='Choose the interface to launch'
    )
    
    parser.add_argument(
        '--port', 
        type=int, 
        default=5000,
        help='Port for API service (default: 5000)'
    )
    
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host for API service (default: 0.0.0.0)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    
    args = parser.parse_args()
    
    print(f"AGI System - Starting {args.interface.upper()} interface...")
    
    try:
        if args.interface == 'cli':
            from interfaces.cli import main as cli_main
            cli_main()
            
        elif args.interface == 'gui':
            from interfaces.gui import ChatApp
            app = ChatApp()
            app.run()
            
        elif args.interface == 'api':
            from interfaces.api import main as api_main
            # Pass arguments to API main function
            sys.argv = ['api_main', '--host', args.host, '--port', str(args.port)]
            if args.debug:
                sys.argv.append('--debug')
            api_main()
            
    except ImportError as e:
        print(f"Error importing {args.interface} interface: {e}")
        print("Make sure all dependencies are installed.")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print(f"\n{args.interface.upper()} interface stopped by user")
        sys.exit(0)
        
    except Exception as e:
        print(f"Error starting {args.interface} interface: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()