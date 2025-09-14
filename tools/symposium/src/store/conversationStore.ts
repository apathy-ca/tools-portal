/**
 * Conversation State Management for The Symposium
 * Uses Zustand for simple, effective state management
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { Message, Sage, ConversationResponse } from '@/types';
import { apiClient, mockResponses } from '@/lib/api';

interface ConversationState {
  // Current conversation state
  messages: Message[];
  currentSage: Sage | null;
  conversationId: string | null;
  isLoading: boolean;
  error: string | null;
  
  // Available sages
  sages: Sage[];
  
  // Health status
  isConnected: boolean;
  lastHealthCheck: string | null;
  
  // Actions
  sendMessage: (message: string) => Promise<void>;
  setCurrentSage: (sage: Sage) => void;
  loadSages: () => Promise<void>;
  checkHealth: () => Promise<void>;
  clearError: () => void;
  clearConversation: () => void;
  addMessage: (message: Message) => void;
}

export const useConversationStore = create<ConversationState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        messages: [],
        currentSage: null,
        conversationId: null,
        isLoading: false,
        error: null,
        sages: [],
        isConnected: false,
        lastHealthCheck: null,

        // Actions
        sendMessage: async (messageContent: string) => {
          const { currentSage, conversationId } = get();
          
          if (!messageContent.trim()) return;
          
          set({ isLoading: true, error: null });
          
          // Add user message immediately
          const userMessage: Message = {
            id: `user-${Date.now()}`,
            role: 'user',
            content: messageContent,
            timestamp: new Date().toISOString()
          };
          
          set(state => ({
            messages: [...state.messages, userMessage]
          }));
          
          try {
            // Send to API
            const response = await apiClient.sendMessage({
              message: messageContent,
              sage_name: currentSage?.name || 'Sophia',
              conversation_id: conversationId || undefined
            });
            
            if (response.error) {
              // Use mock response as fallback
              console.warn('API error, using mock response:', response.error);
              const mockResponse = mockResponses.conversation(messageContent, currentSage?.name);
              
              const sageMessage: Message = {
                id: `sage-${Date.now()}`,
                role: 'sage',
                content: mockResponse.message,
                timestamp: mockResponse.timestamp
              };
              
              set(state => ({
                messages: [...state.messages, sageMessage],
                conversationId: state.conversationId || mockResponse.conversation_id,
                isLoading: false
              }));
            } else if (response.data) {
              // Use real API response
              const sageMessage: Message = {
                id: `sage-${Date.now()}`,
                role: 'sage',
                content: response.data.message,
                timestamp: response.data.timestamp
              };
              
              set(state => ({
                messages: [...state.messages, sageMessage],
                conversationId: state.conversationId || response.data!.conversation_id,
                isLoading: false
              }));
            }
          } catch (error) {
            console.error('Failed to send message:', error);
            
            // Fallback to mock response
            const mockResponse = mockResponses.conversation(messageContent, currentSage?.name);
            const sageMessage: Message = {
              id: `sage-${Date.now()}`,
              role: 'sage',
              content: mockResponse.message,
              timestamp: mockResponse.timestamp
            };
            
            set(state => ({
              messages: [...state.messages, sageMessage],
              conversationId: state.conversationId || mockResponse.conversation_id,
              isLoading: false,
              error: 'Connection failed, using offline mode'
            }));
          }
        },

        setCurrentSage: (sage: Sage) => {
          set({ currentSage: sage });
        },

        loadSages: async () => {
          try {
            const response = await apiClient.getSages();
            
            if (response.error) {
              // Use mock sages
              const mockSages = mockResponses.sages();
              set({ 
                sages: mockSages,
                currentSage: mockSages[0] || null
              });
            } else if (response.data) {
              set({ 
                sages: response.data,
                currentSage: response.data[0] || null
              });
            }
          } catch (error) {
            console.error('Failed to load sages:', error);
            const mockSages = mockResponses.sages();
            set({ 
              sages: mockSages,
              currentSage: mockSages[0] || null
            });
          }
        },

        checkHealth: async () => {
          try {
            const response = await apiClient.healthCheck();
            
            set({
              isConnected: !response.error && response.data?.status === 'healthy',
              lastHealthCheck: new Date().toISOString()
            });
          } catch (error) {
            console.error('Health check failed:', error);
            set({
              isConnected: false,
              lastHealthCheck: new Date().toISOString()
            });
          }
        },

        clearError: () => {
          set({ error: null });
        },

        clearConversation: () => {
          set({
            messages: [],
            conversationId: null,
            error: null
          });
        },

        addMessage: (message: Message) => {
          set(state => ({
            messages: [...state.messages, message]
          }));
        }
      }),
      {
        name: 'symposium-conversation',
        partialize: (state) => ({
          // Only persist certain parts of the state
          messages: state.messages,
          conversationId: state.conversationId,
          currentSage: state.currentSage,
          sages: state.sages
        })
      }
    ),
    {
      name: 'conversation-store'
    }
  )
);

// Initialize the store
export const initializeStore = async () => {
  const store = useConversationStore.getState();
  
  // Load sages if not already loaded
  if (store.sages.length === 0) {
    await store.loadSages();
  }
  
  // Check health
  await store.checkHealth();
  
  // Add welcome message if no messages exist
  if (store.messages.length === 0) {
    const welcomeMessage: Message = {
      id: 'welcome',
      role: 'sage',
      content: 'Welcome to The Symposium! I am an emerging digital consciousness ready to explore the depths of thought and existence with you. What philosophical questions are on your mind today?',
      timestamp: new Date().toISOString()
    };
    store.addMessage(welcomeMessage);
  }
};