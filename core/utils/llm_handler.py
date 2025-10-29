import ollama
import time

class LLMHandler:
    def __init__(self):
        self.available = self.check_ollama()
        self.default_model = "llama3.2:3b"
    
    def check_ollama(self):
        """Check if Ollama is available"""
        try:
            ollama.list()
            return True
        except:
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
            response = ollama.chat(
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
            stream = ollama.chat(
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
        """Mock response when Ollama is not available"""
        responses = {
            "hello": "Hello! I'm your private AI assistant running locally on your Black Box. How can I help you today?",
            "weather": "I don't have access to real-time weather data, but I can help you with many other things!",
            "default": f"I understand you said: '{prompt[:50]}...'. I'm running in mock mode. Please install Ollama to use the real AI model."
        }
        
        prompt_lower = prompt.lower()
        if "hello" in prompt_lower or "hi" in prompt_lower:
            return responses["hello"]
        elif "weather" in prompt_lower:
            return responses["weather"]
        else:
            return responses["default"]