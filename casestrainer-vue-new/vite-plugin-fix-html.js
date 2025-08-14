// Custom Vite plugin to fix HTML formatting issues
const fs = require('fs');
const path = require('path');

/**
 * Vite plugin to fix HTML formatting issues in the build output
 * @returns {import('vite').Plugin}
 */
export default function fixHtmlPlugin() {
  return {
    name: 'fix-html',
    enforce: 'post',
    closeBundle() {
      const indexPath = path.join(__dirname, 'dist', 'index.html');
      
      try {
        // Read the generated index.html
        let html = fs.readFileSync(indexPath, 'utf8');
        
        // Fix malformed HTML by reconstructing it
        const headMatch = html.match(/<head>([\s\S]*?)<\/head>/i);
        const bodyMatch = html.match(/<body>([\s\S]*?)<\/body>/i);
        
        if (headMatch && bodyMatch) {
          const headContent = headMatch[1];
          const bodyContent = bodyMatch[1];
          
          // Reconstruct the HTML with proper formatting
          const fixedHtml = `<!DOCTYPE html>
<html lang="en">
  <head>${headContent}
  </head>
  <body>${bodyContent}
  </body>
</html>`;
          
          // Write the fixed HTML back to the file
          fs.writeFileSync(indexPath, fixedHtml, 'utf8');
          console.log('✅ Fixed HTML formatting in index.html');
        } else {
          console.warn('⚠️ Could not find head or body tags in index.html');
        }
      } catch (error) {
        console.error('❌ Error fixing HTML:', error);
      }
    }
  };
}
