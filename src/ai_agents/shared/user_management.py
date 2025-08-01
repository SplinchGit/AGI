"""
Dynamic User Management System for AGI Chat
Supports three default users (human, Claude, Qwen) with permission-based dynamic user addition.
Memory efficient - only creates user instances when they're actually active.
"""

from typing import Dict, Any, List, Optional, Set, Callable
from enum import Enum
from datetime import datetime, timedelta
import json
import threading
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict


class UserType(Enum):
    HUMAN = "human"
    AI_CLAUDE = "ai_claude"
    AI_QWEN = "ai_qwen"
    AI_GEMINI = "ai_gemini"
    AI_CUSTOM = "ai_custom"
    SYSTEM = "system"


class Permission(Enum):
    READ_CHAT = "read_chat"
    SEND_MESSAGE = "send_message"
    ADD_USER = "add_user"
    REMOVE_USER = "remove_user"
    MODIFY_PERMISSIONS = "modify_permissions"
    ACCESS_MEMORY = "access_memory"
    SYSTEM_ADMIN = "system_admin"


class UserStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    OFFLINE = "offline"


@dataclass
class UserConfig:
    """Configuration for a user"""
    user_id: str
    display_name: str
    user_type: UserType
    permissions: Set[Permission]
    color_theme: str
    max_message_length: int = 2000
    rate_limit_per_minute: int = 30
    auto_timeout_minutes: int = 30
    created_at: str = ""
    last_active: str = ""
    custom_settings: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at == "":
            self.created_at = datetime.now().isoformat()
        if self.custom_settings is None:
            self.custom_settings = {}


class ActiveUser:
    """Represents an active user instance (memory efficient)"""
    
    def __init__(self, config: UserConfig):
        self.config = config
        self.status = UserStatus.ACTIVE
        self.message_count = 0
        self.last_message_time = None
        self.session_start = datetime.now()
        self.rate_limit_tracker = []
        self.lock = threading.Lock()
    
    def can_send_message(self) -> bool:
        """Check if user can send a message (rate limiting)"""
        with self.lock:
            now = datetime.now()
            # Clean old entries
            self.rate_limit_tracker = [
                timestamp for timestamp in self.rate_limit_tracker 
                if now - timestamp < timedelta(minutes=1)
            ]
            
            # Check rate limit
            if len(self.rate_limit_tracker) >= self.config.rate_limit_per_minute:
                return False
            
            return Permission.SEND_MESSAGE in self.config.permissions
    
    def record_message(self):
        """Record that user sent a message"""
        with self.lock:
            self.message_count += 1
            self.last_message_time = datetime.now()
            self.rate_limit_tracker.append(datetime.now())
            self.config.last_active = datetime.now().isoformat()
    
    def is_timed_out(self) -> bool:
        """Check if user has timed out"""
        if self.last_message_time is None:
            return False
        
        timeout_delta = timedelta(minutes=self.config.auto_timeout_minutes)
        return datetime.now() - self.last_message_time > timeout_delta
    
    def get_stats(self) -> Dict[str, Any]:
        """Get user statistics"""
        return {
            'user_id': self.config.user_id,
            'display_name': self.config.display_name,
            'status': self.status.value,
            'message_count': self.message_count,
            'session_duration': str(datetime.now() - self.session_start),
            'last_active': self.config.last_active,
            'rate_limit_remaining': max(0, self.config.rate_limit_per_minute - len(self.rate_limit_tracker))
        }


