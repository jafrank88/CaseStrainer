FROM nginx:alpine

# Create necessary directories
RUN mkdir -p /etc/ssl/certs /etc/ssl/private /usr/share/nginx/html/static

# Copy SSL certificates to standard locations
COPY ssl/WolfCertBundle.crt /etc/ssl/certs/
COPY ssl/wolf.law.uw.edu.key /etc/ssl/private/

# Create symbolic links for SSL certificates
RUN ln -sf /etc/ssl/certs/WolfCertBundle.crt /etc/ssl/certs/cert.pem && \
    ln -sf /etc/ssl/private/wolf.law.uw.edu.key /etc/ssl/private/key.pem

# Copy Nginx configuration
COPY nginx/conf.d/ /etc/nginx/conf.d/

# Copy static files
COPY static/ /usr/share/nginx/html/static/

# Set proper permissions for SSL files
RUN chmod 644 /etc/ssl/certs/WolfCertBundle.crt && \
    chmod 600 /etc/ssl/private/wolf.law.uw.edu.key
