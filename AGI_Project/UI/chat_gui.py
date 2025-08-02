"""
GUI Interface for AGI Chat System
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import queue
from datetime import datetime


class ChatGUI:
    def __init__(self, chat_manager):
        self.chat_manager = chat_manager
        self.message_queue = queue.Queue()
        self.running = True
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("AGI Chat")
        self.root.geometry("900x700")
        self.root.minsize(600, 400)
        
        # Configure style
        self.style = ttk.Style()
        self.setup_ui()
        
        # Start message processing thread
        self.process_thread = threading.Thread(target=self.process_messages, daemon=True)
        self.process_thread.start()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(
            header_frame,
            text="AGI Chat System",
            font=("Arial", 16, "bold")
        ).pack(side=tk.LEFT)
        
        # Status label
        self.status_label = ttk.Label(
            header_frame,
            text="Ready",
            font=("Arial", 10),
            foreground="green"
        )
        self.status_label.pack(side=tk.RIGHT, padx=(20, 0))
        
        # Chat display area
        chat_frame = ttk.LabelFrame(main_frame, text="Conversation", padding="10")
        chat_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        chat_frame.columnconfigure(0, weight=1)
        chat_frame.rowconfigure(0, weight=1)
        
        # Chat text widget with scrollbar
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            width=70,
            height=25,
            font=("Consolas", 10),
            bg="#1e1e1e",
            fg="#ffffff",
            insertbackground="#ffffff",
            state="disabled"
        )
        self.chat_display.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure tags for different speakers
        self.chat_display.tag_configure("user", foreground="#4CAF50")
        self.chat_display.tag_configure("claude", foreground="#2196F3")
        self.chat_display.tag_configure("james", foreground="#FF9800")
        self.chat_display.tag_configure("system", foreground="#9E9E9E", font=("Consolas", 9, "italic"))
        self.chat_display.tag_configure("timestamp", foreground="#666666", font=("Consolas", 8))
        
        # Input area
        input_frame = ttk.LabelFrame(main_frame, text="Your Message", padding="10")
        input_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        input_frame.columnconfigure(0, weight=1)
        
        # Input text widget
        self.input_text = tk.Text(
            input_frame,
            height=4,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#2b2b2b",
            fg="#ffffff",
            insertbackground="#ffffff"
        )
        self.input_text.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Bind Enter key to send message (Shift+Enter for new line)
        self.input_text.bind("<Return>", self.on_enter_key)
        self.input_text.bind("<Shift-Return>", lambda e: None)
        
        # Button frame
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Send button
        self.send_button = ttk.Button(
            button_frame,
            text="Send (Enter)",
            command=self.send_message
        )
        self.send_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Clear button
        ttk.Button(
            button_frame,
            text="Clear Chat",
            command=self.clear_chat
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # Exit button
        ttk.Button(
            button_frame,
            text="Exit",
            command=self.exit_chat
        ).pack(side=tk.RIGHT)
        
        # Info label
        info_label = ttk.Label(
            main_frame,
            text="Chat with Claude and your AI clone James. Type /help for commands.",
            font=("Arial", 9),
            foreground="#666666"
        )
        info_label.grid(row=3, column=0, pady=(10, 0))
        
        # Focus on input
        self.input_text.focus_set()
        
        # Show welcome message
        self.display_message("System", "Welcome to AGI Chat! You're chatting with Claude and James (your AI clone).")
        self.display_message("System", "Type your message and press Enter to send. Type /help for available commands.")
        
    def on_enter_key(self, event):
        """Handle Enter key press"""
        if not event.state & 0x1:  # Check if Shift is not pressed
            self.send_message()
            return "break"  # Prevent default behavior
        
    def send_message(self):
        """Send the user's message"""
        message = self.input_text.get("1.0", tk.END).strip()
        if not message:
            return
            
        # Clear input
        self.input_text.delete("1.0", tk.END)
        
        # Display user message
        self.display_message("You", message)
        
        # Handle special commands
        if message.startswith("/"):
            self.handle_command(message)
            return
            
        # Send to chat manager in separate thread
        threading.Thread(
            target=self.process_user_message,
            args=(message,),
            daemon=True
        ).start()
        
    def handle_command(self, command):
        """Handle special commands"""
        cmd = command.lower().strip()
        
        if cmd == "/help":
            help_text = """Available commands:
/help - Show this help message
/clear - Clear the chat display
/save - Save the current conversation
/exit or /quit - Exit the chat
/model <name> - Switch AI model (claude or james)
/history - Show conversation history"""
            self.display_message("System", help_text)
            
        elif cmd == "/clear":
            self.clear_chat()
            
        elif cmd == "/save":
            self.chat_manager.save_session()
            self.display_message("System", "Conversation saved.")
            
        elif cmd in ["/exit", "/quit"]:
            self.exit_chat()
            
        elif cmd.startswith("/model "):
            model = cmd.split(" ", 1)[1]
            self.display_message("System", f"Model switching not implemented yet. Current models: Claude and James")
            
        elif cmd == "/history":
            history = self.chat_manager.get_conversation_history()
            if history:
                self.display_message("System", "=== Conversation History ===")
                for msg in history[-10:]:  # Show last 10 messages
                    self.display_message(msg['role'], msg['content'], show_timestamp=False)
            else:
                self.display_message("System", "No conversation history.")
                
        else:
            self.display_message("System", f"Unknown command: {command}")
            
    def process_user_message(self, message):
        """Process user message and get AI responses"""
        try:
            self.update_status("Processing...")
            
            # Send message to chat manager
            response_message = self.chat_manager.send_message("James", message)
            
            # Display AI responses
            if response_message.get("responses"):
                for agent_name, response_data in response_message["responses"].items():
                    self.display_message(agent_name, response_data["content"])
                    
            self.update_status("Ready")
            
        except Exception as e:
            self.display_message("System", f"Error: {str(e)}")
            self.update_status("Error", "red")
            
    def display_message(self, sender, message, show_timestamp=True):
        """Display a message in the chat window"""
        self.chat_display.config(state="normal")
        
        # Add timestamp if requested
        if show_timestamp:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.chat_display.insert(tk.END, f"[{timestamp}] ", "timestamp")
            
        # Determine tag based on sender
        tag = "system"
        if sender.lower() == "you":
            tag = "user"
        elif sender.lower() == "claude":
            tag = "claude"
        elif sender.lower() == "james":
            tag = "james"
            
        # Insert message
        self.chat_display.insert(tk.END, f"{sender}: ", tag)
        self.chat_display.insert(tk.END, f"{message}\n\n")
        
        # Auto-scroll to bottom
        self.chat_display.see(tk.END)
        self.chat_display.config(state="disabled")
        
    def clear_chat(self):
        """Clear the chat display"""
        self.chat_display.config(state="normal")
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.config(state="disabled")
        self.display_message("System", "Chat cleared.")
        
    def update_status(self, status, color="green"):
        """Update status label"""
        self.status_label.config(text=status, foreground=color)
        
    def process_messages(self):
        """Process messages from queue (for thread-safe updates)"""
        while self.running:
            try:
                # Check for messages in queue
                try:
                    sender, message = self.message_queue.get(timeout=0.1)
                    self.display_message(sender, message)
                except queue.Empty:
                    pass
            except Exception as e:
                print(f"Message processing error: {e}")
                
    def exit_chat(self):
        """Exit the chat application"""
        self.running = False
        self.chat_manager.save_session()
        self.root.quit()
        
    def run(self):
        """Run the GUI application"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.exit_chat)
            self.root.mainloop()
        except Exception as e:
            print(f"GUI Error: {e}")
            import traceback
            traceback.print_exc()