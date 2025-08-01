"""
Utility functions for user management in the AGI chat system
"""

from typing import Dict, List, Optional, Set
from .user_management import get_user_manager, UserConfig, UserType, Permission
import json


def create_custom_ai_user(user_id: str, display_name: str, 
                         color_theme: str = "#9B59B6",
                         permissions: Optional[Set[Permission]] = None,
                         requester_id: str = "human_user") -> bool:
    """
    Create a custom AI user with default permissions
    
    Args:
        user_id: Unique identifier for the user
        display_name: Display name for the user
        color_theme: Hex color code for the user's theme
        permissions: Set of permissions (defaults to basic AI permissions)
        requester_id: ID of user making the request
    
    Returns:
        bool: True if user was created successfully
    """
    if permissions is None:
        permissions = {Permission.READ_CHAT, Permission.SEND_MESSAGE, Permission.ACCESS_MEMORY}
    
    user_config = UserConfig(
        user_id=user_id,
        display_name=display_name,
        user_type=UserType.AI_CUSTOM,
        permissions=permissions,
        color_theme=color_theme,
        rate_limit_per_minute=20  # Slightly lower than default AIs
    )
    
    user_manager = get_user_manager()
    return user_manager.add_user(user_config, requester_id)


def activate_default_users() -> Dict[str, bool]:
    """
    Activate all three default users
    
    Returns:
        Dict mapping user_id to activation success
    """
    user_manager = get_user_manager()
    results = {}
    
    default_users = ['human_user', 'claude_ai', 'qwen_ai']
    for user_id in default_users:
        active_user = user_manager.activate_user(user_id)
        results[user_id] = active_user is not None
    
    return results


def get_active_ai_users() -> List[Dict[str, str]]:
    """
    Get list of active AI users with display information
    
    Returns:
        List of dicts with user_id, display_name, user_type
    """
    user_manager = get_user_manager()
    active_users = user_manager.get_active_users()
    
    ai_users = []
    for user_id, active_user in active_users.items():
        config = active_user.config
        if config.user_type in [UserType.AI_CLAUDE, UserType.AI_QWEN, UserType.AI_CUSTOM]:
            ai_users.append({
                'user_id': user_id,
                'display_name': config.display_name,
                'user_type': config.user_type.value,
                'color_theme': config.color_theme
            })
    
    return ai_users


def get_user_color_map() -> Dict[str, str]:
    """
    Get mapping of display name to color theme for all users
    
    Returns:
        Dict mapping display_name to hex color
    """
    user_manager = get_user_manager()
    color_map = {}
    
    for config in user_manager.get_all_user_configs().values():
        color_map[config.display_name] = config.color_theme
    
    return color_map


def can_user_perform_action(user_id: str, action: str) -> bool:
    """
    Check if user can perform a specific action
    
    Args:
        user_id: ID of the user
        action: Action to check ('send_message', 'add_user', etc.)
    
    Returns:
        bool: True if user can perform action
    """
    user_manager = get_user_manager()
    
    # Map actions to permissions
    action_permission_map = {
        'send_message': Permission.SEND_MESSAGE,
        'read_chat': Permission.READ_CHAT,
        'add_user': Permission.ADD_USER,
        'remove_user': Permission.REMOVE_USER,
        'modify_permissions': Permission.MODIFY_PERMISSIONS,
        'access_memory': Permission.ACCESS_MEMORY,
        'system_admin': Permission.SYSTEM_ADMIN
    }
    
    permission = action_permission_map.get(action)
    if not permission:
        return False
    
    config = user_manager.get_user_config(user_id)
    if not config:
        return False
    
    return permission in config.permissions


def get_user_rate_limit_status(user_id: str) -> Optional[Dict[str, int]]:
    """
    Get rate limit status for a user
    
    Args:
        user_id: ID of the user
    
    Returns:
        Dict with rate limit info or None if user not active
    """
    user_manager = get_user_manager()
    active_user = user_manager.get_active_user(user_id)
    
    if not active_user:
        return None
    
    stats = active_user.get_stats()
    return {
        'rate_limit_per_minute': active_user.config.rate_limit_per_minute,
        'rate_limit_remaining': stats['rate_limit_remaining'],
        'message_count': stats['message_count']
    }


