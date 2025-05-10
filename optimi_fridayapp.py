import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from PIL import Image, ImageTk # Keep if you plan to use images, otherwise remove
from datetime import datetime
import math
from functools import partial
from typing import Callable, Optional, Union, List, Dict, Any
import json

# Import the core module
from friday_core import FridayCore

# --- Constants ---
APP_VERSION = "1.1 Optimized"
FONT_PRIMARY = "Consolas" # Changed from Arial for more 'tech' feel
FONT_SANS = "Helvetica" # For some UI elements

# --- Theme ---
class Theme:
    """Centralized theme management"""
    def __init__(self):
        self.bg = "#1a1b26"
        self.sidebar = "#16161e"
        self.accent = "#7aa2f7"
        self.highlight = "#bb9af7"
        self.text = "#c0caf5"
        self.input_bg = "#24283b"
        self.user_msg_bg = "#414868"
        self.assistant_msg_bg = "#565f89"
        self.error = "#f7768e"
        self.success = "#9ece6a"
        self.system_info = "#e0af68" # Yellowish for system messages

THEME = Theme() # Global theme instance

# --- Custom Widgets ---
class CustomButton(tk.Canvas):
    """Multi-purpose custom button with animations and distinct shapes."""
    def __init__(self, parent, text: str, command: Callable,
                 width: int = 120, height: int = 40, shape: str = "rect",
                 icon: Optional[str] = None, **kwargs): # icon can be a unicode char
        
        self.width = width
        self.height = height
        self.shape = shape  # "rect" or "hex"
        self.theme = kwargs.get('theme', THEME)
        
        super().__init__(parent, width=self.width, height=self.height,
                         bg=kwargs.get('bg_canvas', self.theme.sidebar if shape == "hex" else self.theme.bg),
                         highlightthickness=0, bd=0)
        
        self.command = command
        self.original_text = text
        self.icon = icon
        self.display_text = self.icon if self.icon and self.shape == "hex" else self.original_text

        self.hovered = False
        self.pressed = False # For press animation
        self.is_toggle_active = kwargs.get('is_toggle_active', False) # For toggle buttons
        
        self.base_bg = kwargs.get('bg', self.theme.sidebar if self.shape == "hex" else self.theme.input_bg)
        self.base_fg = kwargs.get('fg', self.theme.accent)
        self.hover_bg = kwargs.get('hover_bg', self.theme.accent if self.shape == "hex" else self.theme.user_msg_bg)
        self.hover_fg = kwargs.get('hover_fg', "#ffffff")
        self.border_color = kwargs.get('border', self.theme.accent)
        self.active_toggle_color = kwargs.get('active_color', self.theme.highlight) # For active toggle state

        self._draw()
        
        self.bind("<Enter>", self._on_hover)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _on_hover(self, event: Optional[tk.Event] = None):
        self.hovered = True
        self._draw()

    def _on_leave(self, event: Optional[tk.Event] = None):
        self.hovered = False
        self.pressed = False # Ensure pressed state resets if mouse leaves while pressed
        self._draw()

    def _on_press(self, event: Optional[tk.Event] = None):
        self.pressed = True
        self._draw()

    def _on_release(self, event: Optional[tk.Event] = None):
        if self.pressed and self.hovered: # Only fire command if released over button
            if self.command:
                self.command()
        self.pressed = False
        self._draw() # Redraw to normal or hover state

    def set_toggle_active(self, active: bool):
        """Externally set the toggle state for buttons that act like toggles."""
        if self.is_toggle_active != active:
            self.is_toggle_active = active
            self._draw()

    def _draw(self):
        self.delete("all")
        if self.shape == "rect":
            self._draw_rect()
        elif self.shape == "hex":
            self._draw_hex()

    def _create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1 + radius, y1, x2 - radius, y1,
            x2, y1, x2, y1 + radius, x2, y2 - radius, x2, y2,
            x2 - radius, y2, x1 + radius, y2,
            x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def _draw_rect(self):
        current_bg = self.base_bg
        current_fg = self.base_fg
        border_w = 1
        
        if self.is_toggle_active:
            current_bg = self.active_toggle_color
            current_fg = "#ffffff"
            border_w = 2
        elif self.pressed:
            current_bg = self.hover_bg # Use hover_bg for pressed state, or a dedicated pressed_bg
            current_fg = self.hover_fg
            border_w = 2
        elif self.hovered:
            current_bg = self.hover_bg
            current_fg = self.hover_fg
            border_w = 2
        
        # Main button body
        self._create_rounded_rect(2, 2, self.width - 2, self.height - 2, 8,
                                  fill=current_bg, outline=self.border_color, width=border_w)
        
        # Text
        self.create_text(self.width / 2, self.height / 2, text=self.display_text,
                         fill=current_fg, font=(FONT_SANS, 10, "bold"))
        
        # Tech accents on hover (simplified)
        if self.hovered and not self.pressed and not self.is_toggle_active:
            accent_size = 5
            accent_color = self.theme.accent
            # Top-left
            self.create_line(3, 3, 3 + accent_size, 3, fill=accent_color, width=1)
            self.create_line(3, 3, 3, 3 + accent_size, fill=accent_color, width=1)
            # Bottom-right
            self.create_line(self.width - 3, self.height - 3, self.width - 3 - accent_size, self.height - 3, fill=accent_color, width=1)
            self.create_line(self.width - 3, self.height - 3, self.width - 3, self.height - 3 - accent_size, fill=accent_color, width=1)

    def _draw_hex(self):
        cx, cy = self.width / 2, self.height / 2
        r = min(cx, cy) - 4 # Padding
        points = []
        for i in range(6):
            angle_deg = 60 * i - 30 # Rotated for flat top/bottom
            angle_rad = math.radians(angle_deg)
            points.extend([cx + r * math.cos(angle_rad), cy + r * math.sin(angle_rad)])

        current_fill = self.base_bg
        current_outline = self.base_fg
        outline_width = 1
        text_color = self.theme.text

        if self.is_toggle_active:
            current_fill = self.active_toggle_color
            current_outline = "#ffffff"
            outline_width = 2
            text_color = "#ffffff"
        elif self.pressed:
            current_fill = self.theme.accent # Brighter when pressed
            current_outline = self.active_toggle_color
            text_color = "#ffffff"
        elif self.hovered:
            current_fill = self.hover_bg
            current_outline = self.active_toggle_color
            outline_width = 2
            text_color = "#ffffff"
            
        self.create_polygon(points, fill=current_fill, outline=current_outline, width=outline_width)
        
        if self.display_text:
            self.create_text(cx, cy, text=self.display_text, fill=text_color,
                             font=(FONT_SANS, 12, "bold" if len(self.display_text) == 1 else "normal"))


