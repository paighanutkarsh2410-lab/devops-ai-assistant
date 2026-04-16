# Oracle Cloud Infrastructure Setup

## Overview

Deploy the DevOps AI Assistant on Oracle Cloud Free Tier (Always Free).

## VM Setup

### VM1: Backend + Agents (Application Server)
- **Shape**: VM.Standard.A1.Flex (2 OCPU, 4 GB RAM)
- **OS**: Ubuntu 22.04 LTS
- **Purpose**: FastAPI backend, AI agents, Nginx reverse proxy

### VM2: Database + Cache
- **Shape**: VM.Standard.E2.1.Micro (1 OCPU, 1 GB RAM)
- **OS**: Ubuntu 22.04 LTS
- **Purpose**: PostgreSQL, Redis

## Step-by-Step

### 1. Create Oracle Cloud Account
1. Go to [cloud.oracle.com](https://cloud.oracle.com)
2. Sign up for free tier (no credit card needed for Always Free)
3. Select home region (closest to your users)

### 2. Create Virtual Cloud Network (VCN)
1. Networking → Virtual Cloud Networks → Create VCN
2. Name: `devops-vcn`
3. CIDR: `10.0.0.0/16`
4. Create public subnet: `10.0.0.0/24`

### 3. Security Lists (Firewall Rules)

**Ingress Rules:**
| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 22 | TCP | Your IP | SSH |
| 80 | TCP | 0.0.0.0/0 | HTTP (redirect to HTTPS) |
| 443 | TCP | 0.0.0.0/0 | HTTPS |
| 5432 | TCP | 10.0.0.0/24 | PostgreSQL (internal) |
| 6379 | TCP | 10.0.0.0/24 | Redis (internal) |
| 9090 | TCP | 10.0.0.0/24 | Prometheus (internal) |
| 3002 | TCP | 10.0.0.0/24 | Grafana (internal) |

### 4. Create VM1 (Application)
```bash
# SSH into VM1
ssh -i ~/.ssh/devops-key ubuntu@<VM1_PUBLIC_IP>

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin

# Install Nginx
sudo apt install nginx

# Install Certbot for SSL
sudo apt install certbot python3-certbot-nginx
```

### 5. Create VM2 (Database)
```bash
ssh -i ~/.ssh/devops-key ubuntu@<VM2_PRIVATE_IP>

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

### 6. SSL Certificate (Let's Encrypt)
```bash
# On VM1
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal (already configured by certbot)
sudo certbot renew --dry-run

# Verify cron job
sudo systemctl status certbot.timer
```

### 7. Nginx Configuration
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://localhost:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
    }
}
```

### 8. DNS Configuration
1. Go to your domain registrar
2. Add A record: `yourdomain.com` → `<VM1_PUBLIC_IP>`
3. Add A record: `www.yourdomain.com` → `<VM1_PUBLIC_IP>`
4. Wait for DNS propagation (5-30 minutes)

## Oracle Object Storage (Backups)
1. Storage → Buckets → Create Bucket
2. Name: `devops-backups`
3. Storage Tier: Standard
4. Free tier: 20 GB
