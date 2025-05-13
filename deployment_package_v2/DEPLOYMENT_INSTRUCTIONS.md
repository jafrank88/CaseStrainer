# CaseStrainer Production Deployment Guide

This guide provides step-by-step instructions for deploying the updated "Unconfirmed Citations" and "Confirmed with Multitool" tabs to the production server at https://wolf.law.uw.edu/casestrainer/.

## Files Included in This Deployment Package

1. **app_final.py** - Updated with proper routes for both tabs and enhanced error handling
2. **templates/fixed_form_ajax.html** - Updated with improved data loading for both tabs
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

After deployment, verify that both tabs are working correctly:

1. Visit https://wolf.law.uw.edu/casestrainer/
2. Check the "Unconfirmed Citations" tab to ensure it's displaying data
3. Check the "Confirmed with Multitool" tab to ensure it's displaying the 33 landmark cases
4. Test the pagination and citation details functionality in both tabs

## What Has Been Fixed

This deployment addresses the following issues:

1. **Dynamic URL Detection**: The JavaScript now detects whether it's running in the local or production environment and uses the appropriate base URL.

2. **Robust API Endpoints**: New API endpoints have been added for both the unconfirmed citations and multitool confirmed citations data.

3. **Improved Data Loading**: The frontend code now tries the API endpoint first and then falls back to the JSON file if needed.

4. **Enhanced Error Handling**: Better error handling and logging have been added for easier troubleshooting.

## Troubleshooting

If the tabs are not visible or not displaying data:

1. **Check Server Logs**: Look for any error messages in the server logs.

2. **Verify Database**: Run the following commands to check if the citations were added:
   ```bash
   python -c "import sqlite3; conn = sqlite3.connect('citations.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM multitool_confirmed_citations'); print(cursor.fetchone()[0]); conn.close()"
   ```

3. **Check API Endpoints**: Test the API endpoints directly:
   ```bash
   curl http://localhost:5000/confirmed_with_multitool/data
   curl http://localhost:5000/unconfirmed_citations/data
   ```

4. **Check Browser Console**: Look for any JavaScript errors in the browser console.

## Additional Notes

- The "Confirmed with Multitool" tab displays 33 landmark cases that were verified by alternative sources but not by CourtListener.
- The "Unconfirmed Citations" tab displays citations that could not be verified by any source.
- Both tabs now work seamlessly in both local and production environments.
- This implementation aligns with the planned enhancements for CaseStrainer, particularly the Citation Network Visualization and Machine Learning Citation Classifier features.
