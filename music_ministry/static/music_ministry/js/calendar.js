// Prevent duplicate class declaration
if (typeof CalendarManager === 'undefined') {
    window.CalendarManager = class CalendarManager {
    constructor() {
        this.currentDate = new Date();
        this.selectedDate = null;
        this.events = [];
        this.init();
    }

    init() {
        this.loadEvents();
        this.renderCalendar();
        this.bindEvents();
    }

    async loadEvents() {
        try {
            const response = await fetch('/api/events/');
            this.events = await response.json();
            this.renderCalendar();
        } catch (error) {
            console.error('Error loading events:', error);
        }
    }

    bindEvents() {
        document.getElementById('prevMonth')?.addEventListener('click', () => {
            this.currentDate.setMonth(this.currentDate.getMonth() - 1);
            this.renderCalendar();
        });

        document.getElementById('nextMonth')?.addEventListener('click', () => {
            this.currentDate.setMonth(this.currentDate.getMonth() + 1);
            this.renderCalendar();
        });

        document.getElementById('addEventBtn')?.addEventListener('click', () => {
            this.showAddEventModal();
        });

        document.getElementById('addFirstEventBtn')?.addEventListener('click', () => {
            this.showAddEventModal();
        });

        // Add window resize listener to update display when screen size changes
        window.addEventListener('resize', () => {
            this.renderCalendar();
        });

        // Combined click handler for all document clicks
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('assign-members-btn')) {
                const eventId = e.target.dataset.eventId;
                this.showAssignMembersModal(eventId);
            }

            if (e.target.classList.contains('view-details-btn')) {
                const eventId = e.target.dataset.eventId;
                this.toggleEventDetails(eventId);
            }

            if (e.target.classList.contains('calendar-day') || e.target.closest('.calendar-day')) {
                const dayElement = e.target.classList.contains('calendar-day') ? e.target : e.target.closest('.calendar-day');
                const dayNumber = dayElement.dataset.day;
                const monthNumber = dayElement.dataset.month;
                const yearNumber = dayElement.dataset.year;
                if (dayNumber && monthNumber !== undefined && yearNumber) {
                    this.selectDate(parseInt(dayNumber), parseInt(monthNumber), parseInt(yearNumber));
                }
            }

            // Hide tooltip when clicking elsewhere (especially for mobile)
            if (!e.target.closest('.calendar-event') && !e.target.closest('.event-tooltip')) {
                this.hideEventTooltip();
            }
        });
    }

    renderCalendar() {
        const calendarGrid = document.getElementById('calendarGrid');
        const monthYearElement = document.getElementById('monthYear');

        if (!calendarGrid || !monthYearElement) return;

        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();

        monthYearElement.textContent = new Intl.DateTimeFormat('en-US', {
            month: 'long',
            year: 'numeric'
        }).format(this.currentDate);

        calendarGrid.innerHTML = '';

        // Add day headers
        const dayHeaders = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        dayHeaders.forEach(day => {
            const dayHeader = document.createElement('div');
            dayHeader.className = 'calendar-day-header';
            dayHeader.textContent = day;
            calendarGrid.appendChild(dayHeader);
        });

        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const startDate = new Date(firstDay);
        startDate.setDate(startDate.getDate() - firstDay.getDay());

        const endDate = new Date(lastDay);
        endDate.setDate(endDate.getDate() + (6 - lastDay.getDay()));

        const currentDate = new Date(startDate);
        while (currentDate <= endDate) {
            const dayElement = document.createElement('div');
            dayElement.className = 'calendar-day';
            dayElement.dataset.day = currentDate.getDate();
            dayElement.dataset.month = currentDate.getMonth();
            dayElement.dataset.year = currentDate.getFullYear();

            if (currentDate.getMonth() !== month) {
                dayElement.style.opacity = '0.3';
            }

            if (this.isToday(currentDate)) {
                dayElement.classList.add('today');
            }

            const dayNumber = document.createElement('div');
            dayNumber.className = 'calendar-day-number';
            dayNumber.textContent = currentDate.getDate();
            dayElement.appendChild(dayNumber);

            const dayEvents = this.getEventsForDate(currentDate);
            const self = this; // Store this context
            dayEvents.forEach(event => {
                const eventElement = document.createElement('div');
                eventElement.className = 'calendar-event';

                // Generate initials for mobile, full text for desktop
                const isMobile = window.innerWidth <= 768;
                const displayText = isMobile ? self.generateInitials(event.title) : event.title;

                eventElement.textContent = displayText;
                eventElement.setAttribute('data-full-title', event.title);
                eventElement.setAttribute('tabindex', '0');
                eventElement.setAttribute('role', 'button');
                eventElement.setAttribute('aria-label', `Event: ${event.title}`);

                // Simple click handler
                eventElement.addEventListener('click', (e) => {
                    e.stopPropagation();
                    self.showEventInAllEventsTab(event.id);
                });

                // Long press for mobile (touch devices only)
                let pressTimer = null;
                let isLongPress = false;

                eventElement.addEventListener('touchstart', (e) => {
                    isLongPress = false;
                    pressTimer = setTimeout(() => {
                        isLongPress = true;
                        // Long press - show tooltip if has songs
                        if (event.songs && event.songs.length > 0) {
                            self.showEventTooltip(eventElement, event);
                        }
                    }, 500); // 500ms for long press
                });

                eventElement.addEventListener('touchend', (e) => {
                    clearTimeout(pressTimer);
                    if (isLongPress) {
                        e.preventDefault();
                        e.stopPropagation();
                    }
                });

                eventElement.addEventListener('touchcancel', (e) => {
                    clearTimeout(pressTimer);
                });

                // Add keyboard support
                eventElement.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        self.showEventInAllEventsTab(event.id);
                    }
                });

                // Add hover support for desktop (only if has songs)
                if (event.songs && event.songs.length > 0) {
                    eventElement.addEventListener('mouseenter', (e) => {
                        // Only show on hover for desktop (not mobile)
                        if (window.innerWidth > 768) {
                            self.showEventTooltip(eventElement, event);
                        }
                    });
                    eventElement.addEventListener('mouseleave', () => {
                        self.hideEventTooltip();
                    });
                }

                dayElement.appendChild(eventElement);
            });

            calendarGrid.appendChild(dayElement);
            currentDate.setDate(currentDate.getDate() + 1);
        }
    }

    getEventsForDate(date) {
        return this.events.filter(event => {
            const eventDate = new Date(event.start);
            return this.isSameDay(eventDate, date);
        });
    }

        generateInitials(title) {
            // Split by spaces and get first letter of each word
            const words = title.trim().split(/\s+/);

            if (words.length === 1) {
                // Single word - take first 2 letters
                return words[0].substring(0, 2).toUpperCase();
            } else if (words.length === 2) {
                // Two words - take first letter of each
                return (words[0][0] + words[1][0]).toUpperCase();
            } else {
                // Multiple words - take first letter of each word
                return words.map(word => word[0]).join('').toUpperCase();
            }
        }

    isSameDay(date1, date2) {
        return date1.getDate() === date2.getDate() &&
            date1.getMonth() === date2.getMonth() &&
            date1.getFullYear() === date2.getFullYear();
    }

        isToday(date) {
            const today = new Date();
            return this.isSameDay(date, today);
        }

    selectDate(day, month, year) {
        this.selectedDate = new Date(year, month, day);
        this.showAddEventModal();
    }

    showAddEventModal() {
        const modal = document.getElementById('addEventModal');
        if (modal) {
            if (this.selectedDate) {
                const dateInput = modal.querySelector('input[type="date"]');
                if (dateInput) {
                    dateInput.value = this.selectedDate.toISOString().split('T')[0];
                }
            }
            modal.classList.add('active');
        }
    }

    showAssignMembersModal(eventId) {
        console.log('Showing assign members modal for event:', eventId);
        // Implementation for assign members modal
    }

    toggleEventDetails(eventId) {
        console.log('Toggling event details for:', eventId);
        // Implementation for event details toggle
    }

    showEventInAllEventsTab(eventId) {
        console.log('Showing event in all events tab:', eventId);
        // Switch to events tab
        const eventsTabButton = document.querySelector('[data-tab="events"]');
        const eventsTabContent = document.getElementById('events');
        const calendarTabButton = document.querySelector('[data-tab="calendar"]');
        const calendarTabContent = document.getElementById('calendar');

        if (eventsTabButton && eventsTabContent) {
            // Remove active from calendar tab
            calendarTabButton?.classList.remove('active');
            calendarTabContent?.classList.remove('active');

            // Add active to events tab
            eventsTabButton.classList.add('active');
            eventsTabContent.classList.add('active');

            // Scroll to the specific event if needed
            const eventElement = document.querySelector(`[data-event-id="${eventId}"]`);
            if (eventElement) {
                eventElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                eventElement.style.backgroundColor = '#ede9fe';
                setTimeout(() => {
                    eventElement.style.backgroundColor = '';
                }, 2000);
            }
        }
    }

        showEventTooltip(eventElement, eventData) {
            this.hideEventTooltip();

        const tooltip = document.createElement('div');
        tooltip.className = 'event-tooltip';
        tooltip.innerHTML = `
            <div class="tooltip-header">
                <h4>${eventData.title}</h4>
            </div>
            <div class="tooltip-songs">
                <h5>Songs:</h5>
                ${eventData.songs.map(song => `
                    <div class="tooltip-song">
                        <span class="tooltip-song-type">${song.type}:</span>
                        <span class="tooltip-song-title">${song.title}</span>
                    </div>
                `).join('')}
            </div>
        `;

        document.body.appendChild(tooltip);

        const rect = eventElement.getBoundingClientRect();
        tooltip.style.left = rect.left + 'px';
        tooltip.style.top = (rect.bottom + 5) + 'px';
    }

        hideEventTooltip() {
            const existingTooltip = document.querySelector('.event-tooltip');
            if (existingTooltip) {
                existingTooltip.remove();
        }
        }
    }
} // End of CalendarManager class check

