// Central helper for building protocol-safe API URLs with correct prefix
function apiUrl(path) {
    // Always return a relative URL like /casestrainer/api/endpoint
    const prefix = '/casestrainer';
    let cleanPath = path;
    if (cleanPath.startsWith(prefix)) {
        cleanPath = cleanPath.slice(prefix.length);
    }
    if (!cleanPath.startsWith('/api/')) {
        if (cleanPath.startsWith('/')) {
            cleanPath = '/api' + cleanPath;
        } else {
            cleanPath = '/api/' + cleanPath;
        }
    }
    return prefix + cleanPath;
}

// Export for ES6 modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = apiUrl;
}
