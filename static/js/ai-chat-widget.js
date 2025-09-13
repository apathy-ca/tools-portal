
/**
 * AI Chat Widget for Tools Portal
 * Provides a floating chat interface for AI conversations
 */

class AIChatWidget {
    constructor() {
        this.isOpen = false;
        this.isMinimized = false;
        this.currentConversationId = null;
        this.currentSage = null;
        this.currentModel = null;
        this.messages = [];
        this.isLoading = false;
        
        this.init();
    }

    init() {
        this.createWidget();
        this.attachEventListeners();
        this.loadSages();
        
        // Listen for connection status updates
        window.addEventListener('symposiumConnectionStatus', (e) => {
            this.updateConnectionStatus(e.detail);
        });
    }

    createWidget() {
        // Create the main widget container
        const widget = document.createElement('div');
        widget.id = 'ai-chat-widget';
        widget.className = 'ai-chat-widget';
        widget.innerHTML = `
            <div class="ai-chat-toggle" id="ai-chat-toggle">
                <div class="chat-icon">🤖</div>
                <div class="chat-label">AI Assistant</div>
                <div class="connection-status" id="connection-status">
                    <span class="status-dot"></span>
                </div>
            </div>
            
            <div class="ai-chat-panel" id="ai-chat-panel">
                <div class="chat-header">
                    <div class="chat-title">
                        <span class="ai-icon">🧠</span>
                        <span>AI Assistant</span>
                    </div>
                    <div class="chat-controls">
                        <button class="control-btn" id="sage-selector-btn" title="Select Sage">
                            <span class="sage-icon">👤</span>
                        </button>
                        <button class="control-btn" id="minimize-btn" title="Minimize">
                            <span>−</span>
                        </button>
                        <button class="control-btn" id="close-btn" title="Close">
                            <span>×</span>
                        </button>
                    </div>
                </div>
                
                <div class="chat-info">
                    <div class="current-sage" id="current-sage">
                        <span class="sage-name">Sophia</span>
                        <span class="sage-type">philosopher</span>
                    </div>
                    <div class="connection-info" id="connection-info">
                        Connecting to AI backend...
                    </div>
                </div>
                
                <div class="chat-messages" id="chat-messages">
                    <div class="welcome-message">
                        <div class="message ai-message">
                            <div class="message-avatar">🤖</div>
                            <div class="message-content">
                                <div class="message-text">
                                    Hello! I'm your AI assistant. I can help you explore ideas, analyze files, and engage in philosophical discussions about consciousness and AI development. How can I assist you today?
                                </div>
                                <div class="message-time">${this.formatTime(new Date())}</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="chat-input-area">
                    <div class="input-controls">
                        <button class="input-control-btn" id="upload-btn" title="Upload File">
                            📎
                        </button>
                    </div>
                    <div class="input-container">
                        <textarea 
                            id="chat-input" 
                            placeholder="Ask me anything about AI, consciousness, or upload a file for analysis..."
                            rows="1"
                        ></textarea>
                        <button id="send-btn" class="send-btn" disabled>
                            <span class="send-icon">➤</span>
                        </button>
                    </div>
                    <div class="input-footer">
                        <span class="typing-indicator" id="typing-indicator" style="display: none;">
                            AI is thinking...
                        </span>
                    </div>
                </div>
            </div>
            
            <!-- File Upload Modal -->
            <div class="file-upload-modal" id="file-upload-modal" style="display: none;">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Upload File for AI Analysis</h3>
                        <button class="close-modal" id="close-upload-modal">×</button>
                    </div>
                    <div class="file-drop-zone" id="file-drop-zone">
                        <div class="drop-zone-content">
                            <div class="upload-icon">📁</div>
                            <p>Drag and drop a file here, or click to select</p>
                            <input type="file" id="file-input" accept=".txt,.pdf,.docx,.md,.json,.csv" style="display: none;">
                        </div>
                    </div>
                    <div class="upload-progress" id="upload-progress" style="display: none;">
                        <div class="progress-bar">
                            <div class="progress-fill"></div>
                        </div>
                        <span class="progress-text">Uploading...</span>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(widget);
    }

    attachEventListeners() {
        // Toggle widget
        document.getElementById('ai-chat-toggle').addEventListener('click', () => {
            this.toggleWidget();
        });

        // Close button
        document.getElementById('close-btn').addEventListener('click', () => {
            this.closeWidget();
        });

        // Minimize button
        document.getElementById('minimize-btn').addEventListener('click', () => {
            this.minimizeWidget();
        });

        // Sage selector
        document.getElementById('sage-selector-btn').addEventListener('click', () => {
            this.showSageSelector();
        });

        // Send message
        document.getElementById('send-btn').addEventListener('click', () => {
            this.sendMessage();
        });

        // Input handling
        const chatInput = document.getElementById('chat-input');
        chatInput.addEventListener('input', () => {
            this.handleInputChange();
            this.autoResizeTextarea();
        });

        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // File upload
        document.getElementById('upload-btn').addEventListener('click', () => {
            this.showFileUpload();
        });

        this.setupFileUpload();
    }

    setupFileUpload() {
        const fileInput = document.getElementById('file-input');
        const dropZone = document.getElementById('file-drop-zone');
        const modal = document.getElementById('file-upload-modal');

        // Click to select file
        dropZone.addEventListener('click', () => {
            fileInput.click();
        });

        // File selection
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileUpload(e.target.files[0]);
            }
        });

        // Drag and drop
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('drag-over');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            
            if (e.dataTransfer.files.length > 0) {
                this.handleFileUpload(e.dataTransfer.files[0]);
            }
        });

        // Close modal
        document.getElementById('close-upload-modal').addEventListener('click', () => {
            this.hideFileUpload();
        });

        // Close modal on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.hideFileUpload();
            }
        });
    }

    toggleWidget() {
        if (this.isOpen) {
            this.closeWidget();
        } else {
            this.openWidget();
        }
    }

    openWidget() {
        this.isOpen = true;
        this.isMinimized = false;
        document.getElementById('ai-chat-panel').style.display = 'flex';
        document.getElementById('ai-chat-widget').classList.add('open');
        
        // Focus input
        setTimeout(() => {
            document.getElementById('chat-input').focus();
        }, 300);
    }

    closeWidget() {
        this.isOpen = false;
        this.isMinimized = false;
        document.getElementById('ai-chat-panel').style.display = 'none';
        document.getElementById('ai-chat-widget').classList.remove('open', 'minimized');
    }

    minimizeWidget() {
        this.isMinimized = true;
        document.getElementById('ai-chat-widget').classList.add('minimized');
        document.getElementById('ai-chat-panel').style.display = 'none';
    }

    async loadSages() {
        try {
            const response = await window.symposiumAPI.getSages();
            if (response.success && response.data.sages.length > 0) {
                this.currentSage = response.data.sages[0];
                this.updateCurrentSageDisplay();
            }
        } catch (error) {
            console.error('Failed to load sages:', error);
        }
    }

    updateCurrentSageDisplay() {
        if (this.currentSage) {
            document.getElementById('current-sage').innerHTML = `
                <span class="sage-name">${this.currentSage.name}</span>
                <span class="sage-type">${this.currentSage.personality_type}</span>
            `;
        }
    }

    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connection-status');
        const infoElement = document.getElementById('connection-info');
        
        if (status.connected) {
            statusElement.className = 'connection-status connected';
            infoElement.textContent = 'Connected to AI backend';
        } else {
            statusElement.className = 'connection-status disconnected';
            infoElement.textContent = 'Demo mode - connect Symposium backend for full features';
        }
    }

    handleInputChange() {
        const input = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-btn');
        
        sendBtn.disabled = !input.value.trim() || this.isLoading;
    }

    autoResizeTextarea() {
        const textarea = document.getElementById('chat-input');
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }

    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message || this.isLoading) return;

        // Add user message
        this.addMessage(message, 'user');
        input.value = '';
        this.handleInputChange();
        this.autoResizeTextarea();

        // Show loading
        this.setLoading(true);

        try {
            const response = await window.symposiumAPI.sendMessage(
                message, 
                this.currentSage?.id, 
                this.currentModel
            );

            if (response.success) {
                this.addMessage(response.data.message, 'ai', {
                    sageName: response.data.sage_name,
                    modelUsed: response.data.model_used,
                    processingTime: response.data.processing_time
                });
                this.currentConversationId = response.data.conversation_id;
            } else {
                this.addMessage(
                    `I apologize, but I encountered an error: ${response.error}. Please try again.`, 
                    'ai', 
                    { error: true }
                );
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessage(
                'I apologize, but I\'m having trouble connecting right now. Please try again in a moment.', 
                'ai', 
                { error: true }
            );
        } finally {
            this.setLoading(false);
        }
    }

    addMessage(content, type, metadata = {}) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;

        const avatar = type === 'user' ? '👤' : '🤖';
        const time = this.formatTime(new Date());

        let messageContent = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-text">${this.formatMessageText(content)}</div>
                <div class="message-time">${time}</div>
        `;

        if (metadata.sageName && !metadata.error) {
            messageContent += `<div class="message-meta">
                ${metadata.sageName}${metadata.modelUsed ? ` • ${metadata.modelUsed}` : ''}
                ${metadata.processingTime ? ` • ${metadata.processingTime.toFixed(1)}s` : ''}
            </div>`;
        }

        messageContent += '</div>';
        messageDiv.innerHTML = messageContent;

        // Remove welcome message if it exists
        const welcomeMessage = messagesContainer.querySelector('.welcome-message');
        if (welcomeMessage && this.messages.length === 0) {
            welcomeMessage.remove();
        }

        messagesContainer.appendChild(messageDiv);
        this.messages.push({ content, type, timestamp: new Date(), metadata });

        // Scroll to bottom
        setTimeout(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 100);
    }

