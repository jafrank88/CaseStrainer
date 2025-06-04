# CaseStrainer - Vue.js Frontend

A modern, responsive frontend for the CaseStrainer application built with Vue 3, Vite, and Pinia.

## Features

- 📝 Citation validation and analysis
- 🌐 Responsive design for all devices
- 🚀 Fast and efficient with Vue 3's Composition API
- 🏗️ Modular and maintainable codebase
- 🔄 Real-time updates and feedback

## Prerequisites

- Node.js 16+ (LTS recommended)
- npm 8+ or yarn 1.22+
- Backend API server (see [Backend Setup](#backend-setup))

## Project Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/casestrainer.git
cd casestrainer/casestrainer-vue-new
```

### 2. Install dependencies

```bash
npm install
# or
yarn install
```

## Available Scripts

### Development

Start the development server with hot-reload:

```bash
# Using npm
npm run dev

# Using yarn
yarn dev
```

Or use the provided batch file (Windows):

```bash
dev.bat
```

The application will be available at [http://localhost:5173](http://localhost:5173)

### Build for Production

```bash
# Build for production
npm run build

# Preview the production build locally
npm run preview
```

Or use the provided batch file (Windows):

```bash
build.bat
```

The built files will be in the `dist` directory.

## Backend Setup

The frontend expects a backend API server to be running. By default, it connects to:

- Development: `http://localhost:5000/casestrainer/api`
- Production: `/casestrainer/api` (relative URL)

### Environment Variables

Create a `.env` file in the project root to override default settings:

```env
VITE_APP_NAME=CaseStrainer
VITE_API_BASE_URL=http://localhost:5000/casestrainer/api
VITE_APP_ENV=development
```

## Project Structure

```
src/
├── assets/          # Static assets (images, fonts, etc.)
├── components/      # Reusable Vue components
├── composables/     # Composable functions
├── router/          # Vue Router configuration
├── store/           # Pinia stores
├── utils/           # Utility functions
└── views/           # Page components
```

## API Integration

The application uses Axios for API requests. The main API client is configured in `src/api/api.js`.

## Deployment

### Production Build

1. Build the application:
   ```bash
   npm run build
   ```

2. The built files will be in the `dist` directory. These can be served by any static file server.

### Nginx Configuration (Example)

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location /casestrainer/ {
        alias /path/to/casestrainer/dist/;
        try_files $uri $uri/ /casestrainer/index.html;
    }
    
    location /casestrainer/api/ {
        proxy_pass http://localhost:5000/casestrainer/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## Contributing

1. Fork the repository
2. Create a new branch for your feature
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

[Your License Here]
