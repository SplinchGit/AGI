#!/usr/bin/env python3
"""
Enhanced Kivy GUI for Three-Way Chat Application
A modern, stable chat interface for the Qwen/Claude conversation system
"""

import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.uix.behaviors import ButtonBehavior
from kivy.core.clipboard import Clipboard
from kivy.uix.switch import Switch
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.progressbar import ProgressBar
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.widget import Widget
from kivy.animation import Animation
from kivy.metrics import dp

import threading
import queue
import json
import os
import time
from datetime import datetime
from pathlib import Path
import sys
# Add src directory to path for absolute imports
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from interfaces.cli import EnhancedAGIChat
from ai_agents.shared.user_management import get_user_manager, UserType, Permission, UserConfig
import uuid

kivy.require('2.0.0')

class ThemedWidget(Widget):
    """Base widget with theme support"""
    def __init__(self, theme_manager=None, **kwargs):
        super().__init__(**kwargs)
        self.theme_manager = theme_manager
        self.bind(size=self.update_background, pos=self.update_background)
        
    def update_background(self, *args):
        """Update background based on theme"""
        if not hasattr(self, 'canvas') or not self.theme_manager:
            return
        
        self.canvas.before.clear()
        with self.canvas.before:
            color = (0.15, 0.15, 0.15, 1) if self.theme_manager.current_theme == 'dark' else (0.95, 0.95, 0.95, 1)
            Color(*color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(5)])

class SelectableLabel(ButtonBehavior, Label):
    """Enhanced label with copy functionality and theme support"""
    def __init__(self, theme_manager=None, **kwargs):
        super().__init__(**kwargs)
        self.theme_manager = theme_manager
        self.bind(on_press=self.copy_to_clipboard)
        self.apply_theme()
    
    def apply_theme(self):
        """Apply current theme"""
        if self.theme_manager:
            if self.theme_manager.current_theme == 'dark':
                self.color = [0.9, 0.9, 0.9, 1]
            else:
                self.color = [0.1, 0.1, 0.1, 1]
    
    def copy_to_clipboard(self, instance):
        """Copy label text to clipboard with improved feedback"""
        try:
            Clipboard.copy(self.text)
            self._show_copy_feedback()
        except Exception as e:
            print(f"Copy error: {e}")
    
    def _show_copy_feedback(self):
        """Show copy feedback popup"""
        content = BoxLayout(orientation='vertical', padding=dp(10))
        content.add_widget(Label(
            text='✓ Text copied to clipboard!',
            font_size=dp(14),
            color=[0.2, 0.8, 0.2, 1]
        ))
        
        bg_color = ([0.2, 0.2, 0.2, 0.95] if self.theme_manager and 
                   self.theme_manager.current_theme == 'dark' else [0.95, 0.95, 0.95, 0.95])
        
        popup = Popup(
            title='Success',
            content=content,
            size_hint=(0.4, 0.25),
            auto_dismiss=True,
            background_color=bg_color
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 1.2)

class ThemeManager:
    """Manages dark/light themes"""
    def __init__(self):
        self.current_theme = 'dark'  # Default to dark
        self.themes = {
            'dark': {
                'bg_primary': [0.1, 0.1, 0.1, 1],
                'bg_secondary': [0.15, 0.15, 0.15, 1],
                'bg_tertiary': [0.2, 0.2, 0.2, 1],
                'text_primary': [0.9, 0.9, 0.9, 1],
                'text_secondary': [0.7, 0.7, 0.7, 1],
                'accent': [0.3, 0.6, 0.9, 1],
                'success': [0.2, 0.8, 0.3, 1],
                'warning': [0.9, 0.6, 0.2, 1],
                'error': [0.9, 0.3, 0.3, 1]
            },
            'light': {
                'bg_primary': [0.98, 0.98, 0.98, 1],
                'bg_secondary': [0.95, 0.95, 0.95, 1],
                'bg_tertiary': [0.9, 0.9, 0.9, 1],
                'text_primary': [0.1, 0.1, 0.1, 1],
                'text_secondary': [0.3, 0.3, 0.3, 1],
                'accent': [0.2, 0.4, 0.8, 1],
                'success': [0.1, 0.6, 0.2, 1],
                'warning': [0.8, 0.5, 0.1, 1],
                'error': [0.8, 0.2, 0.2, 1]
            }
        }
    
    def toggle_theme(self):
        """Toggle between dark and light themes"""
        self.current_theme = 'light' if self.current_theme == 'dark' else 'dark'
    
    def get_color(self, color_name):
        """Get color from current theme"""
        return self.themes[self.current_theme].get(color_name, [1, 1, 1, 1])

