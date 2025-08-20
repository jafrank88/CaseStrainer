FROM nginx:alpine

# Create necessary directories
RUN mkdir -p /usr/share/nginx/html/static

# Copy only the server configurations
COPY conf.d/ /etc/nginx/conf.d/

# Note: SSL certificates and static files will be mounted as volumes
