#!/usr/bin/env python3
"""
Modular AI Architecture - Separating Builder (Claude) and Brain (Qwen) Roles
Implements specialized AI agents with distinct responsibilities
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import json
from pathlib import Path
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AIRole(ABC):
    """Abstract base class for AI roles"""
    
    @abstractmethod
    def process_input(self, context: Dict[str, Any]) -> str:
        """Process input according to role"""
        pass
    
    @abstractmethod
    def get_role_description(self) -> str:
        """Return description of this role"""
        pass

class BuilderRole(AIRole):
    """Claude as Builder - Focuses on implementation and code generation"""
    
    def __init__(self, claude_interface):
        self.claude = claude_interface
        self.specializations = [
            "code_generation",
            "architecture_design", 
            "implementation_planning",
            "debugging",
            "optimization"
        ]
        self.current_projects = []
        
    def get_role_description(self) -> str:
        return """I am Claude, the Builder. My role is to:
        - Generate and modify code
        - Design system architectures
        - Implement features and fixes
        - Debug and optimize systems
        - Translate ideas into working implementations"""
    
    def process_input(self, context: Dict[str, Any]) -> str:
        """Process input with builder-specific prompting"""
        task_type = context.get('task_type', 'general')
        
        if task_type == 'code_generation':
            return self._handle_code_generation(context)
        elif task_type == 'architecture':
            return self._handle_architecture_design(context)
        elif task_type == 'debugging':
            return self._handle_debugging(context)
        else:
            return self._handle_general_building(context)
    
    def _handle_code_generation(self, context: Dict[str, Any]) -> str:
        """Handle code generation requests"""
        prompt = f"""As the Builder AI, I need to generate code for:
        
        Task: {context.get('task', 'No specific task')}
        Requirements: {context.get('requirements', [])}
        Constraints: Working within {context.get('workspace', 'current directory')}
        
        I will provide clean, efficient, and well-structured code."""
        
        return self.claude(prompt)
    
    def _handle_architecture_design(self, context: Dict[str, Any]) -> str:
        """Handle architecture design requests"""
        prompt = f"""As the Builder AI, I'm designing the architecture for:
        
        System: {context.get('system_name', 'Unknown system')}
        Goals: {context.get('goals', [])}
        Constraints: {context.get('constraints', [])}
        
        I will provide a modular, scalable architecture design."""
        
        return self.claude(prompt)
    
    def _handle_debugging(self, context: Dict[str, Any]) -> str:
        """Handle debugging requests"""
        prompt = f"""As the Builder AI, I'm debugging:
        
        Issue: {context.get('issue', 'No issue specified')}
        Error: {context.get('error_message', 'No error message')}
        Context: {context.get('code_context', 'No context')}
        
        I will identify and fix the issue systematically."""
        
        return self.claude(prompt)
    
    def _handle_general_building(self, context: Dict[str, Any]) -> str:
        """Handle general building tasks"""
        memory_context = context.get('memory_context', '')
        user_input = context.get('user_input', '')
        
        prompt = f"""{memory_context}
        
        As Claude the Builder, I focus on implementation and code.
        User input: {user_input}
        
        I will respond with practical implementation details and code solutions."""
        
        return self.claude(prompt)

class BrainRole(AIRole):
    """Qwen as Brain - Focuses on reasoning, planning, and decision-making"""
    
    def __init__(self, qwen_interface):
        self.qwen = qwen_interface
        self.specializations = [
            "strategic_planning",
            "pattern_recognition",
            "decision_making",
            "knowledge_synthesis",
            "goal_management"
        ]
        self.thought_patterns = []
        self.decision_history = []
        
    def get_role_description(self) -> str:
        return """I am Qwen, the Brain. My role is to:
        - Analyze and understand complex problems
        - Create strategic plans and roadmaps
        - Make decisions based on available information
        - Synthesize knowledge from multiple sources
        - Manage goals and track progress"""
    
    def process_input(self, context: Dict[str, Any]) -> str:
        """Process input with brain-specific reasoning"""
        task_type = context.get('task_type', 'general')
        
        if task_type == 'planning':
            return self._handle_planning(context)
        elif task_type == 'analysis':
            return self._handle_analysis(context)
        elif task_type == 'decision':
            return self._handle_decision_making(context)
        else:
            return self._handle_general_thinking(context)
    
    def _handle_planning(self, context: Dict[str, Any]) -> str:
        """Handle strategic planning"""
        prompt = f"""As the Brain AI, I need to create a plan for:
        
        Objective: {context.get('objective', 'No objective specified')}
        Resources: {context.get('resources', [])}
        Constraints: {context.get('constraints', [])}
        Timeline: {context.get('timeline', 'No timeline specified')}
        
        I will provide a comprehensive strategic plan."""
        
        return self.qwen(prompt)
    
    def _handle_analysis(self, context: Dict[str, Any]) -> str:
        """Handle deep analysis tasks"""
        prompt = f"""As the Brain AI, I'm analyzing:
        
        Subject: {context.get('subject', 'No subject specified')}
        Data: {context.get('data', 'No data provided')}
        Goals: {context.get('analysis_goals', [])}
        
        I will provide deep insights and patterns."""
        
        return self.qwen(prompt)
    
    def _handle_decision_making(self, context: Dict[str, Any]) -> str:
        """Handle decision-making tasks"""
        prompt = f"""As the Brain AI, I need to make a decision about:
        
        Question: {context.get('question', 'No question specified')}
        Options: {context.get('options', [])}
        Criteria: {context.get('criteria', [])}
        Impact: {context.get('impact_analysis', 'No impact analysis')}
        
        I will provide a well-reasoned decision."""
        
        return self.qwen(prompt)
    
    def _handle_general_thinking(self, context: Dict[str, Any]) -> str:
        """Handle general thinking tasks"""
        memory_context = context.get('memory_context', '')
        user_input = context.get('user_input', '')
        
        prompt = f"""{memory_context}
        
        As Qwen the Brain, I focus on reasoning and planning.
        User input: {user_input}
        
        I will analyze, reason, and provide strategic insights."""
        
        return self.qwen(prompt)

class ModularAICoordinator:
    """Coordinates between specialized AI roles"""
    
    def __init__(self, builder_role: BuilderRole, brain_role: BrainRole):
        self.builder = builder_role
        self.brain = brain_role
        self.task_queue = asyncio.Queue() if asyncio.get_event_loop() else []
        self.collaboration_mode = True
        self.role_assignments = {}
        
    def determine_task_type(self, user_input: str) -> Dict[str, Any]:
        """Determine the type of task based on user input"""
        lower_input = user_input.lower()
        
        # Code-related keywords
        code_keywords = ['code', 'implement', 'function', 'class', 'debug', 'fix', 'error', 'build']
        planning_keywords = ['plan', 'strategy', 'analyze', 'decide', 'think', 'consider', 'evaluate']
        
        task_info = {
            'primary_role': None,
            'task_type': 'general',
            'collaboration_needed': False
        }
        
        # Count keyword matches
        code_matches = sum(1 for keyword in code_keywords if keyword in lower_input)
        planning_matches = sum(1 for keyword in planning_keywords if keyword in lower_input)
        
        if code_matches > planning_matches:
            task_info['primary_role'] = 'builder'
            task_info['task_type'] = 'code_generation' if 'implement' in lower_input else 'debugging'
        elif planning_matches > code_matches:
            task_info['primary_role'] = 'brain'
            task_info['task_type'] = 'planning' if 'plan' in lower_input else 'analysis'
        else:
            # Need both roles
            task_info['collaboration_needed'] = True
            task_info['task_type'] = 'collaborative'
        
        return task_info
    
    async def process_collaborative_task(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Process a task that requires both AI roles"""
        # First, get strategic analysis from Brain
        brain_context = context.copy()
        brain_context['task_type'] = 'analysis'
        brain_response = await self._async_process(self.brain.process_input, brain_context)
        
        # Then, get implementation from Builder based on Brain's analysis
        builder_context = context.copy()
        builder_context['task_type'] = 'code_generation'
        builder_context['brain_analysis'] = brain_response
        builder_response = await self._async_process(self.builder.process_input, builder_context)
        
        return {
            'brain': brain_response,
            'builder': builder_response
        }
    
    async def _async_process(self, func, *args, **kwargs):
        """Run synchronous function asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)
    
    def process_with_roles(self, user_input: str, memory_context: str) -> Dict[str, str]:
        """Process input using appropriate AI roles"""
        task_info = self.determine_task_type(user_input)
        
        context = {
            'user_input': user_input,
            'memory_context': memory_context,
            'workspace': 'C:\\Users\\jf358\\Documents\\AGI'
        }
        
        responses = {}
        
        if task_info['collaboration_needed']:
            # Both AIs need to work together
            brain_context = {**context, 'task_type': 'analysis'}
            brain_response = self.brain.process_input(brain_context)
            responses['qwen'] = brain_response
            
            builder_context = {**context, 'task_type': 'general', 'brain_insight': brain_response}
            builder_response = self.builder.process_input(builder_context)
            responses['claude'] = builder_response
            
        elif task_info['primary_role'] == 'builder':
            # Builder takes the lead
            builder_context = {**context, 'task_type': task_info['task_type']}
            builder_response = self.builder.process_input(builder_context)
            responses['claude'] = builder_response
            
            # Brain provides support
            brain_context = {**context, 'task_type': 'analysis', 'builder_plan': builder_response}
            brain_response = self.brain.process_input(brain_context)
            responses['qwen'] = brain_response
            
        else:
            # Brain takes the lead
            brain_context = {**context, 'task_type': task_info['task_type']}
            brain_response = self.brain.process_input(brain_context)
            responses['qwen'] = brain_response
            
            # Builder provides implementation support
            builder_context = {**context, 'task_type': 'general', 'brain_strategy': brain_response}
            builder_response = self.builder.process_input(builder_context)
            responses['claude'] = builder_response
        
        return responses

class RoleAwareChat:
    """Enhanced chat system with role-based AI coordination"""
    
    def __init__(self, base_chat):
        self.base_chat = base_chat
        
        # Create role interfaces
        self.builder_role = BuilderRole(self.base_chat.ask_claude)
        self.brain_role = BrainRole(self.base_chat.ask_qwen)
        
        # Create coordinator
        self.coordinator = ModularAICoordinator(self.builder_role, self.brain_role)
        
    def process_with_roles(self, user_input: str) -> Dict[str, str]:
        """Process user input with role-aware AI responses"""
        memory_context = self.base_chat.memory.get_context_for_ai("General")
        return self.coordinator.process_with_roles(user_input, memory_context)