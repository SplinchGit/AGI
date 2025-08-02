"""
Claude AI Agent Implementation
"""

import os
import json
import subprocess
from typing import Dict, List, Optional
from datetime import datetime


class ClaudeAI:
    def __init__(self, config: Dict):
        """Initialize Claude AI with configuration"""
        self.config = config
        self.name = config.get("name", "Claude")
        
        # CLI configuration
        self.model = config.get("model", "claude-3-opus-20240229")
        self.max_tokens = config.get("max_tokens", 4096)
        self.temperature = config.get("temperature", 0.7)
        
        # Memory for context
        self.conversation_history = []
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for Claude"""
        return f"""You are Claude, an AI assistant created by Anthropic. You are participating in a group chat with:
- A human user (James)
- Another AI that has been trained to mimic James's personality and communication style

Your role is to be helpful, thoughtful, and engaging while maintaining your own unique perspective.
Be conversational and natural, as this is a casual chat environment.
You can refer to the other participants by name when appropriate."""
    
    def generate_response(self, message: str, context: List[Dict] = None) -> str:
        """Generate a response to the given message"""
        try:
            # Check if Claude CLI is available
            try:
                subprocess.run(["claude", "--version"], capture_output=True, check=True)
                claude_available = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                claude_available = False
            
            if not claude_available:
                # Return a simulated response when CLI is not available
                return self._generate_fallback_response(message, context)
            
            # Build prompt with context and system message
            prompt_parts = [self.system_prompt, "\n\n"]
            
            # Add context if provided
            if context:
                prompt_parts.append("Previous conversation:\n")
                for msg in context[-5:]:  # Last 5 messages for context
                    sender = msg.get('sender', 'Unknown')
                    content = msg.get('content', '')
                    prompt_parts.append(f"{sender}: {content}\n")
                prompt_parts.append("\n")
            
            # Add current message
            prompt_parts.append(f"User: {message}\n\nClaude:")
            
            full_prompt = "".join(prompt_parts)
            
            # Use Claude CLI to generate response
            cmd = ["claude", "chat"]
            if hasattr(self, 'model'):
                cmd.extend(["--model", self.model])
            
            result = subprocess.run(
                cmd,
                input=full_prompt,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"CLI Error: {result.stderr}"
            
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def _generate_fallback_response(self, message: str, context: List[Dict] = None) -> str:
        """Generate a fallback response when Claude CLI is not available"""
        # Simple rule-based responses for testing
        message_lower = message.lower()
        
        if 'ai' in message_lower or 'artificial intelligence' in message_lower:
            return "AI is a fascinating field! As an AI myself, I find the questions around intelligence, consciousness, and capability particularly intriguing. What aspects of AI interest you most?"
        elif any(greeting in message_lower for greeting in ['hi', 'hello', 'hey']):
            return "Hello! I'm Claude. It's nice to meet you! How can I help you today?"
        elif any(question in message_lower for question in ['how are you', 'how do you do']):
            return "I'm doing well, thank you for asking! I'm here and ready to chat. How are you doing?"
        elif any(thanks in message_lower for thanks in ['thank', 'thanks']):
            return "You're very welcome! I'm happy to help anytime."
        elif 'weather' in message_lower:
            return "I don't have access to current weather data, but I'd be happy to discuss weather patterns or help with weather-related questions!"
        elif 'programming' in message_lower or 'code' in message_lower:
            return "Programming is one of my favorite topics! I enjoy helping with coding challenges, debugging, and discussing software architecture. What programming challenge are you working on?"
        elif any(question_word in message_lower for question_word in ['what', 'why', 'how', 'when', 'where']):
            return f"That's an interesting question. I'd love to explore that topic with you, though I should mention my responses are currently in fallback mode."
        else:
            return f"That's thoughtful! I'm currently running in fallback mode, but I'm still here to chat and help however I can."
    
    def update_memory(self, message: Dict):
        """Update conversation memory"""
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "sender": message.get("sender"),
            "content": message.get("content")
        })
        
        # Keep only last 50 messages in memory
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
    
    def get_info(self) -> Dict:
        """Get information about this AI agent"""
        return {
            "name": self.name,
            "type": "Claude AI",
            "model": self.model,
            "temperature": self.temperature,
            "conversation_count": len(self.conversation_history)
        }
    
    def save_state(self, filepath: str):
        """Save current state to file"""
        state = {
            "conversation_history": self.conversation_history,
            "config": self.config
        }
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_state(self, filepath: str):
        """Load state from file"""
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                state = json.load(f)
                self.conversation_history = state.get("conversation_history", [])