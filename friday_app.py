
"""
FRIDAY - Offline AI Assistant
Desktop GUI application module for the FRIDAY assistant
"""

import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import pyautogui
from datetime import datetime

# Import the core module
from friday_core import FridayCore


class FridayApp:
    """
    Desktop GUI application for FRIDAY AI Assistant
    """
    
    def __init__(self, root):
        """Initialize the FRIDAY app interface"""
        self.root = root
        self.root.title("FRIDAY - Offline AI Assistant")
        self.root.geometry("900x600")
        self.root.minsize(800, 500)
        
        # Set theme colors
        self.bg_color = "#1e1e2e"  # Dark background
        self.text_color = "#cdd6f4"  # Light text
        self.accent_color = "#f38ba8"  # Pink accent
        self.input_bg = "#313244"  # Darker input background
        self.send_button_color = "#cba6f7"  # Purple button
        
        # Configure root window
        self.root.configure(bg=self.bg_color)
        
        # Initialize FRIDAY core
        self.friday = FridayCore()
        
        # Voice listening status
        self.voice_active = False
        self.voice_thread = None
        
        # Create GUI elements
        self.create_gui()
        
        # Set up closing protocol
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Initial greeting
        self.display_assistant_message("Hello! I'm FRIDAY, your offline AI assistant. How can I help you today?")

    def create_gui(self):
        """Create all GUI elements"""
        # Main frame to hold all elements
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top bar with title and controls
        self.create_top_bar(main_frame)
        
        # Chat display area
        self.create_chat_area(main_frame)
        
        # Input area
        self.create_input_area(main_frame)
        
        # Status bar
        self.create_status_bar(main_frame)

    def create_top_bar(self, parent):
        """Create top bar with title and controls"""
        top_frame = tk.Frame(parent, bg=self.bg_color)
        top_frame.pack(fill=tk.X, pady=5)
        
        # Title
        title_label = tk.Label(
            top_frame, 
            text="FRIDAY AI Assistant", 
            font=("Arial", 16, "bold"),
            fg=self.accent_color,
            bg=self.bg_color
        )
        title_label.pack(side=tk.LEFT, padx=10)
        
        # Voice button
        self.voice_button = tk.Button(
            top_frame,
            text="🎤 Voice: OFF",
            command=self.toggle_voice,
            bg=self.input_bg,
            fg=self.text_color,
            relief=tk.RAISED,
            padx=10
        )
        self.voice_button.pack(side=tk.RIGHT, padx=5)
        
        # Privacy mode button
        self.privacy_button = tk.Button(
            top_frame,
            text="🔒 Privacy Mode",
            command=self.toggle_privacy,
            bg=self.input_bg,
            fg=self.text_color,
            relief=tk.RAISED,
            padx=10
        )
        self.privacy_button.pack(side=tk.RIGHT, padx=5)
        
        # Save button
        save_button = tk.Button(
            top_frame,
            text="💾 Save Chat",
            command=self.save_chat,
            bg=self.input_bg,
            fg=self.text_color,
            relief=tk.RAISED,
            padx=10
        )
        save_button.pack(side=tk.RIGHT, padx=5)
        
        # Load button
        load_button = tk.Button(
            top_frame,
            text="📂 Load Chat",
            command=self.load_chat,
            bg=self.input_bg,
            fg=self.text_color,
            relief=tk.RAISED,
            padx=10
        )
        load_button.pack(side=tk.RIGHT, padx=5)

    def create_chat_area(self, parent):
        """Create the chat display area"""
        # Chat frame with custom styling
        chat_frame = tk.Frame(parent, bg=self.bg_color)
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create scrolled text widget
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=("Arial", 11),
            bg=self.input_bg,
            fg=self.text_color,
            insertbackground=self.text_color,
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        self.chat_display.config(state=tk.DISABLED)  # Make read-only

    def create_input_area(self, parent):
        """Create the user input area"""
        input_frame = tk.Frame(parent, bg=self.bg_color)
        input_frame.pack(fill=tk.X, pady=10)
        
        # User input field
        self.user_input = tk.Entry(
            input_frame,
            font=("Arial", 12),
            bg=self.input_bg,
            fg=self.text_color,
            insertbackground=self.text_color,
            relief=tk.FLAT
        )
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, ipady=8)
        self.user_input.bind("<Return>", lambda event: self.send_message())
        self.user_input.focus_set()
        
        # Send button
        send_button = tk.Button(
            input_frame,
            text="Send",
            command=self.send_message,
            bg=self.send_button_color,
            fg="#000000",
            font=("Arial", 11, "bold"),
            relief=tk.RAISED,
            padx=15,
            pady=5
        )
        send_button.pack(side=tk.RIGHT, padx=5)

    def create_status_bar(self, parent):
        """Create status bar at bottom"""
        status_frame = tk.Frame(parent, bg=self.input_bg, height=25)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Status label
        self.status_label = tk.Label(
            status_frame,
            text="Ready",
            bg=self.input_bg,
            fg=self.text_color,
            anchor=tk.W,
            padx=10
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X)
        
        # Model info
        model_label = tk.Label(
            status_frame,
            text=f"Model: {self.friday.model_name}",
            bg=self.input_bg,
            fg=self.text_color,
            anchor=tk.E,
            padx=10
        )
        model_label.pack(side=tk.RIGHT)

    def send_message(self):
        """Process and send user message"""
        user_message = self.user_input.get().strip()
        if not user_message:
            return
            
        # Clear input field
        self.user_input.delete(0, tk.END)
        
        # Display user message
        self.display_user_message(user_message)
        
        # Update status
        self.update_status("Processing...")
        
        # Use a thread to prevent UI freezing
        threading.Thread(target=self.process_message_thread, args=(user_message,), daemon=True).start()

    def process_message_thread(self, user_message):
        """Process message in background thread"""
        try:
            # Get response from FRIDAY core
            response = self.friday.process_text_input(user_message)
            
            # Display response
            self.root.after(0, lambda: self.display_assistant_message(response))
            
            # Try to speak the response if voice is active
            if self.voice_active and not self.friday.privacy_mode:
                self.friday.speak(response)
                
            # Update status
            self.root.after(0, lambda: self.update_status("Ready"))
            
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            self.root.after(0, lambda: self.display_system_message(error_msg))
            self.root.after(0, lambda: self.update_status("Error occurred"))

    def display_user_message(self, message):
        """Display user message in chat"""
        self.chat_display.config(state=tk.NORMAL)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_display.insert(tk.END, f"[{timestamp}] ", "timestamp")
        
        # Add user message
        self.chat_display.insert(tk.END, "You: ", "user_label")
        self.chat_display.insert(tk.END, f"{message}\n\n", "user_message")
        
        # Apply tags for styling
        self.chat_display.tag_config("timestamp", foreground="#888888")
        self.chat_display.tag_config("user_label", foreground="#89dceb", font=("Arial", 11, "bold"))
        self.chat_display.tag_config("user_message", foreground=self.text_color)
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def display_assistant_message(self, message):
        """Display assistant message in chat"""
        self.chat_display.config(state=tk.NORMAL)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_display.insert(tk.END, f"[{timestamp}] ", "timestamp")
        
        # Add assistant message
        self.chat_display.insert(tk.END, "FRIDAY: ", "assistant_label")
        self.chat_display.insert(tk.END, f"{message}\n\n", "assistant_message")
        
        # Apply tags for styling
        self.chat_display.tag_config("timestamp", foreground="#888888")
        self.chat_display.tag_config("assistant_label", foreground=self.accent_color, font=("Arial", 11, "bold"))
        self.chat_display.tag_config("assistant_message", foreground=self.text_color)
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def display_system_message(self, message):
        """Display system message in chat"""
        self.chat_display.config(state=tk.NORMAL)
        
        # Add system message
        self.chat_display.insert(tk.END, "System: ", "system_label")
        self.chat_display.insert(tk.END, f"{message}\n\n", "system_message")
        
        # Apply tags for styling
        self.chat_display.tag_config("system_label", foreground="#f9e2af", font=("Arial", 11, "bold"))
        self.chat_display.tag_config("system_message", foreground="#f9e2af")
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def update_status(self, message):
        """Update status bar message"""
        self.status_label.config(text=message)

    def toggle_voice(self):
        """Toggle voice recognition on/off"""
        if self.voice_active:
            # Turn off voice
            self.voice_active = False
            self.voice_button.config(text="🎤 Voice: OFF")
            self.update_status("Voice recognition deactivated")
            # Stop the voice thread
            if self.voice_thread and self.voice_thread.is_alive():
                self.friday.should_stop = True
                self.voice_thread.join(timeout=1)
        else:
            # Turn on voice
            self.voice_active = True
            self.voice_button.config(text="🎤 Voice: ON")
            self.update_status("Voice recognition activated")
            self.display_system_message("Voice recognition activated. Say 'Hey FRIDAY' to get my attention.")
            
            # Start voice thread
            self.friday.should_stop = False
            self.voice_thread = threading.Thread(target=self.voice_listen_thread, daemon=True)
            self.voice_thread.start()

    def voice_listen_thread(self):
        """Background thread for voice recognition"""
        # Reset stop flag
        self.friday.should_stop = False
        
        # Start listening
        try:
            self.friday.listen()
        except Exception as e:
            self.root.after(0, lambda: self.display_system_message(f"Voice error: {str(e)}"))
            self.root.after(0, lambda: self.toggle_voice())  # Turn off voice on error
            
        # Update button if thread exits
        if self.voice_active:
            self.root.after(0, lambda: self.toggle_voice())

    def toggle_privacy(self):
        """Toggle privacy mode"""
        self.friday.toggle_privacy()
        privacy_status = "ON" if self.friday.privacy_mode else "OFF"
        privacy_icon = "🔐" if self.friday.privacy_mode else "🔒"
        
        self.privacy_button.config(text=f"{privacy_icon} Privacy: {privacy_status}")
        self.display_system_message(f"Privacy mode: {privacy_status}")

    def save_chat(self):
        """Save chat history to file"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Save Chat History"
            )
            
            if not file_path:
                return
                
            success = self.friday.save_conversation(file_path)
            
            if success:
                self.display_system_message(f"Chat history saved to {file_path}")
            else:
                self.display_system_message("Failed to save chat history")
                
        except Exception as e:
            self.display_system_message(f"Error saving chat: {str(e)}")

    def load_chat(self):
        """Load chat history from file"""
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Load Chat History"
            )
            
            if not file_path:
                return
                
            success = self.friday.load_conversation(file_path)
            
            if success:
                # Clear chat display
                self.chat_display.config(state=tk.NORMAL)
                self.chat_display.delete(1.0, tk.END)
                self.chat_display.config(state=tk.DISABLED)
                
                # Reload conversation from history
                for message in self.friday.conversation_history:
                    if message["role"] == "user":
                        self.display_user_message(message["content"])
                    else:
                        self.display_assistant_message(message["content"])
                        
                self.display_system_message(f"Chat history loaded from {file_path}")
            else:
                self.display_system_message("Failed to load chat history")
                
        except Exception as e:
            self.display_system_message(f"Error loading chat: {str(e)}")

    def on_closing(self):
        """Handle window closing"""
        # Stop voice thread if running
        if self.voice_active:
            self.friday.should_stop = True
            if self.voice_thread and self.voice_thread.is_alive():
                self.voice_thread.join(timeout=1)
        
        # Ask user to confirm exit
        if messagebox.askokcancel("Quit", "Do you want to quit FRIDAY?"):
            self.root.destroy()
            sys.exit(0)


# Main function to start the app
def main():
    # Create tkinter root
    root = tk.Tk()
    
    # Set window icon (if available)
    try:
        # Set taskbar icon (Windows)
        import ctypes
        myappid = 'ai.friday.assistant.1.0'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except:
        pass
    
    # Create and run app
    app = FridayApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()