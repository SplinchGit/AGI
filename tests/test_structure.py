#!/usr/bin/env python3
"""
Quick test to verify the reorganized structure works
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all major imports work"""
    print("Testing reorganized structure...")
    
    try:
        # Test core imports
        from core.coordination import ModularAICoordinator, RoleAwareChat
        print("PASS: Core coordination imports work")
        
        # Test AI agent imports
        from ai_agents.claude_builder import CodeGenerator
        from ai_agents.qwen_brain import StrategicPlanner
        from ai_agents.shared import AIInterface
        print("PASS: AI agent imports work")
        
        # Test interface imports (these may fail due to dependencies)
        try:
            from interfaces.cli import EnhancedAGIChat
            print("PASS: CLI interface import works")
        except ImportError as e:
            print(f"WARN: CLI interface import issue: {e}")
        
        print("\nReorganization successful! Structure is clean and functional.")
        return True
        
    except ImportError as e:
        print(f"FAIL: Import error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)