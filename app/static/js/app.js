document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const queryInput = document.getElementById('query-input');
    const queryButton = document.getElementById('query-button');
    const loadingIndicator = document.getElementById('loading');
    const sentimentAnalysis = document.getElementById('sentiment-analysis');
    const eventList = document.getElementById('event-list');
    const eventCount = document.getElementById('event-count');
    const eventsContainer = document.getElementById('events-container');
    const initialMessage = document.getElementById('initial-message');
    const mapDiv = document.getElementById('map');
    const eventModal = new bootstrap.Modal(document.getElementById('event-details-modal'));
    const eventDetailsContent = document.getElementById('event-details-content');
    const eventTitle = document.getElementById('event-title');

    // Initialize event listeners
    queryButton.addEventListener('click', processQuery);
    queryInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            processQuery();
        }
    });

    // Function to process the query
    function processQuery() {
        const query = queryInput.value.trim();
        
        if (!query) {
            alert('Please enter a query.');
            return;
        }
        
        // Show loading indicator
        loadingIndicator.classList.remove('d-none');
        sentimentAnalysis.classList.add('d-none');
        eventList.classList.add('d-none');
        
        // Send query to the server
        const formData = new FormData();
        formData.append('query', query);
        
        fetch('/query', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Hide loading indicator
            loadingIndicator.classList.add('d-none');
            
            // Hide initial message
            initialMessage.style.display = 'none';
            
            // Check if there are events to display
            if (data.events && data.events.length > 0) {
                // Update the map
                mapDiv.innerHTML = data.map_html;
                
                // Update sentiment analysis
                updateSentimentAnalysis(data.sentiment, data.sentiment_counts, data.total_events);
                
                // Update event list
                updateEventList(data.events);
            } else {
                // Handle no events case
                mapDiv.innerHTML = '<div class="alert alert-info">No events found for this query. Try a different search term.</div>';
                eventList.classList.remove('d-none');
                eventCount.textContent = '0';
                eventsContainer.innerHTML = '<div class="alert alert-info">No events match your query. Try broadening your search.</div>';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            loadingIndicator.classList.add('d-none');  // Fixed variable name
            alert('An error occurred while processing your query. Please try again.');
        });
    }

    // Function to update sentiment analysis display
    function updateSentimentAnalysis(overallSentiment, counts, totalEvents) {
        // Show sentiment analysis section
        sentimentAnalysis.classList.remove('d-none');
        
        // Update overall sentiment
        const overallSentimentElem = document.getElementById('overall-sentiment');
        overallSentimentElem.textContent = overallSentiment.charAt(0).toUpperCase() + overallSentiment.slice(1);
        
        // Calculate percentages for progress bars
        const percentages = {
            positive: totalEvents > 0 ? (counts.positive / totalEvents) * 100 : 0,
            negative: totalEvents > 0 ? (counts.negative / totalEvents) * 100 : 0,
            mixed: totalEvents > 0 ? (counts.mixed / totalEvents) * 100 : 0
        };
        
        // Update the progress bars and counts
        document.getElementById('positive-bar').style.width = `${percentages.positive}%`;
        document.getElementById('negative-bar').style.width = `${percentages.negative}%`;
        document.getElementById('mixed-bar').style.width = `${percentages.mixed}%`;
        
        document.getElementById('positive-count').textContent = counts.positive;
        document.getElementById('negative-count').textContent = counts.negative;
        document.getElementById('mixed-count').textContent = counts.mixed;
    }

    // Function to update event list
    function updateEventList(events) {
        // Show event list section
        eventList.classList.remove('d-none');
        
        // Update event count
        eventCount.textContent = events.length;
        
        // Clear existing events
        eventsContainer.innerHTML = '';
        
        // Add events to the list
        events.forEach(event => {
            const eventElement = document.createElement('a');
            eventElement.href = '#';
            eventElement.className = `list-group-item list-group-item-action list-group-item-${event.sentiment || 'neutral'}`;
            eventElement.innerHTML = `
                <div class="d-flex w-100 justify-content-between">
                    <h5 class="mb-1">${event.incident_name || 'Unnamed Event'}</h5>
                    <small>${event.year || 'Unknown Year'}</small>
                </div>
                <p class="mb-1">${event.event_type || 'Event'} in ${event.country || 'Unknown Location'}</p>
                <small>${event.outcome || 'Outcome not specified'}</small>
            `;
            
            // Add click event
            eventElement.addEventListener('click', function(e) {
                e.preventDefault();
                showEventDetails(event.event_id);
            });
            
            eventsContainer.appendChild(eventElement);
        });
    }

    // Function to show event details
    window.showEventDetails = function(eventId) {
        // Show the modal
        eventModal.show();
        
        // Reset content
        eventDetailsContent.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;
        
        // Fetch event details
        fetch(`/event/${eventId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server responded with status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Update modal title
                eventTitle.textContent = data.event.incident_name || 'Event Details';
                
                // Create content
                let content = `
                    <div class="event-summary">
                        ${data.summary || 'No summary available.'}
                    </div>
                    
                    <div class="event-metadata">
                        <span class="event-metadata-item">
                            <i class="fas fa-calendar-alt"></i> ${data.event.year || 'Unknown Year'}
                        </span>
                        <span class="event-metadata-item">
                            <i class="fas fa-map-marker-alt"></i> ${data.country?.name || 'Unknown Location'}
                        </span>
                        <span class="event-metadata-item">
                            <i class="fas fa-tag"></i> ${data.event.event_type || 'Unspecified Event Type'}
                        </span>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6">
                            <div class="card event-detail-card">
                                <div class="card-header">
                                    <h5>Event Details</h5>
                                </div>
                                <div class="card-body">
                                    <p><strong>Impact:</strong> ${data.event.impact || 'Not specified'}</p>
                                    <p><strong>Outcome:</strong> ${data.event.outcome || 'Not specified'}</p>
                                    <p><strong>Location:</strong> ${data.country?.name || 'Unknown'} 
                                        (${data.event.latitude || 'N/A'}, ${data.event.longitude || 'N/A'})</p>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            <div class="card event-detail-card">
                                <div class="card-header">
                                    <h5>Responsible Groups</h5>
                                </div>
                                <div class="card-body">
                `;
                
                if (data.groups && data.groups.length > 0) {
                    data.groups.forEach(group => {
                        content += `<p><strong>${group.name || 'Unnamed Group'}</strong></p>`;
                    });
                } else {
                    content += `<p>No specific group identified</p>`;
                    
                    if (data.event.responsible_group) {
                        content += `<p><strong>Noted as:</strong> ${data.event.responsible_group}</p>`;
                    }
                }
                
                content += `
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
                // Update modal content
                eventDetailsContent.innerHTML = content;
            })
            .catch(error => {
                console.error('Error:', error);
                eventDetailsContent.innerHTML = `
                    <div class="alert alert-danger">
                        An error occurred while fetching event details.
                    </div>
                `;
            });
    };
});