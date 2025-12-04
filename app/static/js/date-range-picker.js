/**
 * Date Range Picker - Handles calendar date range selection
 * Supports dual calendar view for selecting start and end dates
 */

(function() {
  'use strict';

  // Calendar state
  let currentMonth1 = new Date();
  let currentMonth2 = new Date();
  let selectedStartDate = null;
  let selectedEndDate = null;
  let isSelectingStart = true;

  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 
                      'July', 'August', 'September', 'October', 'November', 'December'];

  /**
   * Format date for display
   */
  function formatDate(date) {
    if (!date) return '';
    const d = new Date(date);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }

  /**
   * Get number of days in a month
   */
  function getDaysInMonth(year, month) {
    return new Date(year, month + 1, 0).getDate();
  }

  /**
   * Get first day of month (0 = Sunday, 6 = Saturday)
   */
  function getFirstDayOfMonth(year, month) {
    return new Date(year, month, 1).getDay();
  }

  /**
   * Check if date is today
   */
  function isToday(year, month, day) {
    const today = new Date();
    return year === today.getFullYear() && 
           month === today.getMonth() && 
           day === today.getDate();
  }

  /**
   * Check if date is disabled (past dates)
   */
  function isDateDisabled(year, month, day) {
    const date = new Date(year, month, day);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return date < today;
  }

  /**
   * Check if date is in selected range
   */
  function isDateInRange(year, month, day) {
    if (!selectedStartDate || !selectedEndDate) return false;
    const date = new Date(year, month, day);
    return date >= selectedStartDate && date <= selectedEndDate;
  }

  /**
   * Check if date is selected (start or end)
   */
  function isDateSelected(year, month, day) {
    if (!selectedStartDate && !selectedEndDate) return false;
    const date = new Date(year, month, day);
    if (selectedStartDate && date.getTime() === selectedStartDate.getTime()) return 'start';
    if (selectedEndDate && date.getTime() === selectedEndDate.getTime()) return 'end';
    return false;
  }

  /**
   * Render a single calendar
   */
  function renderCalendar(calendarId, monthDate) {
    const calendar = document.getElementById(calendarId);
    if (!calendar) return;
    
    const year = monthDate.getFullYear();
    const month = monthDate.getMonth();
    
    calendar.innerHTML = '';
    
    // Month header
    const monthHeader = document.createElement('div');
    monthHeader.className = 'calendar-month-header';
    monthHeader.textContent = monthNames[month] + ' ' + year;
    monthHeader.style.gridColumn = '1 / -1';
    monthHeader.style.fontSize = '1rem';
    monthHeader.style.fontWeight = '600';
    monthHeader.style.marginBottom = '0.5rem';
    calendar.appendChild(monthHeader);
    
    // Day headers
    dayNames.forEach(day => {
      const dayHeader = document.createElement('div');
      dayHeader.className = 'calendar-day-header';
      dayHeader.textContent = day;
      calendar.appendChild(dayHeader);
    });
    
    const daysInMonth = getDaysInMonth(year, month);
    const firstDay = getFirstDayOfMonth(year, month);
    
    // Empty cells for days before month starts
    for (let i = 0; i < firstDay; i++) {
      const emptyDay = document.createElement('div');
      emptyDay.className = 'calendar-day other-month';
      calendar.appendChild(emptyDay);
    }
    
    // Days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const dayElement = document.createElement('div');
      dayElement.className = 'calendar-day';
      dayElement.textContent = day;
      
      if (isToday(year, month, day)) {
        dayElement.classList.add('today');
      }
      
      if (isDateDisabled(year, month, day)) {
        dayElement.classList.add('disabled');
      } else {
        dayElement.addEventListener('click', () => selectDate(year, month, day));
      }
      
      const dateStatus = isDateSelected(year, month, day);
      if (dateStatus === 'start') {
        dayElement.classList.add('range-start');
      } else if (dateStatus === 'end') {
        dayElement.classList.add('range-end');
      } else if (isDateInRange(year, month, day)) {
        dayElement.classList.add('in-range');
      }
      
      calendar.appendChild(dayElement);
    }
  }

  /**
   * Select a date
   */
  function selectDate(year, month, day) {
    const date = new Date(year, month, day);
    date.setHours(0, 0, 0, 0);
    
    if (isSelectingStart || !selectedStartDate || date < selectedStartDate) {
      selectedStartDate = date;
      selectedEndDate = null;
      isSelectingStart = false;
    } else {
      selectedEndDate = date;
      isSelectingStart = true;
    }
    
    updateDateDisplay();
    renderCalendars();
  }

  /**
   * Update date display in buttons and hidden inputs
   */
  function updateDateDisplay() {
    const startDisplay = document.getElementById('startDateDisplay');
    const endDisplay = document.getElementById('endDateDisplay');
    const startInput = document.getElementById('start_date');
    const endInput = document.getElementById('end_date');
    const startBtn = document.getElementById('startDateBtn');
    const endBtn = document.getElementById('endDateBtn');
    
    if (selectedStartDate && startDisplay && startInput && startBtn) {
      startDisplay.textContent = formatDate(selectedStartDate);
      startInput.value = selectedStartDate.toISOString().split('T')[0];
      startBtn.classList.add('has-value');
    } else if (startDisplay && startInput && startBtn) {
      startDisplay.textContent = 'Select start date';
      startInput.value = '';
      startBtn.classList.remove('has-value');
    }
    
    if (selectedEndDate && endDisplay && endInput && endBtn) {
      endDisplay.textContent = formatDate(selectedEndDate);
      endInput.value = selectedEndDate.toISOString().split('T')[0];
      endBtn.classList.add('has-value');
    } else if (endDisplay && endInput && endBtn) {
      endDisplay.textContent = 'Select end date';
      endInput.value = '';
      endBtn.classList.remove('has-value');
    }
  }

  /**
   * Render both calendars
   */
  function renderCalendars() {
    renderCalendar('calendar1', currentMonth1);
    renderCalendar('calendar2', currentMonth2);
    updateMonthYearDisplay();
  }

  /**
   * Update month/year display
   */
  function updateMonthYearDisplay() {
    const display = document.getElementById('calendarMonthYear');
    if (display) {
      display.textContent = monthNames[currentMonth1.getMonth()] + ' ' + currentMonth1.getFullYear() + 
                           ' - ' + monthNames[currentMonth2.getMonth()] + ' ' + currentMonth2.getFullYear();
    }
  }

  /**
   * Navigate months
   */
  function navigateMonths(direction) {
    currentMonth1.setMonth(currentMonth1.getMonth() + direction);
    currentMonth2.setMonth(currentMonth2.getMonth() + direction);
    renderCalendars();
  }

  /**
   * Initialize calendar date picker
   */
  function setupCalendar() {
    // Initialize months (current and next)
    currentMonth1 = new Date();
    currentMonth2 = new Date();
    currentMonth2.setMonth(currentMonth2.getMonth() + 1);
    
    const startDateBtn = document.getElementById('startDateBtn');
    const endDateBtn = document.getElementById('endDateBtn');
    const prevMonthBtn = document.getElementById('prevMonthBtn');
    const nextMonthBtn = document.getElementById('nextMonthBtn');
    const confirmDatesBtn = document.getElementById('confirmDatesBtn');
    const clearDatesBtn = document.getElementById('clearDatesBtn');
    const calendarOverlay = document.getElementById('calendarOverlay');
    
    if (startDateBtn) {
      startDateBtn.addEventListener('click', () => {
        if (calendarOverlay) {
          calendarOverlay.classList.add('show');
        }
        renderCalendars();
      });
    }
    
    if (endDateBtn) {
      endDateBtn.addEventListener('click', () => {
        if (calendarOverlay) {
          calendarOverlay.classList.add('show');
        }
        renderCalendars();
      });
    }
    
    if (prevMonthBtn) {
      prevMonthBtn.addEventListener('click', () => navigateMonths(-1));
    }
    
    if (nextMonthBtn) {
      nextMonthBtn.addEventListener('click', () => navigateMonths(1));
    }
    
    if (confirmDatesBtn) {
      confirmDatesBtn.addEventListener('click', () => {
        if (calendarOverlay) {
          calendarOverlay.classList.remove('show');
        }
      });
    }
    
    if (clearDatesBtn) {
      clearDatesBtn.addEventListener('click', () => {
        selectedStartDate = null;
        selectedEndDate = null;
        isSelectingStart = true;
        updateDateDisplay();
        renderCalendars();
      });
    }
    
    // Close overlay when clicking outside
    if (calendarOverlay) {
      calendarOverlay.addEventListener('click', (e) => {
        if (e.target.id === 'calendarOverlay') {
          calendarOverlay.classList.remove('show');
        }
      });
    }
    
    renderCalendars();
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupCalendar);
  } else {
    setupCalendar();
  }

  // Export functions for use in other scripts
  window.dateRangePicker = {
    getStartDate: () => selectedStartDate,
    getEndDate: () => selectedEndDate,
    setStartDate: (date) => {
      selectedStartDate = date ? new Date(date) : null;
      updateDateDisplay();
      renderCalendars();
    },
    setEndDate: (date) => {
      selectedEndDate = date ? new Date(date) : null;
      updateDateDisplay();
      renderCalendars();
    },
    open: () => {
      const calendarOverlay = document.getElementById('calendarOverlay');
      if (calendarOverlay) {
        calendarOverlay.classList.add('show');
        renderCalendars();
      }
    },
    close: () => {
      const calendarOverlay = document.getElementById('calendarOverlay');
      if (calendarOverlay) {
        calendarOverlay.classList.remove('show');
      }
    }
  };

})();

