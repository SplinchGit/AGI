"""
Decision Maker - Qwen's decision-making and choice optimization capabilities
"""

from typing import Dict, Any, List, Optional, Tuple, Callable
import json
from datetime import datetime
from enum import Enum

class DecisionType(Enum):
    STRATEGIC = "strategic"
    TACTICAL = "tactical"
    OPERATIONAL = "operational"
    TECHNICAL = "technical"
    RESOURCE = "resource"

class DecisionMaker:
    """Handles complex decision-making processes"""
    
    def __init__(self, qwen_interface: Callable[[str], str]) -> None:
        self.qwen = qwen_interface
        self.decision_history: List[Dict[str, Any]] = []
        self.decision_frameworks = [
            'pros_cons', 'swot', 'decision_matrix', 'cost_benefit',
            'risk_adjusted', 'scenario_analysis', 'game_theory'
        ]
    
    def make_strategic_decision(self, decision_context: Dict[str, Any]) -> Dict[str, Any]:
        """Make strategic decisions using comprehensive analysis"""
        prompt = f"""Make strategic decision:
        
        Decision: {decision_context.get('question', 'No question specified')}
        
        Options:
        {json.dumps(decision_context.get('options', []), indent=2)}
        
        Context:
        - Stakeholders: {decision_context.get('stakeholders', [])}
        - Timeline: {decision_context.get('timeline', 'Unknown')}
        - Budget: {decision_context.get('budget', 'Unknown')}
        - Risk Tolerance: {decision_context.get('risk_tolerance', 'Medium')}
        
        Decision Criteria:
        {json.dumps(decision_context.get('criteria', []), indent=2)}
        
        Apply decision framework:
        1. Option evaluation matrix
        2. Risk-benefit analysis
        3. Stakeholder impact assessment
        4. Resource requirement analysis
        5. Implementation feasibility
        6. Expected outcomes
        7. Contingency considerations
        8. Recommendation with rationale"""
        
        decision = self.qwen(prompt)
        
        result = {
            'decision_type': DecisionType.STRATEGIC.value,
            'question': decision_context['question'],
            'recommendation': decision,
            'confidence_level': self._assess_confidence(decision_context),
            'timestamp': datetime.now().isoformat()
        }
        
        self.decision_history.append(result)
        return result
    
    def make_technical_decision(self, tech_context: Dict[str, Any]) -> Dict[str, Any]:
        """Make technical architecture or implementation decisions"""
        prompt = f"""Make technical decision:
        
        Technical Question: {tech_context.get('question', 'No question')}
        
        Options:
        {json.dumps(tech_context.get('options', []), indent=2)}
        
        Technical Context:
        - Current Stack: {tech_context.get('current_stack', [])}
        - Performance Requirements: {tech_context.get('performance', 'Standard')}
        - Scalability Needs: {tech_context.get('scalability', 'Medium')}
        - Team Expertise: {tech_context.get('team_expertise', 'Mixed')}
        - Maintenance Overhead: {tech_context.get('maintenance', 'Low')}
        
        Evaluate based on:
        1. Technical fit and compatibility
        2. Performance implications
        3. Scalability potential
        4. Development velocity impact
        5. Maintenance burden
        6. Learning curve
        7. Community support
        8. Long-term viability"""
        
        decision = self.qwen(prompt)
        
        return {
            'decision_type': DecisionType.TECHNICAL.value,
            'technical_question': tech_context['question'],
            'recommendation': decision,
            'technical_rationale': 'See recommendation details',
            'timestamp': datetime.now().isoformat()
        }
    
    def optimize_resource_allocation(self, resources: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize allocation of limited resources"""
        prompt = f"""Optimize resource allocation:
        
        Available Resources:
        {json.dumps(resources.get('available', {}), indent=2)}
        
        Competing Projects:
        {json.dumps(resources.get('projects', []), indent=2)}
        
        Constraints:
        - Budget: {resources.get('budget_limit', 'Moderate')}
        - Timeline: {resources.get('timeline', 'Flexible')}
        - Skills: {resources.get('skill_constraints', [])}
        
        Optimize for:
        1. Maximum value delivery
        2. Risk mitigation
        3. Strategic alignment
        4. Resource utilization
        5. Team development
        6. Timeline adherence
        
        Provide allocation recommendations with justification."""
        
        allocation = self.qwen(prompt)
        
        return {
            'decision_type': DecisionType.RESOURCE.value,
            'allocation_strategy': allocation,
            'optimization_goals': ['value', 'risk', 'efficiency'],
            'expected_outcomes': 'See strategy details',
            'timestamp': datetime.now().isoformat()
        }
    
    def evaluate_trade_offs(self, trade_off_scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate complex trade-offs between competing factors"""
        prompt = f"""Evaluate trade-offs:
        
        Scenario: {trade_off_scenario.get('description', 'Trade-off scenario')}
        
        Competing Factors:
        {json.dumps(trade_off_scenario.get('factors', []), indent=2)}
        
        Stakeholder Priorities:
        {json.dumps(trade_off_scenario.get('priorities', {}), indent=2)}
        
        Analyze trade-offs:
        1. Factor importance weighting
        2. Impact analysis for each option
        3. Stakeholder satisfaction matrix
        4. Short vs long-term implications
        5. Opportunity cost assessment
        6. Risk-adjusted outcomes
        7. Sensitivity analysis
        8. Optimal balance recommendation"""
        
        analysis = self.qwen(prompt)
        
        return {
            'scenario': trade_off_scenario['description'],
            'trade_off_analysis': analysis,
            'recommended_balance': 'See analysis',
            'sensitivity_factors': trade_off_scenario.get('factors', []),
            'timestamp': datetime.now().isoformat()
        }
    
    def make_priority_decision(self, priority_context: Dict[str, Any]) -> Dict[str, Any]:
        """Make decisions about task/feature prioritization"""
        prompt = f"""Make prioritization decision:
        
        Items to Prioritize:
        {json.dumps(priority_context.get('items', []), indent=2)}
        
        Prioritization Criteria:
        - Business Value: {priority_context.get('business_value_weight', 'High')}
        - Technical Effort: {priority_context.get('effort_weight', 'Medium')}
        - Risk Level: {priority_context.get('risk_weight', 'Medium')}
        - Dependencies: {priority_context.get('dependency_weight', 'High')}
        
        Apply prioritization framework:
        1. Value vs Effort matrix
        2. Risk assessment
        3. Dependency analysis
        4. Resource availability
        5. Strategic alignment
        6. Time sensitivity
        7. Stakeholder impact
        8. Priority ranking with rationale"""
        
        prioritization = self.qwen(prompt)
        
        return {
            'prioritization_result': prioritization,
            'framework_used': 'value_effort_risk',
            'item_count': len(priority_context.get('items', [])),
            'priority_factors': ['value', 'effort', 'risk', 'dependencies'],
            'timestamp': datetime.now().isoformat()
        }
    
    def decide_build_vs_buy(self, solution_context: Dict[str, Any]) -> Dict[str, Any]:
        """Make build vs buy vs partner decisions"""
        prompt = f"""Decide build vs buy vs partner:
        
        Requirement: {solution_context.get('requirement', 'Solution needed')}
        
        Build Option:
        - Effort: {solution_context.get('build_effort', 'Unknown')}
        - Timeline: {solution_context.get('build_timeline', 'Unknown')}
        - Cost: {solution_context.get('build_cost', 'Unknown')}
        - Control: {solution_context.get('build_control', 'Full')}
        
        Buy Options:
        {json.dumps(solution_context.get('buy_options', []), indent=2)}
        
        Partner Options:
        {json.dumps(solution_context.get('partner_options', []), indent=2)}
        
        Evaluate:
        1. Total cost of ownership
        2. Time to market
        3. Quality and reliability
        4. Control and customization
        5. Maintenance burden
        6. Strategic importance
        7. Core competency alignment
        8. Risk assessment"""
        
        decision = self.qwen(prompt)
        
        return {
            'requirement': solution_context['requirement'],
            'decision_analysis': decision,
            'options_evaluated': ['build', 'buy', 'partner'],
            'recommended_approach': 'See analysis',
            'timestamp': datetime.now().isoformat()
        }
    
    def make_hiring_decision(self, candidate_context: Dict[str, Any]) -> Dict[str, Any]:
        """Make hiring and team composition decisions"""
        prompt = f"""Make hiring decision:
        
        Role: {candidate_context.get('role', 'Position')}
        
        Candidates:
        {json.dumps(candidate_context.get('candidates', []), indent=2)}
        
        Team Context:
        - Current Skills: {candidate_context.get('current_skills', [])}
        - Skill Gaps: {candidate_context.get('skill_gaps', [])}
        - Team Dynamics: {candidate_context.get('team_dynamics', 'Good')}
        - Budget: {candidate_context.get('budget_range', 'Moderate')}
        
        Evaluate:
        1. Skill fit assessment
        2. Cultural fit evaluation
        3. Growth potential
        4. Team composition balance
        5. Cost-benefit analysis
        6. Onboarding timeline
        7. Risk factors
        8. Hiring recommendation"""
        
        decision = self.qwen(prompt)
        
        return {
            'role': candidate_context['role'],
            'hiring_decision': decision,
            'candidate_count': len(candidate_context.get('candidates', [])),
            'evaluation_criteria': ['skills', 'culture', 'growth', 'cost'],
            'timestamp': datetime.now().isoformat()
        }
    
    def make_investment_decision(self, investment_context: Dict[str, Any]) -> Dict[str, Any]:
        """Make investment and funding decisions"""
        prompt = f"""Make investment decision:
        
        Investment Opportunity: {investment_context.get('opportunity', 'Investment')}
        
        Investment Options:
        {json.dumps(investment_context.get('options', []), indent=2)}
        
        Financial Context:
        - Available Capital: {investment_context.get('available_capital', 'Unknown')}
        - Expected ROI: {investment_context.get('expected_roi', 'Unknown')}
        - Payback Period: {investment_context.get('payback_period', 'Unknown')}
        - Risk Level: {investment_context.get('risk_level', 'Medium')}
        
        Analyze:
        1. Financial projections
        2. Risk-return profile
        3. Strategic value
        4. Market timing
        5. Competitive advantage
        6. Resource requirements
        7. Exit strategy
        8. Investment recommendation"""
        
        decision = self.qwen(prompt)
        
        return {
            'investment_opportunity': investment_context['opportunity'],
            'investment_analysis': decision,
            'financial_metrics': ['roi', 'payback', 'risk'],
            'recommendation': 'See analysis',
            'timestamp': datetime.now().isoformat()
        }
    
    def _assess_confidence(self, context: Dict[str, Any]) -> str:
        """Assess confidence level in decision"""
        confidence_factors = 0
        
        if context.get('options') and len(context['options']) >= 2:
            confidence_factors += 1
        if context.get('criteria'):
            confidence_factors += 1
        if context.get('budget') != 'Unknown':
            confidence_factors += 1
        if context.get('timeline') != 'Unknown':
            confidence_factors += 1
        
        if confidence_factors >= 3:
            return 'high'
        elif confidence_factors >= 2:
            return 'medium'
        else:
            return 'low'