class ChatMessage(BoxLayout):
    """Enhanced chat message widget with timestamps and better styling."""
    def __init__(self, speaker, message, theme_manager=None, timestamp=None, **kwargs):
        super().__init__(**kwargs)
        self.speaker = speaker
        self.message = message
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.spacing = dp(8)
        self.padding = [dp(15), dp(10)]
        self.theme_manager = theme_manager or ThemeManager()
        self.is_user_message = speaker == 'You'
        
        self._setup_background()
        self._setup_content(timestamp)
        
    def _setup_background(self):
        """Setup message background"""
        with self.canvas.before:
            color = 'accent' if self.is_user_message else 'bg_secondary'
            self.bg_color = Color(*self.theme_manager.get_color(color))
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
        self.bind(pos=self.update_bg, size=self.update_bg)
        
    def _setup_content(self, timestamp):
        """Setup message content"""

        header_layout = self._create_header(timestamp or datetime.now().strftime("%H:%M:%S"))
        message_label = self._create_message_label()
        
        self.add_widget(header_layout)
        self.add_widget(message_label)
        self.height = header_layout.height + message_label.height + dp(30)
        
    def _create_header(self, timestamp):
        """Create header with speaker and timestamp"""
        header_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(25),
            spacing=dp(10)
        )
        
        speaker_label = self._create_speaker_label()
        timestamp_label = self._create_timestamp_label(timestamp)
        
        if self.is_user_message:
            header_layout.add_widget(timestamp_label)
            header_layout.add_widget(Widget())
            header_layout.add_widget(speaker_label)
        else:
            header_layout.add_widget(speaker_label)
            header_layout.add_widget(Widget())
            header_layout.add_widget(timestamp_label)
            
        return header_layout
        
    def _create_speaker_label(self):
        """Create speaker label"""
        label = Label(
            text=self.speaker,
            size_hint_y=None,
            height=dp(25),
            font_size=dp(14),
            bold=True,
            color=self._get_speaker_color(self.speaker, self.is_user_message),
            halign='left',
            valign='middle'
        )
        label.bind(texture_size=label.setter('text_size'))
        return label
        
    def _create_timestamp_label(self, timestamp):
        """Create timestamp label"""
        label = Label(
            text=timestamp,
            size_hint_x=None,
            width=dp(60),
            size_hint_y=None,
            height=dp(25),
            font_size=dp(10),
            color=self.theme_manager.get_color('text_secondary'),
            halign='right',
            valign='middle'
        )
        label.bind(texture_size=label.setter('text_size'))
        return label
        
    def _create_message_label(self):
        """Create message content label"""
        return SelectableLabel(
            text=self.message,
            size_hint_y=None,
            text_size=(Window.width - dp(80), None),
            halign='right' if self.is_user_message else 'left',
            valign='top',
            markup=True,
            font_size=dp(13),
            theme_manager=self.theme_manager,
            color=self.theme_manager.get_color('text_primary')
        )

    def set_selected(self, selected):
        """Sets the visual state of the message to selected or not."""
        if selected:
            self.bg_color.rgba = (0.3, 0.6, 0.9, 0.5)
        else:
            color = 'accent' if self.is_user_message else 'bg_secondary'
            self.bg_color.rgba = self.theme_manager.get_color(color)

    def update_bg(self, *args):
        """Update background rectangle"""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def _get_speaker_color(self, speaker, is_user_message=False):
        """Get enhanced colors for different speakers."""
        if is_user_message:
            return self.theme_manager.get_color('text_primary')

        user_manager = get_user_manager()
        
        # Try to get color from user management system first
        for user_id, config in user_manager.get_all_user_configs().items():
            if config.display_name == speaker:
                hex_color = config.color_theme.lstrip('#')
                if len(hex_color) == 6:
                    r = int(hex_color[0:2], 16) / 255.0
                    g = int(hex_color[2:4], 16) / 255.0
                    b = int(hex_color[4:6], 16) / 255.0
                    return [r, g, b, 1]
        
        # Fallback to theme manager colors
        colors = {
            'Qwen': self.theme_manager.get_color('warning'),
            'Claude': self.theme_manager.get_color('accent'),
            'Gemini': [0.258, 0.521, 0.956, 1], # Google Blue
            'System': self.theme_manager.get_color('text_secondary')
        }
        return colors.get(speaker, self.theme_manager.get_color('text_primary'))

