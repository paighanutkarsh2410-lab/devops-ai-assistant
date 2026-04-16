# Deployment Guide: Vercel (Frontend) + Oracle Cloud (Backend)

## Architecture

```
[User Browser] → [Vercel CDN] → Next.js Frontend
                                    ↓ API calls
[User Browser] → [Oracle VPS :80] → Nginx → FastAPI :8000
                                              ↓
                                    PostgreSQL, Redis, Prometheus, Grafana
                                    AI Agents (Monitor, Diagnostic, Remediation, etc.)
```

---

## Part 1: Oracle Cloud VPS (Backend)

### 1.1 Create VM
- Go to Oracle Cloud → Compute → Create Instance
- Shape: VM.Standard.A1.Flex (free tier: 4 OCPU, 24GB RAM)
- OS: Ubuntu 22.04
- Add your SSH public key
- Note the **Public IP** after creation

### 1.2 Open Firewall Ports
In Oracle Cloud Console → Networking → Virtual Cloud Networks → Security Lists:
- Add Ingress Rule: Source `0.0.0.0/0`, Port `80` (HTTP)
- Add Ingress Rule: Source `0.0.0.0/0`, Port `443` (HTTPS)

### 1.3 SSH into Server and Run Setup
```bash
ssh ubuntu@YOUR_SERVER_IP
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/devops-ai-assistant/main/deployment/oracle/setup.sh | bash
```
Or manually:
```bash
git clone https://github.com/YOUR_USERNAME/devops-ai-assistant.git /opt/devops-ai-assistant
cd /opt/devops-ai-assistant/deployment/oracle
chmod +x setup.sh
./setup.sh
```

### 1.4 Configure Environment Variables
```bash
cd /opt/devops-ai-assistant/deployment/oracle

# Backend .env
cp .env.template .env
nano .env
```

Fill in these values in `.env`:
| Variable | How to get it |
|---|---|
| `DB_PASSWORD` | Make up a strong password (e.g. `MyStr0ngP@ss!2026`) |
| `DATABASE_URL` | Use same password: `postgresql://devops_user:MyStr0ngP@ss!2026@postgres:5432/devops_ai` |
| `SECRET_KEY` | Run: `python3 -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `ANTHROPIC_API_KEY` | From https://console.anthropic.com/settings/keys |
| `GROQ_API_KEY` | From https://console.groq.com/keys |
| `CORS_ORIGINS` | Your Vercel URL (e.g. `https://devops-ai-assistant.vercel.app`) |
| `GRAFANA_PASSWORD` | Make up a password for Grafana admin |

```bash
# Agents .env
cp .env.agents.template .env.agents
nano .env.agents
```

Fill in these values in `.env.agents`:
| Variable | How to get it |
|---|---|
| `AGENT_PASSWORD` | Make up a password for the agent service account |
| `ANTHROPIC_API_KEY` | Same key as above |
| `GROQ_API_KEY` | Same key as above |
| `QDRANT_URL` | From https://cloud.qdrant.io (or leave placeholder to skip) |
| `QDRANT_API_KEY` | From Qdrant dashboard (or leave placeholder to skip) |
| `SLACK_WEBHOOK_URL` | From Slack App settings (or leave placeholder to skip) |
| `SLACK_BOT_TOKEN` | From Slack App settings (or leave placeholder to skip) |
| `RESEND_API_KEY` | From https://resend.com (or leave placeholder to skip) |

### 1.5 Configure Nginx
```bash
sudo cp nginx.conf /etc/nginx/sites-available/devops-api
sudo ln -s /etc/nginx/sites-available/devops-api /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Edit to set your server IP and Vercel URL
sudo nano /etc/nginx/sites-available/devops-api
# Replace YOUR_SERVER_IP with your Oracle VM public IP
# Replace YOUR_VERCEL_URL with your Vercel URL (e.g. https://devops-ai-assistant.vercel.app)

sudo nginx -t
sudo systemctl reload nginx
```

### 1.6 Start Services
```bash
cd /opt/devops-ai-assistant/deployment/oracle
docker compose up -d
```

Verify:
```bash
docker compose ps          # All services should be "Up"
curl http://localhost:8000/health   # Should return {"status": "healthy"}
```

---

## Part 2: Vercel (Frontend)

### 2.1 Deploy to Vercel
1. Go to https://vercel.com and sign in with GitHub
2. Click **"Add New Project"**
3. Import your `devops-ai-assistant` repo
4. Configure:
   - **Framework Preset**: Next.js (auto-detected)
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (default)
   - **Output Directory**: `.next` (default)

### 2.2 Set Environment Variable
In Vercel Project Settings → Environment Variables, add:

| Name | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `http://YOUR_ORACLE_SERVER_IP` |

> Replace `YOUR_ORACLE_SERVER_IP` with your Oracle VM's public IP (e.g. `http://129.154.xx.xx`)

### 2.3 Deploy
Click **Deploy**. Vercel will build and give you a URL like:
`https://devops-ai-assistant-xxxxx.vercel.app`

### 2.4 Update Backend CORS
After getting your Vercel URL, update the Oracle backend:
```bash
# On Oracle VM
cd /opt/devops-ai-assistant/deployment/oracle
nano .env
# Set CORS_ORIGINS=https://devops-ai-assistant-xxxxx.vercel.app

# Also update Nginx
sudo nano /etc/nginx/sites-available/devops-api
# Replace YOUR_VERCEL_URL with the actual Vercel URL

docker compose restart backend
sudo systemctl reload nginx
```

---

## Verification Checklist

- [ ] `http://YOUR_ORACLE_IP/health` returns `{"status": "healthy"}`
- [ ] `http://YOUR_ORACLE_IP/docs` shows FastAPI Swagger UI
- [ ] Vercel URL loads the dashboard
- [ ] Can register/login on the frontend
- [ ] Dashboard shows metrics (after agents start collecting)

---

## Quick Reference: All Values You Need

| # | Value | Where to get it |
|---|---|---|
| 1 | Oracle VM Public IP | Oracle Cloud Console |
| 2 | Anthropic API Key | console.anthropic.com |
| 3 | Groq API Key | console.groq.com |
| 4 | DB Password | Make one up |
| 5 | JWT Secret | `python3 -c "import secrets; print(secrets.token_urlsafe(64))"` |
| 6 | Grafana Password | Make one up |
| 7 | Agent Password | Make one up |
| 8 | Vercel URL | After deploying frontend |
| 9 | *(Optional)* Qdrant URL + Key | cloud.qdrant.io |
| 10 | *(Optional)* Slack Webhook + Token | Slack API |
| 11 | *(Optional)* Resend API Key | resend.com |
