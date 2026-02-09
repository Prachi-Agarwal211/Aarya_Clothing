#!/bin/bash

# Aarya Clothing - SSL Certificate Setup Script
# This script generates self-signed SSL certificates for aaryaclothing.cloud

set -e

echo "=========================================="
echo "Aarya Clothing - SSL Certificate Setup"
echo "=========================================="

# Create SSL directory if it doesn't exist
mkdir -p docker/nginx/ssl

# Generate private key
echo "Generating private key..."
openssl genrsa -out docker/nginx/ssl/aaryaclothing.cloud.key 2048

# Generate certificate signing request
echo "Generating certificate signing request..."
openssl req -new -key docker/nginx/ssl/aaryaclothing.cloud.key \
    -out docker/nginx/ssl/aaryaclothing.cloud.csr \
    -subj "/C=IN/ST=Delhi/L=Delhi/O=AaryaClothing/OU=IT/CN=aaryaclothing.cloud"

# Generate self-signed certificate
echo "Generating self-signed certificate..."
openssl x509 -req -days 365 \
    -in docker/nginx/ssl/aaryaclothing.cloud.csr \
    -signkey docker/nginx/ssl/aaryaclothing.cloud.key \
    -out docker/nginx/ssl/aaryaclothing.cloud.crt \
    -extfile <(cat <<EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names
[alt_names]
DNS.1 = aaryaclothing.cloud
DNS.2 = www.aaryaclothing.cloud
EOF
)

# Set proper permissions
chmod 600 docker/nginx/ssl/aaryaclothing.cloud.key
chmod 644 docker/nginx/ssl/aaryaclothing.cloud.crt

# Remove CSR file (not needed after certificate generation)
rm docker/nginx/ssl/aaryaclothing.cloud.csr

echo "=========================================="
echo "SSL certificates generated successfully!"
echo "=========================================="
echo "Certificate: docker/nginx/ssl/aaryaclothing.cloud.crt"
echo "Private Key: docker/nginx/ssl/aaryaclothing.cloud.key"
echo ""
echo "Note: These are self-signed certificates for testing."
echo "For production, use Let's Encrypt or purchase SSL certificates."
echo "=========================================="
