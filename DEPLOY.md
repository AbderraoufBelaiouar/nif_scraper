# NIF Checker API - Deployment Guide

## Quick Start (Local)

```bash
cd /home/abderraouf/Desktop/AI/scraper
python3 api.py
```

API runs at `http://localhost:5000`

---

## Option 1: Docker (Recommended)

### 1. Create Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY nif_checker.py api.py ./
RUN pip install requests beautifulsoup4

EXPOSE 5000

CMD ["python3", "api.py"]
```

### 2. Build & Run

```bash
docker build -t nif-checker .
docker run -d -p 5000:5000 --name nif-api nif-checker
```

### 3. Access
```
http://localhost:5000/api/check-nif/123456789012345
```

---

## Option 2: PythonAnywhere (Free)

1. Create account at https://www.pythonanywhere.com
2. Go to **Files** → upload `nif_checker.py` and `api.py`
3. Click **Web** → **Add a new web app**
4. Select **Manual configuration** → **Python 3.12**
5. Create `wsgi.py`:

```python
import sys
sys.path.insert(0, '/home/yourusername')
from api import app as application
```

6. Edit `/etc/nginx/sites-enabled/default` or use PythonAnywhere's **Web** tab → **WSGI configuration**

---

## Option 3: Railway (Free Tier)

```bash
# Install Railway CLI
npm install -g @railway/cli

railway login
railway init

# Create railway.json
echo '{
  "build": {
    "builder": "PYTHON",
    "pythonVersion": "3.12"
  },
  "deploy": {
    "numReplicas": 1,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}' > railway.json

railway up
```

---

## Option 4: Render (Free)

1. Push code to GitHub
2. Go to https://dashboard.render.com
3. **New** → **Web Service**
4. Connect GitHub repo
5. Configure:
   - Build command: `pip install -r requirements-api.txt` (create one)
   - Start command: `python3 api.py`

---

## Option 5: VPS (DigitalOcean/Render/Vultr)

### DigitalOcean Droplet

```bash
# Create droplet, SSH in
sudo apt update && sudo apt install -y python3 python3-pip

# Upload files
scp nif_checker.py api.py root@your-ip:/root/

# Install dependencies
pip3 install requests beautifulsoup4

# Run with systemd
sudo nano /etc/systemd/system/nif-api.service
```

Create `/etc/systemd/system/nif-api.service`:
```ini
[Unit]
Description=NIF Checker API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root
ExecStart=/usr/bin/python3 /root/api.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable nif-api
sudo systemctl start nif-api
```

---

## Testing the API

```bash
# GET request
curl http://localhost:5000/api/check-nif/123456789012345

# POST request
curl -X POST http://localhost:5000/api/check-nif \
  -H "Content-Type: application/json" \
  -d '{"nif": "123456789012345"}'
```

**Response format:**
```json
{
  "status": "valid",
  "nif": "123456789012345",
  "name": "Company Name",
  "message": "NIF is valid"
}
```

---

## Production Tips

1. **Use Gunicorn** (better performance):
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 api:app
   ```

2. **Nginx reverse proxy**:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:5000;
       }
   }
   ```

3. **Environment variables**:
   ```python
   port = int(os.environ.get('PORT', 5000))
   ```

---

## Recommended: Railway Quick Deploy

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and init
railway login
railway init --name nif-api

# Set environment
railway variables set PORT=5000

# Deploy
railway up
```

After deployment, you'll get a public URL like `https://nif-api-production.up.railway.app`

---

## Summary

| Platform | Cost | Difficulty |
|----------|------|-------------|
| Docker | Free | Easy |
| PythonAnywhere | Free (limited) | Easy |
| Railway | Free tier | Easy |
| Render | Free tier | Easy |
| DigitalOcean VPS | $4/mo | Medium |