class TabManager {
    constructor() {
        this.init();
    }

    init() {
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabContents = document.querySelectorAll('.tab-content');

        console.log('Tab manager initialized. Found:', tabButtons.length, 'buttons and', tabContents.length, 'contents');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const targetTab = button.dataset.tab;
                console.log('Tab clicked:', targetTab);

                // Remove active class from all tabs and contents
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));

                // Add active class to clicked tab and corresponding content
                button.classList.add('active');
                const targetContent = document.getElementById(targetTab);
                if (targetContent) {
                    targetContent.classList.add('active');
                    console.log('Tab switched to:', targetTab);
                }
            });
        });
    }
}

class ModalManager {
    constructor() {
        this.init();
    }

    init() {
        // Close modal functionality
        const modalCloses = document.querySelectorAll('.modal-close');
        modalCloses.forEach(closeBtn => {
            closeBtn.addEventListener('click', () => {
                const modal = closeBtn.closest('.modal');
                if (modal) {
                    modal.classList.remove('active');
                }
            });
        });

        // Close modal when clicking outside
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('active');
                }
            });
        });
    }

    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
        }
    }
}

// Prevent duplicate class declaration
if (typeof EventFilter === 'undefined') {
    window.EventFilter = class EventFilter {
    constructor() {
        this.init();
    }

    init() {
        const dateFilter = document.getElementById('dateFilter');
        const clearFilter = document.getElementById('clearFilter');
        const todayFilter = document.getElementById('todayFilter');
        const filterStatus = document.getElementById('filterStatus');

        if (!dateFilter || !clearFilter || !todayFilter) return;

        // Date filter change event
        dateFilter.addEventListener('change', () => {
            this.filterByDate(dateFilter.value);
        });

        // Clear filter button
        clearFilter.addEventListener('click', () => {
            dateFilter.value = '';
            this.clearFilter();
        });

        // Today filter button
        todayFilter.addEventListener('click', () => {
            const today = new Date().toISOString().split('T')[0];
            dateFilter.value = today;
            this.filterByDate(today);
        });

        // Initialize status
        this.updateStatus();
    }

    filterByDate(selectedDate) {
        const eventItems = document.querySelectorAll('.event-item');
        let visibleCount = 0;
        let totalCount = eventItems.length;

        eventItems.forEach(item => {
            const eventDate = item.dataset.eventDate;

            if (!selectedDate || eventDate === selectedDate) {
                item.style.display = 'block';
                visibleCount++;
            } else {
                item.style.display = 'none';
            }
        });

        this.updateStatus(selectedDate, visibleCount, totalCount);
    }

    clearFilter() {
        const eventItems = document.querySelectorAll('.event-item');
        eventItems.forEach(item => {
            item.style.display = 'block';
        });
        this.updateStatus();
    }

    updateStatus(selectedDate = null, visibleCount = null, totalCount = null) {
        const filterStatus = document.getElementById('filterStatus');
        if (!filterStatus) return;

        if (selectedDate) {
            const date = new Date(selectedDate);
            const formattedDate = date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });

            if (visibleCount === 0) {
                filterStatus.textContent = `No events found for ${formattedDate}`;
                filterStatus.style.color = '#ef4444';
            } else if (visibleCount === 1) {
                filterStatus.textContent = `Showing 1 event for ${formattedDate}`;
                filterStatus.style.color = '#059669';
            } else {
                filterStatus.textContent = `Showing ${visibleCount} events for ${formattedDate}`;
                filterStatus.style.color = '#059669';
            }
        } else {
            const eventItems = document.querySelectorAll('.event-item');
            const total = eventItems.length;

            if (total === 0) {
                filterStatus.textContent = 'No events scheduled';
                filterStatus.style.color = '#6b7280';
            } else if (total === 1) {
                filterStatus.textContent = 'Showing 1 event';
                filterStatus.style.color = '#6b7280';
            } else {
                filterStatus.textContent = `Showing all ${total} events`;
                filterStatus.style.color = '#6b7280';
            }
        }
    }

    // Method to be called when new events are added dynamically
    refreshFilter() {
        const dateFilter = document.getElementById('dateFilter');
        if (dateFilter && dateFilter.value) {
            this.filterByDate(dateFilter.value);
        } else {
            this.updateStatus();
        }
    }
}
} // End of EventFilter class check

