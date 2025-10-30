# 🎬 DawnGuard Demo Mode - Recording Guide

## Quick Start for Demo Recording

### Option 1: Using docker-compose.demo.yml (Recommended)
```bash
# Stop any running containers
docker-compose down

# Start in demo mode (web only, no Ollama)
docker-compose -f docker-compose.demo.yml up -d

# Access at http://localhost:8000
```

### Option 2: Using docker-compose.override.yml
```bash
# The override file automatically merges with docker-compose.yml
# Just run normally, and Ollama dependency is removed:
docker-compose up -d

# Access at http://localhost:8000
```

### Option 3: Run without Docker
```bash
# Activate virtual environment
source venv/bin/activate

# Run migrations
python manage.py migrate

# Start dev server
python manage.py runserver

# Access at http://localhost:8000
```

## ✅ Demo Mode Features

When Ollama is not running, DawnGuard automatically uses **mock AI responses**:

### Enhanced Mock Responses Include:
- ✅ Greeting responses
- ✅ Weekend/activity planning (with detailed suggestions)
- ✅ File/storage management help
- ✅ Security/privacy explanations
- ✅ AI/LLM information
- ✅ Photos/memories guidance
- ✅ Kids homework assistance
- ✅ P2P/blockchain explanations
- ✅ Cost/pricing details
- ✅ Setup/technical help

### Kids AI Tutor Mock Responses:
- 📐 Math homework help
- 🔬 Science explanations (e.g., photosynthesis)
- ✍️ Essay writing guidance
- 👋 Friendly greetings
- 💡 General learning assistance

## 🎥 Recording Tips

1. **Clean your desktop** - Close unnecessary apps
2. **Test first** - Do a dry run before recording
3. **Use demo data** - Have 2-3 test photos ready
4. **Internet not needed** - Everything runs locally
5. **Mock mode is visible** - Demo badge shows at top of Kids AI interface

## 🔄 Switching Back to Full Mode

To re-enable Ollama after demo:

```bash
# Stop demo mode
docker-compose down

# Remove override file (if using option 2)
rm docker-compose.override.yml

# Start with full config
docker-compose up -d

# Pull Ollama model
docker exec dawnguard_ollama ollama pull llama3.2:3b
```

## 📝 Demo Script

Follow the updated **DEMO_VIDEO_SCRIPT.md** which has been corrected to match actual app features:
- ✅ Simplified setup (no multi-step wizard shown)
- ✅ Family Dashboard focus
- ✅ Family Vault with encryption
- ✅ Kids-Safe AI Tutor with mock responses
- ✅ Realistic feature showcase

## 🚨 Common Issues

**Issue**: "Ollama not available" errors in logs
- **Solution**: This is expected in demo mode! Mock responses will be used automatically.

**Issue**: Docker port 8000 already in use
- **Solution**: Stop other containers: `docker-compose down`

**Issue**: Database locked
- **Solution**: `rm db.sqlite3` then `python manage.py migrate`

## 💡 Pro Tips

1. **Disable notifications** during recording (Do Not Disturb mode)
2. **Use Chrome in Incognito mode** for clean browser
3. **Have script open on second monitor** for reference
4. **Record in 1080p** (1920x1080) for best quality
5. **Use good lighting** if showing yourself

---

**Ready to record?** Follow DEMO_VIDEO_SCRIPT.md step by step! 🎬
