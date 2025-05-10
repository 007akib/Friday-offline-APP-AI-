"""
FRIDAY - Offline AI Assistant
Core module containing all assistant functionality in a single script
"""

import os
import re
import json
import time
import random
import threading
import queue
import requests
import pyttsx3
import speech_recognition as sr
from datetime import datetime
from collections import deque


class FridayCore:
    """
    Core class for the FRIDAY AI Assistant
    Contains all essential functionality in a single class
    """

    def __init__(self, wake_word="friday", max_context_length=10):
        """Initialize FRIDAY with essential components"""
        print("Initializing FRIDAY Assistant...")
        
        # Core components
        self.name = "FRIDAY"
        self.wake_word = wake_word.lower()
        self.is_listening = False
        self.should_stop = False
        self.privacy_mode = False
        
        # Context management
        self.max_context_length = max_context_length
        self.conversation_history = deque(maxlen=max_context_length)
        self.current_emotion = "neutral"
        
        # Initialize voice components
        self.initialize_voice()
        
        # Initialize LLM connection
        self.initialize_llm()
        
        # Command handling
        self.initialize_commands()
        
        # Queue for communication between threads
        self.audio_queue = queue.Queue()
        
        print(f"{self.name} initialized and ready.")
        self.speak("I am here and ready to assist you.")

    def initialize_voice(self):
        """Set up speech recognition and synthesis"""
        # Text-to-Speech
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate',150)  # Speed of speech
        
        # Get available voices and set to female voice if available
        voices = self.engine.getProperty('voices')
        for voice in voices:
                self.engine.setProperty('voice', voice.id)
                break
        
        # Speech recognition
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 2000
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        
        try:
            # Test microphone availability
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print("Microphone initialized successfully")
        except Exception as e:
            print(f"Warning: Microphone initialization failed: {e}")
            print("Voice input will not be available")

    def initialize_llm(self):
        """Set up connection to local LLM via Ollama"""
        self.model_name = "deepseek-r1:1.5b"
        self.ollama_url = "http://localhost:11434/api/generate"
        
        # Test connection to Ollama
        try:
            response = requests.get("http://localhost:11434/api/tags")
            models = response.json().get("models", [])
            model_exists = any(model["name"] == self.model_name for model in models)
            
            if not model_exists:
                print(f"Warning: {self.model_name} not found. Please run: ollama pull {self.model_name}")
            else:
                print(f"Successfully connected to Ollama with {self.model_name}")
                
        except requests.exceptions.ConnectionError:
            print("Warning: Cannot connect to Ollama server. Is it running?")
            print("Start Ollama with: ollama serve")

    def initialize_commands(self):
        """Set up command handling"""
        self.commands = {
            "tell me a story": self.tell_story,
            "what time is it": self.tell_time,
            "what's the time": self.tell_time,
            "current time": self.tell_time,
            "privacy shield": self.toggle_privacy,
            "privacy mode": self.toggle_privacy,
            "stop listening": self.stop_listening,
            "goodbye": self.stop_listening,
            "exit": self.stop_listening,
            "help": self.show_help,
        }

    def speak(self, text):
        """Convert text to speech"""
        if self.privacy_mode:
            print(f"[PRIVACY MODE] {self.name} would say: {text}")
            return
            
        print(f"{self.name}: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self):
        """Listen for wake word and commands"""
        self.is_listening = True
        self.should_stop = False
        
        print(f"Listening for wake word: 'Hey {self.name}'")
        
        # Start background listening thread
        threading.Thread(target=self._listen_thread, daemon=True).start()
        
        # Process audio queue in main thread
        while not self.should_stop:
            try:
                audio_data = self.audio_queue.get(timeout=0.5)
                self._process_audio(audio_data)
            except queue.Empty:
                pass
            except KeyboardInterrupt:
                self.should_stop = True
                break
        
        self.is_listening = False
        print(f"{self.name} has stopped listening.")

    def _listen_thread(self):
        """Background thread to capture audio"""
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            while not self.should_stop:
                try:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=10)
                    self.audio_queue.put(audio)
                except sr.WaitTimeoutError:
                    pass
                except Exception as e:
                    print(f"Error in listen thread: {e}")
                    time.sleep(1)

    def _process_audio(self, audio):
        """Process captured audio"""
        try:
            # First try with Google (online, more accurate when available)
            text = self.recognizer.recognize_google(audio)
        except sr.RequestError:
            try:
                # Fallback to Sphinx (offline, less accurate)
                text = self.recognizer.recognize_sphinx(audio)
            except:
                return
        except:
            return
            
        text = text.lower()
        print(f"Recognized: {text}")
        
        # Check for wake word
        wake_patterns = [
            f"hey {self.wake_word}",
            f"ok {self.wake_word}",
            f"okay {self.wake_word}",
            f"hi {self.wake_word}",
            self.wake_word
        ]
        
        if any(pattern in text for pattern in wake_patterns):
            # Remove wake phrase from text
            for pattern in wake_patterns:
                if pattern in text:
                    command = text.replace(pattern, "").strip()
                    break
            else:
                command = ""
                
            self._process_command(command)

    def _process_command(self, command):
        """Process voice command"""
        if not command:
            self.speak("How can I help you?")
            return
            
        # Check for direct command matches
        for cmd, func in self.commands.items():
            if cmd in command:
                func()
                return
                
        # If no direct match, send to LLM
        self._handle_conversation(command)

    def _handle_conversation(self, user_input):
        """Process conversation with LLM"""
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # Get response from LLM
        response = self.query_llm(user_input)
        
        # Add assistant response to history
        self.conversation_history.append({"role": "assistant", "content": response})
        
        # Speak the response
        self.speak(response)

    def query_llm(self, prompt):
        """Send prompt to Ollama LLM and get response"""
        try:
            # Build context from conversation history
            context = ""
            for message in self.conversation_history:
                role_prefix = "User: " if message["role"] == "user" else f"{self.name}: "
                context += f"{role_prefix}{message['content']}\n"
            
            # Add current query if not in history yet
            if not any(message["content"] == prompt and message["role"] == "user" 
                      for message in self.conversation_history):
                context += f"User: {prompt}\n{self.name}: "
            
            # Prepare request for Ollama
            data = {
                "model": self.model_name,
                "prompt": context,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "top_k": 40,
                    "num_predict": 256,  # Limit response length to save resources
                }
            }
            
            # Send request
            response = requests.post(self.ollama_url, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "I'm sorry, I couldn't process that request.")
            else:
                print(f"LLM request failed with status code: {response.status_code}")
                return "I'm having trouble connecting to my brain right now."
        
        except requests.exceptions.RequestException as e:
            print(f"Error communicating with Ollama: {e}")
            return "I'm having trouble connecting to my language model. Is Ollama running?"
        except Exception as e:
            print(f"Unexpected error in LLM query: {e}")
            return "I encountered an unexpected error. Please try again."

    def analyze_sentiment(self, text):
        """Simple rule-based sentiment analysis to detect emotion"""
        # This is a very basic implementation
        # In a production system, you might use a proper NLP model
        
        text = text.lower()
        
        # Simple keyword matching
        if any(word in text for word in ["happy", "great", "excellent", "glad", "joy"]):
            return "happy"
        elif any(word in text for word in ["sad", "sorry", "unhappy", "unfortunate"]):
            return "sad"
        elif any(word in text for word in ["angry", "mad", "furious", "upset"]):
            return "angry"
        elif any(word in text for word in ["confused", "unclear", "don't understand"]):
            return "confused"
        else:
            return "neutral"

    # Command Functions
    def tell_time(self):
        """Tell the current time"""
        current_time = datetime.now().strftime("%I:%M %p")
        self.speak(f"The current time is {current_time}")

    def tell_story(self):
        """Generate a short story using the LLM"""
        self.speak("Let me think of a story for you...")
        story_prompt = "Generate a short, engaging story (less than 100 words)"
        story = self.query_llm(story_prompt)
        self.speak(story)

    def toggle_privacy(self):
        """Toggle privacy mode on/off"""
        self.privacy_mode = not self.privacy_mode
        if self.privacy_mode:
            self.speak("Privacy shield activated. I'll be more discreet.")
        else:
            self.speak("Privacy shield deactivated. Normal operations resumed.")

    def stop_listening(self):
        """Stop the assistant from listening"""
        self.speak("Goodbye. Going offline now.")
        self.should_stop = True

    def show_help(self):
        """Show available commands"""
        help_text = "Here are some commands you can use: "
        for i, cmd in enumerate(self.commands.keys()):
            if i > 0:
                help_text += ", "
            help_text += cmd
        self.speak(help_text)
    
    def process_text_input(self, text):
        """Process text input from GUI"""
        if not text:
            return "Please enter a message."
            
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": text})
        
        # Check for direct commands
        for cmd, func in self.commands.items():
            if cmd in text.lower():
                func()
                return f"Command '{cmd}' executed."
        
        # Get response from LLM
        response = self.query_llm(text)
        
        # Add to conversation history
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return response

    def save_conversation(self, filepath):
        """Save conversation history to a file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(list(self.conversation_history), f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving conversation: {e}")
            return False

    def load_conversation(self, filepath):
        """Load conversation history from a file"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    loaded_history = json.load(f)
                    # Clear current history and add loaded messages
                    self.conversation_history.clear()
                    for message in loaded_history:
                        self.conversation_history.append(message)
                return True
            return False
        except Exception as e:
            print(f"Error loading conversation: {e}")
            return False


# If run directly, start FRIDAY in voice mode
if __name__ == "__main__":
    try:
        friday = FridayCore()
        friday.listen()
    except KeyboardInterrupt:
        print("\nShutting down FRIDAY...")
    except Exception as e:
        print(f"Error: {e}")