/**
 * Trip Delete Confirmation - Handles confirmation modal for deleting trips
 * Specific to trips.html
 */

(function() {
  'use strict';

  let confirmModal = null;
  let confirmMessage = null;
  let confirmOk = null;
  let confirmCancel = null;
  let pendingFormId = null;

  /**
   * Show confirmation modal for deleting a trip
   * @param {string} tripId - The trip ID to delete
   * @param {string} destination - The destination name for the message
   */
  function confirmDelete(tripId, destination) {
    if (!confirmModal || !confirmMessage) return;
    confirmMessage.textContent = `Are you sure you want to delete your trip to ${destination}? This action cannot be undone.`;
    pendingFormId = `deleteForm${tripId}`;
    confirmModal.classList.add('show');
  }

  /**
   * Hide confirmation modal
   */
  function hideConfirmModal() {
    if (confirmModal) {
      confirmModal.classList.remove('show');
    }
    pendingFormId = null;
  }

  /**
   * Handle confirmation OK button click
   */
  function handleConfirmOk(e) {
    e.preventDefault();
    if (pendingFormId) {
      const form = document.getElementById(pendingFormId);
      if (form) {
        // Get trip ID from form ID
        const tripId = pendingFormId.replace('deleteForm', '');
        const tripCard = document.querySelector(`.trip-card[data-trip-id="${tripId}"]`);
        
        // Remove trip card from DOM immediately with animation
        if (tripCard) {
          tripCard.style.transition = 'opacity 0.3s, transform 0.3s';
          tripCard.style.opacity = '0';
          tripCard.style.transform = 'translateX(-20px)';
          
          setTimeout(() => {
            tripCard.remove();
            // Update trip count
            const tripsCount = document.querySelector('.trips-count');
            if (tripsCount) {
              const currentCount = parseInt(tripsCount.textContent) || 0;
              const newCount = Math.max(0, currentCount - 1);
              tripsCount.textContent = `${newCount} trip(s)`;
            }
          }, 300);
        }
        
        // Submit form to delete from server (will cause page reload, but card is already removed)
        form.submit();
      }
    }
    hideConfirmModal();
  }

  /**
   * Initialize event listeners
   */
  function initTripDeleteConfirmation() {
    // Get elements when DOM is ready
    confirmModal = document.getElementById('confirmModal');
    confirmMessage = document.getElementById('confirmMessage');
    confirmOk = document.getElementById('confirmOk');
    confirmCancel = document.getElementById('confirmCancel');

    // Only set up event listeners if elements exist
    if (confirmOk) {
      confirmOk.addEventListener('click', handleConfirmOk);
    }

    if (confirmCancel) {
      confirmCancel.addEventListener('click', hideConfirmModal);
    }

    // Close modal when clicking outside
    if (confirmModal) {
      confirmModal.addEventListener('click', function(e) {
        if (e.target === confirmModal) {
          hideConfirmModal();
        }
      });
    }

    // Handle delete button clicks using data attributes
    document.addEventListener('click', function(e) {
      if (e.target.classList.contains('btn-delete-small')) {
        const tripId = e.target.getAttribute('data-trip-id');
        const destination = e.target.getAttribute('data-destination');
        if (tripId && destination) {
          confirmDelete(tripId, destination);
        }
      }
    });
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTripDeleteConfirmation);
  } else {
    initTripDeleteConfirmation();
  }

  // Export function to window for use in other scripts if needed
  window.confirmDeleteTrip = confirmDelete;

})();

