# CaseStrainer

A web application for extracting, analyzing, and validating legal citations from legal documents.

## 📁 Project Structure

- `casestrainer-vue-new/` - Current Vue.js frontend (Vite + Vue 3)
  - Uses modern tooling and best practices
  - Active development happens here
- `src/` - Backend source code
  - `app_final_vue.py` - Main Flask application
  - `vue_api_endpoints.py` - Vue.js API endpoints
  - `citation_api.py` - Citation API endpoints
- `docs/` - Documentation
- `docker-compose.prod.yml` - Production Docker configuration
- `launcher.ps1` - PowerShell launcher with auto-restart capabilities

## ✨ Features

### Modern Web Interface

- Built with Vue 3 Composition API and Vite
- Responsive design for all devices
- Real-time citation verification

### Document Processing

- Extract citations from PDF, DOCX, and text files
- Process multiple document formats
- Clean and normalize extracted text

### Citation Analysis

- Validate citations against CourtListener API v4
- Cross-reference with legal databases
- Generate citation networks

### User Experience

- Intuitive drag-and-drop interface
- Real-time feedback and progress tracking
- Exportable results in multiple formats

### Production Features

- Docker containerization with health checks
- Auto-restart system with service monitoring
- Redis-based task queue for background processing
- Nginx reverse proxy for production deployment

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+** with pip
- **Node.js 16+** (LTS recommended)
- **Windows 10/11** or **Windows Server 2019/2022**
- **Docker Desktop** (for production deployment)
- **Git** for version control

### Quick Start

1. **Clone the repository**

   ```bash
   git clone https://github.com/jafrank88/CaseStrainer.git
   cd CaseStrainer
   ```

2. **Start with launcher (Recommended)**

   ```powershell
   .\launcher.ps1
   ```

   Choose your environment:
   - **Development**: Local development with hot reload
   - **Production**: Production deployment with Nginx
   - **DockerDevelopment**: Docker-based development
   - **DockerProduction**: Full Docker production stack

3. **Manual Setup (Alternative)**

   ```bash
   # Set up Python environment
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   
   # Set up Vue.js frontend
   cd casestrainer-vue-new
   npm install
   npm run build
   cd ..
   ```

## 🚀 Deployment Options

### Development Mode

```powershell
.\launcher.ps1 -Environment Development
```

- Backend: `http://localhost:5000`
- Frontend: `http://localhost:5173`
- Redis: Local or Docker container

### Production Mode

```powershell
.\launcher.ps1 -Environment Production
```

- Backend: `http://localhost:5000`
- Frontend: Built and served by Flask
- Nginx: Reverse proxy on port 443

### Docker Production (Recommended)

```powershell
.\launcher.ps1 -Environment DockerProduction
```

- Backend: Containerized with Waitress WSGI
- Frontend: Nginx container serving Vue.js build
- Redis: Dedicated container with persistence
- RQ Workers: Multiple worker containers for background tasks
- Health checks: Automatic monitoring and recovery

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```ini
# Flask Configuration
FLASK_APP=src.app_final_vue
FLASK_ENV=production
SECRET_KEY=your-secret-key-here

# API Keys
COURTLISTENER_API_KEY=your-courtlistener-api-key
LANGSEARCH_API_KEY=your-langsearch-api-key

# Database
DATABASE_FILE=data/citations.db

# Redis (for Docker)
REDIS_URL=redis://casestrainer-redis-prod:6379/0

# Email (UW SMTP)
MAIL_SERVER=smtp.uw.edu
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-netid
MAIL_PASSWORD=your-password
MAIL_DEFAULT_SENDER=your-netid@uw.edu
```

### Setting Up API Keys

1. **CourtListener API**
   - Get your API key from [CourtListener](https://www.courtlistener.com/api/)
   - Only v4 of the API is supported

2. **Other Services**
   - LangSearch (optional): Set `LANGSEARCH_API_KEY`
   - Other integrations: Refer to respective documentation

## 🛠 Development

### Project Structure

```text
CaseStrainer/
├── casestrainer-vue-new/  # Vue 3 frontend
│   ├── src/               # Source files
│   ├── public/            # Static files
│   └── package.json       # Frontend dependencies
├── src/                   # Backend source code
│   ├── app_final_vue.py   # Main Flask application
│   ├── vue_api_endpoints.py # Vue.js API endpoints
│   ├── citation_api.py    # Citation API endpoints
│   └── config.py          # Configuration management
├── docker-compose.prod.yml # Production Docker setup
├── launcher.ps1           # PowerShell launcher
├── docs/                  # Documentation
└── logs/                  # Application logs
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/casestrainer/api/analyze` | POST | Analyze and validate citations |
| `/casestrainer/api/task_status/<task_id>` | GET | Check processing status |
| `/casestrainer/api/health` | GET | Health check |
| `/casestrainer/api/version` | GET | Application version |
| `/casestrainer/api/server_stats` | GET | Server statistics |

### Common Tasks

```bash
# Run tests
pytest

# Lint code
ruff check .

# Format code
ruff format .

# Build frontend
cd casestrainer-vue-new
npm run build
cd ..

# Start Docker production
docker-compose -f docker-compose.prod.yml up -d
```

## 🔧 Troubleshooting

### Health Check Issues

If services fail health checks:

1. **Check logs**: `logs/` directory contains detailed logs
2. **Restart services**: Use launcher menu option 4 (Stop All Services)
3. **Docker issues**: Restart Docker Desktop and try again
4. **Port conflicts**: Ensure ports 5000, 5001, 6379, 443 are available

### Common Issues

- **502 Bad Gateway**: Backend not running or port mismatch
- **Redis connection errors**: Docker Desktop not running
- **Frontend not loading**: Vue.js build not updated
- **Health check failures**: Recent fixes implemented - check launcher logs

## 📚 Documentation

- [Development Guide](docs/DEVELOPMENT.md) - Development setup and guidelines
- [Deployment Guide](docs/DEPLOYMENT_VUE.md) - Production deployment instructions
- [Auto-Restart Guide](docs/AUTO_RESTART_GUIDE.md) - Service monitoring and recovery
- [API Documentation](docs/API_DOCUMENTATION.md) - API reference
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details. 