"""
Shared interfaces for AI coordination and communication
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
import json
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AIInterface(ABC):
    """Abstract interface for AI agents"""
    
    def __init__(self, name: str, capabilities: List[str]):
        self.name = name
        self.capabilities = capabilities
        self.task_history = []
        self.performance_metrics = {}
        self.is_available = True
        
    @abstractmethod
    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task and return results"""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, str]:
        """Get current status of the AI agent"""
        pass
    
    def can_handle_task(self, task_type: str) -> bool:
        """Check if this AI can handle the specified task type"""
        return task_type in self.capabilities
    
    def get_load_factor(self) -> float:
        """Get current load factor (0.0 to 1.0)"""
        # Simple load calculation based on recent tasks
        recent_tasks = [t for t in self.task_history 
                       if (datetime.now() - datetime.fromisoformat(t['timestamp'])).seconds < 3600]
        return min(len(recent_tasks) / 10.0, 1.0)
    
    def add_task_to_history(self, task: Dict[str, Any], result: Dict[str, Any]):
        """Add completed task to history"""
        self.task_history.append({
            'task': task,
            'result': result,
            'timestamp': datetime.now().isoformat(),
            'duration': result.get('processing_time', 0)
        })
        
        # Keep only last 100 tasks
        if len(self.task_history) > 100:
            self.task_history = self.task_history[-100:]

class TaskCoordinator:
    """Coordinates tasks between different AI agents"""
    
    def __init__(self):
        self.agents = {}  # name -> AIInterface
        self.task_queue = []
        self.active_tasks = {}
        self.completed_tasks = []
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def register_agent(self, agent: AIInterface):
        """Register an AI agent with the coordinator"""
        self.agents[agent.name] = agent
        
    def submit_task(self, task: Dict[str, Any]) -> str:
        """Submit a task for processing"""
        task_id = f"task_{len(self.task_queue)}_{datetime.now().timestamp()}"
        
        task_wrapper = {
            'id': task_id,
            'task': task,
            'priority': TaskPriority(task.get('priority', 2)),
            'status': TaskStatus.PENDING,
            'submitted_at': datetime.now().isoformat(),
            'assigned_agent': None,
            'retries': 0,
            'max_retries': task.get('max_retries', 3)
        }
        
        self.task_queue.append(task_wrapper)
        self._schedule_task(task_wrapper)
        
        return task_id
    
    def _schedule_task(self, task_wrapper: Dict[str, Any]):
        """Schedule a task to the most appropriate agent"""
        task = task_wrapper['task']
        task_type = task.get('type', 'general')
        
        # Find capable agents
        capable_agents = [agent for agent in self.agents.values() 
                         if agent.can_handle_task(task_type) and agent.is_available]
        
        if not capable_agents:
            print(f"No capable agents for task type: {task_type}")
            task_wrapper['status'] = TaskStatus.FAILED
            return
        
        # Select agent with lowest load
        selected_agent = min(capable_agents, key=lambda a: a.get_load_factor())
        
        task_wrapper['assigned_agent'] = selected_agent.name
        task_wrapper['status'] = TaskStatus.IN_PROGRESS
        self.active_tasks[task_wrapper['id']] = task_wrapper
        
        # Execute task asynchronously
        future = self.executor.submit(self._execute_task, task_wrapper, selected_agent)
        future.add_done_callback(lambda f: self._handle_task_completion(task_wrapper['id'], f))
    
    def _execute_task(self, task_wrapper: Dict[str, Any], agent: AIInterface) -> Dict[str, Any]:
        """Execute a task with the assigned agent"""
        start_time = datetime.now()
        
        try:
            result = agent.process_task(task_wrapper['task'])
            result['processing_time'] = (datetime.now() - start_time).total_seconds()
            result['success'] = True
            
            # Add to agent's history
            agent.add_task_to_history(task_wrapper['task'], result)
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processing_time': (datetime.now() - start_time).total_seconds()
            }
    
    def _handle_task_completion(self, task_id: str, future):
        """Handle task completion"""
        if task_id not in self.active_tasks:
            return
            
        task_wrapper = self.active_tasks[task_id]
        
        try:
            result = future.result()
            
            if result['success']:
                task_wrapper['status'] = TaskStatus.COMPLETED
                task_wrapper['result'] = result
                task_wrapper['completed_at'] = datetime.now().isoformat()
            else:
                # Retry if possible
                if task_wrapper['retries'] < task_wrapper['max_retries']:
                    task_wrapper['retries'] += 1
                    task_wrapper['status'] = TaskStatus.PENDING
                    self._schedule_task(task_wrapper)
                    return
                else:
                    task_wrapper['status'] = TaskStatus.FAILED
                    task_wrapper['error'] = result.get('error', 'Unknown error')
                    
        except Exception as e:
            task_wrapper['status'] = TaskStatus.FAILED
            task_wrapper['error'] = str(e)
        
        # Move to completed tasks
        self.completed_tasks.append(self.active_tasks.pop(task_id))
        
        # Keep only last 1000 completed tasks
        if len(self.completed_tasks) > 1000:
            self.completed_tasks = self.completed_tasks[-1000:]
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task"""
        # Check active tasks
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]
        
        # Check completed tasks
        for task in self.completed_tasks:
            if task['id'] == task_id:
                return task
        
        # Check pending tasks
        for task in self.task_queue:
            if task['id'] == task_id:
                return task
        
        return None
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            'agents': {name: agent.get_status() for name, agent in self.agents.items()},
            'queued_tasks': len(self.task_queue),
            'active_tasks': len(self.active_tasks),
            'completed_tasks': len(self.completed_tasks),
            'system_load': sum(agent.get_load_factor() for agent in self.agents.values()) / len(self.agents) if self.agents else 0
        }
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or active task"""
        # Check pending tasks
        for i, task in enumerate(self.task_queue):
            if task['id'] == task_id:
                task['status'] = TaskStatus.CANCELLED
                self.task_queue.pop(i)
                self.completed_tasks.append(task)
                return True
        
        # Check active tasks (can't cancel running tasks in this simple implementation)
        if task_id in self.active_tasks:
            # In a more sophisticated implementation, we would signal the task to stop
            print(f"Cannot cancel active task {task_id} - task is already running")
            return False
        
        return False
    
    def get_agent_performance(self, agent_name: str) -> Dict[str, Any]:
        """Get performance metrics for a specific agent"""
        if agent_name not in self.agents:
            return {}
        
        agent = self.agents[agent_name]
        
        if not agent.task_history:
            return {'tasks_completed': 0}
        
        total_tasks = len(agent.task_history)
        total_time = sum(task['duration'] for task in agent.task_history)
        avg_time = total_time / total_tasks if total_tasks > 0 else 0
        
        recent_tasks = [t for t in agent.task_history 
                       if (datetime.now() - datetime.fromisoformat(t['timestamp'])).seconds < 3600]
        
        return {
            'tasks_completed': total_tasks,
            'average_processing_time': avg_time,
            'recent_tasks_count': len(recent_tasks),
            'current_load': agent.get_load_factor(),
            'is_available': agent.is_available
        }

