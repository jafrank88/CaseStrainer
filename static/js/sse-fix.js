// SSE connection fix for CaseStrainer
document.addEventListener('DOMContentLoaded', function() {
    console.log('SSE fix script loaded');
    
    // Override the setupEventSource function to use the correct path
    window.originalSetupEventSource = window.setupEventSource;
    
    window.setupEventSource = function(url, options = {}) {
        console.log('Original URL:', url);
        
        // Fix the URL path
        let fixedUrl = url;
        if (url.startsWith('/casestrainer/')) {
            fixedUrl = url.replace('/casestrainer/', '/');
            console.log('Fixed URL:', fixedUrl);
        }
        
        // Use the original function with the fixed URL
        return window.originalSetupEventSource ? 
               window.originalSetupEventSource(fixedUrl, options) : 
               new EventSource(fixedUrl);
    };
    
    console.log('SSE connection fix applied');
});
