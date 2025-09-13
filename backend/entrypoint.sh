#!/usr/bin/env sh
set -e

echo "🚀 Starting Django application..."

echo "📊 Running database migrations..."
python manage.py migrate --noinput

echo "🌱 Seeding default control data..."
python manage.py seed_default_controls

echo "✅ Database setup complete!"
echo "🎯 Default controls created:"
echo "   • MFA Control - OTP Authentication"
echo "   • SSO Login Control - Microsoft Azure AD"

echo "🚀 Starting Django development server..."
exec python manage.py runserver 0.0.0.0:8000


