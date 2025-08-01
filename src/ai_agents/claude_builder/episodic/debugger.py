"""
Debugger - Claude's debugging and error resolution capabilities
"""

from typing import Dict, Any, List, Optional, Tuple, Callable
import traceback
import re
from datetime import datetime

class Debugger:
    """Handles debugging and error resolution tasks"""
    
    def __init__(self, claude_interface: Callable[[str], str]) -> None:
        self.claude = claude_interface
        self.debug_history: List[Dict[str, Any]] = []
        self.known_patterns: Dict[str, str] = {
            'syntax_error': r'SyntaxError: (.+)',
            'name_error': r'NameError: name \'(.+)\' is not defined',
            'type_error': r'TypeError: (.+)',
            'value_error': r'ValueError: (.+)',
            'index_error': r'IndexError: (.+)',
            'key_error': r'KeyError: (.+)',
            'attribute_error': r'AttributeError: (.+)',
            'import_error': r'ImportError: (.+)',
        }
        
    def debug_error(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Debug an error and provide solution"""
        error_message = error_info.get('error', '')
        code_context = error_info.get('code', '')
        stack_trace = error_info.get('stack_trace', '')
        
        # Identify error type
        error_type = self._identify_error_type(error_message)
        
        prompt = f"""Debug this error:
        
        Error Type: {error_type}
        Error Message: {error_message}
        
        Stack Trace:
        {stack_trace}
        
        Code Context:
        ```
        {code_context}
        ```
        
        Provide:
        1. Root cause analysis
        2. Step-by-step fix
        3. Corrected code
        4. Prevention tips"""
        
        solution = self.claude(prompt)
        
        result = {
            'error_type': error_type,
            'original_error': error_message,
            'solution': solution,
            'timestamp': datetime.now().isoformat()
        }
        
        self.debug_history.append(result)
        return result
    
    def analyze_performance_issue(self, code: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze and fix performance issues"""
        prompt = f"""Analyze performance issues in this code:
        
        Code:
        ```
        {code}
        ```
        
        Performance Metrics:
        - Execution Time: {metrics.get('execution_time', 'Unknown')}
        - Memory Usage: {metrics.get('memory_usage', 'Unknown')}
        - CPU Usage: {metrics.get('cpu_usage', 'Unknown')}
        - Bottlenecks: {metrics.get('bottlenecks', [])}
        
        Provide:
        1. Performance analysis
        2. Identified issues
        3. Optimized code
        4. Expected improvements"""
        
        analysis = self.claude(prompt)
        
        return {
            'original_metrics': metrics,
            'analysis': analysis,
            'optimization_applied': True,
            'timestamp': datetime.now().isoformat()
        }
    
    def fix_code_smell(self, code: str, smell_type: str) -> str:
        """Fix specific code smells"""
        prompt = f"""Fix the {smell_type} code smell in this code:
        
        ```
        {code}
        ```
        
        Common issues for {smell_type}:
        - Long methods
        - Duplicate code
        - Large classes
        - Long parameter lists
        - Divergent change
        - Feature envy
        
        Refactor to eliminate the smell while maintaining functionality."""
        
        result: str = self.claude(prompt)
        return result
    
    def debug_logic_error(self, code: str, expected_behavior: str, 
                         actual_behavior: str) -> Dict[str, Any]:
        """Debug logical errors in code"""
        prompt = f"""Debug this logic error:
        
        Code:
        ```
        {code}
        ```
        
        Expected Behavior: {expected_behavior}
        Actual Behavior: {actual_behavior}
        
        Identify:
        1. Logic flaws
        2. Edge cases not handled
        3. Incorrect assumptions
        4. Fixed implementation"""
        
        solution = self.claude(prompt)
        
        return {
            'issue': 'Logic Error',
            'expected': expected_behavior,
            'actual': actual_behavior,
            'solution': solution,
            'timestamp': datetime.now().isoformat()
        }
    
    def analyze_memory_leak(self, code: str, symptoms: List[str]) -> Dict[str, Any]:
        """Analyze and fix memory leaks"""
        prompt = f"""Analyze potential memory leaks:
        
        Code:
        ```
        {code}
        ```
        
        Symptoms:
        {chr(10).join(f'- {symptom}' for symptom in symptoms)}
        
        Check for:
        1. Circular references
        2. Unclosed resources
        3. Growing collections
        4. Event listener leaks
        5. Cache without limits
        
        Provide fixes and best practices."""
        
        analysis = self.claude(prompt)
        
        return {
            'symptoms': symptoms,
            'analysis': analysis,
            'fixes_suggested': True,
            'timestamp': datetime.now().isoformat()
        }
    
    def suggest_error_handling(self, code: str) -> str:
        """Suggest comprehensive error handling"""
        prompt = f"""Add comprehensive error handling to this code:
        
        ```
        {code}
        ```
        
        Include:
        1. Try-catch blocks where appropriate
        2. Input validation
        3. Graceful degradation
        4. Meaningful error messages
        5. Logging for debugging
        6. Recovery mechanisms"""
        
        result: str = self.claude(prompt)
        return result
    
    def _identify_error_type(self, error_message: str) -> str:
        """Identify the type of error from message"""
        for error_type, pattern in self.known_patterns.items():
            if re.search(pattern, error_message):
                return error_type
        return 'unknown_error'
    
    def generate_debug_plan(self, problem_description: str) -> List[str]:
        """Generate a debugging plan for a problem"""
        prompt = f"""Create a systematic debugging plan for:
        
        Problem: {problem_description}
        
        Generate step-by-step debugging approach including:
        1. Information gathering steps
        2. Hypothesis formation
        3. Testing procedures
        4. Tools to use
        5. Common pitfalls to avoid"""
        
        plan = self.claude(prompt)
        
        # Parse plan into steps
        steps = [step.strip() for step in plan.split('\n') if step.strip()]
        return steps
    
    def analyze_crash_dump(self, dump_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze crash dump or core dump"""
        prompt = f"""Analyze this crash dump:
        
        Error: {dump_info.get('error', 'Unknown')}
        Last Known State: {dump_info.get('state', {})}
        Call Stack: {dump_info.get('call_stack', [])}
        Variables: {dump_info.get('variables', {})}
        
        Determine:
        1. Root cause
        2. Sequence of events
        3. Fix recommendation
        4. Prevention measures"""
        
        analysis = self.claude(prompt)
        
        return {
            'crash_analysis': analysis,
            'severity': self._assess_severity(dump_info),
            'recovery_possible': True,
            'timestamp': datetime.now().isoformat()
        }
    
    def _assess_severity(self, dump_info: Dict[str, Any]) -> str:
        """Assess severity of crash"""
        error = dump_info.get('error', '').lower()
        if any(critical in error for critical in ['segmentation', 'corruption', 'overflow']):
            return 'critical'
        elif any(high in error for high in ['null', 'undefined', 'type']):
            return 'high'
        else:
            return 'medium'