#!/bin/sh

# Default domain name if not set
DOMAIN_NAME=${DOMAIN_NAME:-localhost}

# Check if SSL certificates exist
if [ -f "/etc/letsencrypt/live/${DOMAIN_NAME}/fullchain.pem" ] && [ -f "/etc/letsencrypt/live/${DOMAIN_NAME}/privkey.pem" ]; then
    echo "SSL certificates found for ${DOMAIN_NAME}, using HTTPS configuration"
    # Use SSL-enabled configuration
    envsubst '${DOMAIN_NAME}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf
else
    echo "No SSL certificates found for ${DOMAIN_NAME}, using HTTP-only configuration"
    echo "Run certbot to obtain certificates, then restart nginx"
    # Check if HTTP-only config exists, otherwise create a basic one
    if [ -f "/etc/nginx/nginx-http.conf" ]; then
        envsubst '${DOMAIN_NAME}' < /etc/nginx/nginx-http.conf > /etc/nginx/conf.d/default.conf
    else
        # Create basic HTTP config that allows ACME challenges
        cat > /etc/nginx/conf.d/default.conf <<EOF
upstream django {
    server web:8000;
}

server {
    listen 80;
    server_name ${DOMAIN_NAME};

    # Allow certbot challenges
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
        try_files \$uri =404;
    }

    client_max_body_size 100M;

    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /app/media/;
        expires 7d;
    }

    location /gun {
        proxy_pass http://django;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_read_timeout 86400;
    }

    location / {
        proxy_pass http://django;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
    }
}
EOF
    fi
fi

# Execute the CMD
exec "$@"
