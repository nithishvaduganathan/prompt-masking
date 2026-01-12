// Chat functionality for Privacy-Preserving Chatbot

// Global variables
let sessionId = generateSessionId();

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeChatInterface();
});

/**
 * Generate a unique session ID
 */
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

/**
 * Initialize chat interface
 */
function initializeChatInterface() {
    const chatForm = document.getElementById('chatForm');
    const userInput = document.getElementById('userInput');
    const exampleButtons = document.querySelectorAll('.example-btn');
    
    // Handle form submission
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const message = userInput.value.trim();
        if (message) {
            sendMessage(message);
            userInput.value = '';
        }
    });
    
    // Handle example button clicks
    exampleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const example = this.getAttribute('data-example');
            userInput.value = example;
            userInput.focus();
        });
    });
    
    // Auto-focus on input
    userInput.focus();
}

/**
 * Send a message to the chatbot
 */
async function sendMessage(message) {
    // Display user message
    addUserMessage(message);
    
    // Show loading indicator
    showLoading(true);
    
    // Disable input while processing
    setInputEnabled(false);
    
    try {
        // Call the chat API
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId,
                use_spacy: false
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // Display bot response
            addBotMessage(data.final_response, data);
            
            // Update privacy details panel
            updatePrivacyDetails(data);
        } else {
            throw new Error(data.error || 'Unknown error occurred');
        }
        
    } catch (error) {
        console.error('Error:', error);
        addBotMessage(
            `Sorry, I encountered an error: ${error.message}. Please try again.`,
            null,
            true
        );
    } finally {
        // Hide loading indicator and re-enable input
        showLoading(false);
        setInputEnabled(true);
        
        // Focus back on input
        document.getElementById('userInput').focus();
    }
}

/**
 * Add a user message to the chat
 */
function addUserMessage(message) {
    const chatMessages = document.getElementById('chatMessages');
    const time = getCurrentTime();
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user-message';
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-user"></i>
        </div>
        <div class="message-content">
            <div class="message-text">
                <p>${escapeHtml(message)}</p>
            </div>
            <div class="message-time">${time}</div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

/**
 * Add a bot message to the chat
 */
function addBotMessage(message, privacyData = null, isError = false) {
    const chatMessages = document.getElementById('chatMessages');
    const time = getCurrentTime();
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';
    
    let privacyInfoHtml = '';
    
    // Add privacy information if available
    if (privacyData && !isError) {
        privacyInfoHtml = `
            <div class="privacy-info">
                <strong><i class="fas fa-shield-alt me-2"></i>Privacy Protection Applied</strong>
                <div class="privacy-item">
                    <i class="fas fa-lock"></i>
                    <div class="privacy-item-content">
                        <div class="privacy-label">Detected Entities:</div>
                        <div class="masked-text">${privacyData.detected_entities.length} sensitive item(s) protected</div>
                    </div>
                </div>
                <div class="privacy-item">
                    <i class="fas fa-exchange-alt"></i>
                    <div class="privacy-item-content">
                        <div class="privacy-label">Masked Prompt Sent to AI:</div>
                        <div class="masked-text">${escapeHtml(privacyData.masked_prompt)}</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-robot"></i>
        </div>
        <div class="message-content">
            <div class="message-text ${isError ? 'bg-danger-subtle' : ''}">
                <p>${escapeHtml(message)}</p>
            </div>
            ${privacyInfoHtml}
            <div class="message-time">${time}</div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

/**
 * Update the privacy details panel
 */
function updatePrivacyDetails(data) {
    const privacyDetails = document.getElementById('privacyDetails');
    
    if (!data.detected_entities || data.detected_entities.length === 0) {
        privacyDetails.innerHTML = `
            <div class="alert alert-info mb-0">
                <i class="fas fa-info-circle me-2"></i>
                No sensitive information detected in this message.
            </div>
        `;
        return;
    }
    
    let entitiesHtml = '';
    data.detected_entities.forEach(entity => {
        entitiesHtml += `
            <div class="detected-entity">
                <i class="fas fa-exclamation-triangle"></i>
                ${escapeHtml(entity)}
            </div>
        `;
    });
    
    privacyDetails.innerHTML = `
        <div class="mb-3">
            <h6 class="text-success">
                <i class="fas fa-check-circle me-2"></i>
                Protected Entities
            </h6>
            ${entitiesHtml}
        </div>
        
        <div class="prompt-comparison">
            <div class="prompt-box original-prompt">
                <div class="prompt-label">
                    <i class="fas fa-user me-2"></i>
                    Original Prompt:
                </div>
                ${escapeHtml(data.original_prompt)}
            </div>
            
            <div class="prompt-box masked-prompt">
                <div class="prompt-label">
                    <i class="fas fa-lock me-2"></i>
                    Masked Prompt (sent to AI):
                </div>
                ${escapeHtml(data.masked_prompt)}
            </div>
        </div>
        
        <div class="alert alert-success mt-3 mb-0">
            <small>
                <i class="fas fa-shield-alt me-2"></i>
                <strong>${data.detected_entities.length}</strong> sensitive item(s) were protected!
            </small>
        </div>
    `;
}

/**
 * Show or hide loading indicator
 */
function showLoading(show) {
    const loadingIndicator = document.getElementById('loadingIndicator');
    loadingIndicator.style.display = show ? 'block' : 'none';
    
    if (show) {
        scrollToBottom();
    }
}

/**
 * Enable or disable user input
 */
function setInputEnabled(enabled) {
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    
    userInput.disabled = !enabled;
    sendBtn.disabled = !enabled;
}

/**
 * Scroll chat to bottom
 */
function scrollToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    setTimeout(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 100);
}

/**
 * Get current time formatted
 */
function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
    });
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Display error message
 */
function showError(message) {
    addBotMessage(message, null, true);
}

// Export functions for testing (if needed)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        generateSessionId,
        escapeHtml,
        getCurrentTime
    };
}
