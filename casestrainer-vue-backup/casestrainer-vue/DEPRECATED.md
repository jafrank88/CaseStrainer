# DEPRECATED - Do Not Use

This directory contains the legacy Vue.js frontend that has been replaced by a new Vite-based implementation.

## Status
- ❌ Deprecated
- 🔄 Replaced by: `casestrainer-vue-new/` (Vite + Vue 3)
- 📅 Date Archived: 2025-06-06
- ℹ️ Reason: Migrated to Vite for better performance and developer experience

## Usage
This directory is kept for reference only. Do not use this code in production.

### When to Reference This Code
- Debugging issues in the new Vite implementation
- Comparing old and new implementations
- Historical reference for component behavior

### Key Differences from New Version
- Uses Webpack instead of Vite
- Different build configuration
- May contain outdated dependencies
- Different project structure

---
**Note**: The active development now happens in `casestrainer-vue-new/`

# Deprecated/Archived Files

**The following files and components have been archived as part of the CaseStrainer UI/API simplification.**

- These files are no longer used in the current application.
- They are kept for reference and recovery, but should not be imported or referenced in new code.
- If you need to restore functionality, move them back to their original location and update imports as needed.

## Archived Components
- `src/components/FileUpload.vue` — superseded by unified input interface
- `src/components/TextPaste.vue` — superseded by unified input interface
- `src/components/EnhancedFileUpload.vue` — superseded by unified input interface
- `src/components/EnhancedTextPaste.vue` — superseded by unified input interface

## Archived API/Service Files
- `src/api/citations.js` — legacy API service, replaced by unified API calls

## Other Candidates
- Any utility or service file only used by the above components
- Any view that only referenced the above components

**If you find a file in this list being imported in active code, please remove the import and use the new unified interface instead.**