class ConnectionStatus(BoxLayout):
    """Enhanced connection status widget with dynamic user support"""
    def __init__(self, theme_manager=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(40)
        self.spacing = dp(10)
        self.padding = [dp(10), dp(5)]
        self.theme_manager = theme_manager or ThemeManager()
        self.user_manager = get_user_manager()
        
        # Dynamic status indicators for AI users
        self.status_labels = {}
        self._create_status_indicators()
        
        # Subscribe to user management events
        self.user_manager.subscribe_to_events('user_activated', self._on_user_activated)
        self.user_manager.subscribe_to_events('user_deactivated', self._on_user_deactivated)
    
    def _create_status_indicators(self):
        """Create status indicators for core AI users first, then custom ones"""
        # Core AI users get priority display - only show the 4 default AI users
        core_users = ['qwen_ai', 'claude_ai', 'gemini_ai']
        custom_users = []
        
        # Only add additional users if they're truly custom (not default users)
        default_user_ids = self.user_manager.get_default_users()
        
        for user_id, config in self.user_manager.get_all_user_configs().items():
            # Skip human user as it's not shown in connection status
            if config.user_type == UserType.HUMAN:
                continue
                
            if config.user_type == UserType.AI_CUSTOM:
                custom_users.append(user_id)
            elif user_id not in core_users and user_id in default_user_ids:
                # This handles any additional default AI users
                core_users.append(user_id)
        
        # Limit to 4 total core users to match expected display
        all_ai_users = core_users[:4] + custom_users[:1]  # Only show 1 custom user to keep total at reasonable number
        
        for user_id in all_ai_users:
            config = self.user_manager.get_user_config(user_id)
            if config:
                status_label = Label(
                    text=f'{config.display_name}: Disconnected',
                    size_hint_x=1.0 / len(all_ai_users) if all_ai_users else 1.0,
                    font_size=dp(11),
                    color=self.theme_manager.get_color('error')
                )
                
                self.status_labels[config.user_id] = status_label
                self.add_widget(status_label)
        
        # Show count if there are more custom users
        if len(custom_users) > 3:
            overflow_label = Label(
                text=f'+{len(custom_users) - 3} more',
                size_hint_x=None,
                width=dp(60),
                font_size=dp(10),
                color=self.theme_manager.get_color('text_secondary')
            )
            self.add_widget(overflow_label)
    
    def _on_user_activated(self, data):
        """Handle user activation"""
        user_id = data['user_id']
        config = self.user_manager.get_user_config(user_id)
        if config and config.user_type in [UserType.AI_CLAUDE, UserType.AI_QWEN, UserType.AI_GEMINI, UserType.AI_CUSTOM]:
            if user_id not in self.status_labels:
                self._refresh_status_indicators()
    
    def _on_user_deactivated(self, data):
        """Handle user deactivation"""
        user_id = data['user_id']
        if user_id in self.status_labels:
            self.update_user_status(user_id, False)
    
    def _refresh_status_indicators(self):
        """Refresh all status indicators"""
        # Clear existing widgets
        self.clear_widgets()
        self.status_labels.clear()
        
        # Recreate indicators
        self._create_status_indicators()
    
    def update_user_status(self, user_id: str, connected: bool):
        """Update user connection status"""
        if user_id in self.status_labels:
            config = self.user_manager.get_user_config(user_id)
            if config:
                status_text = f'{config.display_name}: {"Connected ✓" if connected else "Disconnected ✗"}'
                self.status_labels[user_id].text = status_text
                self.status_labels[user_id].color = (
                    self.theme_manager.get_color('success') if connected 
                    else self.theme_manager.get_color('error')
                )
    
    def update_qwen_status(self, connected):
        """Update Qwen connection status (legacy compatibility)"""
        self.update_user_status('qwen_ai', connected)
    
    def update_claude_status(self, connected):
        """Update Claude connection status (legacy compatibility)"""
        self.update_user_status('claude_ai', connected)

class DatasetViewer(BoxLayout):
    """Enhanced dataset and memory viewer with theme support"""
    def __init__(self, theme_manager=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(10)
        self.padding = dp(10)
        self.theme_manager = theme_manager or ThemeManager()
        
        # Title with theme support
        title = Label(
            text='Datasets & Memory',
            size_hint_y=None,
            height=dp(40),
            font_size=dp(18),
            bold=True,
            color=self.theme_manager.get_color('text_primary')
        )
        self.add_widget(title)
        
        # Data display area with enhanced styling
        self.data_scroll = ScrollView()
        self.data_layout = GridLayout(
            cols=1,
            spacing=dp(5),
            size_hint_y=None,
            padding=dp(10)
        )
        self.data_layout.bind(minimum_height=self.data_layout.setter('height'))
        
        # Background for data area
        with self.data_layout.canvas.before:
            Color(*self.theme_manager.get_color('bg_secondary'))
            self.data_bg = RoundedRectangle(pos=self.data_layout.pos, size=self.data_layout.size, radius=[dp(5)])
        self.data_layout.bind(pos=self.update_data_bg, size=self.update_data_bg)
        
        self.data_scroll.add_widget(self.data_layout)
        self.add_widget(self.data_scroll)
    
    def update_data_bg(self, *args):
        """Update data background"""
        self.data_bg.pos = self.data_layout.pos
        self.data_bg.size = self.data_layout.size
        
        # Load data
        self.load_data()
    
    def load_data(self):
        """Load and display dataset information"""
        data_dir = Path("C:/Users/jf358/Documents/AGI/data")
        
        # Memory data
        memory_file = data_dir / "sessions" / "persistent_memory.json"
        if memory_file.exists():
            try:
                with open(memory_file, 'r') as f:
                    memory_data = json.load(f)
                
                memory_label = Label(
                    text=f"Memory Sessions: {len(memory_data.get('conversations', []))}",
                    size_hint_y=None,
                    height=dp(30),
                    halign='left',
                    font_size=dp(12),
                    color=self.theme_manager.get_color('text_primary')
                )
                memory_label.bind(texture_size=memory_label.setter('text_size'))
                self.data_layout.add_widget(memory_label)
                
                for i, conv in enumerate(memory_data.get('conversations', [])[:5]):  # Show first 5
                    conv_label = SelectableLabel(
                        text=f"Session {i+1}: {len(conv.get('messages', []))} messages",
                        size_hint_y=None,
                        height=dp(25),
                        halign='left',
                        font_size=dp(11),
                        theme_manager=self.theme_manager
                    )
                    conv_label.bind(texture_size=conv_label.setter('text_size'))
                    self.data_layout.add_widget(conv_label)
                    
            except Exception as e:
                error_label = Label(
                    text=f"Error loading memory: {str(e)}",
                    size_hint_y=None,
                    height=dp(30),
                    font_size=dp(11),
                    color=self.theme_manager.get_color('error')
                )
                self.data_layout.add_widget(error_label)

class EnhancedTextInput(TextInput):
    """Enhanced text input with multi-line support and better formatting"""
    def __init__(self, theme_manager=None, **kwargs):
        super().__init__(**kwargs)
        self.theme_manager = theme_manager or ThemeManager()
        self.multiline = True
        self.font_size = dp(14)
        self.padding = [dp(10), dp(8)]
        self.apply_theme()
        
        # File drop functionality placeholder
        self.allow_file_drop = True
        
    def apply_theme(self):
        """Apply theme colors"""
        if self.theme_manager.current_theme == 'dark':
            self.background_color = [0.2, 0.2, 0.2, 1]
            self.foreground_color = [0.9, 0.9, 0.9, 1]
            self.cursor_color = [0.3, 0.6, 0.9, 1]
        else:
            self.background_color = [0.95, 0.95, 0.95, 1]
            self.foreground_color = [0.1, 0.1, 0.1, 1]
            self.cursor_color = [0.2, 0.4, 0.8, 1]
    
    def insert_file_reference(self, file_path):
        """Insert file reference into text"""
        file_ref = f"[File: {file_path}]\n"
        cursor_pos = self.cursor_index()
        self.text = self.text[:cursor_pos] + file_ref + self.text[cursor_pos:]

class FileShareWidget(BoxLayout):
    """File sharing widget with drag-drop support"""
    def __init__(self, text_input=None, theme_manager=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(35)
        self.spacing = dp(5)
        self.text_input = text_input
        self.theme_manager = theme_manager or ThemeManager()
        
        # File chooser button
        self.file_button = Button(
            text='📎 Attach',
            size_hint_x=None,
            width=dp(80),
            font_size=dp(12),
            background_color=self.theme_manager.get_color('accent')
        )
        self.file_button.bind(on_press=self.open_file_chooser)
        
        # Image button
        self.image_button = Button(
            text='🖼️ Image',
            size_hint_x=None,
            width=dp(80),
            font_size=dp(12),
            background_color=self.theme_manager.get_color('accent')
        )
        self.image_button.bind(on_press=self.open_image_chooser)
        
        # Status label
        self.status_label = Label(
            text='',
            font_size=dp(10),
            color=self.theme_manager.get_color('text_secondary')
        )
        
        self.add_widget(self.file_button)
        self.add_widget(self.image_button)
        self.add_widget(self.status_label)
    
    def open_file_chooser(self, instance):
        """Open file chooser dialog"""
        content = BoxLayout(orientation='vertical')
        
        file_chooser = FileChooserListView(
            path=str(Path.home()),
            filters=['*']
        )
        
        buttons = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10)
        )
        
        select_btn = Button(text='Select', size_hint_x=0.5)
        cancel_btn = Button(text='Cancel', size_hint_x=0.5)
        
        buttons.add_widget(select_btn)
        buttons.add_widget(cancel_btn)
        
        content.add_widget(file_chooser)
        content.add_widget(buttons)
        
        popup = Popup(
            title='Choose File',
            content=content,
            size_hint=(0.8, 0.8)
        )
        
        def select_file(instance):
            if file_chooser.selection:
                file_path = file_chooser.selection[0]
                if self.text_input:
                    self.text_input.insert_file_reference(file_path)
                self.status_label.text = f'Attached: {Path(file_path).name}'
            popup.dismiss()
        
        select_btn.bind(on_press=select_file)
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        popup.open()
    
    def open_image_chooser(self, instance):
        """Open image chooser dialog"""
        content = BoxLayout(orientation='vertical')
        
        file_chooser = FileChooserListView(
            path=str(Path.home()),
            filters=['*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp']
        )
        
        buttons = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10)
        )
        
        select_btn = Button(text='Select', size_hint_x=0.5)
        cancel_btn = Button(text='Cancel', size_hint_x=0.5)
        
        buttons.add_widget(select_btn)
        buttons.add_widget(cancel_btn)
        
        content.add_widget(file_chooser)
        content.add_widget(buttons)
        
        popup = Popup(
            title='Choose Image',
            content=content,
            size_hint=(0.8, 0.8)
        )
        
        def select_image(instance):
            if file_chooser.selection:
                file_path = file_chooser.selection[0]
                if self.text_input:
                    self.text_input.insert_file_reference(file_path)
                self.status_label.text = f'Image: {Path(file_path).name}'
            popup.dismiss()
        
        select_btn.bind(on_press=select_image)
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        popup.open()

