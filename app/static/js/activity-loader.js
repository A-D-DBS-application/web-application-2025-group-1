/**
 * Activity Loader - Handles loading and displaying activities for trip forms
 * Supports both create_trip.html and edit_trip.html
 */

(function() {
  'use strict';

  // Global state
  let activityLoaderState = {
    allActivities: [],
    requiredActivities: new Set(),
    excludedActivities: new Set(),
    travellers: [],
    destination: '',
    initialized: false
  };

  /**
   * Calculate age from birth date
   */
  function calculateAge(birthDate) {
    if (!birthDate) return null;
    const birth = new Date(birthDate);
    const today = new Date();
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
      age--;
    }
    return age;
  }

  /**
   * Get min and max age from travellers
   */
  function getTravellerAges(travellers) {
    if (!travellers || travellers.length === 0) {
      return { minAge: 0, maxAge: 120 };
    }

    const ages = travellers
      .map(t => {
        // Support both birthDate and birth_date formats
        const birthDate = t.birthDate || t.birth_date;
        return calculateAge(birthDate);
      })
      .filter(age => age !== null);

    if (ages.length === 0) {
      return { minAge: 0, maxAge: 120 };
    }

    return {
      minAge: Math.min(...ages),
      maxAge: Math.max(...ages)
    };
  }

  /**
   * Filter activities by destination and age suitability
   */
  function filterActivities(activities, destination, travellers) {
    if (!destination) {
      return [];
    }

    // Filter by destination
    const destinationActivities = activities.filter(a => {
      if (!a.destination) return false;
      return a.destination.toLowerCase() === destination.toLowerCase();
    });

    if (destinationActivities.length === 0) {
      return [];
    }

    // Filter by age suitability
    const { minAge, maxAge } = getTravellerAges(travellers);
    
    const suitableActivities = destinationActivities.filter(a => {
      // Check minimum age
      if (a.min_age && maxAge < a.min_age) {
        return false;
      }
      // Check maximum age
      if (a.max_age && minAge > a.max_age) {
        return false;
      }
      return true;
    });

    return suitableActivities;
  }

  /**
   * Render activity item HTML
   */
  function renderActivityItem(activity, status) {
    const activityId = activity.activity_type_id;
    const statusClass = status !== 'neutral' ? status : '';
    
    return `
      <div class="activity-item ${statusClass}" data-activity-id="${activityId}">
        <div class="activity-info">
          <div class="activity-name">${activity.name || 'Unnamed Activity'}</div>
          <div class="activity-details">
            ${activity.description || ''}${activity.min_age ? ' • Min age: ' + activity.min_age : ''}${activity.max_age ? ', Max age: ' + activity.max_age : ''}
          </div>
        </div>
        <div class="activity-actions">
          <button type="button" class="btn-activity ${status === 'required' ? 'required' : 'neutral'}" data-action="required">
            ${status === 'required' ? '✓ Must Include' : 'Must Include'}
          </button>
          <button type="button" class="btn-activity ${status === 'excluded' ? 'excluded' : 'neutral'}" data-action="excluded">
            ${status === 'excluded' ? '✕ Must Exclude' : 'Must Exclude'}
          </button>
        </div>
      </div>
    `;
  }

  /**
   * Load and display activities
   */
  function loadActivities(config) {
    const {
      activityListId = 'activityList',
      destination,
      travellers = [],
      allActivities = [],
      requiredActivities = new Set(),
      excludedActivities = new Set()
    } = config;

    const activityListEl = document.getElementById(activityListId);
    if (!activityListEl) {
      console.warn('Activity list element not found:', activityListId);
      return;
    }

    // Check destination
    if (!destination) {
      activityListEl.innerHTML = '<p class="empty-state">Please select a destination first</p>';
      return;
    }

    // Check activities data
    if (!allActivities || allActivities.length === 0) {
      activityListEl.innerHTML = '<p class="empty-state">No activities available. Please refresh the page.</p>';
      return;
    }

    // Filter activities
    const suitableActivities = filterActivities(allActivities, destination, travellers);

    if (suitableActivities.length === 0) {
      const destinationMatches = allActivities.filter(a => 
        a.destination && a.destination.toLowerCase() === destination.toLowerCase()
      );
      
      const { minAge, maxAge } = getTravellerAges(travellers);
      const message = destinationMatches.length > 0 
        ? `No activities found matching traveller ages (${minAge}-${maxAge} years). Found ${destinationMatches.length} activities for ${destination} but none match age requirements.`
        : `No activities found for destination "${destination}".`;
      
      activityListEl.innerHTML = '<p class="empty-state">' + message + '</p>';
      return;
    }

    // Render activities
    activityListEl.innerHTML = suitableActivities.map(activity => {
      const activityId = activity.activity_type_id;
      const status = requiredActivities.has(activityId) ? 'required' : 
                    excludedActivities.has(activityId) ? 'excluded' : 'neutral';
      return renderActivityItem(activity, status);
    }).join('');

    // Add event listeners
    activityListEl.querySelectorAll('.btn-activity').forEach(btn => {
      btn.addEventListener('click', function() {
        const activityId = parseInt(this.closest('.activity-item').dataset.activityId);
        const action = this.dataset.action;
        toggleActivity(activityId, action, config);
      });
    });
  }

  /**
   * Toggle activity status (required/excluded)
   */
  function toggleActivity(activityId, action, config) {
    const {
      requiredActivities = new Set(),
      excludedActivities = new Set(),
      onToggle
    } = config;

    if (action === 'required') {
      if (requiredActivities.has(activityId)) {
        requiredActivities.delete(activityId);
      } else {
        requiredActivities.add(activityId);
        excludedActivities.delete(activityId);
      }
    } else {
      if (excludedActivities.has(activityId)) {
        excludedActivities.delete(activityId);
      } else {
        excludedActivities.add(activityId);
        requiredActivities.delete(activityId);
      }
    }

    // Update hidden inputs
    if (config.requiredInputId) {
      const requiredInput = document.getElementById(config.requiredInputId);
      if (requiredInput) {
        requiredInput.value = Array.from(requiredActivities).join(',');
      }
    }
    if (config.excludedInputId) {
      const excludedInput = document.getElementById(config.excludedInputId);
      if (excludedInput) {
        excludedInput.value = Array.from(excludedActivities).join(',');
      }
    }

    // Reload activities to update UI
    loadActivities(config);

    // Call custom callback if provided
    if (onToggle && typeof onToggle === 'function') {
      onToggle(activityId, action, requiredActivities, excludedActivities);
    }
  }

  /**
   * Initialize activity loader for create_trip.html
   */
  function initCreateTripLoader() {
    const activityListEl = document.getElementById('activityList');
    if (!activityListEl) return;

    // Check if we're on create_trip page
    const form = document.getElementById('tripForm') || document.getElementById('createTripForm');
    if (!form) return;

    // Get activities data
    let allActivities = [];
    try {
      const activitiesDataEl = document.getElementById('activities-data');
      if (activitiesDataEl) {
        allActivities = JSON.parse(activitiesDataEl.textContent);
        if (!Array.isArray(allActivities)) {
          allActivities = [];
        }
      }
    } catch (e) {
      console.warn('Could not load activities:', e);
      allActivities = [];
    }

    // Get required/excluded inputs
    const requiredInput = document.getElementById('required_activity_ids');
    const excludedInput = document.getElementById('excluded_activity_ids');

    // Initialize sets from existing values
    const requiredActivities = new Set();
    const excludedActivities = new Set();

    if (requiredInput && requiredInput.value) {
      requiredInput.value.split(',').forEach(id => {
        const numId = parseInt(id.trim());
        if (!isNaN(numId)) requiredActivities.add(numId);
      });
    }
    if (excludedInput && excludedInput.value) {
      excludedInput.value.split(',').forEach(id => {
        const numId = parseInt(id.trim());
        if (!isNaN(numId)) excludedActivities.add(numId);
      });
    }

    // Export functions to window for create_trip.html
    window.loadActivities = function() {
      const selectedDestination = window.selectedDestination || '';
      const travellers = window.travellers || [];
      
      loadActivities({
        activityListId: 'activityList',
        destination: selectedDestination,
        travellers: travellers,
        allActivities: allActivities,
        requiredActivities: requiredActivities,
        excludedActivities: excludedActivities,
        requiredInputId: 'required_activity_ids',
        excludedInputId: 'excluded_activity_ids'
      });
    };

    window.toggleActivity = function(activityId, type) {
      toggleActivity(activityId, type, {
        requiredActivities: requiredActivities,
        excludedActivities: excludedActivities,
        requiredInputId: 'required_activity_ids',
        excludedInputId: 'excluded_activity_ids',
        onToggle: () => {
          // Reload after toggle
          window.loadActivities();
        }
      });
    };

    window.prepareActivities = function() {
      if (requiredInput) {
        requiredInput.value = Array.from(requiredActivities).join(',');
      }
      if (excludedInput) {
        excludedInput.value = Array.from(excludedActivities).join(',');
      }
    };
  }

  /**
   * Initialize activity loader for edit_trip.html
   */
  function initEditTripLoader() {
    const activityListEl = document.getElementById('activityList');
    if (!activityListEl) return;

    // Check if we're on edit_trip page
    const form = document.getElementById('editTripForm');
    if (!form) return;

    // Get activities data
    let allActivities = [];
    try {
      const activitiesDataEl = document.getElementById('activities-data');
      if (activitiesDataEl) {
        const activitiesData = JSON.parse(activitiesDataEl.textContent);
        allActivities = Array.isArray(activitiesData) ? activitiesData : [];
      }
    } catch (e) {
      console.warn('Could not load activities:', e);
      allActivities = [];
    }

    // Get travellers data
    let travellers = [];
    try {
      const travellersDataEl = document.getElementById('travellers-data');
      if (travellersDataEl) {
        travellers = JSON.parse(travellersDataEl.textContent);
        if (!Array.isArray(travellers)) {
          travellers = [];
        }
      }
    } catch (e) {
      console.warn('Could not load travellers:', e);
      travellers = [];
    }

    // Get inputs
    const destinationInput = document.getElementById('destinationInput');
    const requiredInput = document.getElementById('required_activity_ids');
    const excludedInput = document.getElementById('excluded_activity_ids');

    // Initialize sets from existing values
    const requiredActivities = new Set();
    const excludedActivities = new Set();

    if (requiredInput && requiredInput.value) {
      requiredInput.value.split(',').forEach(id => {
        const numId = parseInt(id.trim());
        if (!isNaN(numId)) requiredActivities.add(numId);
      });
    }
    if (excludedInput && excludedInput.value) {
      excludedInput.value.split(',').forEach(id => {
        const numId = parseInt(id.trim());
        if (!isNaN(numId)) excludedActivities.add(numId);
      });
    }

    // Load activities function
    function loadActivitiesForEdit() {
      const destination = destinationInput ? destinationInput.value : '';
      
      loadActivities({
        activityListId: 'activityList',
        destination: destination,
        travellers: travellers,
        allActivities: allActivities,
        requiredActivities: requiredActivities,
        excludedActivities: excludedActivities,
        requiredInputId: 'required_activity_ids',
        excludedInputId: 'excluded_activity_ids'
      });
    }

    // Listen for destination changes
    if (destinationInput) {
      // Listen to destination card clicks (they update the hidden input)
      const destinationCards = document.querySelectorAll('.destination-card');
      destinationCards.forEach(card => {
        card.addEventListener('click', function() {
          setTimeout(loadActivitiesForEdit, 100);
        });
      });

      // Also listen to input changes
      destinationInput.addEventListener('change', loadActivitiesForEdit);
    }

    // Try to load activities on initialization
    function tryLoadActivities() {
      if (!activityListEl || !destinationInput) return;
      if (!destinationInput.value) {
        activityListEl.innerHTML = '<p class="empty-state">Please select a destination first</p>';
        return;
      }
      if (allActivities.length === 0) {
        activityListEl.innerHTML = '<p class="empty-state">No activities available. Please refresh the page.</p>';
        return;
      }
      loadActivitiesForEdit();
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function() {
        setTimeout(tryLoadActivities, 100);
      });
    } else {
      setTimeout(tryLoadActivities, 100);
    }

    // Fallback after delay
    setTimeout(tryLoadActivities, 1000);
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      initCreateTripLoader();
      initEditTripLoader();
    });
  } else {
    initCreateTripLoader();
    initEditTripLoader();
  }

})();