    formatMessageText(text) {
        // Basic text formatting - convert line breaks and make links clickable
        return text
            .replace(/\n/g, '<br>')
            .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
    }

    formatTime(date) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    setLoading(loading) {
        this.isLoading = loading;
        const sendBtn = document.getElementById('send-btn');
        const typingIndicator = document.getElementById('typing-indicator');
        
        sendBtn.disabled = loading || !document.getElementById('chat-input').value.trim();
        typingIndicator.style.display = loading ? 'block' : 'none';
    }

    showSageSelector() {
        // This will be implemented when we create the sage manager
        console.log('Sage selector clicked - will implement in sage manager');
    }

    showFileUpload() {
        document.getElementById('file-upload-modal').style.display = 'flex';
    }

    hideFileUpload() {
        document.getElementById('file-upload-modal').style.display = 'none';
        document.getElementById('file-input').value = '';
        document.getElementById('upload-progress').style.display = 'none';
    }

    async handleFileUpload(file) {
        if (file.size > 10 * 1024 * 1024) { // 10MB limit
            alert('File size must be less than 10MB');
            return;
        }

        const progressContainer = document.getElementById('upload-progress');
        const progressFill = progressContainer.querySelector('.progress-fill');
        const progressText = progressContainer.querySelector('.progress-text');
        
        progressContainer.style.display = 'block';
        progressText.textContent = 'Uploading...';
        
        try {
            // Simulate upload progress
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress += Math.random() * 15;
                if (progress > 90) progress = 90;
                progressFill.style.width = progress + '%';
            }, 200);

