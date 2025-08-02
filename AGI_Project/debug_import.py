import sys
import os

print("Python version:", sys.version)
print("Default encoding:", sys.getdefaultencoding())

try:
    print("Importing json...")
    import json
    print("Success!")
except Exception as e:
    print(f"Failed: {e}")

try:
    print("Importing os...")
    import os
    print("Success!")
except Exception as e:
    print(f"Failed: {e}")

try:
    print("Importing datetime...")
    from datetime import datetime
    print("Success!")
except Exception as e:
    print(f"Failed: {e}")

try:
    print("Importing typing...")
    from typing import Dict, List, Optional
    print("Success!")
except Exception as e:
    print(f"Failed: {e}")

try:
    print("Importing threading...")
    import threading
    print("Success!")
except Exception as e:
    print(f"Failed: {e}")

try:
    print("Importing queue...")
    import queue
    print("Success!")
except Exception as e:
    print(f"Failed: {e}")

print("\nNow testing local imports...")

try:
    print("Importing ClaudeAI...")
    from AIs.Claude.claude_ai import ClaudeAI
    print("Success!")
except Exception as e:
    print(f"Failed: {e}")
    import traceback
    traceback.print_exc()

try:
    print("Importing JamesCloneAI...")
    from AIs.JamesClone.james_ai import JamesCloneAI
    print("Success!")
except Exception as e:
    print(f"Failed: {e}")
    import traceback
    traceback.print_exc()

try:
    print("Importing MemorySystem...")
    from Chat.memory_system import MemorySystem
    print("Success!")
except Exception as e:
    print(f"Failed: {e}")
    import traceback
    traceback.print_exc()

try:
    print("Importing MessageHandler...")
    from Chat.message_handler import MessageHandler
    print("Success!")
except Exception as e:
    print(f"Failed: {e}")
    import traceback
    traceback.print_exc()