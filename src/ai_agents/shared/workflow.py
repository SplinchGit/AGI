"""
Workflow orchestration and task management for AI agents
"""

from typing import Dict, Any, List, Optional, Callable
from enum import Enum
import json
from datetime import datetime, timedelta
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid

class WorkflowStatus(Enum):
    CREATED = "created"
    RUNNING = "running" 
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class WorkflowTask:
    """Represents a single task in a workflow"""
    
    def __init__(self, task_id: str, name: str, task_type: str, 
                 assigned_agent: str, inputs: Dict[str, Any],
                 dependencies: List[str] = None):
        self.id = task_id
        self.name = name
        self.task_type = task_type
        self.assigned_agent = assigned_agent
        self.inputs = inputs
        self.dependencies = dependencies or []
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None
        self.retry_count = 0
        self.max_retries = 3
    
    def start(self):
        """Mark task as started"""
        self.status = TaskStatus.RUNNING
        self.start_time = datetime.now()
    
    def complete(self, result: Any):
        """Mark task as completed"""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.end_time = datetime.now()
    
    def fail(self, error: str):
        """Mark task as failed"""
        self.status = TaskStatus.FAILED
        self.error = error
        self.end_time = datetime.now()
    
    def skip(self, reason: str):
        """Mark task as skipped"""
        self.status = TaskStatus.SKIPPED
        self.error = f"Skipped: {reason}"
        self.end_time = datetime.now()
    
    def can_retry(self) -> bool:
        """Check if task can be retried"""
        return self.retry_count < self.max_retries and self.status == TaskStatus.FAILED
    
    def retry(self):
        """Reset task for retry"""
        if self.can_retry():
            self.retry_count += 1
            self.status = TaskStatus.PENDING
            self.error = None
            self.start_time = None
            self.end_time = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'task_type': self.task_type,
            'assigned_agent': self.assigned_agent,
            'inputs': self.inputs,
            'dependencies': self.dependencies,
            'status': self.status.value,
            'result': self.result,
            'error': self.error,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }

class Workflow:
    """Represents a workflow of interconnected tasks"""
    
    def __init__(self, workflow_id: str, name: str, description: str = ""):
        self.id = workflow_id
        self.name = name
        self.description = description
        self.tasks = {}  # task_id -> WorkflowTask
        self.status = WorkflowStatus.CREATED
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.metadata = {}
        
        # Execution tracking
        self.execution_log = []
        self.task_results = {}
    
    def add_task(self, task: WorkflowTask):
        """Add a task to the workflow"""
        self.tasks[task.id] = task
    
    def remove_task(self, task_id: str):
        """Remove a task from the workflow"""
        if task_id in self.tasks:
            # Remove dependencies on this task from other tasks
            for other_task in self.tasks.values():
                if task_id in other_task.dependencies:
                    other_task.dependencies.remove(task_id)
            
            del self.tasks[task_id]
    
    def get_ready_tasks(self) -> List[WorkflowTask]:
        """Get tasks that are ready to execute (dependencies completed)"""
        ready_tasks = []
        
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING:
                # Check if all dependencies are completed
                dependencies_met = all(
                    self.tasks[dep_id].status == TaskStatus.COMPLETED
                    for dep_id in task.dependencies
                    if dep_id in self.tasks
                )
                
                if dependencies_met:
                    ready_tasks.append(task)
        
        return ready_tasks
    
    def get_failed_tasks(self) -> List[WorkflowTask]:
        """Get tasks that have failed"""
        return [task for task in self.tasks.values() if task.status == TaskStatus.FAILED]
    
    def get_completed_tasks(self) -> List[WorkflowTask]:
        """Get completed tasks"""
        return [task for task in self.tasks.values() if task.status == TaskStatus.COMPLETED]
    
    def is_complete(self) -> bool:
        """Check if workflow is complete"""
        if not self.tasks:
            return True
        
        return all(
            task.status in [TaskStatus.COMPLETED, TaskStatus.SKIPPED]
            for task in self.tasks.values()
        )
    
    def has_failed(self) -> bool:
        """Check if workflow has failed (unrecoverable failures)"""
        return any(
            task.status == TaskStatus.FAILED and not task.can_retry()
            for task in self.tasks.values()
        )
    
    def get_progress(self) -> float:
        """Get workflow progress as percentage"""
        if not self.tasks:
            return 100.0
        
        completed_count = len([
            task for task in self.tasks.values()
            if task.status in [TaskStatus.COMPLETED, TaskStatus.SKIPPED]
        ])
        
        return (completed_count / len(self.tasks)) * 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'progress': self.get_progress(),
            'task_count': len(self.tasks),
            'completed_tasks': len(self.get_completed_tasks()),
            'failed_tasks': len(self.get_failed_tasks()),
            'tasks': {task_id: task.to_dict() for task_id, task in self.tasks.items()},
            'metadata': self.metadata
        }

