/**
 * Toast Notification System
 * Replaces alert() with beautiful toast notifications matching Ayurveda theme
 */

(function() {
  'use strict';

  // Create toast container if it doesn't exist
  function getToastContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      document.body.appendChild(container);
    }
    return container;
  }

  /**
   * Show a toast notification
   * @param {string} message - The message to display
   * @param {string} type - 'success', 'error', 'warning', 'info'
   * @param {number} duration - Duration in milliseconds (default: 4000)
   */
  function showToast(message, type = 'info', duration = 4000) {
    const container = getToastContainer();
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    // Icons for each type
    const icons = {
      success: '✅',
      error: '❌',
      warning: '⚠️',
      info: 'ℹ️'
    };
    
    toast.innerHTML = `
      <span class="toast-icon">${icons[type] || icons.info}</span>
      <span class="toast-content">${message}</span>
      <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    // Add to container
    container.appendChild(toast);
    
    // Auto remove after duration
    if (duration > 0) {
      setTimeout(() => {
        toast.classList.add('hiding');
        setTimeout(() => {
          if (toast.parentElement) {
            toast.remove();
          }
        }, 300);
      }, duration);
    }
    
    return toast;
  }

  // Expose global functions
  window.showToast = showToast;
  
  // Convenience functions
  window.toastSuccess = (message, duration) => showToast(message, 'success', duration);
  window.toastError = (message, duration) => showToast(message, 'error', duration);
  window.toastWarning = (message, duration) => showToast(message, 'warning', duration);
  window.toastInfo = (message, duration) => showToast(message, 'info', duration);
  
  // Replace alert() globally (optional - can be disabled)
  // Uncomment if you want to automatically replace all alerts
  /*
  const originalAlert = window.alert;
  window.alert = function(message) {
    showToast(message, 'info', 4000);
  };
  */
})();