// Prevent duplicate class declaration
if (typeof LineupFilter === 'undefined') {
    window.LineupFilter = class LineupFilter {
    constructor() {
        this.init();
    }

    init() {
        const dateFilter = document.getElementById('lineupDateFilter');
        const clearFilter = document.getElementById('clearLineupFilter');
        const todayFilter = document.getElementById('todayLineupFilter');
        const filterStatus = document.getElementById('lineupFilterStatus');

        if (!dateFilter || !clearFilter || !todayFilter) return;

        // Date filter change event
        dateFilter.addEventListener('change', () => {
            this.filterByDate(dateFilter.value);
        });

        // Clear filter button
        clearFilter.addEventListener('click', () => {
            dateFilter.value = '';
            this.clearFilter();
        });

        // Today filter button
        todayFilter.addEventListener('click', () => {
            const today = new Date().toISOString().split('T')[0];
            dateFilter.value = today;
            this.filterByDate(today);
        });

        // Initialize status
        this.updateStatus();
    }

    filterByDate(selectedDate) {
        const lineupItems = document.querySelectorAll('.lineup-item');
        let visibleCount = 0;
        let totalCount = lineupItems.length;

        lineupItems.forEach(item => {
            const eventDate = item.dataset.eventDate;

            if (!selectedDate || eventDate === selectedDate) {
                item.style.display = 'block';
                visibleCount++;
            } else {
                item.style.display = 'none';
            }
        });

        this.updateStatus(selectedDate, visibleCount, totalCount);
    }

    clearFilter() {
        const lineupItems = document.querySelectorAll('.lineup-item');
        lineupItems.forEach(item => {
            item.style.display = 'block';
        });
        this.updateStatus();
    }

    updateStatus(selectedDate = null, visibleCount = null, totalCount = null) {
        const filterStatus = document.getElementById('lineupFilterStatus');
        if (!filterStatus) return;

        if (selectedDate) {
            const date = new Date(selectedDate);
            const formattedDate = date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });

            if (visibleCount === 0) {
                filterStatus.textContent = `No lineups found for ${formattedDate}`;
                filterStatus.className = 'filter-status filter-status-warning';
            } else if (visibleCount === 1) {
                filterStatus.textContent = `Showing 1 lineup for ${formattedDate}`;
                filterStatus.className = 'filter-status filter-status-success';
            } else {
                filterStatus.textContent = `Showing ${visibleCount} of ${totalCount} lineups for ${formattedDate}`;
                filterStatus.className = 'filter-status filter-status-success';
            }
        } else {
            const allLineupItems = document.querySelectorAll('.lineup-item');
            const totalLineups = allLineupItems.length;
            filterStatus.textContent = `Showing all ${totalLineups} lineups`;
            filterStatus.className = 'filter-status';
        }
    }

    // Method to be called when new lineups are added dynamically
    refreshFilter() {
        const dateFilter = document.getElementById('lineupDateFilter');
        if (dateFilter && dateFilter.value) {
            this.filterByDate(dateFilter.value);
        } else {
            this.updateStatus();
        }
    }
}
} // End of LineupFilter class check

