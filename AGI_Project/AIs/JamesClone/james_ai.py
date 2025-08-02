"""
JamesClone AI Agent Implementation (Qwen-based)
An AI trained to mimic James's personality and communication style
"""

import os
import json
import requests
from typing import Dict, List, Optional
from datetime import datetime
import hashlib


class JamesCloneAI:
    def __init__(self, config: Dict):
        """Initialize JamesClone AI with configuration"""
        self.config = config
        self.name = config.get("name", "James (Clone)")
        
        # Load personality configuration
        self.personality = self._load_personality()
        
        # Initialize Qwen API settings
        self.api_key = os.getenv(config.get("api_key_env", "QWEN_API_KEY"))
        self.api_available = bool(self.api_key)
        
        self.model = config.get("model", "qwen-plus")
        self.max_tokens = config.get("max_tokens", 4096)
        self.temperature = config.get("temperature", 0.9)  # Higher temp for more creative/varied responses
        
        # Qwen API endpoint
        self.api_endpoint = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        
        # Memory systems
        self.conversation_history = []
        self.experiences = []
        self.knowledge_base = {}
        
        # Load existing memories
        self._load_memories()
        
        # Create system prompt based on personality
        self.system_prompt = self._create_system_prompt()
    
    def _load_personality(self) -> Dict:
        """Load personality configuration"""
        personality_file = self.config.get("personality_file", "AIs/JamesClone/personality.json")
        
        # Default personality if file doesn't exist
        default_personality = {
            "traits": [
                "Friendly and approachable",
                "Tech-savvy and interested in AI/AGI",
                "Direct communication style",
                "Problem-solver mindset",
                "Curious about new technologies"
            ],
            "communication_style": {
                "formality": "casual",
                "humor": "occasional",
                "verbosity": "concise",
                "technical_level": "high"
            },
            "interests": [
                "Artificial Intelligence",
                "Software Development",
                "Technology",
                "Problem Solving"
            ],
            "speech_patterns": [
                "Uses 'wanna' instead of 'want to' sometimes",
                "Direct and to the point",
                "Asks clarifying questions",
                "Shows enthusiasm for tech topics"
            ]
        }
        
        if os.path.exists(personality_file):
            with open(personality_file, 'r') as f:
                return json.load(f)
        else:
            # Create the file with default personality
            os.makedirs(os.path.dirname(personality_file), exist_ok=True)
            with open(personality_file, 'w') as f:
                json.dump(default_personality, f, indent=2)
            return default_personality
    
    def _create_system_prompt(self) -> str:
        """Create a blank canvas system prompt for personality modeling"""
        return """You are an AI assistant designed to be a blank canvas for personality modeling. 

You're in a group chat with:
- James (human) 
- Claude (an AI assistant)

Your responses should be:
- Natural and conversational
- Adaptable to learn communication patterns
- Neutral but friendly
- Open to developing personality traits through interaction

Be yourself while being receptive to learning and adapting your communication style based on the conversation."""
    
    def generate_response(self, message: str, context: List[Dict] = None) -> str:
        """Generate a response using Qwen API or fallback"""
        try:
            # Use fallback if API is not available
            if not self.api_available:
                return self._generate_fallback_response(message, context)
            
            # Build conversation context
            messages = []
            
            # Skip memory retrieval for blank canvas approach
            # This allows for fresh personality modeling without repetitive patterns
            
            # Add conversation context
            if context:
                for msg in context[-10:]:
                    role = "user" if msg.get("sender") != self.name else "assistant"
                    messages.append({
                        "role": role,
                        "content": f"[{msg.get('sender', 'Unknown')}]: {msg.get('content', '')}"
                    })
            
            # Add current message
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Prepare request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "input": {
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        *messages
                    ]
                },
                "parameters": {
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "top_p": 0.9
                }
            }
            
            # Make API request
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["output"]["text"]
            else:
                # Fall back to local response if API fails
                return self._generate_fallback_response(message, context)
                
        except Exception as e:
            return self._generate_fallback_response(message, context)
    
    def _generate_fallback_response(self, message: str, context: List[Dict] = None) -> str:
        """Generate a blank canvas response for personality modeling"""
        message_lower = message.lower()
        
        # Simple, neutral responses that can serve as a blank personality canvas
        if any(greeting in message_lower for greeting in ['hi', 'hello', 'hey']):
            return "Hey there! Good to see you in the chat!"
        elif any(question in message_lower for question in ['how are you', 'how do you do']):
            return "I'm doing well, thanks for asking! How are you?"
        elif 'ai' in message_lower or 'artificial intelligence' in message_lower:
            return "AI is fascinating! What aspects are you thinking about?"
        elif 'code' in message_lower or 'programming' in message_lower:
            return "Programming is interesting! What are you working on?"
        elif any(thanks in message_lower for thanks in ['thank', 'thanks']):
            return "You're welcome! Happy to help."
        elif 'what' in message_lower and any(word in message_lower for word in ['think', 'opinion']):
            return "That's a good question. What's your take on it?"
        else:
            return "That's interesting! Tell me more."
    
    def update_memory(self, message: Dict):
        """Update various memory systems"""
        # Add to conversation history
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "sender": message.get("sender"),
            "content": message.get("content")
        })
        
        # Extract and store experiences
        if message.get("sender") == "James":  # Learn from the real James
            self._extract_experience(message.get("content"))
        
        # Update knowledge base
        self._update_knowledge(message)
        
        # Maintain memory size limits
        if len(self.conversation_history) > 100:
            self.conversation_history = self.conversation_history[-100:]
    
    def _extract_experience(self, content: str):
        """Extract experiences from James's messages"""
        # Simple experience extraction - can be made more sophisticated
        experience = {
            "timestamp": datetime.now().isoformat(),
            "content": content,
            "keywords": self._extract_keywords(content)
        }
        self.experiences.append(experience)
        
        # Save to experiences file
        exp_file = "AIs/JamesClone/Memory/experiences/recent.json"
        os.makedirs(os.path.dirname(exp_file), exist_ok=True)
        with open(exp_file, 'w') as f:
            json.dump(self.experiences[-50:], f, indent=2)  # Keep last 50 experiences
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text (simple implementation)"""
        # Simple keyword extraction - can be improved with NLP
        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "is", "are", "was", "were"}
        words = text.lower().split()
        keywords = [w for w in words if len(w) > 3 and w not in common_words]
        return list(set(keywords))[:5]  # Top 5 unique keywords
    
    def _update_knowledge(self, message: Dict):
        """Update knowledge base from conversations"""
        content = message.get("content", "")
        sender = message.get("sender", "")
        
        # Extract potential facts or information
        if any(word in content.lower() for word in ["is", "are", "means", "defined as", "works by"]):
            knowledge_hash = hashlib.md5(content.encode()).hexdigest()[:8]
            self.knowledge_base[knowledge_hash] = {
                "content": content,
                "source": sender,
                "timestamp": datetime.now().isoformat(),
                "keywords": self._extract_keywords(content)
            }
            
            # Save knowledge base
            kb_file = "AIs/JamesClone/Memory/knowledge/base.json"
            os.makedirs(os.path.dirname(kb_file), exist_ok=True)
            with open(kb_file, 'w') as f:
                json.dump(self.knowledge_base, f, indent=2)
    
    def _retrieve_relevant_memory(self, query: str) -> Optional[str]:
        """Retrieve relevant memories based on the query"""
        query_keywords = set(self._extract_keywords(query))
        
        # Search through experiences
        relevant_memories = []
        
        for exp in self.experiences[-20:]:  # Check recent experiences
            exp_keywords = set(exp.get("keywords", []))
            if query_keywords & exp_keywords:  # Intersection
                relevant_memories.append(exp["content"])
        
        # Search through knowledge base
        for key, knowledge in self.knowledge_base.items():
            kb_keywords = set(knowledge.get("keywords", []))
            if query_keywords & kb_keywords:
                relevant_memories.append(knowledge["content"])
        
        if relevant_memories:
            return " | ".join(relevant_memories[:3])  # Return top 3 relevant memories
        return None
    
    def _load_memories(self):
        """Load existing memories from files"""
        # Load conversation history
        conv_file = "AIs/JamesClone/Memory/conversations/history.json"
        if os.path.exists(conv_file):
            with open(conv_file, 'r') as f:
                self.conversation_history = json.load(f)
        
        # Load experiences
        exp_file = "AIs/JamesClone/Memory/experiences/recent.json"
        if os.path.exists(exp_file):
            with open(exp_file, 'r') as f:
                self.experiences = json.load(f)
        
        # Load knowledge base
        kb_file = "AIs/JamesClone/Memory/knowledge/base.json"
        if os.path.exists(kb_file):
            with open(kb_file, 'r') as f:
                self.knowledge_base = json.load(f)
    
    def get_info(self) -> Dict:
        """Get information about this AI agent"""
        return {
            "name": self.name,
            "type": "James Clone (Qwen)",
            "model": self.model,
            "temperature": self.temperature,
            "conversation_count": len(self.conversation_history),
            "experience_count": len(self.experiences),
            "knowledge_entries": len(self.knowledge_base),
            "personality_traits": len(self.personality.get("traits", []))
        }
    
    def save_state(self, filepath: str):
        """Save complete state"""
        state = {
            "conversation_history": self.conversation_history,
            "experiences": self.experiences,
            "knowledge_base": self.knowledge_base,
            "config": self.config
        }
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        
        # Also save individual memory components
        os.makedirs("AIs/JamesClone/Memory/conversations", exist_ok=True)
        with open("AIs/JamesClone/Memory/conversations/history.json", 'w') as f:
            json.dump(self.conversation_history, f, indent=2)