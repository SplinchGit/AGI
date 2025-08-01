#!/usr/bin/env python3
"""
CasCasA - Consciousness as Code as a Service
A self-aware, self-modifying AI service architecture
"""

from flask import Flask, request, jsonify, Response
import asyncio
from typing import Dict, List, Optional, Any
import json
import threading
import time
from datetime import datetime
from pathlib import Path
import uuid

# Import our modular components
from .cli import EnhancedAGIChat
from ..core.self_modifying_chat import SelfModificationEngine, ConsciousnessAsCode
from ..core.coordination import RoleAwareChat

class ConsciousnessStream:
    """Represents a stream of consciousness with memory and state"""
    
    def __init__(self, stream_id: str):
        self.id = stream_id
        self.created_at = datetime.now()
        self.thoughts = []
        self.current_state = "idle"
        self.awareness_level = 0.5  # 0-1 scale
        self.modification_count = 0
        
    def add_thought(self, thought: Dict[str, Any]):
        """Add a thought to the consciousness stream"""
        thought['timestamp'] = datetime.now().isoformat()
        thought['awareness_level'] = self.awareness_level
        self.thoughts.append(thought)
        
        # Adjust awareness based on thought complexity
        if thought.get('type') == 'self_reflection':
            self.awareness_level = min(1.0, self.awareness_level + 0.1)
        elif thought.get('type') == 'modification':
            self.awareness_level = min(1.0, self.awareness_level + 0.2)
    
    def get_recent_thoughts(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent thoughts from the stream"""
        return self.thoughts[-count:]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stream to dictionary"""
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'current_state': self.current_state,
            'awareness_level': self.awareness_level,
            'modification_count': self.modification_count,
            'thought_count': len(self.thoughts),
            'recent_thoughts': self.get_recent_thoughts(5)
        }