// Initialize everything after all classes are defined
document.addEventListener('DOMContentLoaded', () => {
    window.calendarManager = new CalendarManager();
    window.tabManager = new TabManager();
    window.modalManager = new ModalManager();
    window.eventFilter = new EventFilter();
    window.lineupFilter = new LineupFilter();

    const alerts = document.querySelectorAll('.alert-success');
    if (alerts.length > 0) {
        alerts.forEach(alert => {
            if (alert.textContent.includes('Event created successfully')) {
                console.log('Event created, switching to events tab');
                setTimeout(() => {
                    const eventsTabButton = document.querySelector('[data-tab="events"]');
                    const eventsTabContent = document.getElementById('events');
                    const calendarTabButton = document.querySelector('[data-tab="calendar"]');
                    const calendarTabContent = document.getElementById('calendar');

                    console.log('Tab elements found:', { eventsTabButton, eventsTabContent, calendarTabButton, calendarTabContent });

                    if (eventsTabButton && eventsTabContent) {
                        calendarTabButton?.classList.remove('active');
                        calendarTabContent?.classList.remove('active');

                        eventsTabButton.classList.add('active');
                        eventsTabContent.classList.add('active');

                        console.log('Switched to events tab');
                    }
                }, 500);
            }
        });
    }

    if (window.location.hash === '#events') {
        setTimeout(() => {
            const eventsTabButton = document.querySelector('[data-tab="events"]');
            const eventsTabContent = document.getElementById('events');
            const calendarTabButton = document.querySelector('[data-tab="calendar"]');
            const calendarTabContent = document.getElementById('calendar');

            if (eventsTabButton && eventsTabContent) {
                calendarTabButton?.classList.remove('active');
                calendarTabContent?.classList.remove('active');

                eventsTabButton.classList.add('active');
                eventsTabContent.classList.add('active');

                console.log('Switched to events tab via hash navigation');
            }
        }, 100);
    }

    console.log('Calendar app initialized');
});