class CollaborativeTask:
    """Represents a task that requires collaboration between multiple AIs"""
    
    def __init__(self, task_id: str, description: str, participants: List[str]):
        self.id = task_id
        self.description = description
        self.participants = participants
        self.phases = []
        self.current_phase = 0
        self.status = TaskStatus.PENDING
        self.results = {}
        self.created_at = datetime.now().isoformat()
    
    def add_phase(self, phase_name: str, assigned_agent: str, 
                  inputs: Dict[str, Any], dependencies: List[str] = None):
        """Add a phase to the collaborative task"""
        phase = {
            'name': phase_name,
            'assigned_agent': assigned_agent,
            'inputs': inputs,
            'dependencies': dependencies or [],
            'status': TaskStatus.PENDING,
            'result': None
        }
        self.phases.append(phase)
    
    def can_execute_phase(self, phase_index: int) -> bool:
        """Check if a phase can be executed (dependencies completed)"""
        if phase_index >= len(self.phases):
            return False
        
        phase = self.phases[phase_index]
        
        # Check if all dependencies are completed
        for dep in phase['dependencies']:
            dep_phase = next((p for p in self.phases if p['name'] == dep), None)
            if not dep_phase or dep_phase['status'] != TaskStatus.COMPLETED:
                return False
        
        return True
    
    def get_next_executable_phases(self) -> List[int]:
        """Get list of phases that can be executed"""
        executable = []
        for i, phase in enumerate(self.phases):
            if phase['status'] == TaskStatus.PENDING and self.can_execute_phase(i):
                executable.append(i)
        return executable
    
    def complete_phase(self, phase_index: int, result: Dict[str, Any]):
        """Mark a phase as completed with results"""
        if phase_index < len(self.phases):
            self.phases[phase_index]['status'] = TaskStatus.COMPLETED
            self.phases[phase_index]['result'] = result
            self.results[self.phases[phase_index]['name']] = result
    
    def is_complete(self) -> bool:
        """Check if all phases are completed"""
        return all(phase['status'] == TaskStatus.COMPLETED for phase in self.phases)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary representation"""
        return {
            'id': self.id,
            'description': self.description,
            'participants': self.participants,
            'phases': self.phases,
            'current_phase': self.current_phase,
            'status': self.status.value,
            'results': self.results,
            'created_at': self.created_at,
            'is_complete': self.is_complete()
        }