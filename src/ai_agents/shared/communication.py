"""
Communication infrastructure for AI agents
"""

from typing import Dict, Any, List, Optional, Callable
import asyncio
import json
from datetime import datetime
from collections import defaultdict, deque
import threading
from enum import Enum

class MessageType(Enum):
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    STATUS_UPDATE = "status_update"
    COLLABORATION_REQUEST = "collaboration_request"
    KNOWLEDGE_SHARE = "knowledge_share"
    ERROR_REPORT = "error_report"
    SYSTEM_EVENT = "system_event"

class MessagePriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

class Message:
    """Represents a message between AI agents"""
    
    def __init__(self, sender: str, recipient: str, message_type: MessageType,
                 content: Dict[str, Any], priority: MessagePriority = MessagePriority.NORMAL):
        self.id = f"msg_{datetime.now().timestamp()}_{sender}_{recipient}"
        self.sender = sender
        self.recipient = recipient
        self.message_type = message_type
        self.content = content
        self.priority = priority
        self.timestamp = datetime.now().isoformat()
        self.delivered = False
        self.processed = False
        self.response_id = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            'id': self.id,
            'sender': self.sender,
            'recipient': self.recipient,
            'message_type': self.message_type.value,
            'content': self.content,
            'priority': self.priority.value,
            'timestamp': self.timestamp,
            'delivered': self.delivered,
            'processed': self.processed,
            'response_id': self.response_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary"""
        msg = cls(
            sender=data['sender'],
            recipient=data['recipient'],
            message_type=MessageType(data['message_type']),
            content=data['content'],
            priority=MessagePriority(data['priority'])
        )
        msg.id = data['id']
        msg.timestamp = data['timestamp']
        msg.delivered = data['delivered']
        msg.processed = data['processed']
        msg.response_id = data.get('response_id')
        return msg

class MessageBus:
    """Central message bus for AI agent communication"""
    
    def __init__(self):
        self.subscribers = defaultdict(list)  # message_type -> [handlers]
        self.message_queue = deque()
        self.message_history = []
        self.delivery_callbacks = {}
        self.running = False
        self.lock = threading.Lock()
        self.processing_thread = None
        
    def subscribe(self, message_type: MessageType, handler: Callable[[Message], None]):
        """Subscribe to messages of a specific type"""
        with self.lock:
            self.subscribers[message_type].append(handler)
    
    def unsubscribe(self, message_type: MessageType, handler: Callable[[Message], None]):
        """Unsubscribe from messages"""
        with self.lock:
            if handler in self.subscribers[message_type]:
                self.subscribers[message_type].remove(handler)
    
    def publish(self, message: Message, delivery_callback: Optional[Callable] = None) -> str:
        """Publish a message to the bus"""
        with self.lock:
            self.message_queue.append(message)
            if delivery_callback:
                self.delivery_callbacks[message.id] = delivery_callback
        
        return message.id
    
    def send_message(self, sender: str, recipient: str, message_type: MessageType,
                    content: Dict[str, Any], priority: MessagePriority = MessagePriority.NORMAL) -> str:
        """Send a message between agents"""
        message = Message(sender, recipient, message_type, content, priority)
        return self.publish(message)
    
    def start_processing(self):
        """Start processing messages"""
        self.running = True
        self.processing_thread = threading.Thread(target=self._process_messages, daemon=True)
        self.processing_thread.start()
    
    def stop_processing(self):
        """Stop processing messages"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
    
    def _process_messages(self):
        """Process messages from the queue"""
        while self.running:
            try:
                if self.message_queue:
                    with self.lock:
                        message = self.message_queue.popleft()
                    
                    self._deliver_message(message)
                else:
                    # Sleep briefly if no messages
                    threading.Event().wait(0.1)
                    
            except Exception as e:
                print(f"Error processing message: {e}")
                threading.Event().wait(1)  # Wait before retrying
    
    def _deliver_message(self, message: Message):
        """Deliver a message to subscribers"""
        try:
            handlers = self.subscribers.get(message.message_type, [])
            
            # Also check for wildcard subscribers (if any)
            if message.recipient != "*":
                handlers.extend(self.subscribers.get(f"agent_{message.recipient}", []))
            
            delivered = False
            for handler in handlers:
                try:
                    handler(message)
                    delivered = True
                except Exception as e:
                    print(f"Error in message handler: {e}")
            
            message.delivered = delivered
            
            # Store in history
            self.message_history.append(message)
            if len(self.message_history) > 10000:  # Keep last 10k messages
                self.message_history = self.message_history[-10000:]
            
            # Call delivery callback if provided
            callback = self.delivery_callbacks.pop(message.id, None)
            if callback:
                callback(message, delivered)
                
        except Exception as e:
            print(f"Error delivering message {message.id}: {e}")
    
    def get_message_history(self, sender: Optional[str] = None,
                           recipient: Optional[str] = None,
                           message_type: Optional[MessageType] = None,
                           limit: int = 100) -> List[Message]:
        """Get message history with optional filtering"""
        filtered_messages = self.message_history
        
        if sender:
            filtered_messages = [m for m in filtered_messages if m.sender == sender]
        
        if recipient:
            filtered_messages = [m for m in filtered_messages if m.recipient == recipient]
        
        if message_type:
            filtered_messages = [m for m in filtered_messages if m.message_type == message_type]
        
        return filtered_messages[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get message bus statistics"""
        total_messages = len(self.message_history)
        delivered_messages = sum(1 for m in self.message_history if m.delivered)
        processed_messages = sum(1 for m in self.message_history if m.processed)
        
        message_types = defaultdict(int)
        for message in self.message_history:
            message_types[message.message_type.value] += 1
        
        return {
            'total_messages': total_messages,
            'delivered_messages': delivered_messages,
            'processed_messages': processed_messages,
            'delivery_rate': delivered_messages / total_messages if total_messages > 0 else 0,
            'processing_rate': processed_messages / total_messages if total_messages > 0 else 0,
            'queued_messages': len(self.message_queue),
            'message_types': dict(message_types),
            'active_subscribers': sum(len(handlers) for handlers in self.subscribers.values())
        }

class EventBroker:
    """Event broker for system-wide events"""
    
    def __init__(self):
        self.event_handlers = defaultdict(list)
        self.event_history = deque(maxlen=1000)
        self.lock = threading.Lock()
    
    def subscribe_to_event(self, event_type: str, handler: Callable[[Dict[str, Any]], None]):
        """Subscribe to system events"""
        with self.lock:
            self.event_handlers[event_type].append(handler)
    
    def unsubscribe_from_event(self, event_type: str, handler: Callable[[Dict[str, Any]], None]):
        """Unsubscribe from events"""
        with self.lock:
            if handler in self.event_handlers[event_type]:
                self.event_handlers[event_type].remove(handler)
    
    def emit_event(self, event_type: str, event_data: Dict[str, Any]):
        """Emit a system event"""
        event = {
            'type': event_type,
            'data': event_data,
            'timestamp': datetime.now().isoformat(),
            'id': f"event_{datetime.now().timestamp()}"
        }
        
        with self.lock:
            self.event_history.append(event)
        
        # Notify handlers
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"Error in event handler for {event_type}: {e}")
    
    def get_event_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get event history"""
        events = list(self.event_history)
        
        if event_type:
            events = [e for e in events if e['type'] == event_type]
        
        return events[-limit:]

class CommunicationChannel:
    """Direct communication channel between two agents"""
    
    def __init__(self, agent1: str, agent2: str, message_bus: MessageBus):
        self.agent1 = agent1
        self.agent2 = agent2
        self.message_bus = message_bus
        self.channel_history = []
        self.is_active = True
    
    def send_to_partner(self, sender: str, message_type: MessageType, 
                       content: Dict[str, Any]) -> str:
        """Send message to the partner in this channel"""
        recipient = self.agent2 if sender == self.agent1 else self.agent1
        
        if not self.is_active:
            raise ValueError("Communication channel is not active")
        
        message_id = self.message_bus.send_message(sender, recipient, message_type, content)
        
        # Track in channel history
        self.channel_history.append({
            'message_id': message_id,
            'sender': sender,
            'recipient': recipient,
            'timestamp': datetime.now().isoformat()
        })
        
        return message_id
    
    def get_conversation_history(self, limit: int = 50) -> List[Message]:
        """Get conversation history between the two agents"""
        return self.message_bus.get_message_history(
            sender=None,  # Get messages from both agents
            recipient=None,
            limit=limit
        )
    
    def close_channel(self):
        """Close the communication channel"""
        self.is_active = False
    
    def reopen_channel(self):
        """Reopen the communication channel"""
        self.is_active = True

class ConversationManager:
    """Manages conversations between multiple AI agents"""
    
    def __init__(self, message_bus: MessageBus):
        self.message_bus = message_bus
        self.active_conversations = {}
        self.conversation_history = []
    
    def start_conversation(self, participants: List[str], topic: str) -> str:
        """Start a new conversation"""
        conversation_id = f"conv_{datetime.now().timestamp()}_{len(participants)}"
        
        conversation = {
            'id': conversation_id,
            'participants': participants,
            'topic': topic,
            'started_at': datetime.now().isoformat(),
            'messages': [],
            'status': 'active'
        }
        
        self.active_conversations[conversation_id] = conversation
        
        # Notify participants
        for participant in participants:
            self.message_bus.send_message(
                sender="system",
                recipient=participant,
                message_type=MessageType.SYSTEM_EVENT,
                content={
                    'event': 'conversation_started',
                    'conversation_id': conversation_id,
                    'topic': topic,
                    'participants': participants
                }
            )
        
        return conversation_id
    
    def add_message_to_conversation(self, conversation_id: str, message: Message):
        """Add a message to a conversation"""
        if conversation_id in self.active_conversations:
            self.active_conversations[conversation_id]['messages'].append(message.to_dict())
    
    def end_conversation(self, conversation_id: str):
        """End a conversation"""
        if conversation_id in self.active_conversations:
            conversation = self.active_conversations.pop(conversation_id)
            conversation['status'] = 'ended'
            conversation['ended_at'] = datetime.now().isoformat()
            
            self.conversation_history.append(conversation)
            
            # Notify participants
            for participant in conversation['participants']:
                self.message_bus.send_message(
                    sender="system",
                    recipient=participant,
                    message_type=MessageType.SYSTEM_EVENT,
                    content={
                        'event': 'conversation_ended',
                        'conversation_id': conversation_id
                    }
                )
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation details"""
        return self.active_conversations.get(conversation_id)
    
    def get_active_conversations(self) -> List[Dict[str, Any]]:
        """Get all active conversations"""
        return list(self.active_conversations.values())