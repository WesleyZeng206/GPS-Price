document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('hangoutForm');
    const loadingDiv = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');
    const errorDiv = document.getElementById('error');
    const responseContent = document.getElementById('responseContent');
    const errorMessage = document.getElementById('errorMessage');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Get form data
        const budget = parseFloat(document.getElementById('budget').value);
        const distance = parseFloat(document.getElementById('distance').value);
        
        // Validate inputs
        if (!budget || !distance || budget <= 0 || distance <= 0) {
            showError('Please enter valid positive numbers for both budget and distance.');
            return;
        }
        
        // Show loading state
        showLoading();
        
        try {
            const response = await fetch('/api/process-gps', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    budget: budget,
                    distance: distance
                })
            });
            
            if (!response.ok) {
                throw new Error(`Server error: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            showResults(data);
            
        } catch (error) {
            console.error('Error:', error);
            showError(`Failed to fetch hangout spots: ${error.message}`);
        }
    });
    
    function showLoading() {
        hideAllSections();
        loadingDiv.classList.remove('hidden');
    }
    
    function showResults(data) {
        hideAllSections();
        responseContent.innerHTML = formatResponse(data);
        resultsDiv.classList.remove('hidden');
    }
    
    function showError(message) {
        hideAllSections();
        errorMessage.textContent = message;
        errorDiv.classList.remove('hidden');
    }
    
    function hideAllSections() {
        loadingDiv.classList.add('hidden');
        resultsDiv.classList.add('hidden');
        errorDiv.classList.add('hidden');
    }
    
    function formatResponse(data) {
        // Create a readable display of the JSON response
        let html = '<div class="json-display">';
        html += JSON.stringify(data, null, 2);
        html += '</div>';
        
        // If the response has specific structure, we can format it nicely
        if (data && typeof data === 'object') {
            let readableHtml = '<div style="margin-bottom: 20px;">';
            
            // Check for common response fields and format them nicely
            if (data.spots && Array.isArray(data.spots)) {
                readableHtml += '<h3 style="color: #667eea; margin-bottom: 15px;">Found Spots:</h3>';
                data.spots.forEach((spot, index) => {
                    readableHtml += `<div style="background: white; padding: 15px; margin-bottom: 10px; border-radius: 8px; border-left: 3px solid #667eea;">`;
                    readableHtml += `<strong>Spot ${index + 1}:</strong> ${JSON.stringify(spot, null, 2)}`;
                    readableHtml += '</div>';
                });
            } else if (data.message) {
                readableHtml += `<div style="background: white; padding: 15px; border-radius: 8px; border-left: 3px solid #667eea;">`;
                readableHtml += `<strong>Message:</strong> ${data.message}`;
                readableHtml += '</div>';
            } else {
                // Fallback to showing key-value pairs
                Object.entries(data).forEach(([key, value]) => {
                    readableHtml += `<div style="background: white; padding: 15px; margin-bottom: 10px; border-radius: 8px; border-left: 3px solid #667eea;">`;
                    readableHtml += `<strong>${key}:</strong> ${typeof value === 'object' ? JSON.stringify(value, null, 2) : value}`;
                    readableHtml += '</div>';
                });
            }
            
            readableHtml += '</div>';
            readableHtml += '<details style="margin-top: 20px;"><summary style="cursor: pointer; color: #667eea; font-weight: 600;">View Raw JSON Response</summary>' + html + '</details>';
            
            return readableHtml;
        }
        
        return html;
    }
});