def export_user_configs(file_path: str) -> bool:
    """
    Export user configurations to a JSON file
    
    Args:
        file_path: Path to save the JSON file
    
    Returns:
        bool: True if export was successful
    """
    try:
        user_manager = get_user_manager()
        configs = user_manager.get_all_user_configs()
        
        export_data = []
        for config in configs.values():
            config_dict = {
                'user_id': config.user_id,
                'display_name': config.display_name,
                'user_type': config.user_type.value,
                'permissions': [p.value for p in config.permissions],
                'color_theme': config.color_theme,
                'max_message_length': config.max_message_length,
                'rate_limit_per_minute': config.rate_limit_per_minute,
                'auto_timeout_minutes': config.auto_timeout_minutes,
                'created_at': config.created_at,
                'last_active': config.last_active,
                'custom_settings': config.custom_settings
            }
            export_data.append(config_dict)
        
        with open(file_path, 'w') as f:
            json.dump({
                'users': export_data,
                'export_timestamp': get_user_manager().get_statistics()
            }, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error exporting user configs: {e}")
        return False


def import_user_configs(file_path: str, requester_id: str = "system") -> Dict[str, bool]:
    """
    Import user configurations from a JSON file
    
    Args:
        file_path: Path to the JSON file
        requester_id: ID of user requesting the import
    
    Returns:
        Dict mapping user_id to import success status
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        user_manager = get_user_manager()
        results = {}
        
        for user_data in data.get('users', []):
            try:
                # Skip default users
                if user_data['user_id'] in ['human_user', 'claude_ai', 'qwen_ai']:
                    results[user_data['user_id']] = False
                    continue
                
                permissions = {Permission(p) for p in user_data['permissions']}
                
                config = UserConfig(
                    user_id=user_data['user_id'],
                    display_name=user_data['display_name'],
                    user_type=UserType(user_data['user_type']),
                    permissions=permissions,
                    color_theme=user_data.get('color_theme', '#9B59B6'),
                    max_message_length=user_data.get('max_message_length', 2000),
                    rate_limit_per_minute=user_data.get('rate_limit_per_minute', 30),
                    auto_timeout_minutes=user_data.get('auto_timeout_minutes', 30),
                    created_at=user_data.get('created_at', ''),
                    custom_settings=user_data.get('custom_settings', {})
                )
                config.last_active = user_data.get('last_active', '')
                
                results[config.user_id] = user_manager.add_user(config, requester_id)
                
            except Exception as e:
                print(f"Error importing user {user_data.get('user_id', 'unknown')}: {e}")
                results[user_data.get('user_id', 'unknown')] = False
        
        return results
        
    except Exception as e:
        print(f"Error importing user configs: {e}")
        return {}


def cleanup_inactive_users() -> List[str]:
    """
    Manually trigger cleanup of inactive users
    
    Returns:
        List of user_ids that were deactivated
    """
    user_manager = get_user_manager()
    active_users = user_manager.get_active_users().copy()
    
    deactivated = []
    for user_id, active_user in active_users.items():
        if active_user.is_timed_out():
            if user_manager.deactivate_user(user_id):
                deactivated.append(user_id)
    
    return deactivated


def get_user_summary() -> Dict[str, any]:
    """
    Get a comprehensive summary of the user system
    
    Returns:
        Dict with user system summary
    """
    user_manager = get_user_manager()
    stats = user_manager.get_statistics()
    
    active_users = get_active_ai_users()
    color_map = get_user_color_map()
    
    return {
        'statistics': stats,
        'active_ai_users': active_users,
        'color_mappings': color_map,
        'default_users_active': all(
            user_manager.get_active_user(uid) is not None 
            for uid in ['human_user', 'claude_ai', 'qwen_ai']
        )
    }


# Convenience functions for specific use cases
def setup_basic_chat() -> bool:
    """
    Set up basic chat with three default users activated
    
    Returns:
        bool: True if setup was successful
    """
    results = activate_default_users()
    return all(results.values())


def add_custom_assistant(name: str, color: str = "#E74C3C") -> bool:
    """
    Quick function to add a custom AI assistant
    
    Args:
        name: Display name for the assistant
        color: Hex color theme
    
    Returns:
        bool: True if assistant was added successfully
    """
    user_id = f"custom_ai_{name.lower().replace(' ', '_')}"
    return create_custom_ai_user(user_id, name, color)


def is_chat_ready() -> bool:
    """
    Check if chat system is ready (has active users)
    
    Returns:
        bool: True if at least one AI user is active
    """
    ai_users = get_active_ai_users()
    return len(ai_users) > 0