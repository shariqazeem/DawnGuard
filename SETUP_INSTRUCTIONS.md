# 🚀 Setup Instructions for Testing

## Quick Start (Docker - Recommended)

```bash
# 1. Stop existing containers (if running)
docker-compose down

# 2. Run migrations
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate

# 3. Create admin user (optional)
docker-compose exec web python manage.py createsuperuser

# 4. Pull Ollama model (for AI features)
docker-compose exec ollama ollama pull llama3.2:3b

# 5. Access the app
# Open browser: http://localhost:8000
```

## What's New - Family Vault

### Features to Test:
1. **Go to http://localhost:8000/vault/**
2. **Upload Files**: Drag-and-drop or click "Upload Files"
3. **Create Folders**: Click "New Folder"
4. **AI Search**: Type in search bar (e.g., "photo", "document")
5. **Download**: Click download button on any file
6. **Family Members**: Click "Manage Family" to add members

### Test User Journey:
```
1. Register account → Auto-creates Family Member profile
2. Upload some files (images work best for thumbnails)
3. Create a folder
4. Use AI search
5. Check storage usage dashboard
6. Try mobile view (responsive design)
```

## Troubleshooting

### If migrations fail:
```bash
# Delete database and start fresh
docker-compose down
rm db.sqlite3
docker-compose up -d
docker-compose exec web python manage.py migrate
```

### If Ollama is slow:
```bash
# Check if model is downloaded
docker-compose exec ollama ollama list

# If not, pull it:
docker-compose exec ollama ollama pull llama3.2:3b
```

### If file uploads fail:
```bash
# Check media directory permissions
mkdir -p media/vault_files
chmod -R 755 media/
```

## Environment Variables

Make sure these are set in `.env` or docker-compose.yml:
```
DEBUG=True
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-32-char-key
OLLAMA_HOST=http://ollama:11434
```

## Testing Checklist

- [ ] User registration works
- [ ] Login works
- [ ] Wallet connection works (optional)
- [ ] AI Chat works
- [ ] **Family Vault loads** ← NEW!
- [ ] **File upload works** ← NEW!
- [ ] **File download works** ← NEW!
- [ ] **AI search works** ← NEW!
- [ ] **Folder creation works** ← NEW!
- [ ] P2P network page loads
- [ ] Settings page works

## Demo Data (Optional)

To quickly test with demo files:
```bash
# Create sample family members
docker-compose exec web python manage.py shell

# In Python shell:
from django.contrib.auth.models import User
from core.models import FamilyMember

# Create demo users
dad = User.objects.create_user('dad', password='demo123')
mom = User.objects.create_user('mom', password='demo123')
kid = User.objects.create_user('sarah', password='demo123')

# Create family profiles
FamilyMember.objects.create(user=dad, display_name='Dad', role='admin')
FamilyMember.objects.create(user=mom, display_name='Mom', role='member')
FamilyMember.objects.create(user=kid, display_name='Sarah', role='child')
```

## For Hackathon Demo

### Best Demo Flow:
1. **Start**: Show homepage → "This is HomeGuardian AI on Black Box"
2. **Register**: Quick signup → Auto-creates family member
3. **Upload**: Drag-drop 3-4 files (mix of photos + PDFs)
4. **Wait**: Let AI process (shows "AI processing" in background)
5. **Search**: Use AI search → "Show me photos" → Instant results
6. **Value**: Point to "$240/year savings" widget
7. **Family**: Show family members section
8. **Privacy**: Emphasize "localhost" → "Never leaves Black Box"

### Killer Lines:
- "This replaces Dropbox for $0/month"
- "AI search - but 100% private"
- "Perfect for families - parental controls built-in"
- "One Black Box. Unlimited storage. Forever."

## Need Help?

Common issues:
- **Port 8000 busy**: Change port in docker-compose.yml
- **Ollama not responding**: Restart containers
- **Files not uploading**: Check media/ permissions
- **AI not working**: Use mock mode (still functional)

## Next Steps After Testing

If everything works:
1. ✅ Mark Priority 1 complete
2. 🔨 Start building Priority 2 (Kids-Safe AI)
3. 🔨 Build Priority 3 (Black Box Dashboard)
4. 🎬 Record demo video
5. 📝 Write submission docs
6. 🎉 Submit and WIN!

---

**Remember**: You built something REAL that solves a REAL problem. This isn't just a hackathon project - it's a product people will actually use!
