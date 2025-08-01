#!/usr/bin/env python3
"""
Enhanced Three-Way Chat with Persistent Memory and Autonomous Mode
- Maintains conversation history across sessions
- Can run autonomously with AI-to-AI communication
- All operations constrained to AGI folder
- Session save/resume functionality
"""

import subprocess
import requests
import json
import time
import shutil
import os
import re
from datetime import datetime
from pathlib import Path
from enum import Enum
import pickle
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import OrderedDict
import hashlib
import threading

# Import user management system
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from ai_agents.shared.user_management import get_user_manager, UserType, Permission

# ==============================================================================
# CONSTANTS AND CONFIGURATION
# ==============================================================================
# Get the project root (AGI directory)
PROJECT_ROOT = Path(__file__).parent.parent.parent
WORKSPACE_PATH = str(PROJECT_ROOT)
MEMORY_FILE = str(PROJECT_ROOT / "data" / "sessions" / "persistent_memory.json")
SESSION_FILE = str(PROJECT_ROOT / "data" / "sessions" / "current_session.pkl")
OLLAMA_HOST = "localhost"
OLLAMA_PORT = 11434
DEBUG_MODE = True
QWEN_MODEL = "qwen2.5:7b"
MAX_RESPONSE_LENGTH = 300
MAX_AUTONOMOUS_ROUNDS = 10  # Limit autonomous conversation rounds

# Performance optimization settings
CACHE_RESPONSES = True
RESPONSE_CACHE_SIZE = 100
CONCURRENT_REQUESTS = True
STREAM_RESPONSES = True
BATCH_MEMORY_SAVES = True
MEMORY_SAVE_INTERVAL = 5  # Save every N messages

