/**
 * Custom Modal - Handles custom modal dialogs for user messages
 */

(function() {
  'use strict';

  /**
   * Show custom modal with message
   */
  function showCustomModal(message) {
    const overlay = document.getElementById('customModalOverlay');
    const messageEl = document.getElementById('customModalMessage');
    
    if (!overlay || !messageEl) {
      console.warn('Custom modal elements not found');
      return;
    }
    
    messageEl.textContent = message;
    overlay.classList.add('show');
  }

  /**
   * Hide custom modal
   */
  function hideCustomModal() {
    const overlay = document.getElementById('customModalOverlay');
    if (overlay) {
      overlay.classList.remove('show');
    }
  }

  /**
   * Initialize modal event listeners
   */
  function initCustomModal() {
    const okBtn = document.getElementById('customModalOkBtn');
    const overlay = document.getElementById('customModalOverlay');
    
    if (okBtn) {
      okBtn.addEventListener('click', hideCustomModal);
    }
    
    if (overlay) {
      overlay.addEventListener('click', function(e) {
        if (e.target.id === 'customModalOverlay') {
          hideCustomModal();
        }
      });
    }
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCustomModal);
  } else {
    initCustomModal();
  }

  // Export functions to window for use in other scripts
  window.showCustomModal = showCustomModal;
  window.hideCustomModal = hideCustomModal;

})();

