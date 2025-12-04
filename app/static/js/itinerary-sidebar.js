/**
 * Itinerary Sidebar - Handles sidebar toggle functionality for mobile
 * Specific to itinerary.html
 */

(function() {
  'use strict';

  /**
   * Initialize sidebar toggle
   */
  function initSidebarToggle() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (!sidebarToggle || !sidebar) return;

    sidebarToggle.addEventListener('click', function(e) {
      e.stopPropagation();
      sidebar.classList.toggle('show');
      
      // Update button text
      if (sidebar.classList.contains('show')) {
        sidebarToggle.textContent = '✕';
        sidebarToggle.title = 'Hide activities';
      } else {
        sidebarToggle.textContent = '☰';
        sidebarToggle.title = 'Show activities';
      }
    });
    
    // Close sidebar when clicking outside
    document.addEventListener('click', function(e) {
      if (sidebar.classList.contains('show') && 
          !sidebar.contains(e.target) && 
          !sidebarToggle.contains(e.target)) {
        sidebar.classList.remove('show');
        sidebarToggle.textContent = '☰';
        sidebarToggle.title = 'Show activities';
      }
    });
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSidebarToggle);
  } else {
    initSidebarToggle();
  }

})();

