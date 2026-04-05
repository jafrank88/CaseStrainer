# CaseStrainer Browser Extension

Manifest **V3** extension for **Chrome and Edge** (load unpacked). Calls `POST …/casestrainer/api/analyze` with `{ "type": "text", … }` and polls `task_status` when the server returns a `task_id`. Firefox builds are not shipped in this folder.

## Features

✅ **Real-Time Citation Detection** - Automatically detects legal citations on web pages  
✅ **Instant Verification** - Verifies citations using the CaseStrainer API  
✅ **Visual Highlighting** - Color-codes verified (green) and unverified (red) citations  
✅ **Confidence Scores** - Shows verification confidence percentages  
✅ **Batch Processing** - Efficiently processes multiple citations at once  
✅ **Customizable Settings** - Configure colors, API endpoint, and behavior  

## Supported Websites

- Google Scholar
- CourtListener
- Justia
- FindLaw
- Law school websites
- Court websites
- Any page with legal citations

## Detected Citation Formats

- **US Reports**: `123 U.S. 456`
- **Federal Reporter**: `123 F.2d 456`, `123 F.3d 456`
- **Supreme Court Reporter**: `123 S.Ct. 456`
- **State Reporters**: `123 Wash. 2d 456`, `123 Cal.App.4th 456`
- And many more...

## Installation

### Chrome / Edge (Chromium)

1. **Download** or clone this repository
2. **Open** Chrome/Edge and navigate to `chrome://extensions/`
3. **Enable** "Developer mode" (toggle in top-right corner)
4. Click **"Load unpacked"**
5. Select the `browser-extension` folder
6. The extension is now installed!

### Firefox

1. **Download** or clone this repository
2. **Open** Firefox and navigate to `about:debugging#/runtime/this-firefox`
3. Click **"Load Temporary Add-on"**
4. Navigate to the `browser-extension` folder and select `manifest.json`
5. The extension is now installed temporarily

**Note**: For permanent Firefox installation, the extension needs to be signed by Mozilla.

## Usage

### Automatic Mode

1. Visit any legal website (e.g., Google Scholar, CourtListener)
2. The extension automatically detects citations on the page
3. Citations are highlighted:
   - **Green underline** = Verified citation
   - **Red underline** = Unverified or questionable citation
4. Hover over citations to see confidence scores

### Manual Control

1. Click the **CaseStrainer icon** in your browser toolbar
2. View all detected citations in the popup
3. See verification status and confidence scores
4. Click **"Re-analyze Page"** to re-scan the current page

### Settings

1. Click the **CaseStrainer icon** in your browser toolbar
2. Click the **"Settings"** button
3. Configure:
   - Auto-verification on page load
   - Citation highlight colors
   - API endpoint URL
   - Confidence score display

## Configuration

### API Endpoint

Default: `https://wolf.law.uw.edu/casestrainer/api`

To use a custom CaseStrainer API instance:
1. Open extension settings
2. Enter your API URL in the "CaseStrainer API URL" field
3. Click "Save Settings"

### Color Customization

Customize highlight colors in settings:
- **Verified color**: Default green (#28a745)
- **Unverified color**: Default red (#dc3545)

## Architecture

```
browser-extension/
├── manifest.json          # Extension configuration
├── background.js          # Service worker (API calls, state)
├── content-script.js      # Citation detection and highlighting
├── content-styles.css     # Citation highlight styles
├── options.html           # Settings page UI
├── options.js             # Settings page logic
├── popup/
│   ├── popup.html        # Popup UI
│   ├── popup.js          # Popup logic
│   └── popup.css         # Popup styling
└── icons/                 # Extension icons
    ├── icon16.png
    ├── icon48.png
    └── icon128.png
```

## Development

### Prerequisites

- Chrome/Edge or Firefox browser
- Basic knowledge of JavaScript and browser extensions

### Local Development

1. Make changes to the extension files
2. Reload the extension:
   - **Chrome/Edge**: Go to `chrome://extensions/` and click the reload icon
   - **Firefox**: Go to `about:debugging` and click "Reload"
3. Test on legal websites

### Testing

1. Visit test sites:
   - https://scholar.google.com/ (search for legal cases)
   - https://www.courtlistener.com/
   - https://www.justia.com/

2. Check console for errors: Right-click → Inspect → Console

3. Verify:
   - Citations are detected
   - API calls succeed
   - Highlighting appears correctly
   - Popup displays citation data

## API Integration

The extension uses the CaseStrainer API at `https://wolf.law.uw.edu/casestrainer/api/analyze`

### Request Format

```json
{
  "text": "citation text or document content",
  "source_type": "text"
}
```

### Response Format

```json
{
  "results": [
    {
      "citation": "123 U.S. 456",
      "exists": true,
      "is_hallucinated": false,
      "confidence": 0.95,
      "case_name": "Sample Case Name",
      "method": "api",
      "similarity_score": 0.85
    }
  ]
}
```

## Permissions

The extension requires these permissions:

- **activeTab**: Access current page content to detect citations
- **storage**: Save user settings and preferences
- **host_permissions**: Connect to CaseStrainer API at wolf.law.uw.edu

## Privacy

- ✅ No browsing history is collected or tracked
- ✅ Citations are processed locally in your browser
- ✅ Only citation text is sent to the API for verification
- ✅ No personal data is stored or transmitted
- ✅ Settings are stored locally in your browser

## Troubleshooting

### Citations not detected

- **Refresh the page** after installing the extension
- Check if the website is in the supported list
- Try clicking "Re-analyze Page" in the popup

### API errors

- Verify your internet connection
- Check that the API endpoint is accessible
- Try resetting settings to defaults

### Extension not loading

- Make sure Developer mode is enabled
- Check browser console for errors
- Try removing and re-adding the extension

### Highlighting not appearing

- Check that highlighting is enabled in settings
- Verify the content script is loaded (check console)
- Ensure the page has legal citations

## Contributing

We welcome contributions! To contribute:

1. Fork the repository: https://github.com/jafrank88/casestrainer
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

- **Documentation**: https://github.com/jafrank88/casestrainer/tree/main/docs
- **Issues**: https://github.com/jafrank88/casestrainer/issues
- **Discussions**: https://github.com/jafrank88/casestrainer/discussions
- **Website**: https://wolf.law.uw.edu/casestrainer/

## Roadmap

### Current Version (1.0.0)
- ✅ Citation detection
- ✅ API integration
- ✅ Visual highlighting
- ✅ Popup interface
- ✅ Settings page

### Planned Features (1.1.0)
- [ ] Firefox Add-ons support
- [ ] Citation export (BibTeX, EndNote)
- [ ] Citation history
- [ ] Custom verification rules

### Future roadmap
- [ ] Safari support
- [ ] Offline mode with cached results
- [ ] Team collaboration features
- [ ] Advanced filtering

## License

Part of the CaseStrainer project. See the main repository LICENSE file for details.

## Links

- **Main Repository**: https://github.com/jafrank88/casestrainer
- **Web Application**: https://wolf.law.uw.edu/casestrainer/
- **Documentation**: https://github.com/jafrank88/casestrainer/tree/main/docs

---

**Version**: 1.0.0  
**Last Updated**: 2025-01-20  
**Status**: Beta Release
