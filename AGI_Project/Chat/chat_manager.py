"""
Chat Manager - Orchestrates conversations between all participants
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import threading
import queue

from AIs.Claude.claude_ai import ClaudeAI
from AIs.JamesClone.james_ai import JamesCloneAI
from Chat.memory_system import MemorySystem
from Chat.message_handler import MessageHandler


class ChatManager:
    def __init__(self, config: Dict, debug: bool = False):
        """Initialize the chat manager with all AI agents"""
        self.config = config
        self.debug = debug
        
        # Initialize AI agents
        self.agents = {}
        self._initialize_agents()
        
        # Initialize memory system
        self.memory_system = MemorySystem(config.get("memory_settings", {}))
        
        # Initialize message handler
        self.message_handler = MessageHandler()
        
        # Chat state
        self.active_session = {
            "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "started_at": datetime.now().isoformat(),
            "participants": ["James", "Claude", "James (Clone)"],
            "messages": []
        }
        
        # Message queue for async processing
        self.message_queue = queue.Queue()
        
        # Load previous session if exists
        self._load_session()
    
    def _initialize_agents(self):
        """Initialize all AI agents"""
        ai_configs = self.config.get("ai_agents", {})
        
        # Initialize Claude
        if "claude" in ai_configs:
            try:
                self.agents["Claude"] = ClaudeAI(ai_configs["claude"])
                if self.debug:
                    print("* Claude AI initialized")
            except Exception as e:
                print(f"Failed to initialize Claude: {e}")
                self.agents["Claude"] = None
        
        # Initialize James Clone
        if "james_clone" in ai_configs:
            try:
                self.agents["James (Clone)"] = JamesCloneAI(ai_configs["james_clone"])
                if self.debug:
                    print("* James Clone AI initialized")
            except Exception as e:
                print(f"Failed to initialize James Clone: {e}")
                self.agents["James (Clone)"] = None
    
    def send_message(self, sender: str, content: str) -> Dict:
        """Send a message from a participant"""
        # Create message object
        message = {
            "id": len(self.active_session["messages"]) + 1,
            "timestamp": datetime.now().isoformat(),
            "sender": sender,
            "content": content,
            "responses": {}
        }
        
        # Add to session
        self.active_session["messages"].append(message)
        
        # Update memory for all agents
        for agent_name, agent in self.agents.items():
            if agent and agent_name != sender:
                agent.update_memory(message)
        
        # Save to memory system
        self.memory_system.add_message(message)
        
        # Get responses from AI agents (if sender is not an AI)
        if sender == "James":  # Human user
            responses = self._get_ai_responses(message)
            message["responses"] = responses
        
        # Auto-save session
        if self.config.get("chat_settings", {}).get("save_history", True):
            self.save_session()
        
        return message
    
    def _get_ai_responses(self, message: Dict) -> Dict:
        """Get responses from all AI agents"""
        responses = {}
        context = self.active_session["messages"][-20:]  # Last 20 messages for context
        
        # Get responses in parallel using threads
        threads = []
        response_queue = queue.Queue()
        
        for agent_name, agent in self.agents.items():
            if agent and agent_name != message["sender"]:
                thread = threading.Thread(
                    target=self._get_agent_response,
                    args=(agent_name, agent, message["content"], context, response_queue)
                )
                thread.start()
                threads.append(thread)
        
        # Wait for all responses
        for thread in threads:
            thread.join(timeout=30)  # 30 second timeout per agent
        
        # Collect responses
        while not response_queue.empty():
            agent_name, response = response_queue.get()
            responses[agent_name] = {
                "content": response,
                "timestamp": datetime.now().isoformat()
            }
            
            # Create a message for this response
            response_message = {
                "id": len(self.active_session["messages"]) + 1,
                "timestamp": datetime.now().isoformat(),
                "sender": agent_name,
                "content": response,
                "is_response_to": message["id"]
            }
            
            # Add to session
            self.active_session["messages"].append(response_message)
            
            # Update other agents' memory
            for other_agent_name, other_agent in self.agents.items():
                if other_agent and other_agent_name != agent_name:
                    other_agent.update_memory(response_message)
            
            # Save to memory system
            self.memory_system.add_message(response_message)
        
        return responses
    
    def _get_agent_response(self, agent_name: str, agent, content: str, context: List[Dict], response_queue: queue.Queue):
        """Get response from a single agent (runs in thread)"""
        try:
            response = agent.generate_response(content, context)
            response_queue.put((agent_name, response))
        except Exception as e:
            if self.debug:
                print(f"Error getting response from {agent_name}: {e}")
            response_queue.put((agent_name, f"[Error: {str(e)}]"))
    
    def get_conversation_history(self, limit: int = 50) -> List[Dict]:
        """Get recent conversation history"""
        return self.active_session["messages"][-limit:]
    
    def get_session_info(self) -> Dict:
        """Get information about the current session"""
        return {
            "session_id": self.active_session["session_id"],
            "started_at": self.active_session["started_at"],
            "message_count": len(self.active_session["messages"]),
            "participants": self.active_session["participants"],
            "agents": {
                name: agent.get_info() if agent else {"status": "not initialized"}
                for name, agent in self.agents.items()
            }
        }
    
    def save_session(self):
        """Save current session to file"""
        session_file = self.config.get("chat_settings", {}).get("session_file", "Data/active_session.json")
        os.makedirs(os.path.dirname(session_file), exist_ok=True)
        
        with open(session_file, 'w') as f:
            json.dump(self.active_session, f, indent=2)
        
        # Also save to history
        history_file = self.config.get("chat_settings", {}).get("history_file", "Data/chat_history.json")
        self._append_to_history(history_file)
        
        # Save individual agent states
        for agent_name, agent in self.agents.items():
            if agent:
                state_file = f"Data/agent_states/{agent_name.replace(' ', '_')}_state.json"
                os.makedirs(os.path.dirname(state_file), exist_ok=True)
                agent.save_state(state_file)
    
    def _append_to_history(self, history_file: str):
        """Append current session to history file"""
        os.makedirs(os.path.dirname(history_file), exist_ok=True)
        
        # Load existing history
        history = []
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    history = json.load(f)
            except:
                history = []
        
        # Find or create session in history
        session_found = False
        for i, session in enumerate(history):
            if session.get("session_id") == self.active_session["session_id"]:
                history[i] = self.active_session
                session_found = True
                break
        
        if not session_found:
            history.append(self.active_session)
        
        # Limit history size
        max_history = self.config.get("chat_settings", {}).get("max_history_size", 1000)
        if len(history) > max_history:
            history = history[-max_history:]
        
        # Save updated history
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def _load_session(self):
        """Load previous session if exists"""
        session_file = self.config.get("chat_settings", {}).get("session_file", "Data/active_session.json")
        
        if os.path.exists(session_file):
            try:
                with open(session_file, 'r') as f:
                    loaded_session = json.load(f)
                    
                # Check if session is from today
                session_date = datetime.fromisoformat(loaded_session["started_at"]).date()
                if session_date == datetime.now().date():
                    self.active_session = loaded_session
                    if self.debug:
                        print(f"* Loaded previous session with {len(self.active_session['messages'])} messages")
            except Exception as e:
                if self.debug:
                    print(f"Could not load previous session: {e}")
    
    def clear_session(self):
        """Clear current session and start fresh"""
        self.active_session = {
            "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "started_at": datetime.now().isoformat(),
            "participants": ["James", "Claude", "James (Clone)"],
            "messages": []
        }
        
        # Clear agent memories
        for agent in self.agents.values():
            if agent:
                agent.conversation_history = []
        
        if self.debug:
            print("* Session cleared")
    
    def export_conversation(self, format: str = "json") -> str:
        """Export conversation in various formats"""
        if format == "json":
            return json.dumps(self.active_session, indent=2)
        elif format == "text":
            lines = []
            lines.append(f"Chat Session: {self.active_session['session_id']}")
            lines.append(f"Started: {self.active_session['started_at']}")
            lines.append("=" * 50)
            
            for msg in self.active_session["messages"]:
                lines.append(f"\n[{msg['timestamp']}] {msg['sender']}:")
                lines.append(msg['content'])
                
                if msg.get('responses'):
                    for responder, response in msg['responses'].items():
                        lines.append(f"\n  -> {responder}: {response['content']}")
            
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported export format: {format}")