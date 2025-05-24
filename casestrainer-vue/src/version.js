// version.js - Fetches backend version dynamically
import axios from 'axios';

export async function fetchVersion() {
  try {
    // Adjust for deployment prefix if needed
    const prefix = window.location.pathname.includes('/casestrainer') ? '/casestrainer' : '';
    const response = await axios.get(`${prefix}/api/version`);
    return response.data.version || 'unknown';
  } catch (error) {
    return 'unknown';
  }
}