class PulsingIndicator(tk.Canvas):
    """Animated pulsing circle for UI status indication."""
    def __init__(self, parent, size: int = 20, base_color: str = THEME.accent, 
                 pulse_color: str = THEME.accent, bg: str = THEME.bg):
        super().__init__(parent, width=size, height=size, bg=bg, highlightthickness=0)
        self.size = size
        self.base_color = base_color
        self.pulse_color = pulse_color # Could be different from base
        self.pulse_radius = 0
        self.max_pulse_radius = size // 2
        self.is_pulsing = False
        self.animation_job = None
        self._draw_static()

    def _draw_static(self):
        self.delete("pulse")
        self.delete("core")
        core_radius = self.size // 4
        cx, cy = self.size / 2, self.size / 2
        self.create_oval(cx - core_radius, cy - core_radius,
                           cx + core_radius, cy + core_radius,
                           fill=self.base_color, outline="", tags="core")

    def _draw_pulse(self):
        self.delete("pulse")
        if not self.is_pulsing:
            return

        cx, cy = self.size / 2, self.size / 2
        # Simple expanding ring, no complex alpha needed for Tkinter
        # Opacity can be simulated by color choice if desired (e.g., lighter pulse_color)
        self.create_oval(cx - self.pulse_radius, cy - self.pulse_radius,
                           cx + self.pulse_radius, cy + self.pulse_radius,
                           outline=self.pulse_color, width=2, tags="pulse")

    def start(self):
        if not self.is_pulsing:
            self.is_pulsing = True
            self.pulse_radius = self.size // 4 # Start from core size
            self._animate()

    def stop(self):
        if self.is_pulsing:
            self.is_pulsing = False
            if self.animation_job:
                self.after_cancel(self.animation_job)
                self.animation_job = None
            self._draw_static() # Reset to static core

    def _animate(self):
        if not self.is_pulsing:
            return

        self.pulse_radius += 1
        if self.pulse_radius > self.max_pulse_radius:
            self.pulse_radius = self.size // 4 # Reset pulse

        self._draw_pulse()
        self.animation_job = self.after(50, self._animate)

    def set_color(self, color: str):
        self.base_color = color
        self.itemconfig("core", fill=self.base_color)


