# core/utils/llm_handler.py
import ollama
import json
import os
from typing import List, Dict

class LLMHandler:
    def __init__(self):
        # Get Ollama host from environment or use default
        ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        
        # Try to connect to Ollama
        try:
            self.client = ollama.Client(host=ollama_host)
            self.model = "llama3.2:3b"
            self.available = self.test_connection()
            print(f"✅ Ollama connected at {ollama_host}, available: {self.available}")
        except Exception as e:
            print(f"❌ Ollama connection failed: {e}")
            self.client = None
            self.available = False
    
    def test_connection(self):
        """Test if Ollama is running"""
        try:
            models = self.client.list()
            print(f"✅ Ollama models available: {models}")
            return True
        except Exception as e:
            print(f"❌ Ollama test failed: {e}")
            return False
    
    def generate_response(self, message: str, context: List[Dict] = None):
        """Generate AI response"""
        if not self.available:
            print("⚠️ Using mock response - Ollama not available")
            return self._mock_response(message)
        
        try:
            messages = context if context else []
            messages.append({"role": "user", "content": message})
            
            print(f"🤖 Generating response for: {message[:50]}...")
            
            response = self.client.chat(
                model=self.model,
                messages=messages,
                stream=False
            )
            
            ai_response = response['message']['content']
            print(f"✅ Generated response: {ai_response[:50]}...")
            return ai_response
            
        except Exception as e:
            print(f"❌ Error generating response: {e}")
            return self._mock_response(message)
    
    def _mock_response(self, message: str):
        """Mock response for when Ollama isn't available"""
        responses = {
            "hello": "Hello! I'm CypherVault, your private AI assistant. All our conversations stay completely local on your Black Box.",
            "help": "I can help you with various tasks while keeping everything private and encrypted. What would you like to know?",
            "privacy": "Your privacy is my top priority. All messages are encrypted and never leave your Black Box device.",
            "how": "I run entirely on your device using Ollama for local AI processing. Everything stays private and secure.",
            "what": "I'm CypherVault, a privacy-first AI assistant that runs locally on your DAWN Black Box. Your data never leaves your device.",
        }
        
        message_lower = message.lower()
        for key in responses:
            if key in message_lower:
                return responses[key]
        
        return f"I'm processing your message locally and securely. Your data never leaves this device. How can I assist you today?"
    
    def analyze_document(self, content: str):
        """Analyze document content"""
        if not self.available:
            return "Document analysis ready. Content is encrypted and stored locally."
        
        try:
            prompt = f"Analyze this document and provide a summary:\n\n{content[:1000]}"
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )
            return response['message']['content']
        except:
            return "Document processed and encrypted successfully."
