// version.js - Fetches backend version dynamically
import axios from 'axios';

export async function fetchVersion() {
  try {
    const response = await axios.get('/casestrainer/api/version');
    return response.data.version || 'unknown';
  } catch (error) {
    console.error('Error fetching version:', error);
    return 'unknown';
  }
}
