#!/bin/bash

# Fix Ollama connection and pull model
# Run this after deployment

echo "🤖 Fixing Ollama configuration..."

# Check if Ollama container is running
if ! docker-compose ps ollama | grep -q "Up"; then
    echo "❌ Ollama container is not running!"
    echo "Starting Ollama..."
    docker-compose up -d ollama
    sleep 10
fi

# Check Ollama service
echo "📡 Testing Ollama connection..."
if docker-compose exec -T ollama curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
    echo "✅ Ollama service is running"
else
    echo "⚠️  Ollama service not responding, restarting..."
    docker-compose restart ollama
    sleep 15
fi

# Pull the model
echo "📥 Pulling llama3.2:3b model (this may take 5-10 minutes)..."
docker-compose exec -T ollama ollama pull llama3.2:3b

if [ $? -eq 0 ]; then
    echo "✅ Model downloaded successfully!"
else
    echo "❌ Failed to download model. Trying smaller model..."
    docker-compose exec -T ollama ollama pull llama3.2:1b
fi

# List available models
echo ""
echo "📋 Available models:"
docker-compose exec -T ollama ollama list

# Test the model
echo ""
echo "🧪 Testing model with a simple query..."
docker-compose exec -T ollama ollama run llama3.2:3b "Say hello in 5 words" 2>/dev/null | head -n 1

# Restart Django to pick up Ollama
echo ""
echo "🔄 Restarting Django app..."
docker-compose restart web

echo ""
echo "✅ Ollama setup complete!"
echo "🌐 Your app should now use real AI responses"
echo ""
echo "Test by visiting: http://YOUR_SERVER_IP/chat/"