/**
 * Activity Sliders - Handles preference/interest sliders for activity forms
 * Supports both .activity-slider/.pref-tag and .interest-slider/.interest-tag
 */

(function() {
  'use strict';

  // Configuration for different slider types
  const sliderConfigs = {
    activity: {
      sliderSelector: '.activity-slider',
      tagSelector: '.pref-tag',
      labels: {
        1: 'Not really',
        2: 'A little bit',
        3: 'Nice extra',
        4: 'Great match',
        5: 'Perfect fit'
      }
    },
    interest: {
      sliderSelector: '.interest-slider',
      tagSelector: '.interest-tag',
      labels: {
        1: 'Not my thing',
        2: 'Maybe a little',
        3: 'I could try',
        4: 'Sounds fun!',
        5: 'Absolutely yes!'
      }
    }
  };

  /**
   * Convert slider value to text label
   */
  function valueToText(value, labels) {
    const val = parseInt(value, 10);
    return labels[val] || '';
  }

  /**
   * Update slider visual fill (gradient background)
   */
  function updateSliderFill(slider) {
    const min = parseInt(slider.min || 0, 10);
    const max = parseInt(slider.max || 100, 10);
    const val = parseInt(slider.value, 10);
    const pct = ((val - min) / (max - min)) * 100;
    slider.style.background =
      'linear-gradient(to right, hsl(168, 55%, 40%) 0%, hsl(168, 55%, 40%) ' + pct + '%, hsl(35, 25%, 88%) ' + pct + '%, hsl(35, 25%, 88%) 100%)';
  }

  /**
   * Find tag element - supports both data-for attribute and id="tag-..." pattern
   */
  function findTagElement(key, tagSelector) {
    // Try data-for attribute first
    let tag = document.querySelector(tagSelector + '[data-for="' + key + '"]');
    // If not found, try id="tag-{key}" pattern (used in trip templates)
    if (!tag) {
      tag = document.getElementById('tag-' + key);
    }
    return tag;
  }

  /**
   * Initialize sliders for a specific configuration
   */
  function initSliders(config, options = {}) {
    const sliders = Array.from(document.querySelectorAll(config.sliderSelector));
    if (sliders.length === 0) return null;

    const preferenceInputId = options.preferenceInputId;
    const updateOnInput = options.updateOnInput !== false; // Default true

    sliders.forEach(slider => {
      const key = slider.dataset.key || slider.getAttribute('data-key');
      const tag = findTagElement(key, config.tagSelector);
      
      // Initialize slider fill and tag text
      updateSliderFill(slider);
      if (tag) {
        tag.textContent = valueToText(slider.value, config.labels);
      }

      // Add input event listener
      slider.addEventListener('input', () => {
        updateSliderFill(slider);
        if (tag) {
          tag.textContent = valueToText(slider.value, config.labels);
        }
        // Update preference input on each change (for trip templates)
        if (updateOnInput && preferenceInputId) {
          chooseMainPreference(sliders, preferenceInputId);
        }
      });
    });

    return sliders;
  }

  /**
   * Auto-select main type based on highest slider value
   */
  function chooseMainType(sliders, typeInputId) {
    const typeInput = document.getElementById(typeInputId);
    if (!typeInput || !sliders) return;

    let best = null;
    sliders.forEach(slider => {
      const val = parseInt(slider.value, 10);
      const key = slider.dataset.key || slider.getAttribute('data-key');
      if (!best || val > best.value) {
        best = { key: key, value: val };
      }
    });
    if (best) {
      typeInput.value = best.key;
    }
  }

  /**
   * Choose main preference (alias for chooseMainType, used in trip templates)
   */
  function chooseMainPreference(sliders, preferenceInputId) {
    chooseMainType(sliders, preferenceInputId);
  }

  /**
   * Initialize all slider types
   */
  function initAllSliders() {
    // Initialize activity sliders (for activities.html)
    const activitySliders = initSliders(sliderConfigs.activity, { updateOnInput: false });
    if (activitySliders && activitySliders.length > 0) {
      const form = document.getElementById('activityForm');
      if (form) {
        form.addEventListener('submit', () => {
          chooseMainType(activitySliders, 'typeInput');
        });
      }
    }

    // Initialize interest sliders (for edit_activity.html)
    const interestSliders = initSliders(sliderConfigs.interest, { updateOnInput: false });
    if (interestSliders && interestSliders.length > 0) {
      const form = document.getElementById('editActivityForm');
      if (form) {
        form.addEventListener('submit', () => {
          chooseMainType(interestSliders, 'typeInput');
        });
      }
    }

    // Initialize trip preference sliders (for create_trip.html, edit_trip.html, trips.html)
    // These update the preference input on each slider change
    const tripPreferenceInput = document.getElementById('preferences') || document.getElementById('preferencesInput');
    if (tripPreferenceInput) {
      const tripSliders = initSliders(sliderConfigs.interest, {
        preferenceInputId: tripPreferenceInput.id,
        updateOnInput: true
      });
      // Also update on form submit (if form exists)
      if (tripSliders && tripSliders.length > 0) {
        const form = document.getElementById('createTripForm') || 
                     document.getElementById('editTripForm') ||
                     document.querySelector('form');
        if (form) {
          form.addEventListener('submit', () => {
            chooseMainPreference(tripSliders, tripPreferenceInput.id);
          });
        }
        // Initialize immediately
        chooseMainPreference(tripSliders, tripPreferenceInput.id);
      }
    }
  }

  /**
   * Initialize destination buttons (only for activities.html)
   */
  function initDestinationButtons() {
    const destInput = document.getElementById('destinationInput');
    const destBtns = document.querySelectorAll('.dest-btn');
    
    if (!destInput || destBtns.length === 0) return;

    destBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        destBtns.forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        destInput.value = btn.dataset.value;
      });
    });
  }

  /**
   * Initialize file input text display
   */
  function initFileInput(inputId, textId) {
    const pictureInput = document.getElementById(inputId);
    const fileInputText = document.getElementById(textId);
    
    if (pictureInput && fileInputText) {
      pictureInput.addEventListener('change', function(e) {
        if (e.target.files && e.target.files.length > 0) {
          fileInputText.textContent = e.target.files[0].name;
        } else {
          fileInputText.textContent = 'No file chosen';
        }
      });
    }
  }

  /**
   * Toggle Add Activity Form visibility
   */
  let toggleButtonInitialized = false;
  function initToggleAddActivityForm() {
    const btn = document.getElementById('toggleAddActivityBtn');
    if (!btn || toggleButtonInitialized) return;
    
    toggleButtonInitialized = true;

    btn.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      const form = document.getElementById('addActivityForm');
      if (!form) return;
      
      const isHidden = form.style.display === 'none' || form.style.display === '';
      
      if (isHidden) {
        form.style.display = 'block';
        btn.textContent = '✕ Cancel';
        btn.classList.remove('btn-primary');
        btn.classList.add('btn-outline');
      } else {
        form.style.display = 'none';
        btn.textContent = '➕ Add Activity';
        btn.classList.remove('btn-outline');
        btn.classList.add('btn-primary');
      }
    });
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      initAllSliders();
      initDestinationButtons();
      initFileInput('pictureInput', 'fileInputText');
      initFileInput('pictureInputEdit', 'fileInputTextEdit');
      initToggleAddActivityForm();
    });
  } else {
    // DOM already loaded
    initAllSliders();
    initDestinationButtons();
    initFileInput('pictureInput', 'fileInputText');
    initFileInput('pictureInputEdit', 'fileInputTextEdit');
    initToggleAddActivityForm();
  }

  // Export for backwards compatibility (if onclick is used)
  window.toggleAddActivityForm = function() {
    const form = document.getElementById('addActivityForm');
    const btn = document.getElementById('toggleAddActivityBtn');
    
    if (!form || !btn) return;
    
    if (form.style.display === 'none' || form.style.display === '') {
      form.style.display = 'block';
      btn.textContent = '✕ Cancel';
      btn.classList.remove('btn-primary');
      btn.classList.add('btn-outline');
    } else {
      form.style.display = 'none';
      btn.textContent = '➕ Add Activity';
      btn.classList.remove('btn-outline');
      btn.classList.add('btn-primary');
    }
  };

  // Export updatePreferenceTag for create_trip.html (used in oninput attribute)
  window.updatePreferenceTag = function(key, value) {
    const config = sliderConfigs.interest;
    const tag = findTagElement(key, config.tagSelector);
    if (tag) {
      tag.textContent = valueToText(value, config.labels);
    }
    // Update preference input
    const preferenceInput = document.getElementById('preferences') || document.getElementById('preferencesInput');
    if (preferenceInput) {
      const sliders = Array.from(document.querySelectorAll(config.sliderSelector));
      chooseMainPreference(sliders, preferenceInput.id);
    }
  };

})();

