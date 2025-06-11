# Base image
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy project files
COPY . .

# Expose port 5173 for Vite dev server
EXPOSE 5173

# Start the development server
CMD ["npm", "run", "dev"]
