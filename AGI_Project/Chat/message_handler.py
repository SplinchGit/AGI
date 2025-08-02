"""
Message Handler - Processes and formats messages
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class MessageHandler:
    def __init__(self):
        """Initialize message handler with processing rules"""
        self.message_filters = []
        self.commands = {}
        self._init_commands()
    
    def _init_commands(self):
        """Initialize available commands"""
        self.commands = {
            "/help": self._help_command,
            "/clear": self._clear_command,
            "/stats": self._stats_command,
            "/export": self._export_command,
            "/memory": self._memory_command,
            "/who": self._who_command,
            "/set": self._set_command
        }
    
    def process_message(self, content: str, sender: str) -> Tuple[str, Optional[Dict]]:
        """
        Process incoming message for commands and formatting
        Returns: (processed_content, command_result)
        """
        # Check for commands
        if content.startswith("/"):
            command_parts = content.split()
            command = command_parts[0].lower()
            args = command_parts[1:] if len(command_parts) > 1 else []
            
            if command in self.commands:
                command_result = self.commands[command](args, sender)
                return "", command_result
        
        # Apply filters
        processed_content = self._apply_filters(content)
        
        # Format mentions
        processed_content = self._format_mentions(processed_content)
        
        return processed_content, None
    
    def _apply_filters(self, content: str) -> str:
        """Apply content filters"""
        # Basic profanity filter (can be extended)
        filtered = content
        
        # Remove excessive whitespace
        filtered = re.sub(r'\s+', ' ', filtered).strip()
        
        # Remove excessive punctuation
        filtered = re.sub(r'([!?.]){4,}', r'\1\1\1', filtered)
        
        return filtered
    
    def _format_mentions(self, content: str) -> str:
        """Format @mentions in messages"""
        # Find @mentions
        mentions = re.findall(r'@(\w+)', content)
        
        formatted = content
        for mention in mentions:
            # Highlight mentions (in CLI this would be with color codes)
            formatted = formatted.replace(f'@{mention}', f'@{mention}')
        
        return formatted
    
    def format_message_display(self, message: Dict, show_timestamp: bool = True) -> str:
        """Format message for display"""
        parts = []
        
        if show_timestamp:
            timestamp = datetime.fromisoformat(message["timestamp"])
            parts.append(f"[{timestamp.strftime('%H:%M:%S')}]")
        
        sender = message["sender"]
        content = message["content"]
        
        # Add sender with appropriate prefix
        if sender == "James":
            parts.append(f"{sender}: {content}")
        elif sender == "Claude":
            parts.append(f"> {sender}: {content}")
        elif sender == "James (Clone)":
            parts.append(f"=d {sender}: {content}")
        else:
            parts.append(f"{sender}: {content}")
        
        return " ".join(parts)
    
    def format_conversation_block(self, messages: List[Dict], include_responses: bool = True) -> str:
        """Format a block of conversation for display"""
        lines = []
        
        for message in messages:
            # Main message
            lines.append(self.format_message_display(message))
            
            # Include responses if any
            if include_responses and message.get("responses"):
                for responder, response in message["responses"].items():
                    response_line = f"   {responder}: {response['content']}"
                    lines.append(response_line)
            
            lines.append("")  # Empty line between message blocks
        
        return "\n".join(lines)
    
    # Command implementations
    def _help_command(self, args: List[str], sender: str) -> Dict:
        """Show help information"""
        help_text = """
Available Commands:
  /help          - Show this help message
  /clear         - Clear the current chat session
  /stats         - Show chat statistics
  /export [format] - Export conversation (json/text)
  /memory [query] - Search memory for information
  /who           - Show information about participants
  /set [option] [value] - Change chat settings

Chat Features:
  - Multi-agent conversation with Claude and James Clone
  - Persistent memory across sessions
  - @mentions to address specific participants
  - Automatic conversation saving
"""
        return {
            "type": "help",
            "content": help_text.strip()
        }
    
    def _clear_command(self, args: List[str], sender: str) -> Dict:
        """Clear chat session"""
        return {
            "type": "clear",
            "confirm": True,
            "message": "Are you sure you want to clear the chat session? (yes/no)"
        }
    
    def _stats_command(self, args: List[str], sender: str) -> Dict:
        """Show chat statistics"""
        return {
            "type": "stats",
            "request": "session_stats"
        }
    
    def _export_command(self, args: List[str], sender: str) -> Dict:
        """Export conversation"""
        format = args[0] if args else "json"
        return {
            "type": "export",
            "format": format
        }
    
    def _memory_command(self, args: List[str], sender: str) -> Dict:
        """Search memory"""
        query = " ".join(args) if args else ""
        return {
            "type": "memory_search",
            "query": query
        }
    
    def _who_command(self, args: List[str], sender: str) -> Dict:
        """Show participant information"""
        return {
            "type": "who",
            "request": "participant_info"
        }
    
    def _set_command(self, args: List[str], sender: str) -> Dict:
        """Change settings"""
        if len(args) < 2:
            return {
                "type": "error",
                "message": "Usage: /set <option> <value>"
            }
        
        option = args[0]
        value = " ".join(args[1:])
        
        return {
            "type": "set",
            "option": option,
            "value": value
        }
    
    def validate_message(self, content: str) -> Tuple[bool, Optional[str]]:
        """
        Validate message content
        Returns: (is_valid, error_message)
        """
        # Check message length
        if len(content) == 0:
            return False, "Message cannot be empty"
        
        if len(content) > 4000:
            return False, "Message too long (max 4000 characters)"
        
        # Check for spam patterns
        if len(set(content)) < 3 and len(content) > 10:
            return False, "Message appears to be spam"
        
        return True, None
    
    def extract_urls(self, content: str) -> List[str]:
        """Extract URLs from message content"""
        url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*'
        urls = re.findall(url_pattern, content)
        return urls
    
    def extract_code_blocks(self, content: str) -> List[Dict]:
        """Extract code blocks from message"""
        code_blocks = []
        
        # Find code blocks with language
        pattern = r'```(\w+)?\n(.*?)```'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for lang, code in matches:
            code_blocks.append({
                "language": lang or "plain",
                "code": code.strip()
            })
        
        return code_blocks