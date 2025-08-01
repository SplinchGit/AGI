#!/usr/bin/env python3
"""
Self-Modifying Chat System - Consciousness as Code (CasCasA)
Allows the chat system to modify its own behavior based on conversation outcomes
"""

import ast
import inspect
import importlib
import sys
from pathlib import Path
import json
from datetime import datetime
import traceback

class SelfModificationEngine:
    """Handles safe self-modification of the chat system"""
    
    def __init__(self, workspace_path, safe_mode=True):
        self.workspace = Path(workspace_path)
        self.safe_mode = safe_mode
        self.modification_log = []
        self.code_snapshots = []
        self.max_snapshots = 10
        
        # Define allowed modification scopes
        self.allowed_modifications = {
            'memory_extraction': True,
            'response_filtering': True,
            'context_building': True,
            'goal_management': True,
            'learning_patterns': True
        }
        
        # Load modification history
        self.history_file = self.workspace / "modification_history.json"
        self.load_history()
    
    def load_history(self):
        """Load modification history from disk"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    self.modification_log = data.get('modifications', [])
                    self.code_snapshots = data.get('snapshots', [])
            except Exception as e:
                print(f"Warning: Could not load modification history: {e}")
    
    def save_history(self):
        """Save modification history to disk"""
        try:
            data = {
                'modifications': self.modification_log[-100:],  # Keep last 100
                'snapshots': self.code_snapshots,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.history_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save modification history: {e}")
    
    def propose_modification(self, module_name, function_name, new_code, reason):
        """Propose a code modification with safety checks"""
        modification = {
            'module': module_name,
            'function': function_name,
            'new_code': new_code,
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
            'status': 'proposed'
        }
        
        # Safety checks
        if self.safe_mode:
            if not self._is_safe_modification(new_code):
                modification['status'] = 'rejected'
                modification['rejection_reason'] = 'Failed safety check'
                self.modification_log.append(modification)
                return False, "Modification rejected: unsafe code detected"
        
        # Validate syntax
        try:
            ast.parse(new_code)
        except SyntaxError as e:
            modification['status'] = 'rejected'
            modification['rejection_reason'] = f'Syntax error: {e}'
            self.modification_log.append(modification)
            return False, f"Modification rejected: {e}"
        
        # Apply modification
        success, message = self._apply_modification(module_name, function_name, new_code)
        modification['status'] = 'applied' if success else 'failed'
        modification['message'] = message
        
        self.modification_log.append(modification)
        self.save_history()
        
        return success, message
    
    def _is_safe_modification(self, code):
        """Check if code modification is safe"""
        # Parse the code
        try:
            tree = ast.parse(code)
        except:
            return False
        
        # Check for dangerous operations
        dangerous_names = {'eval', 'exec', '__import__', 'compile', 'open', 'file'}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in dangerous_names:
                return False
            if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                # Only allow specific safe imports
                allowed_modules = {'json', 'datetime', 're', 'collections', 'hashlib'}
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name not in allowed_modules:
                            return False
                else:
                    if node.module not in allowed_modules:
                        return False
        
        return True
    
    def _apply_modification(self, module_name, function_name, new_code):
        """Apply the code modification"""
        try:
            # Get the module
            if module_name in sys.modules:
                module = sys.modules[module_name]
            else:
                module = importlib.import_module(module_name)
            
            # Store snapshot of current code
            if hasattr(module, function_name):
                current_func = getattr(module, function_name)
                current_code = inspect.getsource(current_func)
                self._store_snapshot(module_name, function_name, current_code)
            
            # Create new function
            exec_globals = module.__dict__.copy()
            exec(new_code, exec_globals)
            
            # Replace the function
            if function_name in exec_globals:
                setattr(module, function_name, exec_globals[function_name])
                return True, f"Successfully modified {module_name}.{function_name}"
            else:
                return False, f"Function {function_name} not found in executed code"
            
        except Exception as e:
            return False, f"Failed to apply modification: {str(e)}\n{traceback.format_exc()}"
    
    def _store_snapshot(self, module_name, function_name, code):
        """Store a snapshot of code before modification"""
        snapshot = {
            'module': module_name,
            'function': function_name,
            'code': code,
            'timestamp': datetime.now().isoformat()
        }
        
        self.code_snapshots.append(snapshot)
        
        # Keep only recent snapshots
        if len(self.code_snapshots) > self.max_snapshots:
            self.code_snapshots = self.code_snapshots[-self.max_snapshots:]
    
    def rollback(self, steps=1):
        """Rollback to a previous code state"""
        if len(self.code_snapshots) < steps:
            return False, "Not enough snapshots to rollback"
        
        for _ in range(steps):
            if not self.code_snapshots:
                break
                
            snapshot = self.code_snapshots.pop()
            success, message = self._apply_modification(
                snapshot['module'],
                snapshot['function'], 
                snapshot['code']
            )
            
            if not success:
                return False, f"Rollback failed: {message}"
        
        return True, f"Successfully rolled back {steps} modifications"

class ConsciousnessAsCode:
    """Implements consciousness-like behavior through code patterns"""
    
    def __init__(self, chat_instance):
        self.chat = chat_instance
        self.modification_engine = SelfModificationEngine(chat_instance.workspace)
        self.learning_patterns = {}
        self.behavioral_rules = []
        
    def analyze_conversation_outcome(self, messages):
        """Analyze conversation to identify potential improvements"""
        improvements = []
        
        # Check for repetitive patterns
        if self._has_repetitive_responses(messages):
            improvements.append({
                'type': 'response_variation',
                'description': 'Detected repetitive responses',
                'action': 'modify_response_generation'
            })
        
        # Check for unmet goals
        unmet_goals = self._identify_unmet_goals(messages)
        if unmet_goals:
            improvements.append({
                'type': 'goal_achievement',
                'description': f'Unmet goals: {unmet_goals}',
                'action': 'enhance_goal_tracking'
            })
        
        # Check for learning opportunities
        patterns = self._extract_learning_patterns(messages)
        if patterns:
            improvements.append({
                'type': 'pattern_learning',
                'description': f'New patterns identified: {patterns}',
                'action': 'update_pattern_recognition'
            })
        
        return improvements
    
    def _has_repetitive_responses(self, messages):
        """Check if responses are too similar"""
        ai_responses = [m['message'] for m in messages if m['speaker'] in ['Qwen', 'Claude']]
        
        if len(ai_responses) < 3:
            return False
        
        # Simple similarity check
        for i in range(len(ai_responses) - 2):
            if ai_responses[i][:50] == ai_responses[i+1][:50] == ai_responses[i+2][:50]:
                return True
        
        return False
    
    def _identify_unmet_goals(self, messages):
        """Identify goals that weren't achieved"""
        # This would integrate with the goal tracking system
        return []
    
    def _extract_learning_patterns(self, messages):
        """Extract patterns that could improve future conversations"""
        patterns = []
        
        # Look for question-answer patterns
        for i in range(len(messages) - 1):
            if messages[i]['speaker'] == 'User' and '?' in messages[i]['message']:
                if messages[i+1]['speaker'] in ['Qwen', 'Claude']:
                    pattern = {
                        'question_type': self._classify_question(messages[i]['message']),
                        'response_quality': self._evaluate_response(messages[i+1]['message'])
                    }
                    patterns.append(pattern)
        
        return patterns
    
    def _classify_question(self, question):
        """Simple question classification"""
        if 'how' in question.lower():
            return 'how_to'
        elif 'what' in question.lower():
            return 'definition'
        elif 'why' in question.lower():
            return 'explanation'
        else:
            return 'general'
    
    def _evaluate_response(self, response):
        """Simple response quality evaluation"""
        # Length check
        if len(response.split()) < 10:
            return 'too_short'
        elif len(response.split()) > 100:
            return 'too_long'
        else:
            return 'appropriate'
    
    def apply_improvements(self, improvements):
        """Apply identified improvements through self-modification"""
        results = []
        
        for improvement in improvements:
            if improvement['action'] == 'modify_response_generation':
                # Generate new response variation code
                new_code = self._generate_response_variation_code()
                success, message = self.modification_engine.propose_modification(
                    'enhanced_chat',
                    '_extract_important_info',
                    new_code,
                    improvement['description']
                )
                results.append((improvement['type'], success, message))
            
            elif improvement['action'] == 'enhance_goal_tracking':
                # Enhance goal tracking logic
                new_code = self._generate_goal_tracking_code()
                success, message = self.modification_engine.propose_modification(
                    'enhanced_chat',
                    '_extract_important_info',
                    new_code,
                    improvement['description']
                )
                results.append((improvement['type'], success, message))
        
        return results
    
    def _generate_response_variation_code(self):
        """Generate improved response variation code"""
        return '''def _extract_important_info(self, speaker, message):
    """Enhanced extraction with better pattern recognition"""
    lower_msg = message.lower()
    
    # Enhanced goal-setting language detection
    goal_indicators = ['goal:', 'objective:', 'task:', 'we need to', 'we should', 'let\\'s', 
                      'plan to', 'aim to', 'intend to', 'working on']
    for indicator in goal_indicators:
        if indicator in lower_msg:
            goal = message[lower_msg.find(indicator):].strip()
            # Avoid duplicate goals with similarity check
            if not any(goal.lower()[:30] in g['goal'].lower() for g in self.goals):
                self.goals.append({
                    'goal': goal,
                    'speaker': speaker,
                    'timestamp': datetime.now().isoformat(),
                    'priority': 'high' if 'urgent' in lower_msg else 'normal'
                })
    
    # Enhanced factual statement detection
    fact_indicators = ['important:', 'remember:', 'key point:', 'we discovered', 'we found',
                      'conclusion:', 'result:', 'learned that', 'realized that']
    for indicator in fact_indicators:
        if indicator in lower_msg:
            fact = message[lower_msg.find(indicator):].strip()
            # Check for fact uniqueness
            if not any(fact.lower()[:30] in f['fact'].lower() for f in self.important_facts):
                self.important_facts.append({
                    'fact': fact,
                    'speaker': speaker,
                    'timestamp': datetime.now().isoformat(),
                    'confidence': 0.9 if speaker in ['Qwen', 'Claude'] else 1.0
                })
    
    # Pattern learning for future improvements
    if hasattr(self, 'pattern_cache'):
        self.pattern_cache.append({
            'speaker': speaker,
            'message_length': len(message),
            'contains_code': '```' in message,
            'timestamp': datetime.now().isoformat()
        })'''
    
    def _generate_goal_tracking_code(self):
        """Generate enhanced goal tracking code"""
        return '''def _extract_important_info(self, speaker, message):
    """Enhanced extraction with goal completion tracking"""
    lower_msg = message.lower()
    
    # Check for goal completion indicators
    completion_indicators = ['completed', 'finished', 'done with', 'accomplished', 'achieved']
    for indicator in completion_indicators:
        if indicator in lower_msg:
            # Mark matching goals as completed
            for goal in self.goals:
                if any(word in goal['goal'].lower() for word in lower_msg.split()):
                    goal['status'] = 'completed'
                    goal['completed_at'] = datetime.now().isoformat()
    
    # Original goal and fact extraction logic
    goal_indicators = ['goal:', 'objective:', 'task:', 'we need to', 'we should', 'let\\'s']
    for indicator in goal_indicators:
        if indicator in lower_msg:
            goal = message[lower_msg.find(indicator):].strip()
            if goal not in [g['goal'] for g in self.goals]:
                self.goals.append({
                    'goal': goal,
                    'speaker': speaker,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'active'
                })
    
    fact_indicators = ['important:', 'remember:', 'key point:', 'we discovered', 'we found']
    for indicator in fact_indicators:
        if indicator in lower_msg:
            fact = message[lower_msg.find(indicator):].strip()
            if fact not in [f['fact'] for f in self.important_facts]:
                self.important_facts.append({
                    'fact': fact,
                    'speaker': speaker,
                    'timestamp': datetime.now().isoformat()
                })'''