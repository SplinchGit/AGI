"""
Shared memory and knowledge management for AI agents
"""

from typing import Dict, Any, List, Optional, Set
import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
import threading
from collections import defaultdict, OrderedDict
import hashlib

class SharedMemory:
    """Shared memory system for AI agents"""
    
    def __init__(self, workspace_path: str):
        self.workspace = Path(workspace_path)
        self.memory_file = self.workspace / "shared_memory.json"
        self.lock = threading.RLock()
        
        # Memory structures
        self.short_term_memory = OrderedDict()  # Recent items, LRU cache
        self.long_term_memory = {}  # Persistent important items
        self.working_memory = {}  # Current context and active items
        self.episodic_memory = []  # Sequence of events/experiences
        
        # Memory limits
        self.max_short_term = 1000
        self.max_episodic = 5000
        
        # Load existing memory
        self.load_memory()
    
    def store_short_term(self, key: str, value: Any, ttl_hours: int = 24):
        """Store item in short-term memory with TTL"""
        with self.lock:
            item = {
                'value': value,
                'stored_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(hours=ttl_hours)).isoformat(),
                'access_count': 0,
                'last_accessed': datetime.now().isoformat()
            }
            
            self.short_term_memory[key] = item
            
            # Maintain size limit
            while len(self.short_term_memory) > self.max_short_term:
                self.short_term_memory.popitem(last=False)
    
    def retrieve_short_term(self, key: str) -> Optional[Any]:
        """Retrieve item from short-term memory"""
        with self.lock:
            if key not in self.short_term_memory:
                return None
            
            item = self.short_term_memory[key]
            
            # Check if expired
            if datetime.fromisoformat(item['expires_at']) < datetime.now():
                del self.short_term_memory[key]
                return None
            
            # Update access statistics
            item['access_count'] += 1
            item['last_accessed'] = datetime.now().isoformat()
            
            # Move to end (LRU)
            self.short_term_memory.move_to_end(key)
            
            return item['value']
    
    def store_long_term(self, key: str, value: Any, importance: float = 0.5):
        """Store item in long-term memory"""
        with self.lock:
            self.long_term_memory[key] = {
                'value': value,
                'importance': importance,
                'stored_at': datetime.now().isoformat(),
                'access_count': 0,
                'last_accessed': None
            }
            
            # Auto-save if important
            if importance > 0.8:
                self.save_memory()
    
    def retrieve_long_term(self, key: str) -> Optional[Any]:
        """Retrieve item from long-term memory"""
        with self.lock:
            if key not in self.long_term_memory:
                return None
            
            item = self.long_term_memory[key]
            item['access_count'] += 1
            item['last_accessed'] = datetime.now().isoformat()
            
            return item['value']
    
    def set_working_memory(self, context: Dict[str, Any]):
        """Set current working memory context"""
        with self.lock:
            self.working_memory = {
                'context': context,
                'set_at': datetime.now().isoformat()
            }
    
    def get_working_memory(self) -> Dict[str, Any]:
        """Get current working memory context"""
        with self.lock:
            return self.working_memory.get('context', {})
    
    def add_episode(self, episode: Dict[str, Any]):
        """Add an episode to episodic memory"""
        with self.lock:
            episode_entry = {
                'episode': episode,
                'timestamp': datetime.now().isoformat(),
                'id': f"episode_{len(self.episodic_memory)}"
            }
            
            self.episodic_memory.append(episode_entry)
            
            # Maintain size limit
            if len(self.episodic_memory) > self.max_episodic:
                self.episodic_memory = self.episodic_memory[-self.max_episodic:]
    
    def search_episodes(self, query: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """Search episodic memory"""
        with self.lock:
            matches = []
            
            for episode_entry in reversed(self.episodic_memory):  # Most recent first
                episode = episode_entry['episode']
                score = 0
                
                # Simple matching based on query keys
                for key, value in query.items():
                    if key in episode and episode[key] == value:
                        score += 1
                    elif key in episode and str(value).lower() in str(episode[key]).lower():
                        score += 0.5
                
                if score > 0:
                    matches.append({
                        'episode': episode_entry,
                        'relevance_score': score
                    })
                
                if len(matches) >= limit:
                    break
            
            # Sort by relevance score
            matches.sort(key=lambda x: x['relevance_score'], reverse=True)
            return [m['episode'] for m in matches]
    
    def cleanup_expired(self):
        """Remove expired items from memory"""
        with self.lock:
            now = datetime.now()
            
            # Clean short-term memory
            expired_keys = []
            for key, item in self.short_term_memory.items():
                if datetime.fromisoformat(item['expires_at']) < now:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.short_term_memory[key]
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        with self.lock:
            self.cleanup_expired()
            
            return {
                'short_term_count': len(self.short_term_memory),
                'long_term_count': len(self.long_term_memory),
                'episodic_count': len(self.episodic_memory),
                'working_memory_set': bool(self.working_memory),
                'total_memory_items': len(self.short_term_memory) + len(self.long_term_memory) + len(self.episodic_memory)
            }
    
    def save_memory(self):
        """Save memory to disk"""
        with self.lock:
            try:
                memory_data = {
                    'long_term_memory': self.long_term_memory,
                    'episodic_memory': self.episodic_memory,
                    'saved_at': datetime.now().isoformat()
                }
                
                with open(self.memory_file, 'w', encoding='utf-8') as f:
                    json.dump(memory_data, f, indent=2, ensure_ascii=False)
                    
            except Exception as e:
                print(f"Error saving shared memory: {e}")
    
    def load_memory(self):
        """Load memory from disk"""
        if not self.memory_file.exists():
            return
        
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                memory_data = json.load(f)
                
            with self.lock:
                self.long_term_memory = memory_data.get('long_term_memory', {})
                self.episodic_memory = memory_data.get('episodic_memory', [])
                
        except Exception as e:
            print(f"Error loading shared memory: {e}")

class KnowledgeBase:
    """Structured knowledge base for AI agents"""
    
    def __init__(self, workspace_path: str):
        self.workspace = Path(workspace_path)
        self.kb_file = self.workspace / "knowledge_base.json"
        self.lock = threading.RLock()
        
        # Knowledge structures
        self.concepts = {}  # concept_id -> concept_data
        self.relationships = defaultdict(list)  # concept_id -> [related_concepts]
        self.facts = {}  # fact_id -> fact_data
        self.rules = {}  # rule_id -> rule_data
        self.patterns = {}  # pattern_id -> pattern_data
        
        # Indexes for fast lookup
        self.concept_index = defaultdict(set)  # tag -> {concept_ids}
        self.fact_index = defaultdict(set)  # subject -> {fact_ids}
        
        # Load existing knowledge
        self.load_knowledge_base()
    
    def add_concept(self, concept_id: str, concept_data: Dict[str, Any]) -> bool:
        """Add a concept to the knowledge base"""
        with self.lock:
            self.concepts[concept_id] = {
                **concept_data,
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'access_count': 0
            }
            
            # Update indexes
            for tag in concept_data.get('tags', []):
                self.concept_index[tag].add(concept_id)
            
            return True
    
    def get_concept(self, concept_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a concept"""
        with self.lock:
            if concept_id not in self.concepts:
                return None
            
            concept = self.concepts[concept_id]
            concept['access_count'] += 1
            concept['last_accessed'] = datetime.now().isoformat()
            
            return concept
    
    def add_relationship(self, from_concept: str, to_concept: str, 
                        relationship_type: str, strength: float = 1.0):
        """Add a relationship between concepts"""
        with self.lock:
            relationship = {
                'to_concept': to_concept,
                'type': relationship_type,
                'strength': strength,
                'created_at': datetime.now().isoformat()
            }
            
            self.relationships[from_concept].append(relationship)
    
    def get_related_concepts(self, concept_id: str, 
                           relationship_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get concepts related to a given concept"""
        with self.lock:
            if concept_id not in self.relationships:
                return []
            
            related = self.relationships[concept_id]
            
            if relationship_type:
                related = [r for r in related if r['type'] == relationship_type]
            
            # Sort by relationship strength
            related.sort(key=lambda x: x['strength'], reverse=True)
            
            return related
    
    def add_fact(self, fact_id: str, subject: str, predicate: str, 
                object_value: Any, confidence: float = 1.0):
        """Add a fact to the knowledge base"""
        with self.lock:
            fact = {
                'subject': subject,
                'predicate': predicate,
                'object': object_value,
                'confidence': confidence,
                'created_at': datetime.now().isoformat(),
                'source': 'system'
            }
            
            self.facts[fact_id] = fact
            self.fact_index[subject].add(fact_id)
    
    def get_facts_about(self, subject: str) -> List[Dict[str, Any]]:
        """Get all facts about a subject"""
        with self.lock:
            fact_ids = self.fact_index.get(subject, set())
            return [self.facts[fid] for fid in fact_ids if fid in self.facts]
    
    def add_rule(self, rule_id: str, conditions: List[Dict[str, Any]], 
                conclusions: List[Dict[str, Any]], confidence: float = 1.0):
        """Add an inference rule"""
        with self.lock:
            rule = {
                'conditions': conditions,
                'conclusions': conclusions,
                'confidence': confidence,
                'created_at': datetime.now().isoformat(),
                'applications': 0
            }
            
            self.rules[rule_id] = rule
    
    def add_pattern(self, pattern_id: str, pattern_data: Dict[str, Any]):
        """Add a learned pattern"""
        with self.lock:
            pattern = {
                **pattern_data,
                'created_at': datetime.now().isoformat(),
                'confidence': pattern_data.get('confidence', 0.5),
                'applications': 0
            }
            
            self.patterns[pattern_id] = pattern
    
    def search_concepts(self, query: str, tags: Optional[List[str]] = None) -> List[str]:
        """Search for concepts"""
        with self.lock:
            matching_concepts = set()
            
            # Search by tags
            if tags:
                for tag in tags:
                    matching_concepts.update(self.concept_index.get(tag, set()))
            
            # Search by name/description
            query_lower = query.lower()
            for concept_id, concept_data in self.concepts.items():
                if query_lower in concept_data.get('name', '').lower():
                    matching_concepts.add(concept_id)
                elif query_lower in concept_data.get('description', '').lower():
                    matching_concepts.add(concept_id)
            
            return list(matching_concepts)
    
    def infer_new_facts(self) -> List[Dict[str, Any]]:
        """Apply inference rules to derive new facts"""
        with self.lock:
            new_facts = []
            
            for rule_id, rule in self.rules.items():
                # Simple rule application - check if conditions are met
                conditions_met = True
                
                for condition in rule['conditions']:
                    # This is a simplified implementation
                    subject = condition.get('subject')
                    predicate = condition.get('predicate')
                    
                    facts_about_subject = self.get_facts_about(subject)
                    condition_satisfied = any(
                        fact['predicate'] == predicate 
                        for fact in facts_about_subject
                    )
                    
                    if not condition_satisfied:
                        conditions_met = False
                        break
                
                if conditions_met:
                    # Apply conclusions
                    for conclusion in rule['conclusions']:
                        new_fact_id = f"inferred_{len(self.facts)}_{rule_id}"
                        new_fact = {
                            'subject': conclusion.get('subject'),
                            'predicate': conclusion.get('predicate'),
                            'object': conclusion.get('object'),
                            'confidence': rule['confidence'],
                            'created_at': datetime.now().isoformat(),
                            'source': f'inference_rule_{rule_id}'
                        }
                        
                        new_facts.append(new_fact)
                        self.facts[new_fact_id] = new_fact
                        self.fact_index[new_fact['subject']].add(new_fact_id)
                    
                    # Update rule usage
                    self.rules[rule_id]['applications'] += 1
            
            return new_facts
    
    def get_knowledge_summary(self) -> Dict[str, Any]:
        """Get summary of knowledge base contents"""
        with self.lock:
            return {
                'concept_count': len(self.concepts),
                'relationship_count': sum(len(rels) for rels in self.relationships.values()),
                'fact_count': len(self.facts),
                'rule_count': len(self.rules),
                'pattern_count': len(self.patterns),
                'indexed_tags': len(self.concept_index),
                'indexed_subjects': len(self.fact_index)
            }
    
    def save_knowledge_base(self):
        """Save knowledge base to disk"""
        with self.lock:
            try:
                kb_data = {
                    'concepts': self.concepts,
                    'relationships': dict(self.relationships),
                    'facts': self.facts,
                    'rules': self.rules,
                    'patterns': self.patterns,
                    'saved_at': datetime.now().isoformat()
                }
                
                with open(self.kb_file, 'w', encoding='utf-8') as f:
                    json.dump(kb_data, f, indent=2, ensure_ascii=False)
                    
            except Exception as e:
                print(f"Error saving knowledge base: {e}")
    
    def load_knowledge_base(self):
        """Load knowledge base from disk"""
        if not self.kb_file.exists():
            return
        
        try:
            with open(self.kb_file, 'r', encoding='utf-8') as f:
                kb_data = json.load(f)
            
            with self.lock:
                self.concepts = kb_data.get('concepts', {})
                self.relationships = defaultdict(list, kb_data.get('relationships', {}))
                self.facts = kb_data.get('facts', {})
                self.rules = kb_data.get('rules', {})
                self.patterns = kb_data.get('patterns', {})
                
                # Rebuild indexes
                self._rebuild_indexes()
                
        except Exception as e:
            print(f"Error loading knowledge base: {e}")
    
    def _rebuild_indexes(self):
        """Rebuild search indexes"""
        self.concept_index.clear()
        self.fact_index.clear()
        
        # Rebuild concept index
        for concept_id, concept_data in self.concepts.items():
            for tag in concept_data.get('tags', []):
                self.concept_index[tag].add(concept_id)
        
        # Rebuild fact index
        for fact_id, fact_data in self.facts.items():
            subject = fact_data.get('subject')
            if subject:
                self.fact_index[subject].add(fact_id)