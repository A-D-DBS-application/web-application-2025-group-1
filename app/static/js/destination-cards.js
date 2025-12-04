/**
 * Destination Cards - Handles destination card selection
 * Supports both .destination-card with data-destination and data-value attributes
 */

(function() {
  'use strict';

  /**
   * Initialize destination card selection
   * Supports multiple scenarios:
   * - Cards with data-destination attribute (create_trip.html)
   * - Cards with data-value attribute (edit_trip.html, trips.html)
   */
  function initDestinationCards() {
    const cards = document.querySelectorAll('.destination-card');
    if (cards.length === 0) return;

    cards.forEach(card => {
      // Remove any existing listeners by cloning
      const newCard = card.cloneNode(true);
      card.parentNode.replaceChild(newCard, card);

      newCard.addEventListener('click', function() {
        // Remove selected class from all cards
        document.querySelectorAll('.destination-card').forEach(c => {
          c.classList.remove('selected');
        });

        // Add selected class to clicked card
        this.classList.add('selected');

        // Update destination input
        // Try data-destination first (for create_trip.html)
        const destination = this.dataset.destination || this.getAttribute('data-destination');
        if (destination) {
          const destinationInput = document.getElementById('destination');
          if (destinationInput) {
            destinationInput.value = destination;
            // Trigger change and input events to notify other scripts
            destinationInput.dispatchEvent(new Event('change', { bubbles: true }));
            destinationInput.dispatchEvent(new Event('input', { bubbles: true }));
          }
          // Always update window.selectedDestination (for create_trip.html)
          if (typeof window !== 'undefined') {
            window.selectedDestination = destination;
          }
        }

        // Try data-value (for edit_trip.html, trips.html)
        const value = this.dataset.value || this.getAttribute('data-value');
        if (value) {
          const destinationInput = document.getElementById('destinationInput');
          if (destinationInput) {
            destinationInput.value = value;
          }
        }
      });
    });
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDestinationCards);
  } else {
    initDestinationCards();
  }

})();