class ConfigPanel(BoxLayout):
    """Enhanced settings and configuration panel"""
    def __init__(self, theme_manager=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(10)
        self.padding = dp(10)
        self.theme_manager = theme_manager or ThemeManager()
        
        # Title with theme support
        title = Label(
            text='Settings & Options',
            size_hint_y=None,
            height=dp(40),
            font_size=dp(18),
            bold=True,
            color=self.theme_manager.get_color('text_primary')
        )
        self.add_widget(title)
        
        # Theme toggle button
        theme_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10)
        )
        
        theme_label = Label(
            text='Theme:',
            size_hint_x=None,
            width=dp(100),
            font_size=dp(14),
            color=self.theme_manager.get_color('text_primary')
        )
        
        self.theme_button = Button(
            text=f'{self.theme_manager.current_theme.title()} Mode',
            size_hint_x=0.3,
            font_size=dp(12),
            background_color=self.theme_manager.get_color('accent')
        )
        self.theme_button.bind(on_press=self.toggle_theme)
        
        theme_layout.add_widget(theme_label)
        theme_layout.add_widget(self.theme_button)
        theme_layout.add_widget(Widget())  # Spacer
        
        self.add_widget(theme_layout)
        
        # Settings scroll view with enhanced styling
        settings_scroll = ScrollView()
        settings_layout = GridLayout(
            cols=2,
            spacing=dp(10),
            size_hint_y=None,
            row_default_height=dp(40),
            padding=dp(10)
        )
        settings_layout.bind(minimum_height=settings_layout.setter('height'))
        
        # Background for settings
        with settings_layout.canvas.before:
            Color(*self.theme_manager.get_color('bg_secondary'))
            self.settings_bg = RoundedRectangle(pos=settings_layout.pos, size=settings_layout.size, radius=[dp(5)])
        settings_layout.bind(pos=self.update_settings_bg, size=self.update_settings_bg)
        
        # Debug mode setting with theme support
        debug_label = Label(
            text='Debug Mode:',
            halign='left',
            font_size=dp(12),
            color=self.theme_manager.get_color('text_primary')
        )
        debug_label.bind(texture_size=debug_label.setter('text_size'))
        settings_layout.add_widget(debug_label)
        
        debug_switch = Switch(active=True)
        settings_layout.add_widget(debug_switch)
        
        # Response length setting
        length_label = Label(
            text='Max Response Length:',
            halign='left',
            font_size=dp(12),
            color=self.theme_manager.get_color('text_primary')
        )
        length_label.bind(texture_size=length_label.setter('text_size'))
        settings_layout.add_widget(length_label)
        
        length_slider = Slider(min=100, max=1000, value=300, step=50)
        settings_layout.add_widget(length_slider)
        
        # Model selection
        model_title_label = Label(
            text='Qwen Model:',
            halign='left',
            font_size=dp(12),
            color=self.theme_manager.get_color('text_primary')
        )
        model_title_label.bind(texture_size=model_title_label.setter('text_size'))
        settings_layout.add_widget(model_title_label)
        
        model_label = SelectableLabel(
            text='qwen2.5:7b',
            halign='left',
            font_size=dp(11),
            theme_manager=self.theme_manager
        )
        model_label.bind(texture_size=model_label.setter('text_size'))
        settings_layout.add_widget(model_label)
        
        # Ollama host
        host_title_label = Label(
            text='Ollama Host:',
            halign='left',
            font_size=dp(12),
            color=self.theme_manager.get_color('text_primary')
        )
        host_title_label.bind(texture_size=host_title_label.setter('text_size'))
        settings_layout.add_widget(host_title_label)
        
        host_label = SelectableLabel(
            text='localhost:11434',
            halign='left',
            font_size=dp(11),
            theme_manager=self.theme_manager
        )
        host_label.bind(texture_size=host_label.setter('text_size'))
        settings_layout.add_widget(host_label)
        
        settings_scroll.add_widget(settings_layout)
        self.add_widget(settings_scroll)
        
        # User Management Section
        self.add_user_management_section()
    
    def update_settings_bg(self, *args):
        """Update settings background"""
        self.settings_bg.pos = self.settings_layout.pos if hasattr(self, 'settings_layout') else (0, 0)
        self.settings_bg.size = self.settings_layout.size if hasattr(self, 'settings_layout') else (0, 0)
    
    def toggle_theme(self, instance):
        """Toggle between dark and light themes"""
        self.theme_manager.toggle_theme()
        self.theme_button.text = f'{self.theme_manager.current_theme.title()} Mode'
        # This would normally trigger a full UI refresh
    
    def add_user_management_section(self):
        """Add user management section for dynamic user addition"""
        user_manager = get_user_manager()
        
        # Section title
        user_title = Label(
            text='Chat Participants',
            size_hint_y=None,
            height=dp(30),
            font_size=dp(16),
            bold=True,
            color=self.theme_manager.get_color('text_primary')
        )
        self.add_widget(user_title)
        
        # User list scroll area
        user_scroll = ScrollView(size_hint_y=None, height=dp(150))
        self.user_list_layout = GridLayout(
            cols=1,
            spacing=dp(5),
            size_hint_y=None,
            padding=dp(5)
        )
        self.user_list_layout.bind(minimum_height=self.user_list_layout.setter('height'))
        
        # Background for user list
        with self.user_list_layout.canvas.before:
            Color(*self.theme_manager.get_color('bg_secondary'))
            self.user_list_bg = RoundedRectangle(pos=self.user_list_layout.pos, size=self.user_list_layout.size, radius=[dp(5)])
        self.user_list_layout.bind(pos=self.update_user_list_bg, size=self.update_user_list_bg)
        
        # Populate user list
        self.refresh_user_list()
        
        user_scroll.add_widget(self.user_list_layout)
        self.add_widget(user_scroll)
        
        # Add user button
        add_user_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10)
        )
        
        self.add_user_button = Button(
            text='+ Add AI User',
            size_hint_x=0.3,
            font_size=dp(12),
            background_color=self.theme_manager.get_color('accent')
        )
        self.add_user_button.bind(on_press=self.show_add_user_dialog)
        
        add_user_layout.add_widget(self.add_user_button)
        add_user_layout.add_widget(Widget())  # Spacer
        
        self.add_widget(add_user_layout)
    
    def update_user_list_bg(self, *args):
        """Update user list background"""
        self.user_list_bg.pos = self.user_list_layout.pos
        self.user_list_bg.size = self.user_list_layout.size
    
    def refresh_user_list(self):
        """Refresh the user list display"""
        user_manager = get_user_manager()
        self.user_list_layout.clear_widgets()
        
        # Core users (non-removable)
        core_users = user_manager.get_default_users()
        for user_id in core_users:
            config = user_manager.get_user_config(user_id)
            if config:
                user_row = self.create_user_row(config, is_core=True)
                self.user_list_layout.add_widget(user_row)
        
        # Custom users (removable)
        for user_id, config in user_manager.get_all_user_configs().items():
            if user_id not in core_users:
                user_row = self.create_user_row(config, is_core=False)
                self.user_list_layout.add_widget(user_row)
    
    def create_user_row(self, config, is_core=False):
        """Create a user row widget"""
        row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(30),
            spacing=dp(10)
        )
        
        # User info
        user_info = Label(
            text=f'{config.display_name} ({config.user_type.value})',
            size_hint_x=0.7,
            font_size=dp(11),
            color=self.theme_manager.get_color('text_primary'),
            halign='left'
        )
        user_info.bind(texture_size=user_info.setter('text_size'))
        
        # Status indicator
        user_manager = get_user_manager()
        is_active = user_manager.get_active_user(config.user_id) is not None
        status_color = self.theme_manager.get_color('success') if is_active else self.theme_manager.get_color('text_secondary')
        
        status_label = Label(
            text='●',
            size_hint_x=None,
            width=dp(20),
            font_size=dp(16),
            color=status_color
        )
        
        row.add_widget(user_info)
        row.add_widget(status_label)
        
        # Remove button for custom users only
        if not is_core:
            remove_btn = Button(
                text='✕',
                size_hint_x=None,
                width=dp(30),
                font_size=dp(12),
                background_color=self.theme_manager.get_color('error')
            )
            remove_btn.bind(on_press=lambda x: self.remove_user(config.user_id))
            row.add_widget(remove_btn)
        else:
            row.add_widget(Widget(size_hint_x=None, width=dp(30)))
        
        return row
    
    def show_add_user_dialog(self, instance):
        """Show dialog to add a new user"""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        # User name input
        name_label = Label(text='Display Name:', size_hint_y=None, height=dp(30))
        name_input = TextInput(
            hint_text='Enter display name (e.g., GPT-4)',
            size_hint_y=None,
            height=dp(40),
            multiline=False
        )
        
        # Color picker (simplified)
        color_label = Label(text='Color Theme:', size_hint_y=None, height=dp(30))
        color_spinner = Spinner(
            text='#9B59B6',
            values=['#9B59B6', '#E74C3C', '#1ABC9C', '#F39C12', '#8E44AD', '#27AE60'],
            size_hint_y=None,
            height=dp(40)
        )
        
        # Buttons
        button_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10)
        )
        
        add_btn = Button(text='Add User', size_hint_x=0.5)
        cancel_btn = Button(text='Cancel', size_hint_x=0.5)
        
        button_layout.add_widget(add_btn)
        button_layout.add_widget(cancel_btn)
        
        content.add_widget(name_label)
        content.add_widget(name_input)
        content.add_widget(color_label)
        content.add_widget(color_spinner)
        content.add_widget(button_layout)
        
        popup = Popup(
            title='Add AI User',
            content=content,
            size_hint=(0.6, 0.5)
        )
        
        def add_user(instance):
            name = name_input.text.strip()
            if name:
                self.add_custom_user(name, color_spinner.text)
                popup.dismiss()
        
        add_btn.bind(on_press=add_user)
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        popup.open()
    
    def add_custom_user(self, display_name, color_theme):
        """Add a custom AI user"""
        
        user_manager = get_user_manager()
        
        # Generate unique user ID
        user_id = f'custom_{uuid.uuid4().hex[:8]}'
        
        # Create user config
        new_user = UserConfig(
            user_id=user_id,
            display_name=display_name,
            user_type=UserType.AI_CUSTOM,
            permissions={Permission.READ_CHAT, Permission.SEND_MESSAGE, Permission.ACCESS_MEMORY},
            color_theme=color_theme,
            rate_limit_per_minute=20
        )
        
        # Add user (human user has permission to add users by default)
        success = user_manager.add_user(new_user, 'human_user')
        
        if success:
            self.refresh_user_list()
            # Show success message
            success_popup = Popup(
                title='Success',
                content=Label(text=f'Added {display_name} to the chat!'),
                size_hint=(0.4, 0.3)
            )
            success_popup.open()
            Clock.schedule_once(lambda dt: success_popup.dismiss(), 2.0)
    
    def remove_user(self, user_id):
        """Remove a custom user"""
        user_manager = get_user_manager()
        config = user_manager.get_user_config(user_id)
        
        if config:
            # Confirmation dialog
            content = BoxLayout(orientation='vertical', spacing=dp(10))
            content.add_widget(Label(text=f'Remove {config.display_name} from chat?'))
            
            button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
            confirm_btn = Button(text='Remove', size_hint_x=0.5)
            cancel_btn = Button(text='Cancel', size_hint_x=0.5)
            button_layout.add_widget(confirm_btn)
            button_layout.add_widget(cancel_btn)
            content.add_widget(button_layout)
            
            popup = Popup(
                title='Confirm Removal',
                content=content,
                size_hint=(0.5, 0.4)
            )
            
            def confirm_removal(instance):
                success = user_manager.remove_user(user_id, 'human_user')
                if success:
                    self.refresh_user_list()
                popup.dismiss()
            
            confirm_btn.bind(on_press=confirm_removal)
            cancel_btn.bind(on_press=lambda x: popup.dismiss())
            popup.open()

