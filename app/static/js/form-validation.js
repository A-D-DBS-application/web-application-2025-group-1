/**
 * Form Validation - Handles common form validation patterns
 * Supports inline error messages and date validation
 */

(function() {
  'use strict';

  /**
   * Show inline error message
   */
  function showError(errorElementId, message, duration = 5000) {
    const errorEl = document.getElementById(errorElementId);
    if (!errorEl) return;

    errorEl.textContent = message;
    errorEl.classList.add('show');

    if (duration > 0) {
      setTimeout(() => {
        errorEl.classList.remove('show');
      }, duration);
    }
  }

  /**
   * Hide inline error message
   */
  function hideError(errorElementId) {
    const errorEl = document.getElementById(errorElementId);
    if (errorEl) {
      errorEl.classList.remove('show');
    }
  }

  /**
   * Validate date range (end date must be after start date)
   */
  function validateDateRange(startDateId, endDateId, errorElementId) {
    const startInput = document.getElementById(startDateId);
    const endInput = document.getElementById(endDateId);

    if (!startInput || !endInput) return true;

    const startDate = startInput.value;
    const endDate = endInput.value;

    if (startDate && endDate) {
      if (new Date(endDate) < new Date(startDate)) {
        showError(errorElementId, 'End date cannot be before start date.');
        endInput.value = '';
        return false;
      }
    }

    hideError(errorElementId);
    return true;
  }

  /**
   * Validate destination selection
   */
  function validateDestination(destinationInputId, errorElementId) {
    const destinationInput = document.getElementById(destinationInputId);
    if (!destinationInput) return true;

    if (!destinationInput.value) {
      showError(errorElementId, 'Please choose a destination.');
      return false;
    }

    hideError(errorElementId);
    return true;
  }

  /**
   * Validate date inputs (both must be filled)
   */
  function validateDates(startDateId, endDateId, errorElementId) {
    const startInput = document.getElementById(startDateId);
    const endInput = document.getElementById(endDateId);

    if (!startInput || !endInput) return true;

    if (!startInput.value || !endInput.value) {
      showError(errorElementId, 'Please select both start and end dates.');
      return false;
    }

    hideError(errorElementId);
    return true;
  }

  /**
   * Initialize date validation for edit_trip.html
   */
  function initEditTripValidation() {
    const form = document.getElementById('editTripForm');
    if (!form) return;

    const startInput = document.getElementById('start_date');
    const endInput = document.getElementById('end_date');
    const dateError = document.getElementById('dateError');
    const destinationError = document.getElementById('destinationError');
    const destinationInput = document.getElementById('destinationInput');

    if (!startInput || !endInput) return;

    // Date picker logic - set min date for end date
    if (startInput) {
      startInput.addEventListener('change', function() {
        if (startInput.value) {
          endInput.min = startInput.value;
          if (endInput.value && endInput.value < startInput.value) {
            endInput.value = '';
          }
        }
      });
    }

    // Auto-fill end date when focusing
    if (endInput) {
      endInput.addEventListener('focus', function() {
        if (startInput.value && !endInput.value) {
          const startDate = new Date(startInput.value);
          startDate.setDate(startDate.getDate() + 1);
          const nextDay = startDate.toISOString().split('T')[0];
          endInput.value = nextDay;
        }
      });
    }

    // Validate date range on change
    if (endInput) {
      endInput.addEventListener('change', function() {
        validateDateRange('start_date', 'end_date', 'dateError');
      });
    }

    // Form submit validation
    form.addEventListener('submit', function(e) {
      if (!validateDestination('destinationInput', 'destinationError')) {
        e.preventDefault();
        return;
      }

      if (!validateDates('start_date', 'end_date', 'dateError')) {
        e.preventDefault();
        return;
      }
    });
  }

  /**
   * Initialize date validation for trips.html
   */
  function initTripsValidation() {
    const form = document.getElementById('createTripForm');
    if (!form) return;

    const startInput = document.getElementById('start_date');
    const endInput = document.getElementById('end_date');
    const dateError = document.getElementById('dateError');
    const destinationError = document.getElementById('destinationError');
    const destinationInput = document.getElementById('destinationInput');

    if (!startInput || !endInput) return;

    // Date validation
    if (endInput) {
      endInput.addEventListener('change', function() {
        validateDateRange('start_date', 'end_date', 'dateError');
      });
    }

    // Form submit validation (if form exists)
    if (form) {
      form.addEventListener('submit', function(e) {
        if (destinationInput && !validateDestination('destinationInput', 'destinationError')) {
          e.preventDefault();
          return;
        }

        if (!validateDates('start_date', 'end_date', 'dateError')) {
          e.preventDefault();
          return;
        }
      });
    }
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      initEditTripValidation();
      initTripsValidation();
    });
  } else {
    initEditTripValidation();
    initTripsValidation();
  }

  // Export functions for use in other scripts
  window.formValidation = {
    showError: showError,
    hideError: hideError,
    validateDateRange: validateDateRange,
    validateDestination: validateDestination,
    validateDates: validateDates
  };

})();

