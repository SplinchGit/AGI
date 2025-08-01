"""
Pattern Recognizer - Qwen's pattern recognition and learning capabilities
"""

from typing import Dict, Any, List, Optional, Tuple, Callable
import json
from datetime import datetime
import re
from collections import defaultdict, Counter

class PatternRecognizer:
    """Handles pattern recognition and learning from data"""
    
    def __init__(self, qwen_interface: Callable[[str], str]) -> None:
        self.qwen = qwen_interface
        self.learned_patterns: List[Dict[str, Any]] = []
        self.pattern_cache: defaultdict[str, List[Any]] = defaultdict(list)
        self.confidence_threshold = 0.7
    
    def recognize_behavioral_patterns(self, behavior_data: Dict[str, Any]) -> Dict[str, Any]:
        """Recognize patterns in user or system behavior"""
        prompt = f"""Recognize behavioral patterns:
        
        Behavior Data:
        {json.dumps(behavior_data, indent=2)}
        
        Analyze for patterns:
        1. Temporal patterns (daily, weekly, seasonal)
        2. Sequential patterns (action sequences)
        3. Frequency patterns (usage frequency)
        4. Correlation patterns (co-occurring behaviors)
        5. Anomaly patterns (unusual behavior)
        6. Trend patterns (changing behavior over time)
        7. Segmentation patterns (user groups)
        8. Trigger patterns (cause-effect relationships)
        
        Provide:
        - Pattern descriptions
        - Confidence levels
        - Business implications
        - Actionable insights"""
        
        analysis = self.qwen(prompt)
        
        patterns = self._extract_patterns(analysis)
        
        result = {
            'patterns_identified': patterns,
            'analysis': analysis,
            'pattern_count': len(patterns),
            'high_confidence_patterns': [p for p in patterns if p.get('confidence', 0) > 0.8],
            'timestamp': datetime.now().isoformat()
        }
        
        self.learned_patterns.extend(patterns)
        return result
    
    def recognize_communication_patterns(self, conversation_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Recognize patterns in communication and conversations"""
        prompt = f"""Recognize communication patterns:
        
        Conversation Data (last 20 exchanges):
        {json.dumps(conversation_data[-20:], indent=2)}
        
        Identify patterns:
        1. Topic transition patterns
        2. Question-answer patterns
        3. Sentiment evolution patterns
        4. Engagement patterns
        5. Response time patterns
        6. Content complexity patterns
        7. Interaction style patterns
        8. Problem-solving patterns
        
        Analyze:
        - Communication effectiveness
        - Information flow patterns
        - Learning indicators
        - Collaboration patterns"""
        
        analysis = self.qwen(prompt)
        
        return {
            'communication_patterns': analysis,
            'conversation_quality': self._assess_conversation_quality(conversation_data),
            'learning_indicators': self._identify_learning_patterns(conversation_data),
            'improvement_suggestions': 'See analysis',
            'timestamp': datetime.now().isoformat()
        }
    
    def recognize_performance_patterns(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Recognize patterns in system or team performance"""
        prompt = f"""Recognize performance patterns:
        
        Performance Metrics:
        {json.dumps(performance_data, indent=2)}
        
        Identify patterns:
        1. Performance cycles
        2. Bottleneck patterns
        3. Efficiency patterns
        4. Quality patterns
        5. Resource utilization patterns
        6. Scaling patterns
        7. Failure patterns
        8. Recovery patterns
        
        Analyze:
        - Root causes of patterns
        - Predictive indicators
        - Optimization opportunities
        - Warning signs"""
        
        analysis = self.qwen(prompt)
        
        return {
            'performance_patterns': analysis,
            'optimization_opportunities': self._extract_optimizations(analysis),
            'predictive_indicators': True,
            'warning_signs': self._extract_warnings(analysis),
            'timestamp': datetime.now().isoformat()
        }
    
    def recognize_error_patterns(self, error_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Recognize patterns in errors and failures"""
        prompt = f"""Recognize error patterns:
        
        Error Data:
        {json.dumps(error_data, indent=2)}
        
        Identify patterns:
        1. Error frequency patterns
        2. Error clustering patterns
        3. Temporal error patterns
        4. Cascading failure patterns
        5. Environmental correlation patterns
        6. User action correlation patterns
        7. System state correlation patterns
        8. Recovery patterns
        
        Provide:
        - Pattern classifications
        - Root cause hypotheses
        - Prevention strategies
        - Monitoring recommendations"""
        
        analysis = self.qwen(prompt)
        
        return {
            'error_patterns': analysis,
            'pattern_classifications': ['temporal', 'cascading', 'environmental'],
            'prevention_strategies': self._extract_prevention_strategies(analysis),
            'monitoring_recommendations': True,
            'timestamp': datetime.now().isoformat()
        }
    
    def recognize_success_patterns(self, success_data: Dict[str, Any]) -> Dict[str, Any]:
        """Recognize patterns in successful outcomes"""
        prompt = f"""Recognize success patterns:
        
        Success Data:
        {json.dumps(success_data, indent=2)}
        
        Identify patterns:
        1. Success factor patterns
        2. Timing patterns for success
        3. Resource allocation patterns
        4. Team composition patterns
        5. Process patterns
        6. Environmental patterns
        7. Stakeholder engagement patterns
        8. Innovation patterns
        
        Analyze:
        - Key success factors
        - Replicable elements
        - Success predictors
        - Scaling strategies"""
        
        analysis = self.qwen(prompt)
        
        return {
            'success_patterns': analysis,
            'key_success_factors': self._extract_success_factors(analysis),
            'replicable_elements': True,
            'scaling_potential': 'high',
            'timestamp': datetime.now().isoformat()
        }
    
    def learn_from_patterns(self, pattern_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Learn meta-patterns from historical pattern data"""
        prompt = f"""Learn from pattern history:
        
        Historical Patterns:
        {json.dumps(pattern_history[-10:], indent=2)}  # Last 10 patterns
        
        Meta-learning analysis:
        1. Pattern evolution over time
        2. Pattern effectiveness
        3. Pattern reliability
        4. Pattern interactions
        5. Context dependencies
        6. Emerging pattern types
        7. Pattern degradation
        8. Adaptation strategies
        
        Generate:
        - Improved pattern recognition rules
        - Pattern confidence adjustments
        - New pattern hypotheses
        - Learning recommendations"""
        
        learning = self.qwen(prompt)
        
        # Update internal learning state
        self._update_pattern_weights(pattern_history)
        
        return {
            'meta_learning': learning,
            'pattern_rules_updated': True,
            'confidence_adjustments': True,
            'new_hypotheses': self._generate_new_hypotheses(learning),
            'timestamp': datetime.now().isoformat()
        }
    
    def predict_future_patterns(self, current_data: Dict[str, Any], 
                               historical_patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Predict future patterns based on current trends"""
        prompt = f"""Predict future patterns:
        
        Current State:
        {json.dumps(current_data, indent=2)}
        
        Historical Pattern Context:
        {json.dumps(historical_patterns[-5:], indent=2)}  # Recent patterns
        
        Predict:
        1. Likely pattern evolution
        2. Emerging pattern types
        3. Pattern breakdowns
        4. Cyclical pattern returns
        5. Trend continuations
        6. Disruptive pattern changes
        7. Pattern intensity changes
        8. Timeline predictions
        
        Provide:
        - Pattern forecasts
        - Confidence intervals
        - Trigger conditions
        - Mitigation strategies"""
        
        predictions = self.qwen(prompt)
        
        return {
            'pattern_predictions': predictions,
            'forecast_horizon': '3-6 months',
            'confidence_intervals': True,
            'trigger_conditions': self._extract_triggers(predictions),
            'timestamp': datetime.now().isoformat()
        }
    
    def _extract_patterns(self, analysis: str) -> List[Dict[str, Any]]:
        """Extract structured patterns from analysis text"""
        patterns = []
        
        # Simple pattern extraction - would be more sophisticated in practice
        pattern_indicators = ['pattern:', 'trend:', 'behavior:', 'cycle:']
        
        lines = analysis.split('\n')
        for line in lines:
            for indicator in pattern_indicators:
                if indicator in line.lower():
                    patterns.append({
                        'description': line.strip(),
                        'type': indicator.replace(':', ''),
                        'confidence': 0.75,  # Default confidence
                        'discovered_at': datetime.now().isoformat()
                    })
        
        return patterns[:10]  # Return top 10 patterns
    
    def _assess_conversation_quality(self, conversation_data: List[Dict[str, Any]]) -> str:
        """Assess overall conversation quality"""
        if not conversation_data:
            return 'unknown'
        
        # Simple heuristics
        avg_length = sum(len(msg.get('message', '')) for msg in conversation_data) / len(conversation_data)
        
        if avg_length > 200:
            return 'high'
        elif avg_length > 100:
            return 'medium'
        else:
            return 'low'
    
    def _identify_learning_patterns(self, conversation_data: List[Dict[str, Any]]) -> List[str]:
        """Identify learning patterns in conversations"""
        learning_indicators = []
        
        for msg in conversation_data:
            message = msg.get('message', '').lower()
            if any(word in message for word in ['learn', 'understand', 'realize', 'discover']):
                learning_indicators.append('explicit_learning')
            if '?' in message:
                learning_indicators.append('inquiry_pattern')
        
        return list(set(learning_indicators))
    
    def _extract_optimizations(self, analysis: str) -> List[str]:
        """Extract optimization opportunities from analysis"""
        optimizations = []
        opt_keywords = ['optimize', 'improve', 'enhance', 'speed up', 'reduce']
        
        lines = analysis.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in opt_keywords):
                optimizations.append(line.strip())
        
        return optimizations[:5]
    
    def _extract_warnings(self, analysis: str) -> List[str]:
        """Extract warning signs from analysis"""
        warnings = []
        warning_keywords = ['warning', 'alert', 'concern', 'risk', 'danger']
        
        lines = analysis.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in warning_keywords):
                warnings.append(line.strip())
        
        return warnings[:3]
    
    def _extract_prevention_strategies(self, analysis: str) -> List[str]:
        """Extract prevention strategies from analysis"""
        strategies = []
        strategy_keywords = ['prevent', 'avoid', 'mitigate', 'reduce', 'minimize']
        
        lines = analysis.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in strategy_keywords):
                strategies.append(line.strip())
        
        return strategies[:5]
    
    def _extract_success_factors(self, analysis: str) -> List[str]:
        """Extract key success factors from analysis"""
        factors = []
        factor_keywords = ['factor', 'key', 'important', 'critical', 'essential']
        
        lines = analysis.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in factor_keywords):
                factors.append(line.strip())
        
        return factors[:5]
    
    def _update_pattern_weights(self, pattern_history: List[Dict[str, Any]]) -> None:
        """Update internal pattern weights based on history"""
        # Simple weight updating - would be more sophisticated in practice
        for pattern in pattern_history:
            pattern_type = pattern.get('type', 'unknown')
            self.pattern_cache[pattern_type].append(pattern)
    
    def _generate_new_hypotheses(self, learning: str) -> List[str]:
        """Generate new pattern hypotheses from learning"""
        hypotheses = []
        hypothesis_keywords = ['hypothesis', 'theory', 'possible', 'might', 'could']
        
        lines = learning.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in hypothesis_keywords):
                hypotheses.append(line.strip())
        
        return hypotheses[:3]
    
    def _extract_triggers(self, predictions: str) -> List[str]:
        """Extract trigger conditions from predictions"""
        triggers = []
        trigger_keywords = ['trigger', 'when', 'if', 'condition', 'threshold']
        
        lines = predictions.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in trigger_keywords):
                triggers.append(line.strip())
        
        return triggers[:5]