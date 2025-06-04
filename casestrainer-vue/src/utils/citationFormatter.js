/**
 * Formats a citation string to properly handle reporter abbreviations like F.2d, F.3d, F.4th, etc.
 * @param {string} citation - The citation text to format
 * @returns {string} - The formatted citation with proper HTML entities
 */
export function formatCitation(citation) {
  if (!citation) return '&nbsp;';
  
  // First, escape all HTML special characters
  let formatted = citation
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
  
  // Handle reporter abbreviations (F.2d, F.3d, F.4th, etc.)
  // This pattern matches reporter abbreviations like F.2d, F.3d, F.4th, etc.
  // It looks for a capital letter, followed by a dot, followed by digits, followed by optional 'd' or 'th'
  formatted = formatted.replace(
    /(\b[A-Z]\s*\.\s*\d+)(d|th|rd|nd|st)?\b/gi, 
    (match, p1, p2) => {
      // If there's a suffix (like 'd' or 'th'), wrap it in a span with a class
      if (p2) {
        return `${p1}<span class="reporter-suffix">${p2}</span>`;
      }
      return match;
    }
  );
  
  // Handle special cases like "F.3d" that might have been split
  formatted = formatted.replace(
    /(\b[A-Z]\s*\.\s*)(\d+)(d|th|rd|nd|st)\b/gi,
    (match, p1, p2, p3) => {
      return `${p1}${p2}<span class="reporter-suffix">${p3}</span>`;
    }
  );
  
  // Handle common reporter formats
  const reporterFormats = [
    // Federal Reporters
    { regex: /(\b\d+\s+)(F\.?\s*)(\d+)(d|th|rd|nd|st)\b/gi, replace: '$1$2$3<span class="reporter-suffix">$4</span>' },
    // US Reports
    { regex: /(\b\d+\s+U\.?\s*S\.?\s*)(\d+)\b/gi, replace: '$1$2' },
    // Supreme Court Reporter
    { regex: /(\b\d+\s+S\.?\s*Ct\.?\s*)(\d+)\b/gi, replace: '$1$2' },
    // Lawyer's Edition
    { regex: /(\b\d+\s+L\.?\s*Ed\.?\s*)(\d+)\b/gi, replace: '$1$2' },
  ];
  
  // Apply all reporter formats
  reporterFormats.forEach(format => {
    formatted = formatted.replace(format.regex, format.replace);
  });
  
  return formatted;
}
