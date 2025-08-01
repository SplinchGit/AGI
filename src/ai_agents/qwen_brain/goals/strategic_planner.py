"""
Strategic Planner - Qwen's strategic planning and roadmap capabilities
"""

from typing import Dict, Any, List, Optional, Tuple, Callable
import json
from datetime import datetime, timedelta
from pathlib import Path

class StrategicPlanner:
    """Handles strategic planning and roadmap creation"""
    
    def __init__(self, qwen_interface: Callable[[str], str]) -> None:
        self.qwen = qwen_interface
        self.planning_history: List[Dict[str, Any]] = []
        self.planning_horizons: Dict[str, Tuple[int, int]] = {
            'immediate': (0, 7),    # 0-7 days
            'short_term': (7, 30),  # 1-4 weeks
            'medium_term': (30, 90), # 1-3 months
            'long_term': (90, 365)  # 3-12 months
        }
    
    def create_strategic_plan(self, objectives: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive strategic plan"""
        prompt = f"""As the Brain AI, create a strategic plan for:
        
        Vision: {objectives.get('vision', 'No vision specified')}
        Mission: {objectives.get('mission', 'No mission specified')}
        
        Goals:
        {json.dumps(objectives.get('goals', []), indent=2)}
        
        Constraints:
        - Resources: {objectives.get('resources', 'Limited')}
        - Timeline: {objectives.get('timeline', 'Flexible')}
        - Budget: {objectives.get('budget', 'Moderate')}
        
        Create strategic plan including:
        1. Situation analysis
        2. Strategic objectives breakdown
        3. Key initiatives and milestones
        4. Resource allocation strategy
        5. Risk assessment and mitigation
        6. Success metrics and KPIs
        7. Implementation roadmap"""
        
        plan = self.qwen(prompt)
        
        result = {
            'objectives': objectives,
            'strategic_plan': plan,
            'created_at': datetime.now().isoformat(),
            'horizon': self._determine_horizon(objectives.get('timeline', ''))
        }
        
        self.planning_history.append(result)
        return result
    
    def create_project_roadmap(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed project roadmap"""
        prompt = f"""Create a project roadmap for:
        
        Project: {project.get('name', 'Project')}
        Scope: {project.get('scope', 'Full implementation')}
        
        Features:
        {json.dumps(project.get('features', []), indent=2)}
        
        Team Size: {project.get('team_size', 'Small')}
        Duration: {project.get('duration', '3 months')}
        
        Generate roadmap with:
        1. Phase breakdown
        2. Sprint planning
        3. Feature prioritization (MoSCoW)
        4. Dependency mapping
        5. Resource allocation timeline
        6. Risk checkpoints
        7. Delivery milestones
        8. Buffer time allocation"""
        
        roadmap = self.qwen(prompt)
        
        return {
            'project': project['name'],
            'roadmap': roadmap,
            'phases': self._extract_phases(roadmap),
            'critical_path': True,
            'created_at': datetime.now().isoformat()
        }
    
    def plan_system_migration(self, migration_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Plan system migration strategy"""
        prompt = f"""Plan migration strategy for:
        
        From: {migration_spec.get('from_system', 'Legacy System')}
        To: {migration_spec.get('to_system', 'New System')}
        
        Data Volume: {migration_spec.get('data_volume', 'Large')}
        Downtime Tolerance: {migration_spec.get('downtime', 'Minimal')}
        Rollback Required: {migration_spec.get('rollback', True)}
        
        Components to Migrate:
        {json.dumps(migration_spec.get('components', []), indent=2)}
        
        Create migration plan with:
        1. Pre-migration assessment
        2. Migration phases
        3. Data migration strategy
        4. Parallel run approach
        5. Cutover planning
        6. Rollback procedures
        7. Validation checkpoints
        8. Post-migration tasks"""
        
        plan = self.qwen(prompt)
        
        return {
            'migration_type': f"{migration_spec.get('from_system')} to {migration_spec.get('to_system')}",
            'strategy': plan,
            'risk_level': self._assess_migration_risk(migration_spec),
            'estimated_duration': '2-4 weeks',
            'created_at': datetime.now().isoformat()
        }
    
    def plan_scaling_strategy(self, current_state: Dict[str, Any], 
                            growth_projections: Dict[str, Any]) -> Dict[str, Any]:
        """Plan system scaling strategy"""
        prompt = f"""Plan scaling strategy:
        
        Current State:
        - Users: {current_state.get('users', 'Unknown')}
        - Load: {current_state.get('load', 'Moderate')}
        - Infrastructure: {current_state.get('infrastructure', 'Basic')}
        
        Growth Projections:
        - 3 months: {growth_projections.get('3_months', '2x')}
        - 6 months: {growth_projections.get('6_months', '5x')}
        - 1 year: {growth_projections.get('1_year', '10x')}
        
        Plan scaling strategy including:
        1. Infrastructure scaling roadmap
        2. Database scaling approach
        3. Caching strategy evolution
        4. Service decomposition plan
        5. Performance optimization timeline
        6. Cost projection and optimization
        7. Monitoring enhancement plan
        8. Team scaling requirements"""
        
        strategy = self.qwen(prompt)
        
        return {
            'current_capacity': current_state,
            'target_capacity': growth_projections,
            'scaling_strategy': strategy,
            'implementation_phases': 3,
            'estimated_cost_multiplier': '3-5x',
            'created_at': datetime.now().isoformat()
        }
    
    def plan_tech_debt_reduction(self, debt_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Plan technical debt reduction strategy"""
        prompt = f"""Plan technical debt reduction:
        
        Debt Assessment:
        {json.dumps(debt_assessment, indent=2)}
        
        Priority Areas:
        - Code Quality: {debt_assessment.get('code_quality', 'Poor')}
        - Test Coverage: {debt_assessment.get('test_coverage', 'Low')}
        - Documentation: {debt_assessment.get('documentation', 'Minimal')}
        - Architecture: {debt_assessment.get('architecture', 'Needs refactoring')}
        
        Create reduction plan:
        1. Debt prioritization matrix
        2. Quick wins identification
        3. Refactoring roadmap
        4. Testing improvement plan
        5. Documentation strategy
        6. Architecture evolution
        7. Resource allocation
        8. Progress tracking metrics"""
        
        plan = self.qwen(prompt)
        
        return {
            'debt_assessment': debt_assessment,
            'reduction_plan': plan,
            'estimated_effort': '20% of development capacity',
            'roi_timeline': '6-12 months',
            'created_at': datetime.now().isoformat()
        }
    
    def create_contingency_plan(self, risk_scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create contingency plans for risk scenarios"""
        prompt = f"""Create contingency plans for risks:
        
        Risk Scenarios:
        {json.dumps(risk_scenarios, indent=2)}
        
        For each scenario, provide:
        1. Early warning indicators
        2. Trigger conditions
        3. Response procedures
        4. Resource requirements
        5. Communication plan
        6. Recovery timeline
        7. Success criteria
        8. Lessons learned process"""
        
        plans = self.qwen(prompt)
        
        return {
            'risk_count': len(risk_scenarios),
            'contingency_plans': plans,
            'review_frequency': 'monthly',
            'last_updated': datetime.now().isoformat()
        }
    
    def plan_innovation_initiatives(self, innovation_goals: Dict[str, Any]) -> Dict[str, Any]:
        """Plan innovation and R&D initiatives"""
        prompt = f"""Plan innovation initiatives:
        
        Focus Areas:
        {json.dumps(innovation_goals.get('focus_areas', []), indent=2)}
        
        Budget: {innovation_goals.get('budget', 'Moderate')}
        Timeline: {innovation_goals.get('timeline', '6 months')}
        Risk Tolerance: {innovation_goals.get('risk_tolerance', 'Medium')}
        
        Create innovation plan:
        1. Research priorities
        2. Proof of concept roadmap
        3. Experimentation framework
        4. Resource allocation
        5. Partnership opportunities
        6. IP strategy
        7. Success metrics
        8. Commercialization path"""
        
        plan = self.qwen(prompt)
        
        return {
            'innovation_areas': innovation_goals.get('focus_areas', []),
            'initiative_plan': plan,
            'expected_outcomes': 'See plan details',
            'created_at': datetime.now().isoformat()
        }
    
    def _determine_horizon(self, timeline: str) -> str:
        """Determine planning horizon from timeline"""
        timeline_lower = timeline.lower()
        if 'week' in timeline_lower or 'immediate' in timeline_lower:
            return 'immediate'
        elif 'month' in timeline_lower and '3' not in timeline_lower:
            return 'short_term'
        elif '3 month' in timeline_lower or 'quarter' in timeline_lower:
            return 'medium_term'
        else:
            return 'long_term'
    
    def _extract_phases(self, roadmap: str) -> List[str]:
        """Extract phases from roadmap text"""
        # Simple extraction - would be more sophisticated in practice
        phases = []
        phase_indicators = ['phase', 'sprint', 'milestone', 'stage']
        
        lines = roadmap.lower().split('\n')
        for line in lines:
            if any(indicator in line for indicator in phase_indicators):
                phases.append(line.strip())
        
        return phases[:5]  # Return top 5 phases
    
    def _assess_migration_risk(self, migration_spec: Dict[str, Any]) -> str:
        """Assess migration risk level"""
        risk_factors = 0
        
        if migration_spec.get('data_volume', '') == 'Large':
            risk_factors += 2
        if migration_spec.get('downtime', '') == 'None':
            risk_factors += 2
        if len(migration_spec.get('components', [])) > 5:
            risk_factors += 1
        
        if risk_factors >= 4:
            return 'high'
        elif risk_factors >= 2:
            return 'medium'
        else:
            return 'low'