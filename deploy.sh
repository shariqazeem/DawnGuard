#!/bin/bash

echo "🚀 Deploying CypherVault to Production..."

# Stop existing containers
docker-compose -f docker-compose.prod.yml down

# Build and start containers
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for database
echo "⏳ Waiting for database..."
sleep 15

# Run migrations
docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

# Create superuser
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@cyphervault.com', 'admin123')" | docker-compose -f docker-compose.prod.yml exec -T web python manage.py shell

# Award badges to users
docker-compose -f docker-compose.prod.yml exec -T web python manage.py award_early_adopter || echo "Badge command not found, skipping..."

# Pull Ollama model
echo "🤖 Pulling Ollama model..."
docker-compose -f docker-compose.prod.yml exec -T ollama ollama pull llama3.2:3b

echo ""
echo "✅ Deployment complete!"
echo "🌐 Access your app at: http://141.148.215.239:8000"
echo "🔑 Admin panel: http://141.148.215.239:8000/admin"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "📊 View logs: docker-compose -f docker-compose.prod.yml logs -f"