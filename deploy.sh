#!/bin/bash

# SmartCal Deployment Script for Contabo
echo "🚀 Starting SmartCal deployment..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and pip
echo "🐍 Installing Python and pip..."
sudo apt install python3 python3-pip python3-venv -y

# Install Nginx
echo "🌐 Installing Nginx..."
sudo apt install nginx -y

# Create application directory
echo "📁 Setting up application directory..."
sudo mkdir -p /var/www/smartcal
sudo chown $USER:$USER /var/www/smartcal

# Copy application files
echo "📋 Copying application files..."
cp -r * /var/www/smartcal/

# Create virtual environment
echo "🔧 Setting up Python virtual environment..."
cd /var/www/smartcal
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Create systemd service
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/smartcal.service > /dev/null <<EOF
[Unit]
Description=SmartCal Gunicorn daemon
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=/var/www/smartcal
Environment="PATH=/var/www/smartcal/venv/bin"
ExecStart=/var/www/smartcal/venv/bin/gunicorn --config gunicorn.conf.py wsgi:app
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
echo "🌐 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/smartcal > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;  # Replace with your actual domain

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias /var/www/smartcal/Assets;
    }
}
EOF

# Enable site and service
echo "🔗 Enabling services..."
sudo ln -sf /etc/nginx/sites-available/smartcal /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl enable smartcal
sudo systemctl start smartcal
sudo systemctl restart nginx

# Set up firewall
echo "🔥 Configuring firewall..."
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw --force enable

echo "✅ Deployment completed!"
echo "🌐 Your SmartCal application should now be running at: http://your-domain.com"
echo "📝 Don't forget to:"
echo "   1. Replace 'your-domain.com' with your actual domain in Nginx config"
echo "   2. Set up SSL certificate with Let's Encrypt"
echo "   3. Update SECRET_KEY environment variable"
echo "   4. Configure your domain DNS to point to this server" 