class ChatInterface(BoxLayout):
    """Enhanced main chat interface with dynamic user support"""
    def __init__(self, theme_manager=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(10)
        self.padding = dp(10)
        self.theme_manager = theme_manager or ThemeManager()
        self.user_manager = get_user_manager()
        self.selected_messages = []

        # Keyboard listener for copy-paste
        Window.bind(on_keyboard=self.on_keyboard)
        
        # Initialize chat backend with better error handling
        self.chat_backend = None
        self.message_queue = queue.Queue()
        self.connection_status = {}  # Dynamic connection status
        self.retry_count = 0
        self.max_retries = 3
        
        # Initialize connection status for core AI users first, then custom ones
        self.connection_status = {
            'qwen_ai': False,
            'claude_ai': False,
            'gemini_ai': False
        }
        
        # Add custom AI users
        for config in self.user_manager.get_all_user_configs().values():
            if config.user_type == UserType.AI_CUSTOM:
                self.connection_status[config.user_id] = False
        
        # Core 4-user title with dynamic additions
        core_users = ['You', 'Qwen', 'Claude', 'Gemini']
        additional_users = [config.display_name for config in self.user_manager.get_all_user_configs().values() 
                          if config.user_type == UserType.AI_CUSTOM and config.user_id not in self.user_manager.get_default_users()]
        
        if additional_users:
            user_list = ', '.join(core_users) + f' + {len(additional_users)} more'
        else:
            user_list = ', '.join(core_users)
        
        # Create and add connection status widget
        self.connection_widget = ConnectionStatus(theme_manager=self.theme_manager)
        self.add_widget(self.connection_widget)
        
        # Chat history scroll view with enhanced styling
        self.chat_scroll = ScrollView(size_hint_y=1) # Occupy available vertical space
        self.chat_layout = GridLayout(
            cols=1,
            spacing=dp(8),
            size_hint_y=None,
            padding=dp(5)
        )
        self.chat_layout.bind(minimum_height=self.chat_layout.setter('height'))
        
        # Background for chat area
        with self.chat_layout.canvas.before:
            Color(*self.theme_manager.get_color('bg_primary'))
            self.chat_bg = RoundedRectangle(pos=self.chat_layout.pos, size=self.chat_layout.size, radius=[dp(10)])
        self.chat_layout.bind(pos=self.update_chat_bg, size=self.update_chat_bg)
        
        self.chat_scroll.add_widget(self.chat_layout)
        self.add_widget(self.chat_scroll)
    
    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        """Handles keyboard events for copy-paste."""
        if 'ctrl' in modifier:
            if codepoint == 'a':  # Ctrl+A for Select All
                self.select_all_messages()
            elif codepoint == 'c':  # Ctrl+C for Copy
                self.copy_selected_messages()

    def select_all_messages(self):
        """Selects all messages in the chat."""
        self.selected_messages = list(self.chat_layout.children)
        for widget in self.chat_layout.children:
            if isinstance(widget, ChatMessage):
                widget.set_selected(True)

    def copy_selected_messages(self):
        """Copies the text of selected messages to the clipboard."""
        if not self.selected_messages:
            return

        clipboard_content = ""
        for widget in reversed(self.selected_messages):
            if isinstance(widget, ChatMessage):
                clipboard_content += f"{widget.speaker}: {widget.message}\n"
        
        Clipboard.copy(clipboard_content)

        # Optional: Add feedback to the user
        self.show_copy_feedback()

    def show_copy_feedback(self):
        """Shows a popup to confirm that text has been copied."""
        content = Label(text='Copied to clipboard!', font_size=dp(14))
        popup = Popup(title='Success', content=content, size_hint=(0.4, 0.2), auto_dismiss=True)
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 1.2)

    def on_touch_down(self, touch):
        """Handles touch events to clear selection."""
        if not self.collide_point(*touch.pos):
            self.clear_selection()
        return super().on_touch_down(touch)

    def clear_selection(self):
        """Clears the current selection."""
        for widget in self.selected_messages:
            if isinstance(widget, ChatMessage):
                widget.set_selected(False)
        self.selected_messages = []

    def update_chat_bg(self, *args):
        """Update chat background"""
        self.chat_bg.pos = self.chat_layout.pos
        self.chat_bg.size = self.chat_layout.size
        
        # Enhanced input area with file sharing
        input_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(120),
            spacing=dp(5)
        )
        
        # File sharing widget
        self.file_share = FileShareWidget(theme_manager=self.theme_manager)
        
        # Input layout
        input_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(80),
            spacing=dp(10)
        )
        
        # Enhanced text input with multi-line support
        self.text_input = EnhancedTextInput(
            hint_text='Type your message here... (Shift+Enter for new line, Enter to send)',
            theme_manager=self.theme_manager,
            size_hint_y=None,
            height=dp(80)
        )
        self.text_input.bind(on_text_validate=self.send_message)
        self.file_share.text_input = self.text_input  # Link for file references
        
        # Enhanced send button
        self.send_button = Button(
            text='Send ➤',
            size_hint_x=None,
            width=dp(80),
            font_size=dp(14),
            background_color=self.theme_manager.get_color('accent')
        )
        self.send_button.bind(on_press=self.send_message)
        
        # Loading indicator
        self.loading_bar = ProgressBar(
            max=100,
            value=0,
            size_hint_y=None,
            height=dp(4)
        )
        
        input_layout.add_widget(self.text_input)
        input_layout.add_widget(self.send_button)
        
        input_container.add_widget(self.file_share)
        input_container.add_widget(input_layout)
        input_container.add_widget(self.loading_bar)
        
        self.add_widget(input_container)
        
        # Enhanced status label
        self.status_label = Label(
            text='Initializing chat services...',
            size_hint_y=None,
            height=dp(30),
            font_size=dp(12),
            color=self.theme_manager.get_color('text_secondary')
        )
        self.add_widget(self.status_label)
        
        # Initialize backend with better error handling
        self.init_backend_async()
        
        # Schedule UI updates and health checks
        Clock.schedule_interval(self.update_ui, 0.1)
        Clock.schedule_interval(self.health_check, 30.0)  # Check every 30 seconds

    
    def init_backend_async(self):
        """Initialize chat backend with better error handling"""
        threading.Thread(target=self._init_worker, daemon=True).start()
        
    def _init_worker(self):
        """Background initialization worker"""
        try:
            self.chat_backend = EnhancedAGIChat()
            
            qwen_test = self._test_connection('qwen')
            claude_test = self._test_connection('claude')
            
            self.connection_status.update({
                'qwen': qwen_test,
                'claude': claude_test
            })
            
            self.message_queue.put(('connection_update', 'qwen', qwen_test))
            self.message_queue.put(('connection_update', 'claude', claude_test))
            
            if qwen_test or claude_test:
                self.message_queue.put(('status', 'Chat services ready!'))
                self.add_system_message("Chat initialized. Start typing to begin conversation!")
            else:
                self.message_queue.put(('status', 'No services available'))
                self.add_system_message("Warning: No AI services connected. Check your setup.")
                
        except Exception as e:
            self.message_queue.put(('status', f'Initialization error: {str(e)}'))
            self.add_system_message(f"Failed to initialize: {str(e)}")
            
    def _test_connection(self, service):
        """Test connection to specific service"""
        try:
            if not self.chat_backend:
                return False
                
            if service == 'qwen':
                response = self.chat_backend.ask_qwen("Test connection")
            elif service == 'claude':
                response = self.chat_backend.ask_claude("Test connection")
            else:
                return False
                
            return "error" not in response.lower() and "cannot connect" not in response.lower()
        except Exception:
            return False
    
    
    def health_check(self, dt):
        """Periodic health check of services"""
        if self.chat_backend:
            threading.Thread(target=self._health_check_worker, daemon=True).start()
            
    def _health_check_worker(self):
        """Background health check worker"""
        for service in ['qwen', 'claude']:
            status = self._test_connection(service)
            if status != self.connection_status.get(service, False):
                self.connection_status[service] = status
                self.message_queue.put(('connection_update', service, status))
    
    def add_message(self, speaker, message, timestamp=None):
        """Add message to chat display with enhanced features"""
        try:
            msg_widget = ChatMessage(
                speaker, 
                message, 
                theme_manager=self.theme_manager,
                timestamp=timestamp
            )
            self.chat_layout.add_widget(msg_widget)
            
            # Auto-scroll to bottom with animation
            Clock.schedule_once(lambda dt: self.scroll_to_bottom(), 0.1)
            
            # Auto-save every few messages
            if hasattr(self.chat_backend, 'memory'):
                self.chat_backend.memory.save_memory()
                
        except Exception as e:
            print(f"Error adding message: {e}")
    
    def add_system_message(self, message):
        """Add system message"""
        self.message_queue.put(('message', 'System', message))
    
    def scroll_to_bottom(self):
        """Scroll chat to bottom"""
        self.chat_scroll.scroll_y = 0
    
    def send_message(self, instance=None):
        """Enhanced send message with dynamic user support"""
        message = self.text_input.text.strip()
        if not message:
            return
        
        if not self.chat_backend:
            self.add_system_message("Chat backend not ready yet. Please wait...")
            return
        
        # Activate human user if not already active
        human_user = self.user_manager.activate_user('human_user')
        if not human_user or not human_user.can_send_message():
            self.add_system_message("You cannot send messages right now (rate limited or no permission).")
            return
        
        # Check if any AI services are available
        if not any(self.connection_status.values()):
            self.add_system_message("No AI services available. Please check connections.")
            return
        
        # Record user message
        self.user_manager.record_user_message('human_user')
        
        # Clear input and disable button
        self.text_input.text = ''
        self.send_button.disabled = True
        
        # Show loading
        self.show_loading(True)
        
        # Add user message to display
        human_config = self.user_manager.get_user_config('human_user')
        display_name = human_config.display_name if human_config else 'You'
        self.add_message(display_name, message)
        
        # Update status
        self.message_queue.put(('status', 'Getting responses...'))
        
        # Process in background thread with retry logic
        threading.Thread(
            target=self.process_message_with_retry,
            args=(message,),
            daemon=True
        ).start()
    
    def show_loading(self, show):
        """Show/hide loading indicator"""
        if show:
            self.loading_bar.value = 0
            # Animate loading bar
            anim = Animation(value=100, duration=2.0)
            anim.repeat = True
            anim.start(self.loading_bar)
        else:
            Animation.cancel_all(self.loading_bar)
            self.loading_bar.value = 0
    
    def process_message_with_retry(self, message):
        """Process message with retry logic and better error handling"""
        try:
            # Add to conversation history
            if hasattr(self.chat_backend, 'memory'):
                self.chat_backend.memory.add_message("User", message)
            
            responses_received = 0
            
            # Core AI users (Qwen, Claude) get priority in conversation order
            core_ai_order = ['qwen_ai', 'claude_ai']
            custom_ai_users = [uid for uid in self.connection_status.keys() if uid not in core_ai_order]
            
            # Process core AI users first to maintain the 3-way conversation flow
            for user_id in core_ai_order + custom_ai_users:
                if not self.connection_status.get(user_id, False):
                    continue
                
                config = self.user_manager.get_user_config(user_id)
                if not config:
                    continue
                
                try:
                    # Activate the AI user
                    ai_user = self.user_manager.activate_user(user_id)
                    if not ai_user or not ai_user.can_send_message():
                        continue
                    
                    # Get appropriate response based on AI type
                    if config.user_type == UserType.AI_QWEN:
                        context = self.chat_backend.memory.get_context_for_ai(config.display_name)
                        context += f"\nUser just said: {message}\n\nRespond as {config.display_name} in this 3-way conversation (You, Qwen, Claude). Keep responses focused and under 3 sentences."
                        response = self.chat_backend.ask_qwen(context)
                    elif config.user_type == UserType.AI_CLAUDE:
                        context = self.chat_backend.memory.get_context_for_ai(config.display_name)
                        context += f"\nUser just said: {message}\n\nRespond as {config.display_name} in this 3-way conversation (You, Qwen, Claude). Keep responses focused and under 3 sentences."
                        response = self.chat_backend.ask_claude(context)
                    else:
                        # Custom AI - basic implementation
                        context = f"Previous messages:\n{self.chat_backend.memory.get_context_for_ai(config.display_name)}\n\nUser: {message}\n\nRespond as {config.display_name}:"
                        response = f"{config.display_name}: I'm a custom AI participant in this conversation. [Custom AI implementation needed]"
                    
                    # Check response validity
                    if "error" not in response.lower() and "not found" not in response.lower():
                        self.message_queue.put(('message', config.display_name, response))
                        if hasattr(self.chat_backend, 'memory'):
                            self.chat_backend.memory.add_message(config.display_name, response)
                        
                        # Record AI message
                        self.user_manager.record_user_message(user_id)
                        responses_received += 1
                        
                        # Small delay between responses to maintain conversation flow
                        time.sleep(0.5)
                    else:
                        self.message_queue.put(('connection_update', user_id, False))
                        self.connection_status[user_id] = False
                        
                except Exception as e:
                    self.message_queue.put(('message', 'System', f'{config.display_name} error: {str(e)}'))
                    self.connection_status[user_id] = False
            
            if responses_received > 0:
                self.message_queue.put(('status', f'Ready ({responses_received} responses)'))
            else:
                self.message_queue.put(('status', 'No responses received'))
                self.message_queue.put(('message', 'System', 'No AI services responded. Please check connections.'))
            
        except Exception as e:
            self.message_queue.put(('status', f'Processing error: {str(e)}'))
            self.message_queue.put(('message', 'System', f'Error processing message: {str(e)}'))
        finally:
            # Re-enable send button and hide loading
            self.message_queue.put(('ui_update', 'enable_send'))
    
    def update_ui(self, dt):
        """Enhanced UI update with more message types"""
        try:
            while True:
                msg_type, *args = self.message_queue.get_nowait()
                
                if msg_type == 'message':
                    speaker, message = args
                    timestamp = args[2] if len(args) > 2 else None
                    self.add_message(speaker, message, timestamp)
                elif msg_type == 'status':
                    status_text = args[0]
                    self.status_label.text = status_text
                elif msg_type == 'connection_update':
                    user_id, status = args
                    self.connection_widget.update_user_status(user_id, status)
                    
                    # Legacy compatibility
                    if user_id == 'qwen_ai':
                        self.connection_widget.update_qwen_status(status)
                    elif user_id == 'claude_ai':
                        self.connection_widget.update_claude_status(status)
                elif msg_type == 'ui_update':
                    action = args[0]
                    if action == 'enable_send':
                        self.send_button.disabled = False
                        self.show_loading(False)
                    
        except queue.Empty:
            pass

