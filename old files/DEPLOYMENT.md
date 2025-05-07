/jafrank88# CaseStrainer Deployment Guide

This guide provides instructions for deploying CaseStrainer to production environments.

## Prerequisites

- Python 3.8 or higher
- pip package manager
- OpenAI API key (for production-quality case summaries)
- SSL certificate and key (required for Word add-in)

## Local Deployment

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root:

```
# OpenAI API key
OPENAI_API_KEY=your_openai_api_key_here

# SSL certificate paths
SSL_CERT_PATH=ssl/cert.pem
SSL_KEY_PATH=ssl/key.pem

# Server configuration
DEBUG=False
HOST=0.0.0.0
PORT=5000
```

### 3. Generate SSL Certificate (for Development)

For development purposes, you can generate a self-signed certificate:

```bash
mkdir -p ssl
openssl req -x509 -newkey rsa:4096 -nodes -out ssl/cert.pem -keyout ssl/key.pem -days 365
```

For production, use a proper SSL certificate from a trusted certificate authority.

### 4. Run the Application

```bash
python app.py
```

## Cloud Deployment

### Option 1: Deploy to Heroku

1. Install the Heroku CLI and log in:

```bash
heroku login
```

2. Create a new Heroku app:

```bash
heroku create casestrainer-app
```

3. Add a Procfile to the project root:

```
web: gunicorn app:app
```

4. Add gunicorn to requirements.txt:

```
gunicorn==21.2.0
```

5. Set environment variables:

```bash
heroku config:set OPENAI_API_KEY=your_openai_api_key_here
heroku config:set DEBUG=False
```

6. Deploy the application:

```bash
git add .
git commit -m "Prepare for Heroku deployment"
git push heroku main
```

### Option 2: Deploy to AWS Elastic Beanstalk

1. Install the AWS CLI and EB CLI:

```bash
pip install awscli awsebcli
```

2. Configure AWS credentials:

```bash
aws configure
```

3. Create a new Elastic Beanstalk application:

```bash
eb init -p python-3.8 casestrainer
```

4. Create a `.ebextensions/01_flask.config` file:

```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: app:app
  aws:elasticbeanstalk:application:environment:
    OPENAI_API_KEY: your_openai_api_key_here
    DEBUG: "False"
```

5. Create a `Procfile`:

```
web: gunicorn app:app
```

6. Deploy the application:

```bash
eb create casestrainer-env
```

### Option 3: Deploy to Docker

1. Create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV OPENAI_API_KEY=""
ENV DEBUG="False"
ENV HOST="0.0.0.0"
ENV PORT="5000"
ENV SSL_CERT_PATH="ssl/cert.pem"
ENV SSL_KEY_PATH="ssl/key.pem"

EXPOSE 5000

CMD ["python", "app.py"]
```

2. Build and run the Docker image:

```bash
docker build -t casestrainer .
docker run -p 5000:5000 -e OPENAI_API_KEY=your_openai_api_key_here casestrainer
```

## Word Add-in Deployment

### 1. Update Manifest URLs

Before deploying the Word add-in, update the URLs in `word_addin/manifest.xml` to point to your production server:

```xml
<DefaultSettings>
  <SourceLocation DefaultValue="https://your-production-server.com/word-addin/taskpane.html" />
</DefaultSettings>
```

### 2. Deploy to Microsoft AppSource (Optional)

To publish your add-in to Microsoft AppSource:

1. Create a Microsoft Partner Center account
2. Prepare your add-in for submission following Microsoft's guidelines
3. Submit your add-in for validation and publishing

### 3. Distribute Manually

For internal or limited distribution:

1. Host the manifest file on a web server or shared location
2. Users can install the add-in by going to Insert > Add-ins > Upload My Add-in in Word

## Monitoring and Maintenance

### Logging

Set up logging to monitor application performance and errors:

```python
import logging
logging.basicConfig(
    filename='casestrainer.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Backup

Regularly backup any user data or configuration files.

### Updates

Keep dependencies updated to ensure security and performance:

```bash
pip install --upgrade -r requirements.txt
```

## Security Considerations

1. **API Keys**: Never commit API keys to version control. Always use environment variables.

2. **HTTPS**: Always use HTTPS in production, especially for the Word add-in.

3. **Input Validation**: Validate all user inputs to prevent injection attacks.

4. **Rate Limiting**: Implement rate limiting to prevent abuse of the OpenAI API.

5. **Authentication**: Consider adding user authentication for sensitive deployments.

## Troubleshooting

### Common Issues

1. **SSL Certificate Problems**:
   - Ensure certificates are valid and properly configured
   - Check certificate paths in environment variables

2. **OpenAI API Errors**:
   - Verify API key is valid
   - Check for rate limiting or quota issues

3. **Word Add-in Not Loading**:
   - Ensure HTTPS is properly configured
   - Verify manifest URLs are correct
   - Check browser console for JavaScript errors

### Getting Help

If you encounter issues not covered in this guide, please:

1. Check the GitHub repository issues
2. Consult the OpenAI API documentation
3. Refer to Microsoft's Word Add-in documentation

## License

This project is licensed under the MIT License - see the LICENSE file for details.
