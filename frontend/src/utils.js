/**
 * IP PULSE - Shared Frontend Utilities
 * Provides sanitized escaping, string formatting, and common helpers.
 */

/**
 * Escapes unsafe HTML characters to prevent XSS vulnerabilities.
 * Handles null, undefined, numbers, and strings safely.
 *
 * @param {string|number|null|undefined} str - Raw input to escape.
 * @returns {string} - Escaped safe HTML string.
 */
export function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