class WorkflowEngine:
    """Orchestrates workflow execution"""
    
    def __init__(self, task_coordinator=None):
        self.workflows = {}  # workflow_id -> Workflow
        self.task_coordinator = task_coordinator
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.running_workflows = set()
        self.lock = threading.RLock()
        
        # Event handlers
        self.event_handlers = {
            'workflow_started': [],
            'workflow_completed': [],
            'workflow_failed': [],
            'task_started': [],
            'task_completed': [],
            'task_failed': []
        }
    
    def create_workflow(self, name: str, description: str = "") -> str:
        """Create a new workflow"""
        workflow_id = str(uuid.uuid4())
        workflow = Workflow(workflow_id, name, description)
        
        with self.lock:
            self.workflows[workflow_id] = workflow
        
        return workflow_id
    
    def add_task_to_workflow(self, workflow_id: str, task_name: str, task_type: str,
                           assigned_agent: str, inputs: Dict[str, Any],
                           dependencies: List[str] = None) -> str:
        """Add a task to a workflow"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        task_id = f"{workflow_id}_{len(self.workflows[workflow_id].tasks)}"
        task = WorkflowTask(task_id, task_name, task_type, assigned_agent, inputs, dependencies)
        
        with self.lock:
            self.workflows[workflow_id].add_task(task)
        
        return task_id
    
    def start_workflow(self, workflow_id: str) -> bool:
        """Start workflow execution"""
        if workflow_id not in self.workflows:
            return False
        
        workflow = self.workflows[workflow_id]
        
        if workflow.status != WorkflowStatus.CREATED:
            return False
        
        with self.lock:
            workflow.status = WorkflowStatus.RUNNING
            workflow.started_at = datetime.now()
            self.running_workflows.add(workflow_id)
        
        # Emit workflow started event
        self._emit_event('workflow_started', {'workflow_id': workflow_id})
        
        # Start execution in background
        self.executor.submit(self._execute_workflow, workflow_id)
        
        return True
    
    def pause_workflow(self, workflow_id: str) -> bool:
        """Pause workflow execution"""
        if workflow_id not in self.workflows:
            return False
        
        workflow = self.workflows[workflow_id]
        
        if workflow.status == WorkflowStatus.RUNNING:
            with self.lock:
                workflow.status = WorkflowStatus.PAUSED
            return True
        
        return False
    
    def resume_workflow(self, workflow_id: str) -> bool:
        """Resume paused workflow"""
        if workflow_id not in self.workflows:
            return False
        
        workflow = self.workflows[workflow_id]
        
        if workflow.status == WorkflowStatus.PAUSED:
            with self.lock:
                workflow.status = WorkflowStatus.RUNNING
            
            # Resume execution
            self.executor.submit(self._execute_workflow, workflow_id)
            return True
        
        return False
    
    def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel workflow execution"""
        if workflow_id not in self.workflows:
            return False
        
        workflow = self.workflows[workflow_id]
        
        with self.lock:
            workflow.status = WorkflowStatus.CANCELLED
            self.running_workflows.discard(workflow_id)
        
        return True
    
    def _execute_workflow(self, workflow_id: str):
        """Execute workflow tasks"""
        workflow = self.workflows[workflow_id]
        
        try:
            while workflow.status == WorkflowStatus.RUNNING:
                ready_tasks = workflow.get_ready_tasks()
                
                if not ready_tasks:
                    # Check if workflow is complete
                    if workflow.is_complete():
                        self._complete_workflow(workflow_id)
                        break
                    elif workflow.has_failed():
                        self._fail_workflow(workflow_id, "Workflow has unrecoverable failures")
                        break
                    else:
                        # Wait for tasks to complete
                        threading.Event().wait(1)
                        continue
                
                # Execute ready tasks in parallel
                task_futures = []
                for task in ready_tasks:
                    future = self.executor.submit(self._execute_task, workflow_id, task.id)
                    task_futures.append((task.id, future))
                
                # Wait for at least one task to complete
                if task_futures:
                    for task_id, future in task_futures:
                        try:
                            future.result(timeout=1)  # Quick check
                        except:
                            pass  # Task still running or failed
                
        except Exception as e:
            self._fail_workflow(workflow_id, f"Workflow execution error: {str(e)}")
    
    def _execute_task(self, workflow_id: str, task_id: str):
        """Execute a single task"""
        workflow = self.workflows[workflow_id]
        task = workflow.tasks[task_id]
        
        try:
            task.start()
            self._emit_event('task_started', {
                'workflow_id': workflow_id,
                'task_id': task_id,
                'agent': task.assigned_agent
            })
            
            # Prepare task inputs
            task_inputs = task.inputs.copy()
            
            # Add results from dependency tasks
            for dep_id in task.dependencies:
                if dep_id in workflow.tasks:
                    dep_task = workflow.tasks[dep_id]
                    if dep_task.status == TaskStatus.COMPLETED:
                        task_inputs[f"dependency_{dep_id}"] = dep_task.result
            
            # Execute task
            if self.task_coordinator:
                # Use task coordinator if available
                submitted_task = {
                    'type': task.task_type,
                    'inputs': task_inputs,
                    'assigned_agent': task.assigned_agent
                }
                
                # This is a simplified example - would need proper async handling
                result = self._execute_with_coordinator(submitted_task)
            else:
                # Direct execution (placeholder)
                result = self._execute_direct(task)
            
            task.complete(result)
            workflow.task_results[task_id] = result
            
            self._emit_event('task_completed', {
                'workflow_id': workflow_id,
                'task_id': task_id,
                'result': result
            })
            
        except Exception as e:
            task.fail(str(e))
            
            self._emit_event('task_failed', {
                'workflow_id': workflow_id,
                'task_id': task_id,
                'error': str(e)
            })
            
            # Check if task can be retried
            if task.can_retry():
                task.retry()
                # Re-submit for execution
                self.executor.submit(self._execute_task, workflow_id, task_id)
    
    def _execute_with_coordinator(self, task: Dict[str, Any]) -> Any:
        """Execute task using task coordinator"""
        # Placeholder implementation
        return {"status": "completed", "message": "Task executed via coordinator"}
    
    def _execute_direct(self, task: WorkflowTask) -> Any:
        """Direct task execution (fallback)"""
        # Placeholder implementation
        return {"status": "completed", "message": f"Task {task.name} executed directly"}
    
    def _complete_workflow(self, workflow_id: str):
        """Mark workflow as completed"""
        workflow = self.workflows[workflow_id]
        
        with self.lock:
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.now()
            self.running_workflows.discard(workflow_id)
        
        self._emit_event('workflow_completed', {'workflow_id': workflow_id})
    
    def _fail_workflow(self, workflow_id: str, reason: str):
        """Mark workflow as failed"""
        workflow = self.workflows[workflow_id]
        
        with self.lock:
            workflow.status = WorkflowStatus.FAILED
            workflow.completed_at = datetime.now()
            workflow.metadata['failure_reason'] = reason
            self.running_workflows.discard(workflow_id)
        
        self._emit_event('workflow_failed', {
            'workflow_id': workflow_id,
            'reason': reason
        })
    
    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit workflow event"""
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                print(f"Error in event handler for {event_type}: {e}")
    
    def add_event_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], None]):
        """Add event handler"""
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow status"""
        if workflow_id not in self.workflows:
            return None
        
        return self.workflows[workflow_id].to_dict()
    
    def get_all_workflows(self) -> List[Dict[str, Any]]:
        """Get all workflows"""
        with self.lock:
            return [workflow.to_dict() for workflow in self.workflows.values()]
    
    def get_running_workflows(self) -> List[str]:
        """Get list of running workflow IDs"""
        with self.lock:
            return list(self.running_workflows)

