#!/bin/bash

# Aarya Clothing - Let's Encrypt SSL Setup Script
# This script sets up trusted SSL certificates using Let's Encrypt

set -e

echo "=========================================="
echo "Aarya Clothing - Let's Encrypt SSL Setup"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Check if domain is set
DOMAIN=${1:-aaryaclothing.cloud}
EMAIL=${2:-}

echo "Domain: $DOMAIN"
echo "Email: ${EMAIL:-not provided}"
echo ""

# Step 1: Install certbot
echo "Step 1: Installing certbot..."
apt-get update > /dev/null 2>&1
apt-get install -y certbot > /dev/null 2>&1
echo "✓ Certbot installed"
echo ""

# Step 2: Stop nginx to free up port 80
echo "Step 2: Stopping nginx..."
docker-compose stop nginx
echo "✓ Nginx stopped"
echo ""

# Step 3: Generate SSL certificates
echo "Step 3: Generating SSL certificates..."
if [ -z "$EMAIL" ]; then
    certbot certonly --standalone -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos
else
    certbot certonly --standalone -d $DOMAIN -d www.$DOMAIN --email $EMAIL --non-interactive --agree-tos
fi
echo "✓ Certificates generated"
echo ""

# Step 4: Backup existing certificates
echo "Step 4: Backing up existing certificates..."
if [ -f "docker/nginx/ssl/aaryaclothing.cloud.crt" ]; then
    cp docker/nginx/ssl/aaryaclothing.cloud.crt docker/nginx/ssl/aaryaclothing.cloud.crt.backup
    echo "✓ Certificate backed up"
fi
if [ -f "docker/nginx/ssl/aaryaclothing.cloud.key" ]; then
    cp docker/nginx/ssl/aaryaclothing.cloud.key docker/nginx/ssl/aaryaclothing.cloud.key.backup
    echo "✓ Private key backed up"
fi
echo ""

# Step 5: Copy Let's Encrypt certificates
echo "Step 5: Copying Let's Encrypt certificates..."
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem docker/nginx/ssl/aaryaclothing.cloud.crt
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem docker/nginx/ssl/aaryaclothing.cloud.key
echo "✓ Certificates copied"
echo ""

# Step 6: Set proper permissions
echo "Step 6: Setting permissions..."
chmod 644 docker/nginx/ssl/aaryaclothing.cloud.crt
chmod 600 docker/nginx/ssl/aaryaclothing.cloud.key
echo "✓ Permissions set"
echo ""

# Step 7: Start nginx
echo "Step 7: Starting nginx..."
docker-compose start nginx
echo "✓ Nginx started"
echo ""

# Step 8: Verify certificate
echo "Step 8: Verifying certificate..."
CERT_ISSUER=$(openssl x509 -in docker/nginx/ssl/aaryaclothing.cloud.crt -noout -issuer 2>/dev/null)
if [[ "$CERT_ISSUER" == *"Let's Encrypt"* ]]; then
    echo "✓ Let's Encrypt certificate verified"
else
    echo "⚠ Warning: Certificate issuer may not be Let's Encrypt"
    echo "  Issuer: $CERT_ISSUER"
fi
echo ""

# Step 9: Set up auto-renewal
echo "Step 9: Setting up auto-renewal..."
RENEWAL_CRON="0 0 1 * * certbot renew --quiet && cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /opt/Aarya_Clothing/docker/nginx/ssl/aaryaclothing.cloud.crt && cp /etc/letsencrypt/live/$DOMAIN/privkey.pem /opt/Aarya_Clothing/docker/nginx/ssl/aaryaclothing.cloud.key && docker-compose restart nginx"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "certbot renew"; then
    echo "✓ Auto-renewal cron job already exists"
else
    # Add cron job
    (crontab -l 2>/dev/null; echo "$RENEWAL_CRON") | crontab -
    echo "✓ Auto-renewal cron job added"
fi
echo ""

# Step 10: Test renewal
echo "Step 10: Testing certificate renewal..."
certbot renew --dry-run > /dev/null 2>&1
echo "✓ Certificate renewal test passed"
echo ""

echo "=========================================="
echo "Let's Encrypt SSL Setup Complete!"
echo "=========================================="
echo ""
echo "Your site now has trusted SSL certificates!"
echo ""
echo "Access URLs:"
echo "  Frontend:  https://$DOMAIN"
echo "  Health:    https://$DOMAIN/health"
echo ""
echo "Certificate Details:"
echo "  Issuer: Let's Encrypt"
echo "  Valid for: 90 days (auto-renews monthly)"
echo ""
echo "Next Steps:"
echo "  1. Visit https://$DOMAIN"
echo "  2. No more security warnings!"
echo "  3. Certificates will auto-renew"
echo ""
echo "To check certificate expiry:"
echo "  openssl x509 -in docker/nginx/ssl/aaryaclothing.cloud.crt -noout -enddate"
echo ""
echo "To manually renew certificates:"
echo "  certbot renew && docker-compose restart nginx"
echo ""
echo "=========================================="
