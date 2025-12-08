/**
 * Create Trip Wizard - Handles multi-step wizard for creating trips
 * Specific to create_trip.html
 */

(function() {
  'use strict';

  // Wizard state
  let currentStep = 1;
  const totalSteps = 6;
  let travellers = [];
  let selectedDestination = '';
  let requiredActivities = new Set();
  let excludedActivities = new Set();
  let allActivities = [];

  /**
   * Load activities data from page
   */
  function loadActivitiesData() {
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
  }

  /**
   * Update progress bar and step indicators
   */
  function updateProgress() {
    // Calculate progress
    let progress;
    if (currentStep === totalSteps) {
      progress = 100;
    } else {
      progress = ((currentStep - 1) / (totalSteps - 1)) * 100;
    }
    
    const progressFill = document.getElementById('progressFill');
    if (progressFill) {
      progressFill.style.width = progress + '%';
    }
    
    // Update step indicators
    const steps = document.querySelectorAll('.wizard-step');
    steps.forEach((step) => {
      const stepNum = parseInt(step.getAttribute('data-step'), 10);
      const circle = step.querySelector('.wizard-step-circle');
      
      if (!stepNum || isNaN(stepNum)) return;
      
      // Reset classes
      step.className = 'wizard-step';
      if (circle) {
        circle.className = 'wizard-step-circle';
      }
      
      if (stepNum < currentStep) {
        // Completed steps
        step.className = 'wizard-step completed';
        if (circle) {
          circle.className = 'wizard-step-circle completed';
        }
      } else if (stepNum === currentStep) {
        // Current active step
        step.className = 'wizard-step active';
        if (circle) {
          circle.className = 'wizard-step-circle active';
        }
      }
    });
  }

  /**
   * Change step (next or previous)
   */
  function changeStep(direction) {
    if (direction > 0) {
      if (!validateStep(currentStep)) return;
      // Prepare data before moving to next step
      if (currentStep === 5) {
        if (window.prepareActivities) {
          window.prepareActivities();
        }
      }
    }
    
    if (direction > 0 && currentStep < totalSteps) {
      currentStep++;
    } else if (direction < 0 && currentStep > 1) {
      currentStep--;
    }
    
    showStep(currentStep);
    
    // Force update progress again after DOM updates
    setTimeout(() => {
      updateProgress();
    }, 10);
  }

  /**
   * Validate current step before proceeding
   */
  function validateStep(step) {
    if (step === 1) {
      // Check both the local variable and the input field
      const destinationInput = document.getElementById('destination');
      const destinationValue = destinationInput ? destinationInput.value : '';
      
      // Sync local variable with input field value
      if (destinationValue && destinationValue !== selectedDestination) {
        selectedDestination = destinationValue;
        window.selectedDestination = selectedDestination;
      }
      
      if (!selectedDestination && !destinationValue) {
        if (window.showCustomModal) {
          window.showCustomModal('Please select a destination');
        }
        return false;
      }
      
      // Ensure local variable is set
      if (!selectedDestination && destinationValue) {
        selectedDestination = destinationValue;
        window.selectedDestination = selectedDestination;
      }
    } else if (step === 2) {
      const startDate = document.getElementById('start_date');
      const endDate = document.getElementById('end_date');
      if (!startDate || !endDate || !startDate.value || !endDate.value) {
        if (window.showCustomModal) {
          window.showCustomModal('Please select both start and end dates using the calendar');
        }
        // Open calendar if dates not selected
        if (window.dateRangePicker && window.dateRangePicker.open) {
          window.dateRangePicker.open();
        } else {
          // Fallback: open calendar overlay directly
          const calendarOverlay = document.getElementById('calendarOverlay');
          if (calendarOverlay) {
            calendarOverlay.classList.add('show');
          }
        }
        return false;
      }
      if (new Date(endDate.value) < new Date(startDate.value)) {
        if (window.showCustomModal) {
          window.showCustomModal('End date cannot be before start date');
        }
        return false;
      }
    } else if (step === 3) {
      if (travellers.length === 0) {
        if (window.showCustomModal) {
          window.showCustomModal('Please add at least one traveller before continuing');
        }
        return false;
      }
    }
    return true;
  }

  /**
   * Show specific step
   */
  function showStep(step) {
    document.querySelectorAll('.form-step').forEach(s => s.classList.remove('active'));
    const stepEl = document.getElementById('step' + step);
    if (stepEl) {
      stepEl.classList.add('active');
    }
    
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');
    
    if (prevBtn) {
      prevBtn.style.display = step === 1 ? 'none' : 'inline-flex';
    }
    if (nextBtn) {
      nextBtn.style.display = step === totalSteps ? 'none' : 'inline-flex';
    }
    if (submitBtn) {
      submitBtn.style.display = step === totalSteps ? 'inline-flex' : 'none';
    }
    
    if (step === 5) {
      // Load activities when reaching step 5
      if (window.loadActivities) {
        window.loadActivities();
      }
    }
    
    if (step === 6) {
      // Prepare overview when reaching step 6
      if (window.prepareOverview) {
        window.prepareOverview();
      }
    }
    
    updateProgress();
  }

  /**
   * Add traveller
   */
  function addTraveller() {
    const nameEl = document.getElementById('new_traveller_name');
    const birthDateEl = document.getElementById('new_traveller_birth_date');
    const fitnessEl = document.getElementById('new_traveller_fitness');
    
    if (!nameEl || !birthDateEl) return;
    
    const name = nameEl.value.trim();
    const birthDate = birthDateEl.value;
    const fitness = fitnessEl ? fitnessEl.value : '';
    
    if (!name || !birthDate) {
      if (window.showCustomModal) {
        window.showCustomModal('Please enter name and birth date');
      }
      return;
    }
    
    travellers.push({ name, birthDate, fitness });
    renderTravellers();
    
    // Clear form and close the add traveller section
    nameEl.value = '';
    birthDateEl.value = '';
    if (fitnessEl) {
      fitnessEl.value = '';
    }
    
    // Close the add traveller form after adding
    const form = document.getElementById('addTravellerForm');
    const arrow = document.getElementById('addTravellerArrow');
    if (form && arrow) {
      form.style.display = 'none';
      arrow.textContent = '▼';
    }
  }

  /**
   * Remove traveller
   */
  function removeTraveller(index) {
    travellers.splice(index, 1);
    renderTravellers();
  }

  /**
   * Render travellers list
   */
  function renderTravellers() {
    const list = document.getElementById('travellerList');
    if (!list) return;
    
    list.innerHTML = '';
    
    if (travellers.length === 0) {
      list.innerHTML = '<div class="empty-travellers"><span>👤</span> No travellers added yet</div>';
      return;
    }
    
    travellers.forEach((traveller, index) => {
      const item = document.createElement('div');
      item.className = 'traveller-inline-card';
      const firstLetter = traveller.name ? traveller.name.charAt(0).toUpperCase() : '?';
      const fitnessDisplay = traveller.fitness || '-';
      item.innerHTML = `
        <div class="traveller-inline-header">
          <div class="traveller-avatar-small">${firstLetter}</div>
          <span class="traveller-inline-name">${traveller.name}</span>
          <button type="button" class="btn-icon-delete" onclick="window.createTripWizard.removeTraveller(${index})" title="Remove traveller">✕</button>
        </div>
        <div class="traveller-inline-fields">
          <div class="traveller-field">
            <label>Name</label>
            <input type="text" value="${traveller.name}" readonly>
          </div>
          <div class="traveller-field">
            <label>Birth Date</label>
            <input type="date" value="${traveller.birthDate}" readonly>
          </div>
          <div class="traveller-field">
            <label>Fitness</label>
            <input type="text" value="${fitnessDisplay}" readonly>
          </div>
        </div>
      `;
      list.appendChild(item);
    });
  }
  
  /**
   * Toggle add traveller form
   */
  function toggleAddTraveller() {
    const form = document.getElementById('addTravellerForm');
    const arrow = document.getElementById('addTravellerArrow');
    if (!form || !arrow) return;
    
    if (form.style.display === 'none') {
      form.style.display = 'block';
      arrow.textContent = '▲';
    } else {
      form.style.display = 'none';
      arrow.textContent = '▼';
    }
  }

  /**
   * Prepare overview (step 6)
   */
  function prepareOverview() {
    const content = document.getElementById('overviewContent');
    if (!content) return;
    
    const startDate = document.getElementById('start_date');
    const endDate = document.getElementById('end_date');
    const startDateValue = startDate ? startDate.value : '';
    const endDateValue = endDate ? endDate.value : '';
    
    // Format dates
    function formatDate(dateStr) {
      if (!dateStr) return 'Not set';
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    }
    
    // Calculate trip duration
    function calculateDuration(start, end) {
      if (!start || !end) return '';
      const startDate = new Date(start);
      const endDate = new Date(end);
      const diffTime = Math.abs(endDate - startDate);
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
      return `${diffDays} day${diffDays !== 1 ? 's' : ''}`;
    }
    
    content.innerHTML = `
      <div class="overview-item primary">
        <div class="overview-icon">📍</div>
        <div style="flex: 1;">
          <div class="overview-label">Destination</div>
          <div class="overview-value">${selectedDestination || 'Not selected'}</div>
        </div>
      </div>
      <div class="overview-item gold">
        <div class="overview-icon">📅</div>
        <div style="flex: 1;">
          <div class="overview-label">Travel Dates</div>
          <div class="overview-value">${formatDate(startDateValue)} - ${formatDate(endDateValue)}</div>
          <div style="font-size: 0.75rem; color: var(--muted-foreground); margin-top: 0.25rem;">
            Duration: ${calculateDuration(startDateValue, endDateValue)}
          </div>
        </div>
      </div>
    `;
    
    // Add travellers details
    const travellersDiv = document.createElement('div');
    travellersDiv.className = 'overview-item teal';
    if (travellers.length > 0) {
      const travellersList = travellers.map((t) => {
        const birthDate = new Date(t.birthDate);
        const today = new Date();
        const age = today.getFullYear() - birthDate.getFullYear() - 
          (today.getMonth() < birthDate.getMonth() || 
           (today.getMonth() === birthDate.getMonth() && today.getDate() < birthDate.getDate()) ? 1 : 0);
        return `
          <div style="padding: 0.5rem 0; border-bottom: 1px solid var(--border);">
            <div style="font-weight: 600;">${t.name}</div>
            <div style="font-size: 0.75rem; color: var(--muted-foreground);">
              Age: ${age} years • Fitness: ${t.fitness || 'Not specified'}
            </div>
          </div>
        `;
      }).join('');
      travellersDiv.innerHTML = `
        <div class="overview-icon">👥</div>
        <div style="flex: 1;">
          <div class="overview-label">Travellers (${travellers.length})</div>
          <div style="margin-top: 0.5rem;">
            ${travellersList}
          </div>
        </div>
      `;
    } else {
      travellersDiv.innerHTML = `
        <div class="overview-icon">👥</div>
        <div style="flex: 1;">
          <div class="overview-label">Travellers</div>
          <div class="overview-value">No travellers added</div>
        </div>
      `;
    }
    content.appendChild(travellersDiv);
    
    // Add preferences details
    const prefsDiv = document.createElement('div');
    prefsDiv.className = 'overview-item';
    prefsDiv.style.background = 'hsla(35, 55%, 90%, 0.5)';
    
    // Build preference map from template data
    let preferenceMap = {};
    try {
      const activityTypesDataEl = document.getElementById('activity-types-data');
      if (activityTypesDataEl) {
        const activityTypes = JSON.parse(activityTypesDataEl.textContent);
        activityTypes.forEach(function(pref) {
          preferenceMap[pref.value] = { icon: pref.icon, label: pref.label };
        });
      }
    } catch (e) {
      console.warn('Could not load activity types:', e);
      preferenceMap = {
        'CULTURE': { icon: '🏛️', label: 'Culture' },
        'ADVENTURE': { icon: '🧗‍♂️', label: 'Adventure' },
        'RELAXATION': { icon: '🧘‍♀️', label: 'Relaxation' },
        'NATURE': { icon: '🌿', label: 'Nature' }
      };
    }
    
    const preferencesInput = document.getElementById('preferences');
    const mainPreference = preferencesInput ? preferencesInput.value : '';
    const preferenceInfo = preferenceMap[mainPreference] || { icon: '⭐', label: 'Not set' };
    
    // Helper function to convert slider value to text
    function valueToText(v) {
      const val = parseInt(v, 10);
      switch (val) {
        case 1: return 'Not my thing';
        case 2: return 'Maybe a little';
        case 3: return 'I could try';
        case 4: return 'Sounds fun!';
        case 5: return 'Absolutely yes!';
        default: return 'I could try';
      }
    }
    
    // Get all preference scores
    const prefScores = [];
    document.querySelectorAll('.interest-slider').forEach(slider => {
      const key = slider.getAttribute('data-key');
      const value = parseInt(slider.value, 10);
      const prefInfo = preferenceMap[key];
      if (prefInfo) {
        prefScores.push(`${prefInfo.icon} ${prefInfo.label}: ${valueToText(value)}`);
      }
    });
    
    prefsDiv.innerHTML = `
      <div class="overview-icon">⭐</div>
      <div style="flex: 1;">
        <div class="overview-label">Main Preference</div>
        <div class="overview-value">${preferenceInfo.icon} ${preferenceInfo.label}</div>
        <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid var(--border);">
          <div style="font-size: 0.75rem; font-weight: 600; margin-bottom: 0.5rem; color: var(--muted-foreground);">
            All Preferences:
          </div>
          ${prefScores.map(score => `
            <div style="font-size: 0.75rem; color: var(--muted-foreground); padding: 0.25rem 0;">
              ${score}
            </div>
          `).join('')}
        </div>
      </div>
    `;
    content.appendChild(prefsDiv);
    
    // Add activities details
    const requiredInput = document.getElementById('required_activity_ids');
    const excludedInput = document.getElementById('excluded_activity_ids');
    const requiredIds = requiredInput && requiredInput.value ? requiredInput.value.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id)) : [];
    const excludedIds = excludedInput && excludedInput.value ? excludedInput.value.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id)) : [];
    
    if (requiredIds.length > 0 || excludedIds.length > 0) {
      const activitiesDiv = document.createElement('div');
      activitiesDiv.className = 'overview-item';
      activitiesDiv.style.background = 'hsla(168, 55%, 40%, 0.1)';
      
      const requiredList = requiredIds.map(id => {
        const activity = allActivities.find(a => a.activity_type_id == id);
        return activity ? activity.name : `Activity #${id}`;
      });
      
      const excludedList = excludedIds.map(id => {
        const activity = allActivities.find(a => a.activity_type_id == id);
        return activity ? activity.name : `Activity #${id}`;
      });
      
      let activitiesHTML = '';
      if (requiredList.length > 0) {
        activitiesHTML += `
          <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid var(--border);">
            <div style="font-size: 0.75rem; font-weight: 600; margin-bottom: 0.5rem; color: var(--teal);">
              ✓ Must Include (${requiredList.length}):
            </div>
            ${requiredList.map(name => `
              <div style="font-size: 0.75rem; color: var(--muted-foreground); padding: 0.25rem 0;">
                • ${name}
              </div>
            `).join('')}
          </div>
        `;
      }
      
      if (excludedList.length > 0) {
        activitiesHTML += `
          <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid var(--border);">
            <div style="font-size: 0.75rem; font-weight: 600; margin-bottom: 0.5rem; color: hsl(0, 72%, 55%);">
              ✗ Must Exclude (${excludedList.length}):
            </div>
            ${excludedList.map(name => `
              <div style="font-size: 0.75rem; color: var(--muted-foreground); padding: 0.25rem 0;">
                • ${name}
              </div>
            `).join('')}
          </div>
        `;
      }
      
      activitiesDiv.innerHTML = `
        <div class="overview-icon">🎯</div>
        <div style="flex: 1;">
          <div class="overview-label">Activity Selection</div>
          <div class="overview-value">
            ${requiredList.length} must include, ${excludedList.length} must exclude
          </div>
          ${activitiesHTML}
        </div>
      `;
      content.appendChild(activitiesDiv);
    } else {
      const activitiesDiv = document.createElement('div');
      activitiesDiv.className = 'overview-item';
      activitiesDiv.style.background = 'hsla(168, 55%, 40%, 0.1)';
      activitiesDiv.innerHTML = `
        <div class="overview-icon">🎯</div>
        <div style="flex: 1;">
          <div class="overview-label">Activity Selection</div>
          <div class="overview-value">No specific requirements set</div>
        </div>
      `;
      content.appendChild(activitiesDiv);
    }
  }

  /**
   * Initialize wizard
   */
  function initWizard() {
    // Load activities data
    loadActivitiesData();
    
    // Make selectedDestination and travellers available globally for activity-loader.js
    window.selectedDestination = selectedDestination;
    window.travellers = travellers;
    
    // Watch for destination changes
    const destinationInput = document.getElementById('destination');
    if (destinationInput) {
      // Watch for change events
      destinationInput.addEventListener('change', function() {
        selectedDestination = this.value;
        window.selectedDestination = selectedDestination;
      });
      
      // Watch for input events (from destination-cards.js)
      destinationInput.addEventListener('input', function() {
        if (this.value && this.value !== selectedDestination) {
          selectedDestination = this.value;
          window.selectedDestination = selectedDestination;
        }
      });
      
      // Watch for attribute changes (value attribute changes)
      const observer = new MutationObserver(() => {
        if (destinationInput.value && destinationInput.value !== selectedDestination) {
          selectedDestination = destinationInput.value;
          window.selectedDestination = selectedDestination;
        }
      });
      observer.observe(destinationInput, { attributes: true, attributeFilter: ['value'] });
    }
    
    // Form submission
    const form = document.getElementById('tripForm');
    if (form) {
      form.addEventListener('submit', function(e) {
        if (window.prepareActivities) {
          window.prepareActivities();
        }
      });
    }
    
    // Initial progress update
    updateProgress();
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initWizard);
  } else {
    initWizard();
  }

  // Export functions to window
  window.createTripWizard = {
    changeStep: changeStep,
    addTraveller: addTraveller,
    removeTraveller: removeTraveller,
    prepareOverview: prepareOverview,
    toggleAddTraveller: toggleAddTraveller,
    getTravellers: () => travellers,
    setTravellers: (t) => { travellers = t; window.travellers = t; },
    getSelectedDestination: () => selectedDestination,
    setSelectedDestination: (d) => { selectedDestination = d; window.selectedDestination = d; }
  };

  // Export for onclick handlers
  window.changeStep = changeStep;
  window.addTraveller = addTraveller;
  window.prepareOverview = prepareOverview;
  window.toggleAddTraveller = toggleAddTraveller;

})();

