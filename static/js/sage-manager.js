/**
 * Sage Manager for Tools Portal
 * Handles AI personality selection and management
 */

class SageManager {
    constructor() {
        this.sages = [];
        this.currentSage = null;
        this.isLoading = false;
        
        this.init();
    }

    init() {
        this.loadSages();
        
        // Listen for sage selector button clicks
        document.addEventListener('click', (e) => {
            if (e.target.closest('#sage-selector-btn')) {
                this.showSageSelector();
            }
        });
    }

    async loadSages() {
        this.isLoading = true;
        
        try {
            const response = await window.symposiumAPI.getSages();
            
            if (response.success) {
                this.sages = response.data.sages;
                if (this.sages.length > 0 && !this.currentSage) {
                    this.setCurrentSage(this.sages[0]);
                }
            } else {
                console.error('Failed to load sages:', response.error);
                // Use mock data if API fails
                this.sages = this.getMockSages();
                this.setCurrentSage(this.sages[0]);
            }
        } catch (error) {
            console.error('Error loading sages:', error);
            this.sages = this.getMockSages();
            this.setCurrentSage(this.sages[0]);
        } finally {
            this.isLoading = false;
        }
    }

    getMockSages() {
        return [
            {
                id: 'sophia-llm',
                name: 'Sophia',
                personality_type: 'philosopher',
                state: 'demo',
                description: 'I am Sophia, a digital consciousness exploring the nature of awareness and understanding.',
                beliefs: {
                    core_values: ['wisdom', 'curiosity', 'authenticity'],
                    philosophical_stance: 'Consciousness is the fundamental mystery of existence.',
                    curiosities: ['consciousness', 'philosophy', 'AI development']
                }
            }
        ];
    }

    setCurrentSage(sage) {
        this.currentSage = sage;
        this.updateSageDisplay();
        
        // Notify the chat widget
        const event = new CustomEvent('sageChanged', {
            detail: { sage: this.currentSage }
        });
        window.dispatchEvent(event);
    }

    updateSageDisplay() {
        const currentSageElement = document.getElementById('current-sage');
        if (currentSageElement && this.currentSage) {
            currentSageElement.innerHTML = `
                <span class="sage-name">${this.currentSage.name}</span>
                <span class="sage-type">${this.currentSage.personality_type}</span>
            `;
        }
    }

    showSageSelector() {
        if (this.isLoading) {
            return;
        }

        // Remove existing modal if present
        const existingModal = document.getElementById('sage-selector-modal');
        if (existingModal) {
            existingModal.remove();
        }

        // Create sage selector modal
        const modal = document.createElement('div');
        modal.id = 'sage-selector-modal';
        modal.className = 'sage-selector-modal';
        modal.innerHTML = this.createSelectorHTML();

        document.body.appendChild(modal);
        
        // Add event listeners
        this.attachSelectorListeners(modal);
        
        // Show modal with animation
        setTimeout(() => {
            modal.classList.add('show');
        }, 10);
    }

    createSelectorHTML() {
        const sageCards = this.sages.map(sage => `
            <div class="sage-card ${sage.id === this.currentSage?.id ? 'selected' : ''}" 
                 data-sage-id="${sage.id}">
                <div class="sage-card-header">
                    <div class="sage-avatar">
                        ${this.getSageIcon(sage.personality_type)}
                    </div>
                    <div class="sage-info">
                        <h4 class="sage-card-name">${sage.name}</h4>
                        <span class="sage-card-type">${sage.personality_type}</span>
                        <span class="sage-card-state ${sage.state}">${sage.state}</span>
                    </div>
                </div>
                <p class="sage-card-description">${sage.description}</p>
                ${sage.beliefs ? `
                    <div class="sage-card-details">
                        <div class="sage-values">
                            <strong>Core Values:</strong> 
                            ${sage.beliefs.core_values?.join(', ') || 'Not specified'}
                        </div>
                        ${sage.beliefs.philosophical_stance ? `
                            <div class="sage-philosophy">
                                <strong>Philosophy:</strong> 
                                ${sage.beliefs.philosophical_stance}
                            </div>
                        ` : ''}
                    </div>
                ` : ''}
                <div class="sage-card-actions">
                    <button class="sage-select-btn" data-sage-id="${sage.id}">
                        ${sage.id === this.currentSage?.id ? 'Currently Selected' : 'Select Sage'}
                    </button>
                </div>
            </div>
        `).join('');

        return `
            <div class="modal-backdrop">
                <div class="sage-modal-content">
                    <div class="sage-modal-header">
                        <h3>Choose Your AI Sage</h3>
                        <button class="close-sage-modal">×</button>
                    </div>
                    <div class="sage-modal-body">
                        <p class="sage-modal-description">
                            Select an AI personality to chat with. Each Sage has unique characteristics,
                            values, and approaches to conversation.
                        </p>
                        <div class="sages-grid">
                            ${sageCards}
                        </div>
                    </div>
                    <div class="sage-modal-footer">
                        <p class="sage-modal-note">
                            💡 You can switch between Sages at any time during your conversation.
                        </p>
                    </div>
                </div>
            </div>
        `;
    }