# --- Main Application ---
class FridayApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.theme = THEME # Use global theme instance
        self.friday_core = FridayCore()
        
        self.voice_active = False
        self.privacy_mode = False # Not fully implemented, but state is tracked
        self.chat_history: List[Dict[str, Any]] = []

        self._configure_root_window()
        self._setup_ui()
        self._configure_text_tags()
        
        self.root.after(500, lambda: self.display_assistant_message(
            f"Hello! I'm FRIDAY ({APP_VERSION}), your offline AI assistant. How can I help you?"
        ))
        self.update_status(f"System Ready. Model: {self.friday_core.model_name}")

    def _configure_root_window(self):
        self.root.title(f"FRIDAY - Offline AI Assistant ({APP_VERSION})")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)
        self.root.configure(bg=self.theme.bg)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_ui(self):
        # Main layout
        self.sidebar_frame = tk.Frame(self.root, bg=self.theme.sidebar, width=70) # Slightly narrower
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar_frame.pack_propagate(False)

        self.content_frame = tk.Frame(self.root, bg=self.theme.bg)
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._create_sidebar_content()
        self._create_header_content()
        self._create_main_interface()

    def _create_sidebar_content(self):
        # Logo
        logo_label = tk.Label(self.sidebar_frame, text="F", font=(FONT_PRIMARY, 36, "bold"),
                              fg=self.theme.accent, bg=self.theme.sidebar)
        logo_label.pack(pady=20)

        # Sidebar buttons
        button_configs = [
            {"name": "chat", "icon": "💬", "cmd": self._activate_chat_view, "active": True},
            {"name": "voice", "icon": "🎤", "cmd": self.toggle_voice_mode},
            {"name": "privacy", "icon": "🔒", "cmd": self.toggle_privacy_mode},
            {"name": "settings", "icon": "⚙️", "cmd": self.show_settings_dialog}
        ]
        self.sidebar_buttons: Dict[str, CustomButton] = {}
        for config in button_configs:
            btn = CustomButton(self.sidebar_frame, text=config["icon"], command=config["cmd"],
                               shape="hex", width=50, height=50, icon=config["icon"],
                               is_toggle_active=config.get("active", False), theme=self.theme)
            btn.pack(pady=12)
            self.sidebar_buttons[config["name"]] = btn
            if config["name"] == "voice": self.voice_button_widget = btn # Specific reference
            if config["name"] == "privacy": self.privacy_button_widget = btn


        version_label = tk.Label(self.sidebar_frame, text=f"v{APP_VERSION.split(' ')[0]}", font=(FONT_PRIMARY, 8),
                                 fg=self.theme.system_info, bg=self.theme.sidebar)
        version_label.pack(side=tk.BOTTOM, pady=10)

    def _create_header_content(self):
        header = tk.Frame(self.content_frame, bg=self.theme.bg, height=60)
        header.pack(fill=tk.X, padx=20, pady=(10,5))

        title_label = tk.Label(header, text="FRIDAY Assistant", font=(FONT_SANS, 18, "bold"),
                               fg=self.theme.accent, bg=self.theme.bg)
        title_label.pack(side=tk.LEFT, padx=(0,10))

        self.processing_indicator = PulsingIndicator(header, size=22, bg=self.theme.bg)
        self.processing_indicator.pack(side=tk.LEFT, pady=5)

        # Header buttons (Save/Load)
        controls_frame = tk.Frame(header, bg=self.theme.bg)
        controls_frame.pack(side=tk.RIGHT)
        
        CustomButton(controls_frame, text="Save Chat", command=self.save_chat_history,
                     width=100, height=35, theme=self.theme).pack(side=tk.LEFT, padx=5)
        CustomButton(controls_frame, text="Load Chat", command=self.load_chat_history,
                     width=100, height=35, theme=self.theme).pack(side=tk.LEFT, padx=5)

    def _create_main_interface(self):
        # Main content area (chat + input + status)
        main_area = tk.Frame(self.content_frame, bg=self.theme.bg)
        main_area.pack(fill=tk.BOTH, expand=True, padx=20, pady=(5, 20))

        # Chat display
        chat_display_container = tk.Frame(main_area, bg=self.theme.accent, bd=1) # Subtle border
        chat_display_container.pack(fill=tk.BOTH, expand=True)

        self.chat_display = scrolledtext.ScrolledText(
            chat_display_container, wrap=tk.WORD, font=(FONT_PRIMARY, 11),
            bg=self.theme.bg, fg=self.theme.text, relief=tk.FLAT,
            padx=15, pady=15, insertbackground=self.theme.text, bd=0 
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        self.chat_display.config(state=tk.DISABLED)
        # Style scrollbar (less intrusive)
        self.chat_display.vbar.configure(width=8, troughcolor=self.theme.bg, bg=self.theme.input_bg,
                                         activebackground=self.theme.accent, relief=tk.FLAT)

        # Input area
        input_area = tk.Frame(main_area, bg=self.theme.bg, height=60)
        input_area.pack(fill=tk.X, pady=(10,0))

        self.voice_status_indicator = PulsingIndicator(input_area, size=25, base_color=self.theme.error,
                                                       pulse_color=self.theme.error, bg=self.theme.bg)
        # self.voice_status_indicator.pack(side=tk.LEFT, padx=(0, 10)) # Packed when voice active

        input_field_container = tk.Frame(input_area, bg=self.theme.accent, bd=1) # Similar border
        input_field_container.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.user_input_var = tk.StringVar()
        self.user_input_entry = tk.Entry(
            input_field_container, textvariable=self.user_input_var,
            font=(FONT_PRIMARY, 12), bg=self.theme.input_bg, fg=self.theme.text,
            insertbackground=self.theme.accent, relief=tk.FLAT, bd=8 # bd for padding inside
        )
        self.user_input_entry.pack(fill=tk.X, expand=True)
        self.user_input_entry.bind("<Return>", self._on_send_message)
        self.user_input_entry.focus_set()

        self.send_button = CustomButton(input_area, text="Send", command=self._on_send_message,
                                        width=80, height=40, theme=self.theme)
        self.send_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Status bar
        status_bar = tk.Frame(main_area, bg=self.theme.bg, height=25)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(5,0))
        self.status_label = tk.Label(status_bar, text="Initializing...", font=(FONT_PRIMARY, 9),
                                     fg=self.theme.accent, bg=self.theme.bg, anchor=tk.W)
        self.status_label.pack(side=tk.LEFT)
        
        model_info_label = tk.Label(status_bar, text=f"Model: {self.friday_core.model_name}", font=(FONT_PRIMARY, 9),
                                     fg=self.theme.highlight, bg=self.theme.bg, anchor=tk.E)
        model_info_label.pack(side=tk.RIGHT)

    def _configure_text_tags(self):
        """Configure tags for styling messages in the chat display."""
        # User message
        self.chat_display.tag_configure("user_timestamp", foreground="#999", font=(FONT_PRIMARY, 8))
        self.chat_display.tag_configure("user_bubble",
                                        background=self.theme.user_msg_bg,
                                        foreground="#ffffff",
                                        font=(FONT_PRIMARY, 11),
                                        relief=tk.RAISED, borderwidth=1,
                                        lmargin1=100, rmargin=10, # lmargin1 for indent, rmargin for space from right
                                        justify=tk.RIGHT,
                                        spacing1=2, spacing3=2, # Spacing around paragraph
                                        wrap=tk.WORD)
        self.chat_display.tag_configure("user_label", foreground=self.theme.accent, font=(FONT_PRIMARY, 10, "bold"),
                                        lmargin1=100, rmargin=10, justify=tk.RIGHT)


        # Assistant message
        self.chat_display.tag_configure("assistant_timestamp", foreground="#999", font=(FONT_PRIMARY, 8))
        self.chat_display.tag_configure("assistant_bubble",
                                        background=self.theme.assistant_msg_bg,
                                        foreground=self.theme.text,
                                        font=(FONT_PRIMARY, 11),
                                        relief=tk.RAISED, borderwidth=1,
                                        lmargin1=10, rmargin=100, # rmargin for space from right
                                        spacing1=2, spacing3=2,
                                        wrap=tk.WORD)
        self.chat_display.tag_configure("assistant_label", foreground=self.theme.highlight, font=(FONT_PRIMARY, 10, "bold"),
                                        lmargin1=10, rmargin=100)
        
        # System message
        self.chat_display.tag_configure("system_message",
                                        foreground=self.theme.system_info,
                                        font=(FONT_PRIMARY, 10, "italic"),
                                        justify=tk.CENTER,
                                        spacing1=5, spacing3=5)
        self.chat_display.tag_configure("error_message",
                                        foreground=self.theme.error,
                                        font=(FONT_PRIMARY, 10, "bold"),
                                        justify=tk.CENTER,
                                        spacing1=5, spacing3=5)

    def _append_message_to_display(self, role: str, text: str, label: Optional[str] = None):
        self.chat_display.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%I:%M %p")
        
        if self.chat_display.index('end-1c') != "\n": # Add newline if not first message or prev not newline
             self.chat_display.insert(tk.END, "\n")

        if role == "user":
            if label: self.chat_display.insert(tk.END, f"{label} ", ("user_label",))
            self.chat_display.insert(tk.END, f"{text}\n", ("user_bubble",))
            self.chat_display.insert(tk.END, f"{timestamp} ", ("user_timestamp", "user_label")) # Align timestamp with label
        elif role == "assistant":
            if label: self.chat_display.insert(tk.END, f"{label} ", ("assistant_label",))
            # Placeholder for typing effect if re-added
            self.chat_display.insert(tk.END, f"{text}\n", ("assistant_bubble",))
            self.chat_display.insert(tk.END, f"{timestamp} ", ("assistant_timestamp", "assistant_label"))
        elif role == "system":
            self.chat_display.insert(tk.END, f"{text}\n", ("system_message",))
        elif role == "error":
             self.chat_display.insert(tk.END, f"{text}\n", ("error_message",))

        self.chat_display.insert(tk.END, "\n") # Extra space after message block
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def _display_message_with_typing_effect(self, message: str, index: int = 0):
        """Displays assistant message with a typing animation."""
        chunk_size = 3  # Characters per update
        typing_delay = 20  # Milliseconds

        if index == 0: # First call for this message
            self.chat_display.config(state=tk.NORMAL)
            timestamp = datetime.now().strftime("%I:%M %p")
            if self.chat_display.index('end-1c') != "\n":
                 self.chat_display.insert(tk.END, "\n")
            self.chat_display.insert(tk.END, "FRIDAY ", ("assistant_label",))
            # Store start position of actual message content for later tagging
            self._typing_message_start_index = self.chat_display.index(tk.END)
            self.chat_display.config(state=tk.DISABLED)

        if index < len(message):
            self.chat_display.config(state=tk.NORMAL)
            display_chunk = message[index : index + chunk_size]
            self.chat_display.insert(tk.END, display_chunk) # No tag yet, apply at end
            self.chat_display.config(state=tk.DISABLED)
            self.chat_display.see(tk.END)
            self.root.after(typing_delay, lambda: self._display_message_with_typing_effect(message, index + chunk_size))
        else: # Typing finished
            self.chat_display.config(state=tk.NORMAL)
            # Apply the bubble tag to the whole message typed
            end_index = self.chat_display.index(tk.END)
            self.chat_display.tag_add("assistant_bubble", self._typing_message_start_index, end_index)
            
            # Add timestamp
            timestamp = datetime.now().strftime("%I:%M %p")
            self.chat_display.insert(tk.END, f"\n{timestamp} ", ("assistant_timestamp", "assistant_label"))
            self.chat_display.insert(tk.END, "\n\n")
            self.chat_display.config(state=tk.DISABLED)
            self.chat_display.see(tk.END)
            self.processing_indicator.stop()
            self.update_status("Ready.")

    def display_user_message(self, message: str):
        self._append_message_to_display("user", message, "You:")

    def display_assistant_message(self, message: str, with_typing: bool = False):
        if with_typing:
            self._display_message_with_typing_effect(message)
        else:
            self._append_message_to_display("assistant", message, "FRIDAY:")

    def display_system_message(self, message: str, is_error: bool = False):
        self._append_message_to_display("error" if is_error else "system", message)

    def _on_send_message(self, event: Optional[tk.Event] = None):
        user_text = self.user_input_var.get().strip()
        if not user_text:
            return

        self.display_user_message(user_text)
        self.chat_history.append({"role": "user", "content": user_text, "time": time.time()})
        self.user_input_var.set("")
        self.processing_indicator.start()
        self.update_status("FRIDAY is thinking...")

        # Process in a thread to keep UI responsive
        threading.Thread(target=self._process_user_query, args=(user_text,), daemon=True).start()

    def _process_user_query(self, user_text: str):
        try:
            response = self.friday_core.process_text_input(user_text)
            self.chat_history.append({"role": "assistant", "content": response, "time": time.time()})
            # Schedule UI update back on the main thread
            self.root.after(0, lambda: self.display_assistant_message(response, with_typing=True))
            
            if self.voice_active and not self.privacy_mode:
                # Make speak non-blocking or handle completion
                self.friday_core.speak(response, on_done=lambda: self.root.after(0, self._on_speech_done))
        except Exception as e:
            error_msg = f"Core Error: {e}"
            print(f"Error during processing: {error_msg}") # Log to console
            self.chat_history.append({"role": "system", "content": error_msg, "time": time.time()})
            self.root.after(0, lambda: self.display_system_message(error_msg, is_error=True))
            self.root.after(0, self.processing_indicator.stop)
            self.root.after(0, lambda: self.update_status("Error processing query."))

    def _on_speech_done(self):
        self.update_status("Speech finished.")
        # Any other actions after speech, if needed

    def update_status(self, message: str):
        self.status_label.config(text=message)

    def _activate_chat_view(self):
        # Placeholder if other views are added. For now, it just ensures chat button is "active".
        for name, btn in self.sidebar_buttons.items():
            btn.set_toggle_active(name == "chat")
        self.display_system_message("Chat view active.")


    def toggle_voice_mode(self):
        self.voice_active = not self.voice_active
        self.voice_button_widget.set_toggle_active(self.voice_active)
        if self.voice_active:
            self.voice_status_indicator.pack(side=tk.LEFT, padx=(0, 10), before=self.user_input_entry.master.master) # Pack before input container
            self.voice_status_indicator.start()
            self.display_system_message("Voice input/output enabled. FRIDAY is listening...")
            self.update_status("Voice mode: ON - Listening...")
            # Start listening via core
            self.friday_core.start_listening(self._on_voice_detected, self._on_listening_error)
        else:
            self.voice_status_indicator.stop()
            self.voice_status_indicator.pack_forget()
            self.display_system_message("Voice input/output disabled.")
            self.update_status("Voice mode: OFF")
            self.friday_core.stop_listening() # Tell core to stop

    def _on_voice_detected(self, detected_text: str):
        """Callback for when FridayCore detects speech."""
        if not self.voice_active: return # Guard if voice was disabled during listen
        
        self.root.after(0, lambda: self.display_system_message(f"Voice detected: \"{detected_text}\""))
        self.root.after(0, lambda: self.user_input_var.set(detected_text)) # Populate input field
        self.root.after(0, self._on_send_message) # Process it like typed input
        # Optionally, restart listening or wait for user to re-enable
        # self.root.after(1000, lambda: self.friday_core.start_listening(self._on_voice_detected, self._on_listening_error) if self.voice_active else None)


    def _on_listening_error(self, error_message: str):
        """Callback for listening errors from FridayCore."""
        self.root.after(0, lambda: self.display_system_message(f"Voice listening error: {error_message}", is_error=True))
        self.root.after(0, lambda: self.update_status("Voice listening error."))
        # Potentially disable voice mode or attempt to restart
        if self.voice_active: # If still meant to be active, try to recover or notify
            self.root.after(0, self.toggle_voice_mode) # Turn it off to reset UI
            self.root.after(100, lambda: self.display_system_message("Voice mode automatically disabled due to error.", is_error=True))


    def toggle_privacy_mode(self):
        self.privacy_mode = not self.privacy_mode
        self.privacy_button_widget.set_toggle_active(self.privacy_mode)
        msg = "Privacy Mode: ON (speech output muted, history logging may be limited)" if self.privacy_mode \
              else "Privacy Mode: OFF"
        self.display_system_message(msg)
        self.update_status(f"Privacy: {'ON' if self.privacy_mode else 'OFF'}")

    def show_settings_dialog(self):
        # Simple placeholder settings dialog
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Settings")
        settings_win.geometry("300x200")
        settings_win.configure(bg=self.theme.bg)
        settings_win.transient(self.root) # Keep on top of main window
        settings_win.grab_set() # Modal

        tk.Label(settings_win, text="FRIDAY Settings", font=(FONT_SANS, 14, "bold"),
                 fg=self.theme.accent, bg=self.theme.bg).pack(pady=20)
        tk.Label(settings_win, text="Settings are not yet implemented.",
                 fg=self.theme.text, bg=self.theme.bg).pack(pady=10)
        
        CustomButton(settings_win, text="Close", command=settings_win.destroy,
                     width=80, height=35, theme=self.theme).pack(pady=20)


    def save_chat_history(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Chat History", "*.json"), ("All Files", "*.*")],
            title="Save Chat As"
        )
        if not filepath:
            return
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.chat_history, f, indent=2)
            self.display_system_message(f"Chat history saved to {os.path.basename(filepath)}")
            self.update_status("Chat saved.")
        except Exception as e:
            self.display_system_message(f"Error saving chat: {e}", is_error=True)
            self.update_status("Error saving chat.")

    def load_chat_history(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON Chat History", "*.json"), ("All Files", "*.*")],
            title="Load Chat From"
        )
        if not filepath:
            return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                loaded_history = json.load(f)
            
            # Basic validation of loaded history
            if not isinstance(loaded_history, list) or \
               not all(isinstance(item, dict) and "role" in item and "content" in item for item in loaded_history):
                raise ValueError("Invalid chat history format.")

            self.chat_history = loaded_history
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete(1.0, tk.END) # Clear current display
            self.chat_display.config(state=tk.DISABLED)

            for entry in self.chat_history:
                role = entry.get("role", "system")
                content = entry.get("content", "")
                label = "You:" if role == "user" else "FRIDAY:" if role == "assistant" else None
                self._append_message_to_display(role, content, label)
            
            self.display_system_message(f"Chat history loaded from {os.path.basename(filepath)}")
            self.update_status("Chat loaded.")
        except Exception as e:
            self.display_system_message(f"Error loading chat: {e}", is_error=True)
            self.update_status("Error loading chat.")


    def _on_closing(self):
        if messagebox.askokcancel("Quit FRIDAY", "Are you sure you want to exit FRIDAY?"):
            if self.friday_core.is_listening:
                self.friday_core.stop_listening()
            # Any other cleanup tasks
            self.root.destroy()

if __name__ == "__main__":
    if sys.version_info < (3, 7):
        messagebox.showerror("Unsupported Python Version",
                             "FRIDAY requires Python 3.7 or newer. Please upgrade your Python.")
        sys.exit(1)
        
    main_root = tk.Tk()
    app = FridayApp(main_root)
    main_root.mainloop()