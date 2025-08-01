"""
Performance tracking and collaboration metrics for AI agents
"""

from typing import Dict, Any, List, Optional, Tuple
import time
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading
import statistics
import json

class PerformanceTracker:
    """Tracks performance metrics for AI agents and tasks"""
    
    def __init__(self):
        self.metrics = defaultdict(lambda: defaultdict(list))
        self.task_metrics = {}
        self.agent_metrics = defaultdict(lambda: defaultdict(list))
        self.system_metrics = defaultdict(list)
        self.lock = threading.RLock()
        
        # Metric retention settings
        self.max_metric_age_hours = 24
        self.max_metrics_per_category = 1000
    
    def record_task_start(self, task_id: str, agent_name: str, task_type: str) -> Dict[str, Any]:
        """Record task start and return tracking context"""
        with self.lock:
            context = {
                'task_id': task_id,
                'agent_name': agent_name,
                'task_type': task_type,
                'start_time': time.time(),
                'start_timestamp': datetime.now().isoformat()
            }
            
            self.task_metrics[task_id] = context
            return context
    
    def record_task_completion(self, task_id: str, success: bool = True, 
                             result_quality: Optional[float] = None,
                             additional_metrics: Optional[Dict[str, Any]] = None):
        """Record task completion with metrics"""
        with self.lock:
            if task_id not in self.task_metrics:
                return
            
            context = self.task_metrics[task_id]
            end_time = time.time()
            duration = end_time - context['start_time']
            
            # Update task metrics
            context.update({
                'end_time': end_time,
                'end_timestamp': datetime.now().isoformat(),
                'duration': duration,
                'success': success,
                'result_quality': result_quality,
                'additional_metrics': additional_metrics or {}
            })
            
            agent_name = context['agent_name']
            task_type = context['task_type']
            
            # Record agent-specific metrics
            self.agent_metrics[agent_name]['task_count'].append(1)
            self.agent_metrics[agent_name]['task_duration'].append(duration)
            self.agent_metrics[agent_name]['success_rate'].append(1 if success else 0)
            
            if result_quality is not None:
                self.agent_metrics[agent_name]['quality_score'].append(result_quality)
            
            # Record task type metrics
            self.metrics[task_type]['duration'].append(duration)
            self.metrics[task_type]['success_rate'].append(1 if success else 0)
            
            if result_quality is not None:
                self.metrics[task_type]['quality'].append(result_quality)
            
            # Record system-wide metrics
            self.system_metrics['task_duration'].append(duration)
            self.system_metrics['task_success'].append(1 if success else 0)
            
            # Cleanup old metrics
            self._cleanup_old_metrics()
    
    def record_metric(self, category: str, metric_name: str, value: float, 
                     agent_name: Optional[str] = None):
        """Record a custom metric"""
        with self.lock:
            timestamp = datetime.now()
            
            metric_entry = {
                'value': value,
                'timestamp': timestamp,
                'agent': agent_name
            }
            
            if agent_name:
                self.agent_metrics[agent_name][metric_name].append(value)
            else:
                self.metrics[category][metric_name].append(value)
            
            # Also add to system metrics for aggregation
            self.system_metrics[f"{category}_{metric_name}"].append(value)
            
            self._cleanup_old_metrics()
    
    def get_agent_performance_summary(self, agent_name: str) -> Dict[str, Any]:
        """Get performance summary for a specific agent"""
        with self.lock:
            if agent_name not in self.agent_metrics:
                return {}
            
            metrics = self.agent_metrics[agent_name]
            summary = {}
            
            # Calculate task performance
            if 'task_count' in metrics and metrics['task_count']:
                summary['total_tasks'] = sum(metrics['task_count'])
                
            if 'task_duration' in metrics and metrics['task_duration']:
                durations = metrics['task_duration']
                summary['avg_task_duration'] = statistics.mean(durations)
                summary['median_task_duration'] = statistics.median(durations)
                summary['min_task_duration'] = min(durations)
                summary['max_task_duration'] = max(durations)
                
            if 'success_rate' in metrics and metrics['success_rate']:
                success_rates = metrics['success_rate']
                summary['success_rate'] = statistics.mean(success_rates)
                summary['total_successful_tasks'] = sum(success_rates)
                
            if 'quality_score' in metrics and metrics['quality_score']:
                quality_scores = metrics['quality_score']
                summary['avg_quality_score'] = statistics.mean(quality_scores)
                summary['quality_trend'] = self._calculate_trend(quality_scores)
            
            # Calculate recent performance (last hour)
            recent_tasks = self._get_recent_tasks(agent_name, hours=1)
            if recent_tasks:
                summary['recent_task_count'] = len(recent_tasks)
                summary['recent_avg_duration'] = statistics.mean([t['duration'] for t in recent_tasks])
                summary['recent_success_rate'] = statistics.mean([t['success'] for t in recent_tasks])
            
            return summary
    
    def get_task_type_performance(self, task_type: str) -> Dict[str, Any]:
        """Get performance metrics for a specific task type"""
        with self.lock:
            if task_type not in self.metrics:
                return {}
            
            metrics = self.metrics[task_type]
            summary = {}
            
            if 'duration' in metrics and metrics['duration']:
                durations = metrics['duration']
                summary['avg_duration'] = statistics.mean(durations)
                summary['median_duration'] = statistics.median(durations)
                summary['duration_std'] = statistics.stdev(durations) if len(durations) > 1 else 0
                summary['duration_trend'] = self._calculate_trend(durations)
                
            if 'success_rate' in metrics and metrics['success_rate']:
                success_rates = metrics['success_rate']
                summary['success_rate'] = statistics.mean(success_rates)
                summary['total_attempts'] = len(success_rates)
                summary['successful_attempts'] = sum(success_rates)
                
            if 'quality' in metrics and metrics['quality']:
                quality_scores = metrics['quality']
                summary['avg_quality'] = statistics.mean(quality_scores)
                summary['quality_trend'] = self._calculate_trend(quality_scores)
            
            return summary
    
    def get_system_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get overall system performance summary"""
        with self.lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # Filter recent tasks
            recent_tasks = []
            for task_id, task_data in self.task_metrics.items():
                if 'end_timestamp' in task_data:
                    task_time = datetime.fromisoformat(task_data['end_timestamp'])
                    if task_time >= cutoff_time:
                        recent_tasks.append(task_data)
            
            if not recent_tasks:
                return {'message': 'No recent tasks found'}
            
            summary = {
                'time_period_hours': hours,
                'total_tasks': len(recent_tasks),
                'successful_tasks': sum(1 for t in recent_tasks if t.get('success', False)),
                'failed_tasks': sum(1 for t in recent_tasks if not t.get('success', True)),
            }
            
            # Calculate performance metrics
            durations = [t['duration'] for t in recent_tasks if 'duration' in t]
            if durations:
                summary['avg_task_duration'] = statistics.mean(durations)
                summary['median_task_duration'] = statistics.median(durations)
                summary['throughput_tasks_per_hour'] = len(recent_tasks) / hours
            
            # Success rate
            success_rates = [t.get('success', False) for t in recent_tasks]
            if success_rates:
                summary['overall_success_rate'] = statistics.mean(success_rates)
            
            # Agent distribution
            agent_counts = defaultdict(int)
            for task in recent_tasks:
                agent_counts[task.get('agent_name', 'unknown')] += 1
            summary['tasks_by_agent'] = dict(agent_counts)
            
            # Task type distribution
            type_counts = defaultdict(int)
            for task in recent_tasks:
                type_counts[task.get('task_type', 'unknown')] += 1
            summary['tasks_by_type'] = dict(type_counts)
            
            return summary
    
    def get_collaboration_efficiency(self, agent1: str, agent2: str) -> Dict[str, Any]:
        """Measure collaboration efficiency between two agents"""
        with self.lock:
            # Find tasks involving both agents
            collaborative_tasks = []
            
            for task_id, task_data in self.task_metrics.items():
                if 'collaboration_agents' in task_data:
                    if agent1 in task_data['collaboration_agents'] and agent2 in task_data['collaboration_agents']:
                        collaborative_tasks.append(task_data)
            
            if not collaborative_tasks:
                return {'collaborative_tasks': 0}
            
            # Calculate collaboration metrics
            total_duration = sum(task['duration'] for task in collaborative_tasks if 'duration' in task)
            avg_duration = total_duration / len(collaborative_tasks)
            
            success_rate = statistics.mean([task.get('success', False) for task in collaborative_tasks])
            
            return {
                'collaborative_tasks': len(collaborative_tasks),
                'avg_collaboration_duration': avg_duration,
                'collaboration_success_rate': success_rate,
                'total_collaboration_time': total_duration
            }
    
    def _get_recent_tasks(self, agent_name: str, hours: int = 1) -> List[Dict[str, Any]]:
        """Get recent tasks for an agent"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_tasks = []
        
        for task_id, task_data in self.task_metrics.items():
            if task_data.get('agent_name') == agent_name and 'end_timestamp' in task_data:
                task_time = datetime.fromisoformat(task_data['end_timestamp'])
                if task_time >= cutoff_time:
                    recent_tasks.append(task_data)
        
        return recent_tasks
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction for a list of values"""
        if len(values) < 2:
            return 'insufficient_data'
        
        # Simple trend calculation using first and last quartile averages
        n = len(values)
        first_quarter = values[:n//4] if n >= 4 else values[:1]
        last_quarter = values[-n//4:] if n >= 4 else values[-1:]
        
        first_avg = statistics.mean(first_quarter)
        last_avg = statistics.mean(last_quarter)
        
        if last_avg > first_avg * 1.05:
            return 'improving'
        elif last_avg < first_avg * 0.95:
            return 'declining'
        else:
            return 'stable'
    
    def _cleanup_old_metrics(self):
        """Remove old metrics to prevent memory bloat"""
        cutoff_time = datetime.now() - timedelta(hours=self.max_metric_age_hours)
        
        # Clean up task metrics
        old_task_ids = []
        for task_id, task_data in self.task_metrics.items():
            if 'end_timestamp' in task_data:
                task_time = datetime.fromisoformat(task_data['end_timestamp'])
                if task_time < cutoff_time:
                    old_task_ids.append(task_id)
        
        for task_id in old_task_ids:
            del self.task_metrics[task_id]
        
        # Clean up metric lists (keep only recent entries)
        for category in self.metrics:
            for metric_name in self.metrics[category]:
                if len(self.metrics[category][metric_name]) > self.max_metrics_per_category:
                    # Keep only the most recent entries
                    self.metrics[category][metric_name] = self.metrics[category][metric_name][-self.max_metrics_per_category:]
        
        # Clean up agent metrics
        for agent_name in self.agent_metrics:
            for metric_name in self.agent_metrics[agent_name]:
                if len(self.agent_metrics[agent_name][metric_name]) > self.max_metrics_per_category:
                    self.agent_metrics[agent_name][metric_name] = self.agent_metrics[agent_name][metric_name][-self.max_metrics_per_category:]

class CollaborationMetrics:
    """Tracks collaboration patterns and effectiveness between AI agents"""
    
    def __init__(self):
        self.collaboration_history = []
        self.interaction_patterns = defaultdict(lambda: defaultdict(int))
        self.communication_metrics = defaultdict(lambda: defaultdict(list))
        self.lock = threading.RLock()
    
    def record_collaboration(self, participants: List[str], task_type: str, 
                           duration: float, success: bool, quality_score: Optional[float] = None):
        """Record a collaboration event"""
        with self.lock:
            collaboration = {
                'participants': sorted(participants),
                'task_type': task_type,
                'duration': duration,
                'success': success,
                'quality_score': quality_score,
                'timestamp': datetime.now().isoformat(),
                'id': f"collab_{len(self.collaboration_history)}"
            }
            
            self.collaboration_history.append(collaboration)
            
            # Update interaction patterns
            for i, agent1 in enumerate(participants):
                for j, agent2 in enumerate(participants):
                    if i != j:
                        self.interaction_patterns[agent1][agent2] += 1
            
            # Update communication metrics
            for agent in participants:
                self.communication_metrics[agent]['collaborations'].append(collaboration)
    
    def record_communication_event(self, sender: str, recipient: str, 
                                 message_type: str, response_time: Optional[float] = None):
        """Record a communication event between agents"""
        with self.lock:
            event = {
                'sender': sender,
                'recipient': recipient,
                'message_type': message_type,
                'response_time': response_time,
                'timestamp': datetime.now().isoformat()
            }
            
            self.communication_metrics[sender]['messages_sent'].append(event)
            self.communication_metrics[recipient]['messages_received'].append(event)
            
            if response_time is not None:
                self.communication_metrics[recipient]['response_times'].append(response_time)
    
    def get_collaboration_summary(self) -> Dict[str, Any]:
        """Get overall collaboration summary"""
        with self.lock:
            if not self.collaboration_history:
                return {'total_collaborations': 0}
            
            total_collaborations = len(self.collaboration_history)
            successful_collaborations = sum(1 for c in self.collaboration_history if c['success'])
            
            durations = [c['duration'] for c in self.collaboration_history]
            avg_duration = statistics.mean(durations)
            
            quality_scores = [c['quality_score'] for c in self.collaboration_history 
                            if c['quality_score'] is not None]
            avg_quality = statistics.mean(quality_scores) if quality_scores else None
            
            # Most common collaboration pairs
            pair_counts = defaultdict(int)
            for collab in self.collaboration_history:
                participants = collab['participants']
                if len(participants) == 2:
                    pair = tuple(sorted(participants))
                    pair_counts[pair] += 1
            
            top_pairs = sorted(pair_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                'total_collaborations': total_collaborations,
                'successful_collaborations': successful_collaborations,
                'success_rate': successful_collaborations / total_collaborations,
                'avg_collaboration_duration': avg_duration,
                'avg_quality_score': avg_quality,
                'top_collaboration_pairs': top_pairs,
                'unique_participants': len(set().union(*[c['participants'] for c in self.collaboration_history]))
            }
    
    def get_agent_collaboration_profile(self, agent_name: str) -> Dict[str, Any]:
        """Get collaboration profile for a specific agent"""
        with self.lock:
            # Find collaborations involving this agent
            agent_collaborations = [c for c in self.collaboration_history 
                                  if agent_name in c['participants']]
            
            if not agent_collaborations:
                return {'collaborations': 0}
            
            # Calculate metrics
            total_collaborations = len(agent_collaborations)
            successful_collaborations = sum(1 for c in agent_collaborations if c['success'])
            
            # Collaboration partners
            partners = defaultdict(int)
            for collab in agent_collaborations:
                for participant in collab['participants']:
                    if participant != agent_name:
                        partners[participant] += 1
            
            # Average collaboration duration
            durations = [c['duration'] for c in agent_collaborations]
            avg_duration = statistics.mean(durations)
            
            # Communication metrics
            comm_metrics = self.communication_metrics.get(agent_name, {})
            messages_sent = len(comm_metrics.get('messages_sent', []))
            messages_received = len(comm_metrics.get('messages_received', []))
            
            response_times = comm_metrics.get('response_times', [])
            avg_response_time = statistics.mean(response_times) if response_times else None
            
            return {
                'total_collaborations': total_collaborations,
                'successful_collaborations': successful_collaborations,
                'success_rate': successful_collaborations / total_collaborations,
                'avg_collaboration_duration': avg_duration,
                'frequent_partners': dict(sorted(partners.items(), key=lambda x: x[1], reverse=True)[:5]),
                'messages_sent': messages_sent,
                'messages_received': messages_received,
                'avg_response_time': avg_response_time,
                'collaboration_activity_score': total_collaborations + (messages_sent + messages_received) / 10
            }
    
    def analyze_collaboration_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in collaboration"""
        with self.lock:
            if not self.collaboration_history:
                return {}
            
            # Task type analysis
            task_type_success = defaultdict(lambda: {'total': 0, 'successful': 0})
            for collab in self.collaboration_history:
                task_type = collab['task_type']
                task_type_success[task_type]['total'] += 1
                if collab['success']:
                    task_type_success[task_type]['successful'] += 1
            
            # Calculate success rates by task type
            task_success_rates = {}
            for task_type, stats in task_type_success.items():
                task_success_rates[task_type] = stats['successful'] / stats['total']
            
            # Team size analysis
            team_size_stats = defaultdict(lambda: {'total': 0, 'successful': 0, 'avg_duration': []})
            for collab in self.collaboration_history:
                size = len(collab['participants'])
                team_size_stats[size]['total'] += 1
                team_size_stats[size]['avg_duration'].append(collab['duration'])
                if collab['success']:
                    team_size_stats[size]['successful'] += 1
            
            # Process team size stats
            team_size_analysis = {}
            for size, stats in team_size_stats.items():
                team_size_analysis[size] = {
                    'total_collaborations': stats['total'],
                    'success_rate': stats['successful'] / stats['total'],
                    'avg_duration': statistics.mean(stats['avg_duration'])
                }
            
            return {
                'task_success_rates': task_success_rates,
                'team_size_analysis': team_size_analysis,
                'most_active_collaborators': self._get_most_active_collaborators(),
                'collaboration_trends': self._analyze_collaboration_trends()
            }
    
    def _get_most_active_collaborators(self) -> List[Tuple[str, int]]:
        """Get most active collaborators"""
        agent_activity = defaultdict(int)
        
        for collab in self.collaboration_history:
            for participant in collab['participants']:
                agent_activity[participant] += 1
        
        return sorted(agent_activity.items(), key=lambda x: x[1], reverse=True)[:10]
    
    def _analyze_collaboration_trends(self) -> Dict[str, Any]:
        """Analyze trends in collaboration over time"""
        if len(self.collaboration_history) < 10:
            return {'insufficient_data': True}
        
        # Simple trend analysis: compare first and last halves
        mid_point = len(self.collaboration_history) // 2
        first_half = self.collaboration_history[:mid_point]
        second_half = self.collaboration_history[mid_point:]
        
        first_success_rate = statistics.mean([c['success'] for c in first_half])
        second_success_rate = statistics.mean([c['success'] for c in second_half])
        
        first_avg_duration = statistics.mean([c['duration'] for c in first_half])
        second_avg_duration = statistics.mean([c['duration'] for c in second_half])
        
        return {
            'success_rate_trend': 'improving' if second_success_rate > first_success_rate else 'declining',
            'duration_trend': 'faster' if second_avg_duration < first_avg_duration else 'slower',
            'collaboration_frequency_trend': len(second_half) / len(first_half)
        }