# CaseStrainer Browser Extension

## Overview

The CaseStrainer Browser Extension allows users to verify legal citations directly on legal websites, providing real-time feedback on citation authenticity while browsing.

## Status

**⚠️ PLANNED FEATURE** - This extension is planned for future development as part of CaseStrainer's enhancement roadmap.

## Planned Features

### Real-Time Citation Verification
- **Automatic Detection**: Automatically detects legal citations on web pages
- **Visual Indicators**: Highlights verified and unverified citations with color-coded indicators
- **Hover Information**: Shows citation details on hover without leaving the page
- **Quick Actions**: One-click access to case details and related citations

### Integration Capabilities
- **CourtListener Integration**: Real-time verification using CourtListener API
- **Context Analysis**: Extracts case names and dates from page context
- **Citation Clusters**: Identifies parallel citations on the same page
- **Export Options**: Save verified citations to your CaseStrainer account

### Supported Browsers
- Chrome/Edge (Chromium-based)
- Firefox
- Safari

### Supported Legal Websites
- CourtListener
- Google Scholar
- Justia
- FindLaw
- Law school and court websites
- Any website containing legal citations

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

### API Integration
- **CaseStrainer API**: https://wolf.law.uw.edu/casestrainer/api/
- **Endpoint**: `POST /casestrainer/api/analyze`
- **Authentication**: API key (configured in extension settings)

## Installation (When Available)

### Chrome/Edge
1. Visit the Chrome Web Store
2. Search for "CaseStrainer"
3. Click "Add to Chrome/Edge"
4. Configure your API key in extension settings

### Firefox
1. Visit Firefox Add-ons
2. Search for "CaseStrainer"
3. Click "Add to Firefox"
4. Configure your API key in extension settings

### Safari
1. Visit the App Store
2. Search for "CaseStrainer"
3. Download and install
4. Enable in Safari Extensions preferences

## Configuration

### API Key Setup
1. Open extension settings
2. Navigate to the CaseStrainer web application: https://wolf.law.uw.edu/casestrainer/
3. Generate an API key from your account settings
4. Paste the API key into the extension settings
5. Save settings

### Verification Settings
- **Auto-verify**: Enable/disable automatic citation verification
- **Highlight colors**: Customize colors for verified/unverified citations
- **Confidence threshold**: Set minimum confidence level for verification
- **Performance**: Adjust batch size and verification speed

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