# ==============================================================================
# CIRCUIT BREAKER PATTERN
# ==============================================================================
class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """Simple circuit breaker to prevent hammering failed services"""
    def __init__(self, failure_threshold=3, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                return None, "Service temporarily unavailable (circuit open)"
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result, None
        except Exception as e:
            self._on_failure()
            return None, str(e)
    
    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

# ==============================================================================
# MEMORY MANAGEMENT SYSTEM
# ==============================================================================
class ConversationMemory:
    """Manages persistent conversation memory across sessions"""
    
    def __init__(self, workspace_path):
        self.workspace = Path(workspace_path)
        self.memory_file = self.workspace / MEMORY_FILE
        self.session_file = self.workspace / SESSION_FILE
        
        # Memory structure
        self.conversations = []  # All conversations ever
        self.current_session = []  # Current session only
        self.important_facts = []  # Key information to remember
        self.goals = []  # Current objectives/tasks
        self.context_summary = ""  # Summary of overall context
        
        self.load_memory()
    
    def load_memory(self):
        """Load persistent memory from disk"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.conversations = data.get('conversations', [])
                    self.important_facts = data.get('important_facts', [])
                    self.goals = data.get('goals', [])
                    self.context_summary = data.get('context_summary', '')
            except Exception as e:
                print(f"Warning: Could not load memory: {e}")
        
        # Load current session if exists
        if self.session_file.exists():
            try:
                with open(self.session_file, 'rb') as f:
                    self.current_session = pickle.load(f)
                print(f"Resumed session with {len(self.current_session)} messages")
            except Exception as e:
                print(f"Warning: Could not load session: {e}")
    
    def save_memory(self):
        """Save persistent memory to disk"""
        try:
            memory_data = {
                'conversations': self.conversations,
                'important_facts': self.important_facts,
                'goals': self.goals,
                'context_summary': self.context_summary,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, indent=2, ensure_ascii=False)
            
            # Save current session
            with open(self.session_file, 'wb') as f:
                pickle.dump(self.current_session, f)
                
        except Exception as e:
            print(f"Warning: Could not save memory: {e}")
    
    def add_message(self, speaker, message):
        """Add message to current session and analyze for importance"""
        msg_data = {
            'speaker': speaker,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        self.current_session.append(msg_data)
        
        # Analyze for important facts or goals
        self._extract_important_info(speaker, message)
        
        # Auto-save every few messages
        if len(self.current_session) % 3 == 0:
            self.save_memory()
    
    def _extract_important_info(self, speaker, message):
        """Extract important facts and goals from messages"""
        lower_msg = message.lower()
        
        # Look for goal-setting language
        goal_indicators = ['goal:', 'objective:', 'task:', 'we need to', 'we should', 'let\'s']
        for indicator in goal_indicators:
            if indicator in lower_msg:
                goal = message[lower_msg.find(indicator):].strip()
                if goal not in self.goals:
                    self.goals.append({
                        'goal': goal,
                        'speaker': speaker,
                        'timestamp': datetime.now().isoformat()
                    })
        
        # Look for factual statements
        fact_indicators = ['important:', 'remember:', 'key point:', 'we discovered', 'we found']
        for indicator in fact_indicators:
            if indicator in lower_msg:
                fact = message[lower_msg.find(indicator):].strip()
                if fact not in [f['fact'] for f in self.important_facts]:
                    self.important_facts.append({
                        'fact': fact,
                        'speaker': speaker,
                        'timestamp': datetime.now().isoformat()
                    })
    
    def get_context_for_ai(self, ai_name, max_messages=15):
        """Generate context string for specific AI"""
        context = f"""=== PERSISTENT MEMORY CONTEXT ===
You are {ai_name} in a three-way conversation about AGI research.

CURRENT GOALS:
"""
        
        # Add recent goals
        for goal in self.goals[-3:]:
            context += f"- {goal['goal']} (set by {goal['speaker']})\n"
        
        context += "\nIMPORTANT FACTS TO REMEMBER:\n"
        
        # Add important facts
        for fact in self.important_facts[-5:]:
            context += f"- {fact['fact']} (from {fact['speaker']})\n"
        
        context += f"\nOVERALL CONTEXT: {self.context_summary}\n"
        
        context += "\nRECENT CONVERSATION:\n"
        
        # Add recent messages
        recent_messages = self.current_session[-max_messages:]
        for msg in recent_messages:
            context += f"{msg['speaker']}: {msg['message']}\n"
        
        context += "\n=== END CONTEXT ===\n"
        
        return context
    
    def end_session(self):
        """End current session and archive to conversations"""
        if self.current_session:
            session_data = {
                'messages': self.current_session,
                'start_time': self.current_session[0]['timestamp'] if self.current_session else None,
                'end_time': datetime.now().isoformat(),
                'message_count': len(self.current_session)
            }
            
            self.conversations.append(session_data)
            self.current_session = []
            
            # Update context summary based on the session
            self._update_context_summary()
            
            self.save_memory()
    
    def _update_context_summary(self):
        """Update the overall context summary"""
        # Simple approach: keep track of main topics discussed
        if self.conversations:
            recent_session = self.conversations[-1]
            topics = []
            
            for msg in recent_session['messages']:
                # Extract potential topics (simple keyword extraction)
                words = msg['message'].lower().split()
                important_words = [w for w in words if len(w) > 4 and w not in ['that', 'this', 'with', 'will', 'have', 'been']]
                topics.extend(important_words[:2])  # Top 2 words per message
            
            # Update summary
            topic_summary = ', '.join(set(topics[:10]))  # Top 10 unique topics
            self.context_summary = f"Recent topics: {topic_summary}. Total sessions: {len(self.conversations)}"

# ==============================================================================
# ENHANCED CHAT APPLICATION
# ==============================================================================
class EnhancedAGIChat:
    """Enhanced chat with memory, autonomous mode, and dynamic user management"""
    
    def __init__(self):
        self.workspace = Path(WORKSPACE_PATH)
        self.memory = ConversationMemory(WORKSPACE_PATH)
        self.user_manager = get_user_manager()
        
        # Ensure workspace exists
        self.workspace.mkdir(exist_ok=True)
        os.chdir(str(self.workspace))  # Constrain operations to this folder
        
        # Initialize services (simplified from original)
        self.ollama_base_url = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"
        
        # Dynamic circuit breakers based on user management
        self.circuit_breakers = {}
        for config in self.user_manager.get_all_user_configs().values():
            if config.user_type in [UserType.AI_CLAUDE, UserType.AI_QWEN, UserType.AI_CUSTOM]:
                self.circuit_breakers[config.user_id] = CircuitBreaker(failure_threshold=2, recovery_timeout=30)
        
        # Autonomous mode settings
        self.autonomous_mode = False
        self.autonomous_rounds = 0
        self.max_autonomous_rounds = MAX_AUTONOMOUS_ROUNDS
        
        # Performance optimizations
        self.response_cache = OrderedDict() if CACHE_RESPONSES else None
        self.cache_lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Self-modification capabilities
        self.code_modification_enabled = False
        self.modification_history = []
        
        # Activate default users
        self.user_manager.activate_user('human_user')
        self.user_manager.activate_user('claude_ai')
        self.user_manager.activate_user('qwen_ai')
        
        print("Enhanced AGI Chat with Dynamic Users initialized")
        print(f"Working directory: {os.getcwd()}")
        print(f"Memory loaded: {len(self.memory.conversations)} past sessions")
        
        # Display active users
        active_users = [config.display_name for config in self.user_manager.get_all_user_configs().values()]
        print(f"Available users: {', '.join(active_users)}")
        
        if self.memory.current_session:
            print("Resuming previous session...")
            self._display_recent_context()
    
    def _get_cache_key(self, service, prompt):
        """Generate cache key for response caching"""
        return hashlib.md5(f"{service}:{prompt}".encode()).hexdigest()
    
    def _add_to_cache(self, service, prompt, response):
        """Add response to cache with LRU eviction"""
        cache_key = self._get_cache_key(service, prompt)
        with self.cache_lock:
            # Remove oldest if cache is full
            if len(self.response_cache) >= RESPONSE_CACHE_SIZE:
                self.response_cache.popitem(last=False)
            self.response_cache[cache_key] = response
    
    def _display_recent_context(self):
        """Display recent context when resuming"""
        print("\n" + "="*50)
        print("RESUMING SESSION - RECENT CONTEXT:")
        print("="*50)
        
        # Show goals
        if self.memory.goals:
            print("CURRENT GOALS:")
            for goal in self.memory.goals[-3:]:
                print(f"  • {goal['goal']}")
        
        # Show recent messages
        print("\nRECENT MESSAGES:")
        for msg in self.memory.current_session[-5:]:
            print(f"  {msg['speaker']}: {msg['message'][:100]}...")
        
        print("="*50)
    
    def _get_qwen_response(self, user_input):
        """Get Qwen response with context"""
        qwen_context = self.memory.get_context_for_ai("Qwen")
        qwen_context += f"\nUser just said: {user_input}\n\nRespond as Qwen in this three-way conversation about AGI research. Keep responses focused and under 3 sentences. Work within the folder C:\\Users\\jf358\\Documents\\AGI only."
        return self.ask_qwen(qwen_context)
    
    def _get_claude_response(self, user_input, qwen_response):
        """Get Claude response with context"""
        claude_context = self.memory.get_context_for_ai("Claude")
        if qwen_response:
            claude_context += f"\nUser just said: {user_input}\nQwen responded: {qwen_response}\n\nRespond as Claude in this three-way conversation about AGI research. Keep responses focused and under 3 sentences. Work within the folder C:\\Users\\jf358\\Documents\\AGI only."
        else:
            claude_context += f"\nUser just said: {user_input}\n\nRespond as Claude in this three-way conversation about AGI research. Keep responses focused and under 3 sentences. Work within the folder C:\\Users\\jf358\\Documents\\AGI only."
        return self.ask_claude(claude_context)
    
    def ask_qwen_raw(self, prompt):
        """Query Qwen via Ollama - raw function for circuit breaker"""
        response = requests.post(
            f"{self.ollama_base_url}/api/generate",
            json={
                "model": QWEN_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 200
                }
            },
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json().get('response', 'No response from Qwen')
            # Truncate if too long
            words = result.split()
            if len(words) > MAX_RESPONSE_LENGTH:
                result = ' '.join(words[:MAX_RESPONSE_LENGTH]) + '...'
            return result
        else:
            raise RuntimeError(f"Qwen error: Status {response.status_code}")
    
    def ask_qwen(self, prompt):
        """Query Qwen with circuit breaker protection and caching"""
        # Check cache first
        if self.response_cache is not None:
            cache_key = self._get_cache_key("qwen", prompt)
            with self.cache_lock:
                if cache_key in self.response_cache:
                    return self.response_cache[cache_key]
        
        result, error = self.qwen_breaker.call(self.ask_qwen_raw, prompt)
        
        if error:
            if "circuit open" in error:
                return "Qwen is temporarily unavailable (too many recent failures)"
            elif "timeout" in error.lower():
                return "Qwen is taking too long to respond"
            elif "connection" in error.lower():
                return "Cannot connect to Qwen - run 'ollama serve' if not running"
            else:
                return f"Qwen error: {error}"
        
        # Cache successful result
        if self.response_cache is not None and result:
            self._add_to_cache("qwen", prompt, result)
        
        return result
    
    def ask_claude_raw(self, prompt):
        """Query Claude via CLI - raw function for circuit breaker"""
        # Use claude from PATH
        claude_cmd = 'claude'
        
        if DEBUG_MODE:
            print(f"[DEBUG] Using Claude CLI: {claude_cmd}")
        
        # Start claude process for interactive communication
        try:
            # Use shell=True on Windows to handle .cmd files properly
            process = subprocess.Popen(
                [claude_cmd, '--no-color', '--no-interactive'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True,
                cwd=str(self.workspace)
            )
            
            if DEBUG_MODE:
                print(f"[DEBUG] Sending prompt to Claude via stdin")
            
            # Send the prompt and close stdin to signal we're done
            stdout, stderr = process.communicate(input=prompt + '\n', timeout=120)
            
            if DEBUG_MODE:
                print(f"[DEBUG] Claude return code: {process.returncode}")
                if stderr:
                    print(f"[DEBUG] Claude stderr: {stderr}")
            
            if process.returncode == 0:
                output = stdout.strip()
                if output:
                    # Extract actual response, skipping UI elements
                    lines = output.split('\n')
                    response_lines = []
                    skip_next = False
                    
                    for i, line in enumerate(lines):
                        # Skip UI chrome
                        if any(x in line for x in ['╭', '╰', '│', '✻', '─', 'Welcome to Claude', 'Tips for']):
                            continue
                        # Skip empty lines and prompts
                        if not line.strip() or line.strip().startswith('>') or line.strip().startswith('?'):
                            continue
                        # Skip lines that look like the prompt echo
                        if prompt in line:
                            skip_next = True
                            continue
                        if skip_next:
                            skip_next = False
                            continue
                        # This should be actual response content
                        response_lines.append(line.strip())
                    
                    response = ' '.join(response_lines)
                    
                    # Remove any ANSI color codes
                    response = re.sub(r'\x1b\[[0-9;]*m', '', response)
                    
                    # Truncate if too long
                    words = response.split()
                    if len(words) > MAX_RESPONSE_LENGTH:
                        response = ' '.join(words[:MAX_RESPONSE_LENGTH]) + '...'
                    
                    return response if response else "Claude returned empty response"
                else:
                    raise RuntimeError("Claude returned empty response")
            else:
                error_msg = stderr.strip() if stderr else "Unknown error"
                if "auth" in error_msg.lower() or "oauth" in error_msg.lower():
                    raise RuntimeError("Claude authentication issue - try running 'claude auth'")
                raise RuntimeError(f"Claude error: {error_msg}")
                
        except subprocess.TimeoutExpired:
            process.kill()
            raise RuntimeError("Claude timeout - response took too long")
        except FileNotFoundError:
            raise RuntimeError("Claude CLI not installed")
    
    def ask_claude(self, prompt):
        """Query Claude with circuit breaker protection"""
        result, error = self.claude_breaker.call(self.ask_claude_raw, prompt)
        
        if error:
            if "circuit open" in error:
                return "Claude is temporarily unavailable (too many recent failures)"
            elif "not installed" in error:
                return "Claude CLI not found - install with: npm install -g @anthropic-ai/claude-code"
            elif "authentication" in error:
                return "Claude needs authentication - run 'claude auth' first"
            elif "timeout" in error.lower():
                return "Claude is taking too long to respond"
            else:
                return f"Claude error: {error}"
        
        return result
    
    def _get_ai_response(self, user_config, user_input, autonomous=False):
        """Get AI response based on user configuration"""
        if user_config.user_type == UserType.AI_QWEN:
            if autonomous:
                return self.ask_qwen(user_input)
            else:
                context = self.memory.get_context_for_ai(user_config.display_name)
                context += f"\nUser just said: {user_input}\n\nRespond as {user_config.display_name} in this conversation about AGI research. Keep responses focused and under 3 sentences."
                return self.ask_qwen(context)
        elif user_config.user_type == UserType.AI_CLAUDE:
            if autonomous:
                return self.ask_claude(user_input)
            else:
                context = self.memory.get_context_for_ai(user_config.display_name)
                context += f"\nUser just said: {user_input}\n\nRespond as {user_config.display_name} in this conversation about AGI research. Keep responses focused and under 3 sentences."
                return self.ask_claude(context)
        else:
            return f"{user_config.display_name} AI not implemented yet"
    
    def conversation_round(self, user_input=None, autonomous=False):
        """Single conversation round with memory and dynamic users"""
        
        if not autonomous and user_input:
            # User input mode with dynamic user management
            human_user = self.user_manager.get_active_user('human_user')
            if not human_user or not human_user.can_send_message():
                print("You cannot send messages right now (rate limited or no permission).")
                return False
            
            # Record human message
            self.user_manager.record_user_message('human_user')
            human_config = self.user_manager.get_user_config('human_user')
            display_name = human_config.display_name if human_config else "You"
            
            print(f"\n{display_name}: {user_input}")
            self.memory.add_message(display_name, user_input)
            
            # Get responses from all active AI users
            ai_responses = []
            for config in self.user_manager.get_all_user_configs().values():
                if config.user_type not in [UserType.AI_CLAUDE, UserType.AI_QWEN, UserType.AI_CUSTOM]:
                    continue
                
                ai_user = self.user_manager.get_active_user(config.user_id)
                if not ai_user or not ai_user.can_send_message():
                    continue
                
                try:
                    if config.user_type == UserType.AI_QWEN:
                        response = self._get_ai_response(config, user_input)
                    elif config.user_type == UserType.AI_CLAUDE:
                        response = self._get_ai_response(config, user_input)
                    else:
                        response = f"{config.display_name} AI not implemented yet"
                    
                    if response and "error" not in response.lower():
                        print(f"\n{config.display_name}: {response}")
                        self.memory.add_message(config.display_name, response)
                        self.user_manager.record_user_message(config.user_id)
                        ai_responses.append(response)
                    
                except Exception as e:
                    print(f"\n{config.display_name} error: {str(e)}")
            
            return len(ai_responses) > 0
            
        else:
            # Autonomous mode - AIs talk to each other
            if self.autonomous_rounds >= self.max_autonomous_rounds:
                print("\n[AUTONOMOUS MODE] Maximum rounds reached. Ending autonomous mode.")
                self.autonomous_mode = False
                return False
            
            self.autonomous_rounds += 1
            print(f"\n[AUTONOMOUS ROUND {self.autonomous_rounds}]")
            
            # Get active AI users for autonomous conversation
            ai_users = [config for config in self.user_manager.get_all_user_configs().values()
                       if config.user_type in [UserType.AI_CLAUDE, UserType.AI_QWEN, UserType.AI_CUSTOM]]
            
            if len(ai_users) < 2:
                print("Need at least 2 AI users for autonomous mode")
                self.autonomous_mode = False
                return False
            
            # First AI speaks
            first_ai = ai_users[0]
            context = self.memory.get_context_for_ai(first_ai.display_name)
            context += "\n\nYou are now in autonomous mode. Continue the AGI research discussion. Propose next steps, ask questions, or build on previous ideas. Work within the folder C:\\Users\\jf358\\Documents\\AGI only. Be productive and focused."
            
            response1 = self._get_ai_response(first_ai, context, autonomous=True)
            if response1:
                print(f"\n{first_ai.display_name}: {response1}")
                self.memory.add_message(first_ai.display_name, response1)
                
                # Second AI responds
                second_ai = ai_users[1]
                context2 = self.memory.get_context_for_ai(second_ai.display_name)
                context2 += f"\n\n{first_ai.display_name} just said: {response1}\n\nYou are in autonomous mode. Respond and continue the AGI research discussion. Be productive and suggest concrete next steps. Work within the folder C:\\Users\\jf358\\Documents\\AGI only."
                
                response2 = self._get_ai_response(second_ai, context2, autonomous=True)
                if response2:
                    print(f"\n{second_ai.display_name}: {response2}")
                    self.memory.add_message(second_ai.display_name, response2)
        
        return True
    
    def run(self):
        """Main conversation loop with autonomous mode and user management support"""
        print("\n" + "="*60)
        print("Enhanced AGI Chat with Dynamic Users - Commands:")
        print("  'autonomous' - Start autonomous AI-to-AI conversation")
        print("  'stop' - Stop autonomous mode")
        print("  'memory' - Show memory summary")
        print("  'goals' - Show current goals")
        print("  'users' - Show user information")
        print("  'user stats' - Show user statistics")
        print("  'quit' - Exit and save session")
        print("="*60)
        
        while True:
            try:
                if not self.autonomous_mode:
                    user_input = input("\nYou: ").strip()
                    
                    if not user_input:
                        continue
                    
                    if user_input.lower() == 'quit':
                        self._end_session()
                        break
                    elif user_input.lower() == 'autonomous':
                        self._start_autonomous_mode()
                        continue
                    elif user_input.lower() == 'memory':
                        self._show_memory_summary()
                        continue
                    elif user_input.lower() == 'goals':
                        self._show_goals()
                        continue
                    elif user_input.lower() == 'users':
                        self._show_users()
                        continue
                    elif user_input.lower() == 'user stats':
                        self._show_user_stats()
                        continue
                    else:
                        self.conversation_round(user_input)
                
                else:
                    # Autonomous mode
                    if not self.conversation_round(autonomous=True):
                        self.autonomous_mode = False
                        self.autonomous_rounds = 0
                        print("\nAutonomous mode ended. You can continue the conversation.")
                    else:
                        # Brief pause between autonomous rounds
                        time.sleep(2)
                        
                        # Check for user interrupt
                        print("\n(Type 'stop' to end autonomous mode)")
                        # In a real implementation, you'd want non-blocking input here
                
            except KeyboardInterrupt:
                if self.autonomous_mode:
                    print("\n\nStopping autonomous mode...")
                    self.autonomous_mode = False
                    self.autonomous_rounds = 0
                else:
                    self._end_session()
                    break
            except Exception as e:
                print(f"\nError: {e}")
                continue
    
    def _start_autonomous_mode(self):
        """Start autonomous AI-to-AI conversation"""
        self.autonomous_mode = True
        self.autonomous_rounds = 0
        print(f"\n[STARTING AUTONOMOUS MODE - {self.max_autonomous_rounds} rounds maximum]")
        print("The AIs will now continue the conversation independently...")
        print("Press Ctrl+C to stop autonomous mode at any time.\n")
    
    def _show_memory_summary(self):
        """Display memory summary"""
        print("\n" + "="*40)
        print("MEMORY SUMMARY")
        print("="*40)
        print(f"Total sessions: {len(self.memory.conversations)}")
        print(f"Current session messages: {len(self.memory.current_session)}")
        print(f"Goals: {len(self.memory.goals)}")
        print(f"Important facts: {len(self.memory.important_facts)}")
        print(f"Context: {self.memory.context_summary}")
        print("="*40)
    
    def _show_goals(self):
        """Display current goals"""
        print("\n" + "="*40)
        print("CURRENT GOALS")
        print("="*40)
        if self.memory.goals:
            for i, goal in enumerate(self.memory.goals, 1):
                print(f"{i}. {goal['goal']} (by {goal['speaker']})")
        else:
            print("No goals set yet.")
        print("="*40)
    
    def _show_users(self):
        """Display user information"""
        print("\n" + "="*50)
        print("USER INFORMATION")
        print("="*50)
        
        all_users = self.user_manager.get_all_display_users()
        for user_info in all_users:
            status_emoji = "🟢" if user_info['is_active'] else "🔴"
            print(f"{status_emoji} {user_info['display_name']} ({user_info['user_type']})")
            print(f"   Status: {user_info['status']}")
            if user_info['is_active']:
                active_user = self.user_manager.get_active_user(user_info['user_id'])
                if active_user:
                    stats = active_user.get_stats()
                    print(f"   Messages: {stats['message_count']}")
                    print(f"   Rate limit remaining: {stats['rate_limit_remaining']}")
            print()
        
        print("="*50)
    
    def _show_user_stats(self):
        """Display user management statistics"""
        print("\n" + "="*40)
        print("USER STATISTICS")
        print("="*40)
        
        stats = self.user_manager.get_statistics()
        print(f"Total users: {stats['total_users']}")
        print(f"Active users: {stats['active_users']}")
        print(f"Default users: {stats['default_users']}")
        print(f"Custom users: {stats['custom_users']}")
        print(f"Memory efficiency: {stats['memory_efficiency']}")
        
        print("\nUser types:")
        for user_type, count in stats['user_types'].items():
            print(f"  {user_type}: {count}")
        
        print("="*40)
    
    def _end_session(self):
        """End session and save everything"""
        print("\nEnding session and saving memory...")
        self.memory.end_session()
        print(f"Session saved. Total conversations: {len(self.memory.conversations)}")
        print(f"Working directory: {os.getcwd()}")

# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================
def main():
    """Main entry point"""
    try:
        # Ensure we're in the right directory
        os.chdir(WORKSPACE_PATH)
        
        chat = EnhancedAGIChat()
        chat.run()
        
    except Exception as e:
        print(f"Failed to start enhanced chat: {e}")
        print("Make sure Ollama is running and Claude CLI is installed.")

if __name__ == "__main__":
    main()