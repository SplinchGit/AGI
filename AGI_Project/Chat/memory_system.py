"""
Memory System - Handles persistent memory across sessions
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import sqlite3
import hashlib


class MemorySystem:
    def __init__(self, config: Dict):
        """Initialize memory system with configuration"""
        self.config = config
        self.enabled = config.get("enabled", True)
        self.memory_types = config.get("memory_types", ["conversations", "experiences", "knowledge"])
        self.max_memory_size_mb = config.get("max_memory_size_mb", 100)
        
        # Memory storage paths
        self.memory_base_path = "Data/memory"
        os.makedirs(self.memory_base_path, exist_ok=True)
        
        # Initialize SQLite database for efficient querying
        self.db_path = os.path.join(self.memory_base_path, "memory.db")
        self._init_database()
        
        # In-memory caches
        self.conversation_cache = []
        self.experience_cache = []
        self.knowledge_cache = {}
    
    def _init_database(self):
        """Initialize SQLite database for memory storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                sender TEXT NOT NULL,
                content TEXT NOT NULL,
                session_id TEXT,
                keywords TEXT
            )
        """)
        
        # Experiences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                source TEXT NOT NULL,
                content TEXT NOT NULL,
                importance REAL DEFAULT 0.5,
                keywords TEXT
            )
        """)
        
        # Knowledge table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                source TEXT NOT NULL,
                fact TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                keywords TEXT,
                category TEXT
            )
        """)
        
        # Create indexes for faster searching
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_timestamp ON conversations(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_sender ON conversations(sender)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_exp_timestamp ON experiences(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge(category)")
        
        conn.commit()
        conn.close()
    
    def add_message(self, message: Dict):
        """Add a message to conversation memory"""
        if not self.enabled:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        keywords = self._extract_keywords(message.get("content", ""))
        
        cursor.execute("""
            INSERT INTO conversations (timestamp, sender, content, session_id, keywords)
            VALUES (?, ?, ?, ?, ?)
        """, (
            message.get("timestamp", datetime.now().isoformat()),
            message.get("sender", "Unknown"),
            message.get("content", ""),
            message.get("session_id", ""),
            json.dumps(keywords)
        ))
        
        conn.commit()
        conn.close()
        
        # Update cache
        self.conversation_cache.append(message)
        if len(self.conversation_cache) > 100:
            self.conversation_cache = self.conversation_cache[-100:]
        
        # Check for experiences and knowledge
        self._extract_experience(message)
        self._extract_knowledge(message)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "must", "shall", "can", "need"}
        
        words = text.lower().split()
        keywords = []
        
        for word in words:
            # Clean punctuation
            word = word.strip(".,!?;:\"'")
            if len(word) > 3 and word not in common_words:
                keywords.append(word)
        
        return list(set(keywords))[:10]  # Return top 10 unique keywords
    
    def _extract_experience(self, message: Dict):
        """Extract experiences from messages"""
        content = message.get("content", "").lower()
        sender = message.get("sender", "")
        
        # Look for experience indicators
        experience_indicators = [
            "i learned", "i discovered", "i found out", "i realized",
            "turns out", "apparently", "interestingly", "surprisingly"
        ]
        
        importance = 0.5
        for indicator in experience_indicators:
            if indicator in content:
                importance = 0.8
                break
        
        # Store significant messages as experiences
        if importance > 0.6 or len(content) > 100:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO experiences (timestamp, source, content, importance, keywords)
                VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                sender,
                message.get("content", ""),
                importance,
                json.dumps(self._extract_keywords(content))
            ))
            
            conn.commit()
            conn.close()
    
    def _extract_knowledge(self, message: Dict):
        """Extract factual knowledge from messages"""
        content = message.get("content", "")
        sender = message.get("sender", "")
        
        # Look for factual patterns
        fact_patterns = [
            " is ", " are ", " means ", " refers to ", " defined as ",
            " works by ", " consists of ", " includes ", " requires "
        ]
        
        for pattern in fact_patterns:
            if pattern in content:
                # Generate unique ID for fact
                fact_id = hashlib.md5(content.encode()).hexdigest()[:12]
                
                # Determine category
                category = self._categorize_knowledge(content)
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Check if fact already exists
                cursor.execute("SELECT id FROM knowledge WHERE id = ?", (fact_id,))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO knowledge (id, timestamp, source, fact, confidence, keywords, category)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        fact_id,
                        datetime.now().isoformat(),
                        sender,
                        content,
                        0.7,  # Default confidence
                        json.dumps(self._extract_keywords(content)),
                        category
                    ))
                
                conn.commit()
                conn.close()
                break
    
    def _categorize_knowledge(self, content: str) -> str:
        """Categorize knowledge based on content"""
        content_lower = content.lower()
        
        categories = {
            "technical": ["code", "programming", "software", "algorithm", "api", "function", "class", "method"],
            "ai": ["ai", "artificial intelligence", "machine learning", "neural", "model", "training"],
            "general": ["fact", "information", "data", "statistic"],
            "personal": ["i am", "my", "me", "james", "claude"],
            "process": ["how to", "steps", "process", "procedure", "method"]
        }
        
        for category, keywords in categories.items():
            if any(keyword in content_lower for keyword in keywords):
                return category
        
        return "general"
    
    def search_memory(self, query: str, memory_type: str = "all", limit: int = 10) -> List[Dict]:
        """Search through memories"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        results = []
        query_keywords = self._extract_keywords(query)
        
        if memory_type in ["all", "conversations"]:
            cursor.execute("""
                SELECT timestamp, sender, content FROM conversations
                WHERE content LIKE ? OR keywords LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit))
            
            for row in cursor.fetchall():
                results.append({
                    "type": "conversation",
                    "timestamp": row[0],
                    "sender": row[1],
                    "content": row[2]
                })
        
        if memory_type in ["all", "experiences"]:
            cursor.execute("""
                SELECT timestamp, source, content, importance FROM experiences
                WHERE content LIKE ? OR keywords LIKE ?
                ORDER BY importance DESC, timestamp DESC
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit))
            
            for row in cursor.fetchall():
                results.append({
                    "type": "experience",
                    "timestamp": row[0],
                    "source": row[1],
                    "content": row[2],
                    "importance": row[3]
                })
        
        if memory_type in ["all", "knowledge"]:
            cursor.execute("""
                SELECT timestamp, source, fact, confidence, category FROM knowledge
                WHERE fact LIKE ? OR keywords LIKE ? OR category = ?
                ORDER BY confidence DESC
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", query, limit))
            
            for row in cursor.fetchall():
                results.append({
                    "type": "knowledge",
                    "timestamp": row[0],
                    "source": row[1],
                    "fact": row[2],
                    "confidence": row[3],
                    "category": row[4]
                })
        
        conn.close()
        return results[:limit]
    
    def get_memory_stats(self) -> Dict:
        """Get statistics about stored memories"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        cursor.execute("SELECT COUNT(*) FROM conversations")
        stats["total_conversations"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM experiences")
        stats["total_experiences"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM knowledge")
        stats["total_knowledge"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT sender) FROM conversations")
        stats["unique_participants"] = cursor.fetchone()[0]
        
        # Get database size
        stats["database_size_mb"] = os.path.getsize(self.db_path) / (1024 * 1024)
        
        conn.close()
        return stats
    
    def cleanup_old_memories(self, days_to_keep: int = 30):
        """Clean up old memories to save space"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now().isoformat()[:10]  # Keep for simplicity
        
        # Delete old conversations (keep important ones)
        cursor.execute("""
            DELETE FROM conversations
            WHERE timestamp < date('now', '-' || ? || ' days')
            AND sender NOT IN ('James', 'Claude', 'James (Clone)')
        """, (days_to_keep,))
        
        # Delete low-importance experiences
        cursor.execute("""
            DELETE FROM experiences
            WHERE timestamp < date('now', '-' || ? || ' days')
            AND importance < 0.5
        """, (days_to_keep,))
        
        conn.commit()
        conn.close()
    
    def export_memories(self, export_path: str, format: str = "json"):
        """Export all memories to file"""
        memories = {
            "exported_at": datetime.now().isoformat(),
            "conversations": self.search_memory("", "conversations", limit=10000),
            "experiences": self.search_memory("", "experiences", limit=10000),
            "knowledge": self.search_memory("", "knowledge", limit=10000),
            "stats": self.get_memory_stats()
        }
        
        if format == "json":
            with open(export_path, 'w') as f:
                json.dump(memories, f, indent=2)