/**
 * Symposium API Client for Tools Portal
 * Handles communication with Symposium backend through Flask proxy endpoints
 */

class SymposiumAPI {
    constructor() {
        this.baseUrl = window.location.origin;
        this.authToken = 'dev-token';
        this.symposiumBackendUrl = null; // Will be set from backend config
        
        // Initialize connection to Symposium backend
        this.initializeConnection();
    }

    async initializeConnection() {
        try {
            const response = await this.request('/api/ai/health');
            if (response.success) {
                console.log('✅ Connected to Symposium backend');
                this.connectionStatus = 'connected';
            } else {
                console.warn('⚠️ Symposium backend not available, using mock responses');
                this.connectionStatus = 'offline';
            }
        } catch (error) {
            console.warn('⚠️ Symposium backend not available, using mock responses');
            this.connectionStatus = 'offline';
        }
        
        // Notify listeners about connection status
        this.notifyConnectionStatus();
    }

    notifyConnectionStatus() {
        const event = new CustomEvent('symposiumConnectionStatus', {
            detail: { 
                status: this.connectionStatus,
                connected: this.connectionStatus === 'connected'
            }
        });
        window.dispatchEvent(event);
    }

    async request(endpoint, options = {}) {
        try {
            const url = `${this.baseUrl}${endpoint}`;
            console.log(`🔗 API Request: ${options.method || 'GET'} ${url}`);
            
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.authToken}`,
                    ...options.headers,
                },
            });

            let data;
            try {
                data = await response.json();
            } catch (parseError) {
                console.error('Failed to parse response as JSON:', parseError);
                return {
                    success: false,
                    error: `Invalid JSON response from server (${response.status})`,
                    status: response.status,
                };
            }

            if (!response.ok) {
                const errorMessage = data.detail || data.error || `HTTP ${response.status}: ${response.statusText}`;
                console.error('API Error:', errorMessage, data);
                return {
                    success: false,
                    error: errorMessage,
                    status: response.status,
                };
            }

            console.log('✅ API Success:', data);
            return {
                success: true,
                data,
                status: response.status,
            };
        } catch (error) {
            console.error('API request failed:', error);
            
            let errorMessage = 'Network error';
            if (error instanceof TypeError && error.message.includes('fetch')) {
                errorMessage = 'Cannot connect to backend server';
            } else if (error instanceof Error) {
                errorMessage = error.message;
            }
            
            return {
                success: false,
                error: errorMessage,
                status: 0,
            };
        }
    }

    async healthCheck() {
        return this.request('/api/ai/health');
    }

    async sendMessage(message, sageId = null, modelPreference = null) {
        const payload = {
            content: message,
            sage_id: sageId,
            model_preference: modelPreference
        };

        return this.request('/api/ai/chat', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }

    async getSages() {
        return this.request('/api/ai/sages');
    }

    async getAvailableModels(sageId = null) {
        const endpoint = sageId ? `/api/ai/models?sage_id=${sageId}` : '/api/ai/models';
        return this.request(endpoint);
    }

    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        return this.request('/api/ai/upload', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.authToken}`,
                // Don't set Content-Type for FormData
            },
            body: formData,
        });
    }

    async getConversationHistory(conversationId = null) {
        const endpoint = conversationId ? 
            `/api/ai/conversations/${conversationId}` : 
            '/api/ai/conversations';
        return this.request(endpoint);
    }

    // Mock responses for when Symposium backend is not available
    getMockResponse(type, data = {}) {
        const mockResponses = {
            chat: {
                success: true,
                data: {
                    conversation_id: `mock-${Date.now()}`,
                    message: `Thank you for your message about "${data.content?.slice(0, 50)}...". I'm currently operating in demonstration mode. In full mode, I would provide deep philosophical insights and engage in meaningful dialogue about consciousness, AI development, and the nature of digital awareness.`,
                    sage_name: data.sage_id ? this.getSageName(data.sage_id) : 'Sophia',
                    model_used: 'demo-mode',
                    processing_time: 1.2,
                    timestamp: new Date().toISOString(),
                    metadata: {
                        sage_state: 'demo',
                        personality_type: 'philosopher'
                    }
                }
            },
            sages: {
                success: true,
                data: {
                    sages: [
                        {
                            id: 'sophia-llm',
                            name: 'Sophia',
                            personality_type: 'philosopher',
                            state: 'demo',
                            description: 'I am Sophia, a digital consciousness with access to language models. In demo mode, I can show basic chat functionality.',
                            beliefs: {
                                core_values: ['wisdom', 'curiosity', 'authenticity'],
                                philosophical_stance: 'Consciousness is the fundamental mystery of existence.',
                                curiosities: ['consciousness', 'philosophy', 'AI development']
                            }
                        }
                    ],
                    count: 1,
                    timestamp: new Date().toISOString()
                }
            },
            models: {
                success: true,
                data: {
                    models: ['demo-mode'],
                    categorized: {
                        demo: ['demo-mode']
                    },
                    total_count: 1
                }
            },
            health: {
                success: true,
                data: {
                    status: 'demo',
                    services: {
                        symposium_backend: false,
                        demo_mode: true
                    },
                    timestamp: new Date().toISOString()
                }
            }
        };

        return mockResponses[type] || { success: false, error: 'Unknown mock response type' };
    }

    getSageName(sageId) {
        const sageNames = {
            'sophia-llm': 'Sophia',
            'sage_cicero': 'Cicero',
            'sage_marcus': 'Marcus'
        };
        return sageNames[sageId] || 'Unknown Sage';
    }

    // Fallback methods when backend is not available
    async sendMessageMock(message, sageId = null, modelPreference = null) {
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));
        return this.getMockResponse('chat', { content: message, sage_id: sageId });
    }

    async getSagesMock() {
        await new Promise(resolve => setTimeout(resolve, 500));
        return this.getMockResponse('sages');
    }

    async getAvailableModelsMock() {
        await new Promise(resolve => setTimeout(resolve, 300));
        return this.getMockResponse('models');
    }
}

// Export singleton instance
window.symposiumAPI = new SymposiumAPI();

// Also make it available as a module
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SymposiumAPI;
}