class TaskOrchestrator:
    """High-level task orchestration with workflow templates"""
    
    def __init__(self, workflow_engine: WorkflowEngine):
        self.workflow_engine = workflow_engine
        self.templates = {}
        self.orchestration_history = []
    
    def register_template(self, template_name: str, template_definition: Dict[str, Any]):
        """Register a workflow template"""
        self.templates[template_name] = template_definition
    
    def create_workflow_from_template(self, template_name: str, 
                                    parameters: Dict[str, Any]) -> Optional[str]:
        """Create workflow from template"""
        if template_name not in self.templates:
            return None
        
        template = self.templates[template_name]
        
        # Create workflow
        workflow_id = self.workflow_engine.create_workflow(
            name=template['name'].format(**parameters),
            description=template.get('description', '').format(**parameters)
        )
        
        # Add tasks from template
        for task_def in template['tasks']:
            task_inputs = task_def['inputs'].copy()
            
            # Substitute parameters
            for key, value in task_inputs.items():
                if isinstance(value, str) and '{' in value:
                    task_inputs[key] = value.format(**parameters)
            
            self.workflow_engine.add_task_to_workflow(
                workflow_id=workflow_id,
                task_name=task_def['name'],
                task_type=task_def['type'],
                assigned_agent=task_def['agent'],
                inputs=task_inputs,
                dependencies=task_def.get('dependencies', [])
            )
        
        return workflow_id
    
    def orchestrate_collaboration(self, participants: List[str], objective: str,
                                phases: List[Dict[str, Any]]) -> str:
        """Orchestrate a collaboration between multiple agents"""
        workflow_id = self.workflow_engine.create_workflow(
            name=f"Collaboration: {objective}",
            description=f"Collaborative workflow with {len(participants)} participants"
        )
        
        previous_phase_tasks = []
        
        for i, phase in enumerate(phases):
            phase_tasks = []
            
            for participant in participants:
                if participant in phase.get('participants', participants):
                    task_id = self.workflow_engine.add_task_to_workflow(
                        workflow_id=workflow_id,
                        task_name=f"Phase {i+1}: {phase['name']} ({participant})",
                        task_type=phase.get('task_type', 'collaboration'),
                        assigned_agent=participant,
                        inputs={
                            'phase_name': phase['name'],
                            'phase_description': phase.get('description', ''),
                            'objective': objective,
                            'participants': participants,
                            **phase.get('inputs', {})
                        },
                        dependencies=previous_phase_tasks if i > 0 else []
                    )
                    phase_tasks.append(task_id)
            
            previous_phase_tasks = phase_tasks
        
        return workflow_id
    
    def get_orchestration_statistics(self) -> Dict[str, Any]:
        """Get orchestration statistics"""
        all_workflows = self.workflow_engine.get_all_workflows()
        
        total_workflows = len(all_workflows)
        completed_workflows = len([w for w in all_workflows if w['status'] == 'completed'])
        failed_workflows = len([w for w in all_workflows if w['status'] == 'failed'])
        running_workflows = len([w for w in all_workflows if w['status'] == 'running'])
        
        return {
            'total_workflows': total_workflows,
            'completed_workflows': completed_workflows,
            'failed_workflows': failed_workflows,
            'running_workflows': running_workflows,
            'success_rate': completed_workflows / total_workflows if total_workflows > 0 else 0,
            'template_count': len(self.templates)
        }