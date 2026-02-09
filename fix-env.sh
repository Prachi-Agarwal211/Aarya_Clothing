#!/bin/bash

# Fix .env file - escape special characters that cause shell variable expansion issues

echo "Fixing .env file special characters..."

# Backup original .env
cp .env .env.backup

# Fix JWT_SECRET_KEY - escape $ characters
sed -i 's/JWT_SECRET_KEY=Kj9#mP2\$vL8@wQ5!nR3&tY6\*zX1%bN4^cD7/JWT_SECRET_KEY="Kj9#mP2\$vL8@wQ5!nR3&tY6*zX1%bN4^cD7"/g' .env

# Fix SECRET_KEY - escape $ characters
sed -i 's/SECRET_KEY=Hf4@qW8!rE2&tY6#uI9\$oP3^vB5\*mZ1/SECRET_KEY="Hf4@qW8!rE2&tY6#uI9\$oP3^vB5*mZ1"/g' .env

echo "✓ .env file fixed"
echo "✓ Backup saved as .env.backup"
echo ""
echo "Changes made:"
echo "  - JWT_SECRET_KEY: Wrapped in quotes to prevent shell variable expansion"
echo "  - SECRET_KEY: Wrapped in quotes to prevent shell variable expansion"
echo ""
echo "You can now run: ./deploy-vps.sh"
