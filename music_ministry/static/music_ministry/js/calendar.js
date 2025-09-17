class CalendarManager {
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

        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('assign-members-btn')) {
                const eventId = e.target.dataset.eventId;
                this.showAssignMembersModal(eventId);
            }
        });

        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('view-details-btn')) {
                const eventId = e.target.dataset.eventId;
                this.toggleEventDetails(eventId);
            }
        });

        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('calendar-day') || e.target.closest('.calendar-day')) {
                const dayElement = e.target.classList.contains('calendar-day') ? e.target : e.target.closest('.calendar-day');
                const dayNumber = dayElement.dataset.day;
                const monthNumber = dayElement.dataset.month;
                const yearNumber = dayElement.dataset.year;
                if (dayNumber && monthNumber !== undefined && yearNumber) {
                    this.selectDate(parseInt(dayNumber), parseInt(monthNumber), parseInt(yearNumber));
                }
            }
        });
    }

    renderCalendar() {
        const calendarGrid = document.getElementById('calendarGrid');
        const monthYearElement = document.getElementById('monthYear');

        if (!calendarGrid || !monthYearElement) return;

        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();
        const today = new Date();

        monthYearElement.textContent = this.currentDate.toLocaleString('default', {
            month: 'long',
            year: 'numeric'
        });

        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const startDate = new Date(firstDay);
        startDate.setDate(startDate.getDate() - firstDay.getDay());

        calendarGrid.innerHTML = '';

        const dayHeaders = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        dayHeaders.forEach(day => {
            const headerElement = document.createElement('div');
            headerElement.className = 'calendar-day-header';
            headerElement.textContent = day;
            calendarGrid.appendChild(headerElement);
        });

        const currentDate = new Date(startDate);
        for (let i = 0; i < 42; i++) {
            const dayElement = document.createElement('div');
            dayElement.className = 'calendar-day';
            dayElement.dataset.day = currentDate.getDate();
            dayElement.dataset.month = currentDate.getMonth();
            dayElement.dataset.year = currentDate.getFullYear();

            if (currentDate.getMonth() !== month) {
                dayElement.classList.add('other-month');
                dayElement.style.opacity = '0.3';
            }

            if (this.isSameDay(currentDate, today)) {
                dayElement.classList.add('today');
            }

            const dayNumber = document.createElement('div');
            dayNumber.className = 'calendar-day-number';
            dayNumber.textContent = currentDate.getDate();
            dayElement.appendChild(dayNumber);

            const dayEvents = this.getEventsForDate(currentDate);
            dayEvents.forEach(event => {
                const eventElement = document.createElement('div');
                eventElement.className = 'calendar-event';
                eventElement.textContent = event.title;
                eventElement.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.showEventInAllEventsTab(event.id);
                });

                if (event.songs && event.songs.length > 0) {
                    eventElement.addEventListener('mouseenter', (e) => {
                        this.showEventTooltip(e, event);
                    });
                    eventElement.addEventListener('mouseleave', () => {
                        this.hideEventTooltip();
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

    isSameDay(date1, date2) {
        return date1.getDate() === date2.getDate() &&
            date1.getMonth() === date2.getMonth() &&
            date1.getFullYear() === date2.getFullYear();
    }

    selectDate(day, month, year) {
        this.selectedDate = new Date(year, month, day);
        this.showAddEventModal();
    }

    showAddEventModal() {
        const modal = document.getElementById('addEventModal');
        if (modal) {
            if (this.selectedDate) {
                const dateInput = document.getElementById('eventDate');
                if (dateInput) {
                    dateInput.value = this.selectedDate.toISOString().split('T')[0];
                }
            }
            modal.classList.add('active');
        }
    }

    hideAddEventModal() {
        const modal = document.getElementById('addEventModal');
        if (modal) {
            modal.classList.remove('active');
            this.selectedDate = null;
        }
    }

    showAssignMembersModal(eventId) {
        document.getElementById('assignEventId').value = eventId;

        const eventElement = document.querySelector(`[data-event-id="${eventId}"]`).closest('.event-item');
        const eventTitle = eventElement.querySelector('.event-title').textContent;
        const eventDate = eventElement.querySelector('.event-datetime').textContent.split(' • ')[0];

        document.getElementById('assignEventTitle').textContent = `${eventTitle} - ${eventDate}`;
        document.getElementById('assignMembersForm').action = `/assign-members/${eventId}/`;

        window.modalManager.showModal('assignMembersModal');
    }

    toggleEventDetails(eventId) {
        const eventElement = document.querySelector(`[data-event-id="${eventId}"]`).closest('.event-item');
        const detailsElement = eventElement.querySelector('.event-assignments');
        const button = eventElement.querySelector('.view-details-btn');

        if (detailsElement.style.display === 'none' || !detailsElement.style.display) {
            detailsElement.style.display = 'block';
            button.textContent = 'Hide Details';
        } else {
            detailsElement.style.display = 'none';
            button.textContent = 'View Details';
        }
    }

    showEventInAllEventsTab(eventId) {
        // Switch to All Events tab
        const eventsTabButton = document.querySelector('[data-tab="events"]');
        const eventsTabContent = document.getElementById('events');
        const calendarTabButton = document.querySelector('[data-tab="calendar"]');
        const calendarTabContent = document.getElementById('calendar');

        if (eventsTabButton && eventsTabContent) {
            // Remove active from calendar
            calendarTabButton?.classList.remove('active');
            calendarTabContent?.classList.remove('active');

            // Add active to events
            eventsTabButton.classList.add('active');
            eventsTabContent.classList.add('active');

            // Show the event details
            setTimeout(() => {
                const eventElement = document.querySelector(`[data-event-id="${eventId}"]`);
                if (eventElement) {
                    // Scroll to the event
                    eventElement.scrollIntoView({ behavior: 'smooth', block: 'center' });

                    // Auto-show the details
                    const detailsElement = eventElement.closest('.event-item').querySelector('.event-assignments');
                    const button = eventElement.closest('.event-item').querySelector('.view-details-btn');

                    if (detailsElement && button) {
                        detailsElement.style.display = 'block';
                        button.textContent = 'Hide Details';

                        // Highlight the event briefly
                        eventElement.closest('.event-item').style.backgroundColor = '#ede9fe';
                        setTimeout(() => {
                            eventElement.closest('.event-item').style.backgroundColor = '';
                        }, 2000);
                    }
                }
            }, 100);
        }
    }
}

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

                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));

                button.classList.add('active');
                const targetContent = document.getElementById(targetTab);
                if (targetContent) {
                    targetContent.classList.add('active');
                    console.log('Activated tab:', targetTab);
                } else {
                    console.log('Target content not found:', targetTab);
                }

                if (targetTab === 'calendar' && window.calendarManager) {
                    window.calendarManager.renderCalendar();
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
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal(e.target);
            }

            if (e.target.classList.contains('modal-close')) {
                e.preventDefault();
                e.stopPropagation();
                const modal = e.target.closest('.modal');
                this.closeModal(modal);
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const activeModal = document.querySelector('.modal.active');
                if (activeModal) {
                    this.closeModal(activeModal);
                }
            }
        });
    }

    closeModal(modal) {
        if (modal) {
            modal.classList.remove('active');
            if (window.calendarManager && modal.id === 'addEventModal') {
                window.calendarManager.hideAddEventModal();
            }
        }
    }

    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
        }
    }
}

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

class EventFilter {
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

    showEventTooltip(event, eventData) {
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
                        ${song.song_link ? `<a href="${song.song_link}" target="_blank" class="tooltip-song-link">🔗 Listen</a>` : ''}
                    </div>
                `).join('')}
            </div>
        `;

        document.body.appendChild(tooltip);

        const rect = event.target.getBoundingClientRect();
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

class LineupFilter {
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
        const totalCount = lineupItems.length;

        lineupItems.forEach(item => {
            const eventDate = item.getAttribute('data-event-date');
            if (eventDate === selectedDate) {
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

        if (selectedDate && visibleCount !== null && totalCount !== null) {
            const date = new Date(selectedDate);
            const formattedDate = date.toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });

            if (visibleCount === 0) {
                filterStatus.textContent = `No lineups found for ${formattedDate}`;
                filterStatus.className = 'filter-status filter-status-warning';
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
