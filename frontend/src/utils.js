/**
 * IP PULSE - Shared Frontend Utilities
 * Provides sanitized escaping, string formatting, debouncing, and throttling helpers.
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

/**
 * Creates a debounced function that delays invoking fn until after waitMs milliseconds
 * have elapsed since the last time the debounced function was invoked.
 *
 * @param {Function} fn - Function to debounce.
 * @param {number} waitMs - Delay in milliseconds.
 * @returns {Function} - Debounced function.
 */
export function debounce(fn, waitMs = 150) {
  let timer = null;
  return function (...args) {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => {
      timer = null;
      fn.apply(this, args);
    }, waitMs);
  };
}

/**
 * Creates a throttled function that only invokes fn at most once per every limitMs milliseconds.
 *
 * @param {Function} fn - Function to throttle.
 * @param {number} limitMs - Window in milliseconds.
 * @returns {Function} - Throttled function.
 */
export function throttle(fn, limitMs = 100) {
  let inThrottle = false;
  return function (...args) {
    if (!inThrottle) {
      fn.apply(this, args);
      inThrottle = true;
      setTimeout(() => {
        inThrottle = false;
      }, limitMs);
    }
  };
}