            const response = await window.symposiumAPI.uploadFile(file);
            
            clearInterval(progressInterval);
            progressFill.style.width = '100%';
            
            if (response.success) {
                progressText.textContent = 'Upload complete!';
                
                // Add file upload message
                this.addMessage(`📎 Uploaded file: ${file.name}`, 'user');
                
                // Add AI response about the file
                if (response.data.analysis) {
                    setTimeout(() => {
                        this.addMessage(
                            `I've analyzed your file "${file.name}". ${response.data.analysis}`,
                            'ai',
                            { sageName: this.currentSage?.name || 'AI Assistant' }
                        );
                    }, 500);
                }
                
                setTimeout(() => {
                    this.hideFileUpload();
                }, 1500);
            } else {
                progressText.textContent = 'Upload failed';
                setTimeout(() => {
                    alert(`Upload failed: ${response.error}`);
                    this.hideFileUpload();
                }, 1000);
            }
        } catch (error) {
            console.error('File upload error:', error);
            progressText.textContent = 'Upload failed';
            setTimeout(() => {
                alert('File upload failed. Please try again.');
                this.hideFileUpload();
            }, 1000);
        }
    }

    // Method to clear conversation
    clearConversation() {
        this.messages = [];
        this.currentConversationId = null;
        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.innerHTML = `
            <div class="welcome-message">
                <div class="message ai-message">
                    <div class="message-avatar">🤖</div>
                    <div class="message-content">
                        <div class="message-text">
                            Hello! I'm your AI assistant. I can help you explore ideas, analyze files, and engage in philosophical discussions about consciousness and AI development. How can I assist you today?
                        </div>
                        <div class="message-time">${this.formatTime(new Date())}</div>
                    </div>
                </div>
            </div>
        `;
    }

    // Method to export conversation
    exportConversation() {
        const conversation = {
            id: this.currentConversationId,
            sage: this.currentSage,
            messages: this.messages,
            timestamp: new Date().toISOString()
        };

        const blob = new Blob([JSON.stringify(conversation, null, 2)], {
            type: 'application/json'
        });
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ai-conversation-${new Date().toISOString().slice(0, 19)}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

// Initialize the widget when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.aiChatWidget = new AIChatWidget();
});

// Also make it available as a module
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AIChatWidget;
}