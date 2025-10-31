import ollama
import time
import os

class LLMHandler:
    def __init__(self):
        # Configure Ollama client with host from environment
        self.ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        # Create client with custom host
        self.client = ollama.Client(host=self.ollama_host)

        self.available = self.check_ollama()
        self.default_model = "llama3.2:3b"

    def check_ollama(self):
        """Check if Ollama is available"""
        try:
            self.client.list()
            return True
        except Exception as e:
            print(f"Ollama connection error: {e}")
            return False
    
    def generate_response(self, prompt, context=None, model=None, max_tokens=None):
        """Generate a complete response (non-streaming)"""
        if not self.available:
            return self._mock_response(prompt)

        try:
            messages = []

            # Add context if provided
            if context:
                messages.extend(context)

            # Add current prompt
            messages.append({
                'role': 'user',
                'content': prompt
            })

            # Prepare options
            options = {}
            if max_tokens:
                options['num_predict'] = max_tokens

            # Generate response
            response = self.client.chat(
                model=model or self.default_model,
                messages=messages,
                stream=False,
                options=options if options else None
            )

            return response['message']['content']

        except Exception as e:
            print(f"LLM Error: {e}")
            return self._mock_response(prompt)
    
    def generate_response_stream(self, prompt, context=None, model=None):
        """Generate a streaming response (yields chunks)"""
        if not self.available:
            # Mock streaming for testing
            response = self._mock_response(prompt)
            words = response.split(' ')
            for word in words:
                yield word + ' '
                time.sleep(0.05)
            return
        
        try:
            messages = []
            
            # Add context if provided
            if context:
                messages.extend(context)
            
            # Add current prompt
            messages.append({
                'role': 'user',
                'content': prompt
            })
            
            # Generate streaming response
            stream = self.client.chat(
                model=model or self.default_model,
                messages=messages,
                stream=True
            )
            
            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    yield chunk['message']['content']
            
        except Exception as e:
            print(f"LLM Streaming Error: {e}")
            # Fallback to mock
            response = self._mock_response(prompt)
            words = response.split(' ')
            for word in words:
                yield word + ' '
                time.sleep(0.05)
    
    def _mock_response(self, prompt):
        """
        Enhanced mock responses for demo recording
        Returns realistic AI responses when Ollama is not running
        """
        prompt_lower = prompt.lower()

        # Greeting responses
        if any(word in prompt_lower for word in ['hello', 'hi', 'hey', 'greetings']):
            return "Hello! I'm your private AI assistant running locally on your Black Box. How can I help you today?"

        # File/storage queries
        elif any(word in prompt_lower for word in ['file', 'storage', 'upload', 'vault']):
            return "I can help you manage your family vault! You can upload files, organize them into folders, and search using AI-powered tags. All your data stays encrypted on your Black Box - no cloud needed!"

        # Security/privacy queries
        elif any(word in prompt_lower for word in ['secure', 'private', 'encrypt', 'safe', 'privacy']):
            return "Your privacy is my top priority! All data on DawnGuard is encrypted with AES-256 encryption, stored locally on your Black Box, and never sent to the cloud. You have complete control over your family's data."

        # AI/LLM queries
        elif any(word in prompt_lower for word in ['ai', 'model', 'llm', 'assistant']):
            return "I'm powered by Llama 3.2, running entirely on your Black Box hardware. Unlike cloud AI services, your conversations never leave your home network, ensuring 100% privacy. I can help with general questions, file organization, and family knowledge management!"

        # Weekend/activity planning
        elif any(word in prompt_lower for word in ['weekend', 'activity', 'plan', 'family fun']):
            return """Here are some great family weekend activity ideas:

1. **Nature Hike** - Explore local trails and teach kids about plants and wildlife
2. **Family Game Night** - Board games, card games, or video games together
3. **Cooking Together** - Make homemade pizza or bake cookies as a team
4. **Arts & Crafts** - Create family art projects or DIY home decorations
5. **Movie Marathon** - Pick a theme and watch family favorites

Remember to capture photos and store them in your Family Vault for memories! 📸"""

        # Photos/memories
        elif any(word in prompt_lower for word in ['photo', 'picture', 'memory', 'vacation']):
            return "That's what the Family Vault is perfect for! You can upload unlimited photos, and our local AI will automatically tag them for easy searching. Try searching for 'vacation' or 'birthday' to find specific memories instantly!"

        # Kids/homework help
        elif any(word in prompt_lower for word in ['homework', 'kid', 'child', 'tutor']):
            return "For kids' homework help, check out the Kids-Safe AI Tutor feature! It provides age-appropriate educational assistance with built-in content filtering and parental monitoring. All conversations are logged for your review."

        # P2P/blockchain
        elif any(word in prompt_lower for word in ['p2p', 'blockchain', 'network', 'solana']):
            return "DawnGuard features a P2P network where Black Box owners can share knowledge, vote on governance, and build reputation. Your contributions are tracked on Solana blockchain for transparency and rewards!"

        # Cost/pricing
        elif any(word in prompt_lower for word in ['cost', 'price', 'save', 'money', 'subscription']):
            return "DawnGuard saves your family $480/year compared to Dropbox + ChatGPT subscriptions. With unlimited storage and local AI, you get privacy AND savings. One-time setup, zero monthly fees!"

        # Technical/setup
        elif any(word in prompt_lower for word in ['install', 'setup', 'docker', 'run']):
            return "Setting up DawnGuard is easy! Just run 'docker-compose up -d' and access it at localhost:8000. The setup wizard will guide you through creating your family admin account, adding members, and configuring features. Takes about 2 minutes!"

        # Default helpful response
        else:
            return f"I understand you're asking about: '{prompt[:80]}'. As your local AI assistant, I can help with file management, family organization, knowledge sharing, and general questions. What would you like to know more about?"