class UserManager:
    """Manages users dynamically with memory efficiency"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = Path(config_file) if config_file else Path("data/users/user_configs.json")
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # User configurations (persistent)
        self.user_configs: Dict[str, UserConfig] = {}
        
        # Active user instances (memory efficient - only when needed)
        self.active_users: Dict[str, ActiveUser] = {}
        
        # Event callbacks
        self.event_callbacks: Dict[str, List[Callable]] = defaultdict(list)
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Initialize with default users
        self._setup_default_users()
        self._load_user_configs()
        
        # Start cleanup thread
        self._start_cleanup_thread()
    
    def _setup_default_users(self):
        """Set up the four default users"""
        default_users = [
            UserConfig(
                user_id="human_user",
                display_name="You",
                user_type=UserType.HUMAN,
                permissions={Permission.READ_CHAT, Permission.SEND_MESSAGE, Permission.ACCESS_MEMORY, Permission.ADD_USER, Permission.REMOVE_USER},
                color_theme="#2ECC71",  # Green
                rate_limit_per_minute=60
            ),
            UserConfig(
                user_id="claude_ai",
                display_name="Claude",
                user_type=UserType.AI_CLAUDE,
                permissions={Permission.READ_CHAT, Permission.SEND_MESSAGE, Permission.ACCESS_MEMORY},
                color_theme="#3498DB",  # Blue
                rate_limit_per_minute=30
            ),
            UserConfig(
                user_id="qwen_ai",
                display_name="Qwen",
                user_type=UserType.AI_QWEN,
                permissions={Permission.READ_CHAT, Permission.SEND_MESSAGE, Permission.ACCESS_MEMORY},
                color_theme="#F39C12",  # Orange
                rate_limit_per_minute=30
            ),
            UserConfig(
                user_id="gemini_ai",
                display_name="Gemini",
                user_type=UserType.AI_GEMINI,
                permissions={Permission.READ_CHAT, Permission.SEND_MESSAGE, Permission.ACCESS_MEMORY},
                color_theme="#4285F4",  # Google Blue
                rate_limit_per_minute=30
            )
        ]
        
        for user_config in default_users:
            self.user_configs[user_config.user_id] = user_config
    
    def _load_user_configs(self):
        """Load user configurations from disk"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                for user_data in data.get('users', []):
                    # Convert permissions back to set
                    permissions = {Permission(p) for p in user_data['permissions']}
                    user_data['permissions'] = permissions
                    user_data['user_type'] = UserType(user_data['user_type'])
                    
                    config = UserConfig(**user_data)
                    self.user_configs[config.user_id] = config
            except Exception as e:
                print(f"Warning: Could not load user configs: {e}")
    
    def _save_user_configs(self):
        """Save user configurations to disk"""
        try:
            # Convert to serializable format
            users_data = []
            for config in self.user_configs.values():
                config_dict = asdict(config)
                config_dict['permissions'] = [p.value for p in config.permissions]
                config_dict['user_type'] = config.user_type.value
                users_data.append(config_dict)
            
            data = {
                'users': users_data,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save user configs: {e}")
    
    def add_user(self, user_config: UserConfig, requester_id: str) -> bool:
        """Add a new user (permission checked)"""
        with self.lock:
            # Check if requester has permission
            if not self._user_has_permission(requester_id, Permission.ADD_USER):
                return False
            
            # Check if user already exists
            if user_config.user_id in self.user_configs:
                return False
            
            self.user_configs[user_config.user_id] = user_config
            self._save_user_configs()
            
            # Emit event
            self._emit_event('user_added', {
                'user_id': user_config.user_id,
                'display_name': user_config.display_name,
                'requester_id': requester_id
            })
            
            return True
    
    def remove_user(self, user_id: str, requester_id: str) -> bool:
        """Remove a user (permission checked)"""
        with self.lock:
            # Check permission
            if not self._user_has_permission(requester_id, Permission.REMOVE_USER):
                return False
            
            # Can't remove default users
            if user_id in self.get_default_users():
                return False
            
            # Check if user exists
            if user_id not in self.user_configs:
                return False
            
            # Remove from active users if present
            if user_id in self.active_users:
                del self.active_users[user_id]
            
            # Remove config
            removed_user = self.user_configs.pop(user_id)
            self._save_user_configs()
            
            # Emit event
            self._emit_event('user_removed', {
                'user_id': user_id,
                'display_name': removed_user.display_name,
                'requester_id': requester_id
            })
            
            return True
    
    def activate_user(self, user_id: str) -> Optional[ActiveUser]:
        """Activate a user (create instance only when needed)"""
        with self.lock:
            if user_id not in self.user_configs:
                return None
            
            if user_id not in self.active_users:
                self.active_users[user_id] = ActiveUser(self.user_configs[user_id])
                
                # Emit event
                self._emit_event('user_activated', {
                    'user_id': user_id,
                    'display_name': self.user_configs[user_id].display_name
                })
            
            return self.active_users[user_id]
    
    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user (free memory)"""
        with self.lock:
            if user_id in self.active_users:
                del self.active_users[user_id]
                
                # Emit event
                self._emit_event('user_deactivated', {
                    'user_id': user_id
                })
                return True
            return False
    
    def get_active_user(self, user_id: str) -> Optional[ActiveUser]:
        """Get active user instance"""
        return self.active_users.get(user_id)
    
    def get_user_config(self, user_id: str) -> Optional[UserConfig]:
        """Get user configuration"""
        return self.user_configs.get(user_id)
    
    def get_all_user_configs(self) -> Dict[str, UserConfig]:
        """Get all user configurations"""
        return self.user_configs.copy()
    
    def get_active_users(self) -> Dict[str, ActiveUser]:
        """Get all active users"""
        return self.active_users.copy()
    
    def get_default_users(self) -> List[str]:
        """Get list of default user IDs"""
        return ['human_user', 'claude_ai', 'qwen_ai', 'gemini_ai']
    
    def update_user_permissions(self, user_id: str, permissions: Set[Permission], requester_id: str) -> bool:
        """Update user permissions"""
        with self.lock:
            # Check permission
            if not self._user_has_permission(requester_id, Permission.MODIFY_PERMISSIONS):
                return False
            
            # Can't modify default users' core permissions
            if user_id in ['human_user', 'claude_ai', 'qwen_ai']:
                # Allow only safe permission additions/removals
                safe_permissions = {Permission.ACCESS_MEMORY}
                if not permissions.issubset(self.user_configs[user_id].permissions.union(safe_permissions)):
                    return False
            
            if user_id in self.user_configs:
                self.user_configs[user_id].permissions = permissions
                self._save_user_configs()
                
                # Update active user if exists
                if user_id in self.active_users:
                    self.active_users[user_id].config.permissions = permissions
                
                return True
            return False
    
    def _user_has_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if user has specific permission"""
        if user_id not in self.user_configs:
            return False
        return permission in self.user_configs[user_id].permissions
    
    def can_user_send_message(self, user_id: str) -> bool:
        """Check if user can send a message"""
        active_user = self.get_active_user(user_id)
        if not active_user:
            return False
        return active_user.can_send_message()
    
    def record_user_message(self, user_id: str):
        """Record that user sent a message"""
        active_user = self.get_active_user(user_id)
        if active_user:
            active_user.record_message()
    
    def get_user_display_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get display information for a user"""
        config = self.get_user_config(user_id)
        if not config:
            return None
        
        active_user = self.get_active_user(user_id)
        status = active_user.status if active_user else UserStatus.OFFLINE
        
        return {
            'user_id': config.user_id,
            'display_name': config.display_name,
            'user_type': config.user_type.value,
            'color_theme': config.color_theme,
            'status': status.value,
            'is_active': user_id in self.active_users
        }
    
    def get_all_display_users(self) -> List[Dict[str, Any]]:
        """Get display info for all users"""
        users = []
        for user_id in self.user_configs:
            info = self.get_user_display_info(user_id)
            if info:
                users.append(info)
        return users
    
    def subscribe_to_events(self, event_type: str, callback: Callable):
        """Subscribe to user management events"""
        self.event_callbacks[event_type].append(callback)
    
    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit user management event"""
        for callback in self.event_callbacks[event_type]:
            try:
                callback(data)
            except Exception as e:
                print(f"Error in user management event callback: {e}")
    
    def _start_cleanup_thread(self):
        """Start thread to cleanup inactive users"""
        def cleanup_loop():
            while True:
                try:
                    with self.lock:
                        to_remove = []
                        for user_id, active_user in self.active_users.items():
                            if active_user.is_timed_out():
                                to_remove.append(user_id)
                        
                        for user_id in to_remove:
                            del self.active_users[user_id]
                            self._emit_event('user_timeout', {'user_id': user_id})
                    
                    # Sleep for 1 minute before next cleanup
                    threading.Event().wait(60)
                    
                except Exception as e:
                    print(f"Error in user cleanup: {e}")
                    threading.Event().wait(60)
        
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get user management statistics"""
        with self.lock:
            total_users = len(self.user_configs)
            active_users = len(self.active_users)
            
            user_types = defaultdict(int)
            for config in self.user_configs.values():
                user_types[config.user_type.value] += 1
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'default_users': len(self.get_default_users()),
                'custom_users': total_users - len(self.get_default_users()),
                'user_types': dict(user_types),
                'memory_efficiency': f"{active_users}/{total_users} users in memory"
            }


# Global user manager instance (singleton pattern)
_user_manager = None
_user_manager_lock = threading.Lock()


def get_user_manager(config_file: Optional[str] = None) -> UserManager:
    """Get global user manager instance"""
    global _user_manager
    with _user_manager_lock:
        if _user_manager is None:
            _user_manager = UserManager(config_file)
        return _user_manager


def reset_user_manager():
    """Reset user manager (for testing)"""
    global _user_manager
    with _user_manager_lock:
        _user_manager = None