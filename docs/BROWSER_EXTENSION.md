# CaseStrainer Browser Extension

## Overview

The CaseStrainer Browser Extension allows users to verify legal citations directly on legal websites, providing real-time feedback on citation authenticity while browsing.

## Status

**Available in-repo (Chromium)** — Manifest V3 extension under `browser-extension/` at the repo root. Load unpacked in Chrome or Edge (developer mode). It calls the same CaseStrainer API as the web app (`POST …/analyze`, `GET …/task_status/…` when the server returns a `task_id`).

Firefox / Safari packages are not maintained here yet.

## Features

- **On-page patterns**: Content script matches common reporter-style citation strings on allowlisted legal sites (see `manifest.json` `content_scripts.matches`).
- **Verification**: Background worker sends extracted strings to the API (batched with newlines), maps results back for highlighting and the popup list.
- **Options**: Configurable API base URL (default `https://wolf.law.uw.edu/casestrainer/api`).

## Architecture

### Extension Components
```
browser-extension/
├── manifest.json         # Extension configuration
├── background.js         # Background service worker
├── content-script.js     # Page content analysis
├── popup/
│   ├── popup.html       # Extension popup UI
│   ├── popup.js         # Popup logic
│   └── popup.css        # Popup styling
├── options/
│   ├── options.html     # Settings page
│   ├── options.js       # Settings logic
│   └── options.css      # Settings styling
└── assets/
    ├── icons/           # Extension icons
    └── styles/          # Shared styles
```

### API integration
- **Default API base**: `https://wolf.law.uw.edu/casestrainer/api`
- **Endpoints**: `POST …/analyze`, `GET …/task_status/{task_id}` (when the server responds with `task_id`)
- **CORS**: By default the app allows `chrome-extension://…` and `moz-extension://…` via regex (see `_configure_cors` in `app_final_vue.py`). Set `CORS_ALLOW_BROWSER_EXTENSIONS=false` to turn that off. Override allowed web origins with `CORS_ORIGINS` (comma-separated).

## Installation (Chrome / Edge)

1. Clone https://github.com/jafrank88/casestrainer
2. Open `chrome://extensions` or `edge://extensions`
3. Enable **Developer mode** → **Load unpacked**
4. Choose the `browser-extension` directory (contains `manifest.json`)
5. Optional: open **Extension options** and set the API base (for local dev, e.g. `http://127.0.0.1:5001/casestrainer/api`)

### Firefox / Safari

Not packaged in this repository yet.

## Configuration (Options page)

- **API base URL** — no `/analyze` suffix; the service worker appends `/analyze` and calls `task_status` on the same host.
- **Auto-verify**, **highlight colors**, and related toggles apply to the content script and popup.

## Usage

### Basic Usage
1. Navigate to any legal website
2. The extension automatically detects citations on the page
3. Verified citations are highlighted in green
4. Unverified citations are highlighted in yellow/red
5. Click on any citation to see details

### Advanced Features
- **Batch Verification**: Verify all citations on a page with one click
- **Citation Export**: Export verified citations to BibTeX, EndNote, or CSV
- **History**: View previously verified citations
- **Reports**: Generate citation verification reports

## Privacy & Security

### Data Handling
- **No Tracking**: The extension does not track your browsing history
- **Local Processing**: Citation detection happens locally in your browser
- **Secure API**: All API calls use HTTPS encryption
- **No Data Storage**: Citation data is not stored on external servers

### Permissions
- **activeTab**: Access to current page content
- **storage**: Save extension settings locally
- **https://wolf.law.uw.edu/**: Connect to CaseStrainer API

## Development Roadmap

### Phase 1: Core Features (Q1-Q2 2026)
- [ ] Basic citation detection
- [ ] CourtListener API integration
- [ ] Visual highlighting
- [ ] Chrome/Edge support

### Phase 2: Enhanced Features (Q3 2026)
- [ ] Firefox support
- [ ] Advanced filtering options
- [ ] Citation export
- [ ] Custom verification rules

### Phase 3: Advanced Features (Q4 2026)
- [ ] Safari support
- [ ] Batch verification
- [ ] Citation reports
- [ ] Team collaboration features

## Contributing

We welcome contributions to the CaseStrainer Browser Extension! Please see our contributing guidelines at:

**Repository**: https://github.com/jafrank88/casestrainer

### Development Setup
```bash
# Clone the repository
git clone https://github.com/jafrank88/casestrainer.git

# Navigate to browser extension directory
cd casestrainer/browser-extension

# Install dependencies
npm install

# Build the extension
npm run build

# Load unpacked extension in Chrome/Edge
# Navigate to chrome://extensions/
# Enable "Developer mode"
# Click "Load unpacked" and select the build directory
```

## Support

### Documentation
- **Main Documentation**: https://github.com/jafrank88/casestrainer/tree/main/docs
- **API Documentation**: [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

### Getting Help
- **Issues**: https://github.com/jafrank88/casestrainer/issues
- **Discussions**: https://github.com/jafrank88/casestrainer/discussions
- **Email**: support@wolf.law.uw.edu

## License

CaseStrainer Browser Extension is released under the same license as the main CaseStrainer application. See the LICENSE file in the repository for details.

## Acknowledgments

- **CourtListener**: For providing the citation verification API
- **Legal Community**: For feedback and feature suggestions
- **Contributors**: All developers who contribute to this project

---

**Last Updated**: 2025-01-20  
**Status**: Planned Feature  
**Version**: Not yet released
