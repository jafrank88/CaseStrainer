# CaseStrainer Production Deployment Guide

This guide provides step-by-step instructions for deploying the "Confirmed with Multitool" tab to the production server at https://wolf.law.uw.edu/casestrainer/.

## Files Included in This Deployment Package

1. **app_final.py** - Updated with proper routes for the multitool tab
2. **templates/fixed_form_ajax.html** - Contains the enhanced tab structure with styling
3. **static/js/multitool_confirmed.js** - JavaScript to handle the multitool tab functionality
4. **restore_multitool_data.py** - Script to populate the database with 33 landmark cases

## Deployment Steps

### 1. Upload Files to Production Server

Upload all files in this deployment package to the production server, maintaining the directory structure:

- `app_final.py` → Root directory of CaseStrainer
- `templates/fixed_form_ajax.html` → Templates directory
- `static/js/multitool_confirmed.js` → Static/js directory
- `restore_multitool_data.py` → Root directory of CaseStrainer

### 2. Populate the Database with Citation Data

Run the `restore_multitool_data.py` script on the production server to populate the database with 33 landmark cases:

```bash
cd /path/to/casestrainer
python restore_multitool_data.py
```

You should see output confirming that 33 citations were added to the database.

### 3. Restart the CaseStrainer Application

Restart the CaseStrainer application to apply the changes:

```bash
cd /path/to/casestrainer
python run_production.py --host 0.0.0.0 --port 5000
```

**IMPORTANT**: The application must listen on all interfaces (0.0.0.0), not just localhost (127.0.0.1).

### 4. Verify the Deployment

After deployment, verify that the "Confirmed with Multitool" tab is working correctly:

1. Visit https://wolf.law.uw.edu/casestrainer/
2. Look for the highlighted "Confirmed with Multitool" tab in the navigation
3. Click on the tab to verify that it displays all 33 citations
4. Test the pagination and citation details functionality

## Troubleshooting

If the tab is not visible or not displaying citations:

1. **Check Server Logs**: Look for any error messages in the server logs
2. **Verify Database**: Run the following command to check if the citations were added:
   ```bash
   python -c "import sqlite3; conn = sqlite3.connect('citations.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM multitool_confirmed_citations'); print(cursor.fetchone()[0]); conn.close()"
   ```
3. **Check API Endpoint**: Test the API endpoint directly:
   ```bash
   curl http://localhost:5000/confirmed_with_multitool/data
   ```

## Additional Notes

- The "Confirmed with Multitool" tab is designed to display citations that were verified by alternative sources but not by CourtListener
- This feature aligns with the planned enhancements for CaseStrainer, particularly the Citation Network Visualization and Machine Learning Citation Classifier
- Future updates may include more advanced filtering and search capabilities for these citations
