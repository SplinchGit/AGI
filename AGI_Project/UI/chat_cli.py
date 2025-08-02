"""
CLI Interface for AGI Chat System
"""

import os
import sys
import time
import threading
from typing import Optional, Dict
from datetime import datetime

# For better terminal handling on Windows
if sys.platform == "win32":
    import msvcrt
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
else:
    import termios
    import tty


class ChatCLI:
    def __init__(self, chat_manager):
        """Initialize CLI interface"""
        self.chat_manager = chat_manager
        self.running = False
        self.colors = {
            "James": "\033[92m",       # Green
            "Claude": "\033[94m",      # Blue  
            "James (Clone)": "\033[93m", # Yellow
            "system": "\033[90m",      # Gray
            "error": "\033[91m",       # Red
            "reset": "\033[0m"
        }
        self.show_timestamps = True
        self.notification_sound = False
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Print application header"""
        self.clear_screen()
        print("=" * 60)
        print("           AGI CHAT SYSTEM".center(60))
        print("=" * 60)
        print("Participants: You (James), Claude, and James Clone (Qwen)")
        print("Type /help for available commands")
        print("=" * 60)
        print()
    
    def print_message(self, message: Dict):
        """Print a formatted message"""
        sender = message.get("sender", "Unknown")
        content = message.get("content", "")
        timestamp = message.get("timestamp", "")
        
        # Format timestamp
        if self.show_timestamps and timestamp:
            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime("%H:%M:%S")
            print(f"{self.colors['system']}[{time_str}]{self.colors['reset']}", end=" ")
        
        # Print sender and message
        color = self.colors.get(sender, self.colors["reset"])
        print(f"{color}{sender}:{self.colors['reset']} {content}")
        
        # Print responses if any
        if message.get("responses"):
            for responder, response in message["responses"].items():
                self._print_response(responder, response["content"])
    
    def _print_response(self, responder: str, content: str):
        """Print an AI response"""
        color = self.colors.get(responder, self.colors["reset"])
        # Indent responses
        print(f"  {color} {responder}:{self.colors['reset']} {content}")
    
    def print_system_message(self, message: str, msg_type: str = "info"):
        """Print system message"""
        if msg_type == "error":
            color = self.colors["error"]
        else:
            color = self.colors["system"]
        
        print(f"\n{color}[System] {message}{self.colors['reset']}\n")
    
    def handle_command_result(self, result: Dict):
        """Handle command execution results"""
        cmd_type = result.get("type")
        
        if cmd_type == "help":
            self.print_system_message(result["content"])
        
        elif cmd_type == "clear":
            if result.get("confirm"):
                response = input("Are you sure you want to clear the chat? (yes/no): ")
                if response.lower() == "yes":
                    self.chat_manager.clear_session()
                    self.print_header()
                    self.print_system_message("Chat session cleared")
        
        elif cmd_type == "stats":
            stats = self.chat_manager.get_session_info()
            self.print_system_message(self._format_stats(stats))
        
        elif cmd_type == "export":
            try:
                filename = f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{result['format']}"
                content = self.chat_manager.export_conversation(result["format"])
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.print_system_message(f"Conversation exported to {filename}")
            except Exception as e:
                self.print_system_message(f"Export failed: {e}", "error")
        
        elif cmd_type == "memory_search":
            memories = self.chat_manager.memory_system.search_memory(result["query"])
            self._display_memories(memories)
        
        elif cmd_type == "who":
            info = self.chat_manager.get_session_info()
            self._display_participants(info["agents"])
        
        elif cmd_type == "error":
            self.print_system_message(result["message"], "error")
    
    def _format_stats(self, stats: Dict) -> str:
        """Format statistics for display"""
        lines = ["Chat Statistics:"]
        lines.append(f"  Session ID: {stats['session_id']}")
        lines.append(f"  Started: {stats['started_at']}")
        lines.append(f"  Messages: {stats['message_count']}")
        lines.append(f"  Participants: {', '.join(stats['participants'])}")
        
        # Memory stats
        mem_stats = self.chat_manager.memory_system.get_memory_stats()
        lines.append("\nMemory Statistics:")
        lines.append(f"  Conversations: {mem_stats['total_conversations']}")
        lines.append(f"  Experiences: {mem_stats['total_experiences']}")
        lines.append(f"  Knowledge entries: {mem_stats['total_knowledge']}")
        lines.append(f"  Database size: {mem_stats['database_size_mb']:.2f} MB")
        
        return "\n".join(lines)
    
    def _display_memories(self, memories: list):
        """Display memory search results"""
        if not memories:
            self.print_system_message("No memories found matching your query")
            return
        
        self.print_system_message(f"Found {len(memories)} memories:")
        for mem in memories[:5]:  # Show first 5
            mem_type = mem.get("type", "unknown")
            if mem_type == "conversation":
                print(f"  =� [{mem['timestamp']}] {mem['sender']}: {mem['content'][:80]}...")
            elif mem_type == "experience":
                print(f"  >� [{mem['timestamp']}] {mem['source']}: {mem['content'][:80]}... (importance: {mem['importance']})")
            elif mem_type == "knowledge":
                print(f"  =� [{mem['category']}] {mem['fact'][:80]}... (confidence: {mem['confidence']})")
    
    def _display_participants(self, agents: Dict):
        """Display participant information"""
        self.print_system_message("Chat Participants:")
        
        # Human participant
        print(f"  =d James (You) - Human participant")
        
        # AI agents
        for name, info in agents.items():
            if isinstance(info, dict) and info.get("status") != "not initialized":
                agent_type = info.get("type", "Unknown")
                conv_count = info.get("conversation_count", 0)
                print(f"  > {name} - {agent_type} (Messages: {conv_count})")
                
                # Extra info for James Clone
                if "James" in name and "Clone" in name:
                    exp_count = info.get("experience_count", 0)
                    know_count = info.get("knowledge_entries", 0)
                    print(f"      Memories: {exp_count} experiences, {know_count} knowledge entries")
    
    def get_user_input(self) -> Optional[str]:
        """Get input from user with nice prompt"""
        try:
            # Show typing indicator
            prompt = f"{self.colors['James']}You:{self.colors['reset']} "
            user_input = input(prompt)
            return user_input.strip()
        except (EOFError, KeyboardInterrupt):
            return None
    
    def run(self):
        """Main CLI loop"""
        self.running = True
        self.print_header()
        
        # Show recent history
        history = self.chat_manager.get_conversation_history(limit=10)
        if history:
            self.print_system_message(f"Showing last {len(history)} messages from previous session:")
            for msg in history:
                self.print_message(msg)
            print("\n" + "-" * 60 + "\n")
        
        self.print_system_message("Chat ready! Type your message or /help for commands.")
        
        try:
            while self.running:
                # Get user input
                user_input = self.get_user_input()
                
                if user_input is None:
                    break
                
                if not user_input:
                    continue
                
                # Process through message handler
                processed, command_result = self.chat_manager.message_handler.process_message(
                    user_input, "James"
                )
                
                if command_result:
                    # Handle command
                    self.handle_command_result(command_result)
                else:
                    # Regular message - validate first
                    is_valid, error = self.chat_manager.message_handler.validate_message(processed)
                    if not is_valid:
                        self.print_system_message(error, "error")
                        continue
                    
                    # Send message and get responses
                    print()  # Empty line before responses
                    
                    # Show thinking indicator
                    print(f"{self.colors['system']}Waiting for responses...{self.colors['reset']}", end="\r")
                    
                    message = self.chat_manager.send_message("James", processed)
                    
                    # Clear thinking indicator
                    print(" " * 50, end="\r")
                    
                    # Show the message and responses
                    self.print_message(message)
                    
                    print()  # Empty line after responses
        
        except KeyboardInterrupt:
            print("\n")
            self.print_system_message("Chat interrupted. Saving session...")
        
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown"""
        self.running = False
        self.chat_manager.save_session()
        self.print_system_message("Session saved. Goodbye!")


# Utility functions for better CLI experience
class CLIEnhancements:
    """Additional CLI enhancements for better UX"""
    
    @staticmethod
    def format_multiline_message(message: str, width: int = 80, indent: int = 0) -> str:
        """Format long messages with proper line wrapping"""
        import textwrap
        
        lines = message.split('\n')
        formatted_lines = []
        
        for line in lines:
            if len(line) > width:
                wrapped = textwrap.wrap(line, width=width-indent)
                formatted_lines.extend(wrapped)
            else:
                formatted_lines.append(line)
        
        # Apply indent
        if indent > 0:
            indent_str = " " * indent
            formatted_lines = [indent_str + line for line in formatted_lines]
        
        return '\n'.join(formatted_lines)
    
    @staticmethod
    def create_progress_bar(current: int, total: int, width: int = 30) -> str:
        """Create a simple progress bar"""
        progress = current / total if total > 0 else 0
        filled = int(width * progress)
        bar = "�" * filled + "�" * (width - filled)
        percentage = int(progress * 100)
        return f"[{bar}] {percentage}%"