class MainInterface(BoxLayout):
    """A unified main interface for the chat application."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.theme_manager = ThemeManager()

        # Main chat interface (takes up 70% of the width)
        self.chat_interface = ChatInterface(
            theme_manager=self.theme_manager, 
            size_hint_x=0.7
        )
        self.add_widget(self.chat_interface)

        # Sidebar for settings and data (takes up 30% of the width)
        sidebar = BoxLayout(
            orientation='vertical', 
            size_hint_x=0.3, 
            spacing=dp(10), 
            padding=dp(10)
        )
        
        # Add a background to the sidebar
        with sidebar.canvas.before:
            Color(*self.theme_manager.get_color('bg_secondary'))
            self.sidebar_bg = RoundedRectangle(pos=sidebar.pos, size=sidebar.size, radius=[dp(5)])
        
        def update_sidebar_bg(*args):
            self.sidebar_bg.pos = sidebar.pos
            self.sidebar_bg.size = sidebar.size
        
        sidebar.bind(pos=update_sidebar_bg, size=update_sidebar_bg)

        # Add the config panel and dataset viewer to the sidebar
        self.config_panel = ConfigPanel(theme_manager=self.theme_manager)
        sidebar.add_widget(self.config_panel)
        
        self.dataset_viewer = DatasetViewer(theme_manager=self.theme_manager)
        sidebar.add_widget(self.dataset_viewer)

        self.add_widget(sidebar)

        # Ensure theme changes are propagated
        if hasattr(self.config_panel, 'theme_button'):
            self.config_panel.theme_button.bind(on_press=self.on_theme_toggle)

    def on_theme_toggle(self, instance):
        """Refreshes the UI when the theme is toggled."""
        # The theme manager will handle theme changes, but we can trigger
        # a redraw or update specific components if needed.
        # For now, we'll just print a debug message.
        print("Theme toggled. UI refresh needed for full effect.")

class ChatApp(App):
    """Enhanced main Kivy application with stability improvements"""
    def build(self):
        # Enhanced window settings
        Window.size = (1200, 800)
        Window.minimum_width, Window.minimum_height = 900, 600
        self.title = 'AGI Chat'
        
        # Set window background color
        Window.clearcolor = (0.1, 0.1, 0.1, 1)  # Dark background
        
        # Create main interface
        self.main_interface = MainInterface()
        return self.main_interface
    
    def on_stop(self):
        """Enhanced cleanup on app close"""
        try:
            # Save any pending data
            if hasattr(self.main_interface, 'chat_interface'):
                chat = self.main_interface.chat_interface
                if chat.chat_backend and hasattr(chat.chat_backend, 'memory'):
                    chat.chat_backend.memory.save_memory()
                    print("Chat memory saved successfully")
        except Exception as e:
            print(f"Error during cleanup: {e}")
        return True

if __name__ == '__main__':
    ChatApp().run()