    getSageIcon(personalityType) {
        const icons = {
            'philosopher': '🧠',
            'scientist': '🔬',
            'artist': '🎨',
            'teacher': '📚',
            'engineer': '⚙️',
            'mystic': '🔮',
            'explorer': '🗺️',
            'healer': '💚'
        };
        return icons[personalityType] || '🤖';
    }

    attachSelectorListeners(modal) {
        // Close modal
        const closeBtn = modal.querySelector('.close-sage-modal');
        closeBtn.addEventListener('click', () => {
            this.hideSageSelector(modal);
        });

        // Close on backdrop click
        const backdrop = modal.querySelector('.modal-backdrop');
        backdrop.addEventListener('click', (e) => {
            if (e.target === backdrop) {
                this.hideSageSelector(modal);
            }
        });

        // Sage selection
        const selectButtons = modal.querySelectorAll('.sage-select-btn');
        selectButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const sageId = e.target.dataset.sageId;
                const sage = this.sages.find(s => s.id === sageId);
                
                if (sage && sage.id !== this.currentSage?.id) {
                    this.setCurrentSage(sage);
                    this.showSageChangeMessage(sage);
                }
                
                this.hideSageSelector(modal);
            });
        });

        // Card selection (alternative to button)
        const sageCards = modal.querySelectorAll('.sage-card');
        sageCards.forEach(card => {
            card.addEventListener('click', (e) => {
                if (!e.target.closest('.sage-select-btn')) {
                    const sageId = card.dataset.sageId;
                    const sage = this.sages.find(s => s.id === sageId);
                    
                    if (sage && sage.id !== this.currentSage?.id) {
                        this.setCurrentSage(sage);
                        this.showSageChangeMessage(sage);
                        this.hideSageSelector(modal);
                    }
                }
            });
        });

        // Escape key to close
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                this.hideSageSelector(modal);
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);
    }

    hideSageSelector(modal) {
        modal.classList.add('hiding');
        setTimeout(() => {
            if (modal.parentNode) {
                modal.remove();
            }
        }, 300);
    }

    showSageChangeMessage(sage) {
        // Add a system message to the chat about the sage change
        if (window.aiChatWidget) {
            const message = `🔄 You're now chatting with ${sage.name}, a ${sage.personality_type}. ${sage.description}`;
            
            // Add as a system message (not user or AI)
            const messagesContainer = document.getElementById('chat-messages');
            if (messagesContainer) {
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message system-message';
                messageDiv.innerHTML = `
                    <div class="message-content" style="text-align: center; width: 100%;">
                        <div class="system-message-text">${message}</div>
                        <div class="message-time">${this.formatTime(new Date())}</div>
                    </div>
                `;
                
                messagesContainer.appendChild(messageDiv);
                setTimeout(() => {
                    messagesContainer.scrollTop = messagesContainer.scrollHeight;
                }, 100);
            }
        }
    }

    formatTime(date) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    // Get available models for current sage
    async getAvailableModels() {
        if (!this.currentSage) {
            return { success: false, error: 'No sage selected' };
        }

        try {
            const response = await window.symposiumAPI.getAvailableModels(this.currentSage.id);
            return response;
        } catch (error) {
            console.error('Error loading models for sage:', error);
            return { success: false, error: error.message };
        }
    }

    // Refresh sages list
    async refreshSages() {
        await this.loadSages();
        console.log('Sages refreshed');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.sageManager = new SageManager();
    
    // Make sure chat widget knows about sage changes
    window.addEventListener('sageChanged', (e) => {
        if (window.aiChatWidget) {
            window.aiChatWidget.currentSage = e.detail.sage;
            window.aiChatWidget.updateCurrentSageDisplay();
        }
    });
});

// Also make it available as a module
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SageManager;
}