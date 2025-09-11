FROM nginx:alpine

# Install curl for healthcheck
RUN apk add --no-cache curl

# Create necessary directories
RUN mkdir -p /usr/share/nginx/html/casestrainer
RUN mkdir -p /etc/nginx/ssl

# Copy the main nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy the site configuration
COPY conf.d/casestrainer.conf /etc/nginx/conf.d/default.conf

# Set permissions
RUN chown -R nginx:nginx /usr/share/nginx/html
RUN chmod -R 755 /usr/share/nginx/html

# Disable the default nginx entrypoint that tries to modify files
ENTRYPOINT []

# Expose ports
EXPOSE 80 443

# Start nginx
CMD ["nginx", "-g", "daemon off;"]