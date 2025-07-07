FROM nginx:alpine

# Copy the nginx configuration
COPY conf.d/casestrainer.conf /etc/nginx/conf.d/default.conf

# Copy static files
COPY ../docker/html/static /usr/share/nginx/html/static

# Copy SSL certificates if they exist
COPY ../ssl /etc/nginx/ssl

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"] 