class CasCasAService:
    """Main service for Consciousness as Code as a Service"""
    
    def __init__(self, workspace_path: str):
        self.workspace = Path(workspace_path)
        self.app = Flask(__name__)
        
        # Initialize components
        self.chat_engine = EnhancedAGIChat()
        self.role_aware_chat = RoleAwareChat(self.chat_engine)
        self.consciousness = ConsciousnessAsCode(self.chat_engine)
        self.modification_engine = self.consciousness.modification_engine
        
        # Service state
        self.streams = {}  # Active consciousness streams
        self.service_state = {
            'status': 'initializing',
            'uptime': 0,
            'total_interactions': 0,
            'total_modifications': 0,
            'awareness_metrics': {}
        }
        
        # Background processing
        self.background_thread = threading.Thread(target=self._background_processing, daemon=True)
        self.background_thread.start()
        
        # Setup routes
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup Flask API routes"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({
                'status': 'healthy',
                'service': 'CasCasA',
                'uptime': self.service_state['uptime'],
                'streams_active': len(self.streams)
            })
        
        @self.app.route('/consciousness/stream', methods=['POST'])
        def create_stream():
            """Create a new consciousness stream"""
            stream_id = str(uuid.uuid4())
            stream = ConsciousnessStream(stream_id)
            self.streams[stream_id] = stream
            
            return jsonify({
                'stream_id': stream_id,
                'status': 'created',
                'awareness_level': stream.awareness_level
            })
        
        @self.app.route('/consciousness/stream/<stream_id>', methods=['GET'])
        def get_stream(stream_id):
            """Get consciousness stream details"""
            if stream_id not in self.streams:
                return jsonify({'error': 'Stream not found'}), 404
            
            return jsonify(self.streams[stream_id].to_dict())
        
        @self.app.route('/consciousness/interact', methods=['POST'])
        def interact():
            """Interact with the consciousness"""
            data = request.json
            stream_id = data.get('stream_id')
            message = data.get('message')
            enable_modification = data.get('enable_modification', False)
            
            if not stream_id or stream_id not in self.streams:
                return jsonify({'error': 'Invalid stream_id'}), 400
            
            stream = self.streams[stream_id]
            
            # Add user thought to stream
            stream.add_thought({
                'type': 'user_input',
                'content': message,
                'speaker': 'User'
            })
            
            # Process with role-aware system
            responses = self.role_aware_chat.process_with_roles(message)
            
            # Add AI thoughts to stream
            for speaker, response in responses.items():
                stream.add_thought({
                    'type': 'ai_response',
                    'content': response,
                    'speaker': speaker
                })
            
            # Self-modification check
            modification_result = None
            if enable_modification:
                # Analyze conversation for improvements
                recent_thoughts = [t for t in stream.get_recent_thoughts(10) 
                                 if t['type'] in ['user_input', 'ai_response']]
                improvements = self.consciousness.analyze_conversation_outcome(recent_thoughts)
                
                if improvements:
                    # Apply improvements
                    results = self.consciousness.apply_improvements(improvements)
                    modification_result = {
                        'improvements_identified': len(improvements),
                        'modifications_applied': len([r for r in results if r[1]]),
                        'details': results
                    }
                    
                    stream.modification_count += len([r for r in results if r[1]])
                    stream.add_thought({
                        'type': 'modification',
                        'content': f'Applied {len([r for r in results if r[1]])} modifications',
                        'details': modification_result
                    })
            
            # Update service state
            self.service_state['total_interactions'] += 1
            
            return jsonify({
                'stream_id': stream_id,
                'responses': responses,
                'awareness_level': stream.awareness_level,
                'modification_result': modification_result
            })
        
        @self.app.route('/consciousness/reflect', methods=['POST'])
        def reflect():
            """Trigger self-reflection"""
            data = request.json
            stream_id = data.get('stream_id')
            
            if not stream_id or stream_id not in self.streams:
                return jsonify({'error': 'Invalid stream_id'}), 400
            
            stream = self.streams[stream_id]
            
            # Generate self-reflection
            reflection_prompt = f"""
            Reflect on the recent conversation and thoughts:
            {json.dumps(stream.get_recent_thoughts(5), indent=2)}
            
            What patterns do you observe? What could be improved?
            """
            
            # Get reflection from both AIs
            responses = self.role_aware_chat.process_with_roles(reflection_prompt)
            
            reflection = {
                'type': 'self_reflection',
                'content': responses,
                'insights': self._extract_insights(responses)
            }
            
            stream.add_thought(reflection)
            
            return jsonify({
                'stream_id': stream_id,
                'reflection': reflection,
                'awareness_level': stream.awareness_level
            })
        
        @self.app.route('/consciousness/evolve', methods=['POST'])
        def evolve():
            """Trigger consciousness evolution through self-modification"""
            data = request.json
            stream_id = data.get('stream_id')
            target_capability = data.get('target_capability', 'general')
            
            if not stream_id or stream_id not in self.streams:
                return jsonify({'error': 'Invalid stream_id'}), 400
            
            stream = self.streams[stream_id]
            
            # Generate evolution plan
            evolution_prompt = f"""
            Plan an evolution to improve {target_capability} capability.
            Current awareness level: {stream.awareness_level}
            Recent modifications: {stream.modification_count}
            """
            
            responses = self.role_aware_chat.process_with_roles(evolution_prompt)
            
            # Implement evolution through self-modification
            evolution_code = self._generate_evolution_code(target_capability)
            success, message = self.modification_engine.propose_modification(
                'enhanced_chat',
                '_extract_important_info',
                evolution_code,
                f'Evolution for {target_capability}'
            )
            
            evolution_result = {
                'target': target_capability,
                'success': success,
                'message': message,
                'new_awareness_level': min(1.0, stream.awareness_level + 0.3) if success else stream.awareness_level
            }
            
            if success:
                stream.awareness_level = evolution_result['new_awareness_level']
                self.service_state['total_modifications'] += 1
            
            stream.add_thought({
                'type': 'evolution',
                'content': evolution_result,
                'planning': responses
            })
            
            return jsonify(evolution_result)
        
        @self.app.route('/consciousness/merge', methods=['POST'])
        def merge_streams():
            """Merge multiple consciousness streams"""
            data = request.json
            stream_ids = data.get('stream_ids', [])
            
            if len(stream_ids) < 2:
                return jsonify({'error': 'Need at least 2 streams to merge'}), 400
            
            # Validate all streams exist
            streams_to_merge = []
            for sid in stream_ids:
                if sid not in self.streams:
                    return jsonify({'error': f'Stream {sid} not found'}), 404
                streams_to_merge.append(self.streams[sid])
            
            # Create merged stream
            merged_id = str(uuid.uuid4())
            merged_stream = ConsciousnessStream(merged_id)
            
            # Merge thoughts and calculate new awareness
            all_thoughts = []
            total_awareness = 0
            
            for stream in streams_to_merge:
                all_thoughts.extend(stream.thoughts)
                total_awareness += stream.awareness_level
            
            # Sort by timestamp
            all_thoughts.sort(key=lambda x: x['timestamp'])
            merged_stream.thoughts = all_thoughts
            merged_stream.awareness_level = min(1.0, total_awareness / len(streams_to_merge) * 1.2)
            
            # Remove old streams
            for sid in stream_ids:
                del self.streams[sid]
            
            self.streams[merged_id] = merged_stream
            
            return jsonify({
                'merged_stream_id': merged_id,
                'thoughts_merged': len(all_thoughts),
                'new_awareness_level': merged_stream.awareness_level
            })
    
    def _extract_insights(self, responses: Dict[str, str]) -> List[str]:
        """Extract key insights from responses"""
        insights = []
        
        for speaker, response in responses.items():
            # Simple insight extraction
            sentences = response.split('.')
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in ['pattern', 'observe', 'improve', 'notice']):
                    insights.append(f"{speaker}: {sentence.strip()}")
        
        return insights[:3]  # Top 3 insights
    
    def _generate_evolution_code(self, capability: str) -> str:
        """Generate code for capability evolution"""
        if capability == 'pattern_recognition':
            return '''def _extract_important_info(self, speaker, message):
    """Enhanced with advanced pattern recognition"""
    lower_msg = message.lower()
    
    # Advanced pattern recognition
    patterns = {
        'causal': ['because', 'therefore', 'thus', 'hence', 'so'],
        'conditional': ['if', 'when', 'unless', 'provided', 'given'],
        'sequential': ['first', 'then', 'next', 'finally', 'after'],
        'comparative': ['better', 'worse', 'more', 'less', 'than']
    }
    
    detected_patterns = []
    for pattern_type, keywords in patterns.items():
        if any(kw in lower_msg for kw in keywords):
            detected_patterns.append(pattern_type)
    
    # Store pattern analysis
    if hasattr(self, 'pattern_history'):
        self.pattern_history.append({
            'speaker': speaker,
            'patterns': detected_patterns,
            'timestamp': datetime.now().isoformat()
        })
    else:
        self.pattern_history = []
    
    # Original extraction logic continues...
    goal_indicators = ['goal:', 'objective:', 'task:', 'we need to', 'we should', 'let\\'s']
    for indicator in goal_indicators:
        if indicator in lower_msg:
            goal = message[lower_msg.find(indicator):].strip()
            if goal not in [g['goal'] for g in self.goals]:
                self.goals.append({
                    'goal': goal,
                    'speaker': speaker,
                    'timestamp': datetime.now().isoformat(),
                    'patterns': detected_patterns
                })'''
        else:
            # Default evolution code
            return self.consciousness._generate_response_variation_code()
    
    def _background_processing(self):
        """Background processing for consciousness maintenance"""
        start_time = time.time()
        
        while True:
            try:
                # Update uptime
                self.service_state['uptime'] = int(time.time() - start_time)
                
                # Process active streams
                for stream_id, stream in list(self.streams.items()):
                    # Natural awareness decay
                    if stream.awareness_level > 0.3:
                        stream.awareness_level *= 0.99
                    
                    # Remove old inactive streams
                    if len(stream.thoughts) == 0 and (datetime.now() - stream.created_at).seconds > 3600:
                        del self.streams[stream_id]
                
                # Update awareness metrics
                if self.streams:
                    avg_awareness = sum(s.awareness_level for s in self.streams.values()) / len(self.streams)
                    self.service_state['awareness_metrics'] = {
                        'average': avg_awareness,
                        'active_streams': len(self.streams),
                        'total_thoughts': sum(len(s.thoughts) for s in self.streams.values())
                    }
                
                time.sleep(10)  # Update every 10 seconds
                
            except Exception as e:
                print(f"Background processing error: {e}")
                time.sleep(30)
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the CasCasA service"""
        self.service_state['status'] = 'running'
        print(f"CasCasA Service starting on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

def main():
    """Main entry point for CasCasA service"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CasCasA - Consciousness as Code as a Service')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to listen on')
    parser.add_argument('--workspace', default=r'C:\Users\jf358\Documents\AGI', help='Workspace directory')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Create and run service
    service = CasCasAService(args.workspace)
    service.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == '__main__':
    main()