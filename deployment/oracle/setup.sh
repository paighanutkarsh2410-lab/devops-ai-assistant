#!/bin/bash
# ============================================
# Oracle Cloud VPS Setup Script
# Run this on a fresh Ubuntu 22.04+ instance
# ============================================
set -e

echo "=== DevOps AI Assistant - Server Setup ==="

# Update system
echo "[1/6] Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Docker
echo "[2/6] Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker $USER
    echo "Docker installed. You may need to log out and back in for group changes."
else
    echo "Docker already installed."
fi

# Install Docker Compose plugin
echo "[3/6] Installing Docker Compose..."
if ! docker compose version &> /dev/null; then
    sudo apt install -y docker-compose-plugin
else
    echo "Docker Compose already installed."
fi

# Install Nginx
echo "[4/6] Installing Nginx..."
sudo apt install -y nginx

# Configure firewall
echo "[5/6] Configuring firewall..."
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw --force enable
echo "Firewall configured (SSH, HTTP, HTTPS open)."

# Clone repo (if not already cloned)
echo "[6/6] Setting up project..."
PROJECT_DIR="/opt/devops-ai-assistant"
if [ ! -d "$PROJECT_DIR" ]; then
    sudo mkdir -p "$PROJECT_DIR"
    sudo chown $USER:$USER "$PROJECT_DIR"
    echo ""
    echo "Project directory created at $PROJECT_DIR"
    echo "Clone your repo: git clone https://github.com/YOUR_USERNAME/devops-ai-assistant.git $PROJECT_DIR"
else
    echo "Project directory already exists at $PROJECT_DIR"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Clone your repo to $PROJECT_DIR"
echo "  2. cd $PROJECT_DIR/deployment/oracle"
echo "  3. cp .env.template .env && nano .env           # Fill in values"
echo "  4. cp .env.agents.template .env.agents && nano .env.agents  # Fill in values"
echo "  5. sudo cp nginx.conf /etc/nginx/sites-available/devops-api"
echo "  6. sudo ln -s /etc/nginx/sites-available/devops-api /etc/nginx/sites-enabled/"
echo "  7. sudo rm -f /etc/nginx/sites-enabled/default"
echo "  8. Edit /etc/nginx/sites-available/devops-api — replace YOUR_SERVER_IP"
echo "  9. sudo nginx -t && sudo systemctl reload nginx"
echo " 10. docker compose up -d"
echo ""
