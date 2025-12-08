/**
 * Itinerary Mapbox - Handles Mapbox map initialization and activity markers
 * Specific to itinerary.html
 */

(function() {
  'use strict';

  // Mapbox access token - should be set via environment variable or config
  // For now, using a placeholder - this should be injected from server-side config
  const MAPBOX_ACCESS_TOKEN = window.MAPBOX_ACCESS_TOKEN || '';

  let map = null;
  const markers = {};
  let currentPopup = null;
  let currentIndex = 0;
  let points = [];
  let activitiesData = [];

  /**
   * Truncate text to max length
   */
  function truncate(text, maxLen) {
    if (!text) return '';
    if (text.length <= maxLen) return text;
    return text.slice(0, maxLen - 3) + '...';
  }

  /**
   * Set active card in sidebar
   */
  function setActiveCard(id) {
    // Alle cards resetten
    document.querySelectorAll('.activity-card').forEach(card => {
      card.classList.remove('active');
    });
    const card = document.getElementById('activity-card-' + id);
    if (card) card.classList.add('active');
  }

  /**
   * Open popup by index
   */
  function openPopupByIndex(index) {
    if (!points.length || !map) return;
    if (index < 0 || index >= points.length) return;
    currentIndex = index;

    const p = points[index];
    const marker = markers[p.id];
    if (!marker) return;

    const lngLat = [p.lng, p.lat];

    // Eventuele vorige popup sluiten
    if (currentPopup) {
      currentPopup.remove();
      currentPopup = null;
    }

    // Map centreren / zoomen
    map.flyTo({
      center: lngLat,
      zoom: 11,
      speed: 0.8,
      offset: [0, -180],
      curve: 1.2,
      essential: true
    });

    // Popup HTML
    const desc = truncate(p.description, 180);

    const popupHTML = `
      <div class="popup-card">
        <div class="popup-header">
          <div>
            <div class="popup-day">Day ${p.day}</div>
            <div class="popup-date">${p.date}</div>
          </div>
          <div class="popup-nav">
            <button id="popup-prev" title="Vorige activiteit">←</button>
            <button id="popup-next" title="Volgende activiteit">→</button>
          </div>
        </div>
        ${p.image ? `
          <div class="popup-image-wrap">
            <img src="${p.image}" alt="${p.name}" onerror="this.parentElement.innerHTML='<div style=\\'text-align: center; padding: 2rem; font-size: 3rem; background: #f0f0f0; border-radius: 0.5rem;\\'>🎯</div>'">
          </div>
        ` : `
          <div class="popup-image-wrap" style="text-align: center; padding: 2rem; font-size: 3rem; background: #f0f0f0; border-radius: 0.5rem;">
            🎯
          </div>
        `}
        <div class="popup-body">
          <div class="popup-title">${p.name}</div>
          <div class="popup-meta-row">
            ${p.duration !== null ? `
              <div class="popup-pill">
                ⏱️ ${p.duration} ${p.duration === 1 ? 'hour' : 'hours'}
              </div>
            ` : ''}
          </div>
          ${desc ? `
            <div class="popup-description">
              ${desc}
            </div>
          ` : ''}
        </div>
      </div>
    `;

    const popup = new mapboxgl.Popup({
      closeOnClick: false,
      offset: 18
    })
    .setLngLat(lngLat)
    .setHTML(popupHTML)
    .addTo(map);

    currentPopup = popup;
    setActiveCard(p.id);

    // Buttons koppelen nadat popup in DOM zit
    setTimeout(() => {
      const prevBtn = document.getElementById('popup-prev');
      const nextBtn = document.getElementById('popup-next');
      if (prevBtn) {
        prevBtn.onclick = (e) => {
          e.stopPropagation();
          const prevIndex = (currentIndex - 1 + points.length) % points.length;
          openPopupByIndex(prevIndex);
        };
      }
      if (nextBtn) {
        nextBtn.onclick = (e) => {
          e.stopPropagation();
          const nextIndex = (currentIndex + 1) % points.length;
          openPopupByIndex(nextIndex);
        };
      }
    }, 0);
  }

  /**
   * Focus on activity by ID
   */
  function focusActivity(id) {
    const idx = points.findIndex(p => p.id === id);
    if (idx === -1) return;
    openPopupByIndex(idx);
  }

  /**
   * Load activities data from page
   */
  function loadActivitiesData() {
    try {
      const activitiesDataEl = document.getElementById('activities-data');
      if (activitiesDataEl) {
        activitiesData = JSON.parse(activitiesDataEl.textContent);
      }
    } catch(e) {
      console.warn('Could not load activities:', e);
      activitiesData = [];
    }
  }

  /**
   * Build date to day mapping
   * Calculates day number based on trip start date (not just sequential)
   */
  function buildDateMap() {
    const dateToDay = {};
    
    // Get trip start date from the page
    let tripStartDate = null;
    try {
      const startDateEl = document.getElementById('trip-start-date');
      if (startDateEl) {
        tripStartDate = new Date(JSON.parse(startDateEl.textContent));
      }
    } catch(e) {
      console.warn('Could not load trip start date:', e);
    }
    
    if (tripStartDate && activitiesData.length > 0) {
      // Calculate day number based on trip start date
      activitiesData.forEach(function(act) {
        if (act.date) {
          const dateStr = String(act.date);
          if (!dateToDay[dateStr]) {
            const activityDate = new Date(act.date);
            const daysDiff = Math.floor((activityDate - tripStartDate) / (1000 * 60 * 60 * 24));
            dateToDay[dateStr] = daysDiff + 1; // Day 1, 2, 3, etc. (relative to trip start)
          }
        }
      });
    } else {
      // Fallback: sequential numbering based on first activity date
      if (activitiesData.length > 0 && activitiesData[0].date) {
        const firstDate = new Date(activitiesData[0].date);
        activitiesData.forEach(function(act) {
          if (act.date) {
            const dateStr = String(act.date);
            if (!dateToDay[dateStr]) {
              const activityDate = new Date(act.date);
              const daysDiff = Math.floor((activityDate - firstDate) / (1000 * 60 * 60 * 24));
              dateToDay[dateStr] = daysDiff + 1;
            }
          }
        });
      } else {
        // Last resort: sequential numbering
        let dayCounter = 1;
        activitiesData.forEach(function(act) {
          if (act.date) {
            const dateStr = String(act.date);
            if (!dateToDay[dateStr]) {
              dateToDay[dateStr] = dayCounter++;
            }
          }
        });
      }
    }
    return dateToDay;
  }

  /**
   * Process activities data into points
   */
  function processActivitiesData() {
    const dateToDay = buildDateMap();

    // Activiteiten-array in JS (in volgorde van activities-list)
    points = activitiesData
      .filter(function(act) {
        return act.activity && act.activity.latitude && act.activity.longitude;
      })
      .map(function(act) {
        const dateStr = String(act.date || '');
        return {
          id: act.activity.activity_type_id,
          name: act.activity.name || '',
          lat: act.activity.latitude,
          lng: act.activity.longitude,
          date: dateStr,
          day: dateToDay[dateStr] || 1,
          duration: act.activity.duration !== null && act.activity.duration !== undefined ? act.activity.duration : null,
          description: act.activity.description || '',
          image: (act.activity.picture_url && act.activity.picture_url.trim() !== '' && act.activity.picture_url !== 'null') ? act.activity.picture_url : null
        };
      });
  }

  /**
   * Create markers on map
   */
  function createMarkers() {
    points.forEach((p, idx) => {
      const marker = new mapboxgl.Marker({ color: '#E67E22' })
        .setLngLat([p.lng, p.lat])
        .addTo(map);
      marker.getElement().addEventListener('click', () => {
        openPopupByIndex(idx);
      });
      markers[p.id] = marker;
    });
  }

  /**
   * Add event listeners to activity cards
   */
  function setupActivityCardListeners() {
    document.querySelectorAll('.activity-card').forEach(function(card) {
      card.addEventListener('click', function() {
        const activityId = parseInt(this.getAttribute('data-activity-id'));
        if (activityId) {
          focusActivity(activityId);
        }
      });
    });
  }

  /**
   * Initialize Mapbox map
   */
  function initMapbox() {
    // Check if mapboxgl is available
    if (typeof mapboxgl === 'undefined') {
      console.error('Mapbox GL JS is not loaded');
      return;
    }

    // Set access token
    mapboxgl.accessToken = MAPBOX_ACCESS_TOKEN;

    // Create map
    map = new mapboxgl.Map({
      container: 'map',
      style: 'mapbox://styles/mapbox/outdoors-v12',
      center: [16.5, -28.5],
      zoom: 4.5
    });

    // Load activities data
    loadActivitiesData();
    processActivitiesData();

    // Create markers
    createMarkers();

    // Add event listeners to activity cards
    setupActivityCardListeners();

    // Na load: focus automatisch op eerste activiteit (als er één is)
    map.on('load', () => {
      if (points.length > 0) {
        openPopupByIndex(0);
      }
    });
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMapbox);
  } else {
    // If mapboxgl might not be loaded yet, wait a bit
    if (typeof mapboxgl !== 'undefined') {
      initMapbox();
    } else {
      // Wait for mapboxgl to load
      window.addEventListener('load', initMapbox);
    }
  }

  // Export functions to window for use in other scripts if needed
  window.itineraryMapbox = {
    focusActivity: focusActivity,
    openPopupByIndex: openPopupByIndex
  };

})();

