/**
 * Utility function to dynamically load a script
 * @param {string} url - The URL of the script to load
 * @returns {Promise<void>} A promise that resolves when the script is loaded
 */
export function loadScript(url) {
  return new Promise((resolve, reject) => {
    // Check if script is already loaded
    const existingScript = document.querySelector(`script[src="${url}"]`);
    if (existingScript) {
      resolve();
      return;
    }
    
    // Create a new script element
    const script = document.createElement('script');
    script.src = url;
    script.type = 'text/javascript';
    script.async = true;
    
    // Handle script load
    script.onload = () => {
      console.log(`Script loaded: ${url}`);
      resolve();
    };
    
    // Handle script error
    script.onerror = (error) => {
      console.error(`Error loading script: ${url}`, error);
      document.head.removeChild(script);
      reject(new Error(`Failed to load script: ${url}`));
    };
    
    // Append the script to the document head
    document.head.appendChild(script);
  });
}

/**
 * Utility function to load a CSS file dynamically
 * @param {string} url - The URL of the CSS file to load
 * @returns {Promise<void>} A promise that resolves when the CSS is loaded
 */
export function loadCSS(url) {
  return new Promise((resolve, reject) => {
    // Check if CSS is already loaded
    const existingLink = document.querySelector(`link[href="${url}"]`);
    if (existingLink) {
      resolve();
      return;
    }
    
    // Create a new link element
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = url;
    
    // Handle CSS load
    link.onload = () => {
      console.log(`CSS loaded: ${url}`);
      resolve();
    };
    
    // Handle CSS error
    link.onerror = (error) => {
      console.error(`Error loading CSS: ${url}`, error);
      document.head.removeChild(link);
      reject(new Error(`Failed to load CSS: ${url}`));
    };
    
    // Append the link to the document head
    document.head.appendChild(link);
  });
}

export default {
  loadScript,
  loadCSS
};
