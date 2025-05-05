# API Setup Guide

This guide explains how to set up API keys for CaseStrainer.

## LangSearch API

CaseStrainer can use the LangSearch API to generate case summaries. To use this feature, you need to provide a LangSearch API key.

### Setting Up the LangSearch API Key

There are three ways to provide your LangSearch API key to CaseStrainer:

#### 1. Command Line Argument (Recommended)

When starting the application, use the `--langsearch-key` argument:

```bash
python app.py --langsearch-key YOUR_API_KEY
```

This is the most straightforward method and ensures the API key is correctly set for the current session.

#### 2. Environment Variable

Set the `LANGSEARCH_API_KEY` environment variable before running the application:

**Windows:**
```cmd
set LANGSEARCH_API_KEY=YOUR_API_KEY
python app.py
```

**Linux/macOS:**
```bash
export LANGSEARCH_API_KEY=YOUR_API_KEY
python app.py
```

#### 3. Configuration File

CaseStrainer can load API keys from a configuration file named `config.json` in the root directory of the project. This is a convenient way to store your API keys without having to provide them each time you run the application.

Create or update the `config.json` file with the following structure:

```json
{
    "langsearch_api_key": "YOUR_LANGSEARCH_API_KEY"
}
```

Replace `YOUR_LANGSEARCH_API_KEY` with your actual LangSearch API key.

## CourtListener API

CaseStrainer can use the CourtListener API to check if case citations exist and to generate summaries of cases. To use this feature, you need to obtain an API key from CourtListener.

### Obtaining a CourtListener API Key

1. Go to [CourtListener](https://www.courtlistener.com/)
2. Create an account or log in to your existing account
3. Go to your account settings
4. Find the API section and generate an API key

### Setting Up the CourtListener API Key

There are three ways to provide your CourtListener API key to CaseStrainer:

#### 1. Command Line Argument (Recommended)

When starting the application, use the `--courtlistener-key` argument:

```bash
python app.py --courtlistener-key YOUR_API_KEY
```

This is the most straightforward method and ensures the API key is correctly set for the current session.

#### 2. Environment Variable

Set the `COURTLISTENER_API_KEY` environment variable before running the application:

**Windows:**
```cmd
set COURTLISTENER_API_KEY=YOUR_API_KEY
python app.py
```

**Linux/macOS:**
```bash
export COURTLISTENER_API_KEY=YOUR_API_KEY
python app.py
```

#### 3. Configuration File

CaseStrainer can load API keys from a configuration file named `config.json` in the root directory of the project. This is a convenient way to store your API keys without having to provide them each time you run the application.

Create a file named `config.json` with the following structure:

```json
{
    "courtlistener_api_key": "YOUR_COURTLISTENER_API_KEY",
    "openai_api_key": "YOUR_OPENAI_API_KEY"
}
```

Replace `YOUR_COURTLISTENER_API_KEY` with your actual CourtListener API key. If you don't have an OpenAI API key, you can leave that field empty.

**Note:** The configuration file is already set up with your CourtListener API key. You don't need to modify it unless you want to change the key or add an OpenAI API key.

### Verifying API Setup

When you start CaseStrainer with a valid API key, you should see a message like:

```
Initializing CourtListener API with key: XXXXX...XXXXX
CourtListener API key set in environment variable: XXXXX...XXXXX
CourtListener API connection successful.
API is now available for full functionality.
```

If you see a message about "limited mode" or "rate-limited", it means the API key was not properly set or is invalid.

### Troubleshooting

If you're having issues with the CourtListener API:

1. **Check the API key**: Make sure you're using the correct API key from your CourtListener account.
2. **Check the console output**: Look for error messages that might indicate what's wrong.
3. **Try the command line argument method**: This is the most reliable way to provide the API key.
4. **Check your internet connection**: Make sure you can access the CourtListener website.
5. **Try the local PDF search option**: If you can't use the API, you can use the local PDF search option instead.

## OpenAI API (Optional)

CaseStrainer can also use the OpenAI API to generate case summaries. This is optional and not required for the basic functionality.

### Setting Up the OpenAI API Key

Similar to the CourtListener API key, you can provide your OpenAI API key using:

```bash
python app.py --openai-key YOUR_OPENAI_API_KEY
```

Or set the `OPENAI_API_KEY` environment variable.

## Running CaseStrainer with Both APIs

To use both APIs:

```bash
python app.py --courtlistener-key YOUR_COURTLISTENER_KEY --openai-key YOUR_OPENAI_KEY
```

## Additional Command Line Options

CaseStrainer supports several other command line options:

- `--port PORT`: Specify the port to run the server on (default: 5000)
- `--host HOST`: Specify the host to run the server on (default: 0.0.0.0)
- `--debug`: Run in debug mode

Example:

```bash
python app.py --courtlistener-key YOUR_KEY --port 8080 --debug
