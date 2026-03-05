/**
 * Single source for API base URL.
 * Set VITE_API_BASE_URL in .env or at build time; defaults to /casestrainer/api.
 */
export const API_BASE_URL =
  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) ||
  '/casestrainer/api';
