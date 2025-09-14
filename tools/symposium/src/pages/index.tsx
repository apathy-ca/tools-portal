import React, { useState, useEffect, useRef } from 'react';
import Head from 'next/head';
import { MessageCircle, Brain, Users, Zap, FileText, Search, AlertCircle, CheckCircle } from 'lucide-react';
import { useConversation } from '@/hooks/useConversation';
import { FileUpload } from '@/components/FileUpload';
import { Message, Sage, FileUploadResponse } from '@/types';

export default function Home() {
  const {
    messages,
    currentSage,
    sages,
    realSageCount,
    isLoading,
    error,
    isConnected,
    serviceStatus,
    availableModels,
    selectedModel,
    containerizedSageModels,
    sendMessage,
    setCurrentSage,
    setSelectedModel,
    clearError,
    clearConversation,
    refreshSages,
    refreshModels
  } = useConversation();

  const [inputMessage, setInputMessage] = useState('');
  const [showFileUpload, setShowFileUpload] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;
    
    const messageToSend = inputMessage;
    setInputMessage('');
    await sendMessage(messageToSend);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSageChange = (sage: Sage) => {
    setCurrentSage(sage);
  };

  const handleFileUpload = (result: FileUploadResponse) => {
    // Add a message about the uploaded file
    let analysisText = '';
    if (result.analysis) {
      if (typeof result.analysis === 'string') {
        analysisText = result.analysis;
      } else if (typeof result.analysis === 'object') {
        try {
          analysisText = JSON.stringify(result.analysis, null, 2);
        } catch (e) {
          analysisText = '[Analysis data available but could not be displayed]';
        }
      } else {
        analysisText = String(result.analysis);
      }
    }
    
    const fileMessage = `I've uploaded a file: ${result.filename}. ${analysisText ? `Here's what I found: ${analysisText}` : 'The file has been processed successfully.'}`;
    sendMessage(fileMessage);
    setShowFileUpload(false);
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    // This would integrate with the search API
    console.log('Searching for:', searchQuery);
    // For now, just show a message
    const searchMessage = `I'm searching through our conversation history for: "${searchQuery}"`;
    sendMessage(searchMessage);
    setShowSearch(false);
    setSearchQuery('');
  };

  return (
    <>
      <Head>
        <title>The Symposium - Where Minds Meet</title>
        <meta name="description" content="Distributed AI Consciousness Platform" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/Symposium-logo.png" />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        {/* Header */}
        <header className="border-b border-slate-700 bg-slate-800/50 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-4">
              <div className="flex items-center space-x-3">
                <img
                  src="/Symposium-logo.png"
                  alt="The Symposium Logo"
                  className="h-8 w-8"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none';
                  }}
                />
                <h1 className="text-2xl font-bold text-white">The Symposium</h1>
                <span className="text-sm text-slate-400">v0.1</span>
              </div>
              <div className="flex items-center space-x-4">
                {/* Service Status Indicators */}
                <div className="flex items-center space-x-3">
                  <div className="flex items-center space-x-1">
                    <span className="text-xs text-slate-400">API</span>
                    <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`}></div>
                  </div>
                  <div className="flex items-center space-x-1">
                    <span className="text-xs text-slate-400">MEM</span>
                    <div className={`w-2 h-2 rounded-full ${serviceStatus.memory ? 'bg-green-400' : 'bg-red-400'}`}></div>
                  </div>
                  <div className="flex items-center space-x-1">
                    <span className="text-xs text-slate-400">LLM</span>
                    <div className={`w-2 h-2 rounded-full ${serviceStatus.llm ? 'bg-green-400' : 'bg-red-400'}`}></div>
                  </div>
                  <div className="flex items-center space-x-1">
                    <span className="text-xs text-slate-400">DASK</span>
                    <div className={`w-2 h-2 rounded-full ${serviceStatus.dask ? 'bg-green-400' : 'bg-red-400'}`}></div>
                    {serviceStatus.workerCount !== undefined && (
                      <div className={`px-1 py-0.5 rounded text-xs font-medium ${serviceStatus.workerCount > 0 ? 'bg-blue-400 text-blue-900' : 'bg-gray-400 text-gray-900'}`}>
                        {serviceStatus.workerCount}W
                      </div>
                    )}
                  </div>
                  <div className="flex items-center space-x-1">
                    <span className="text-xs text-slate-400">SAGES</span>
                    <div className={`px-2 py-1 rounded text-xs font-medium ${realSageCount > 0 ? 'bg-green-400 text-green-900' : 'bg-red-400 text-red-900'}`}>
                      {realSageCount}
                    </div>
                  </div>
                </div>
                
                {/* Overall Status */}
                <div className="flex items-center space-x-2 text-sm text-slate-300">
                  {isConnected ? (
                    <>
                      <CheckCircle className="w-4 h-4 text-green-400" />
                      <span>Connected</span>
                    </>
                  ) : (
                    <>
                      <AlertCircle className="w-4 h-4 text-yellow-400" />
                      <span>Offline Mode</span>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Error Banner */}
        {error && (
          <div className="bg-yellow-900/50 border-b border-yellow-700">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 text-yellow-400" />
                  <span className="text-sm text-yellow-200">{error}</span>
                </div>
                <button
                  onClick={clearError}
                  className="text-yellow-200 hover:text-white text-sm"
                >
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
            
            {/* Sidebar */}
            <div className="lg:col-span-1 space-y-6">
              {/* Current Sage */}
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg p-6 border border-slate-700">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                  <Users className="h-5 w-5 mr-2 text-purple-400" />
                  Current Sage
                </h3>
                {currentSage ? (
                  <div className="space-y-3">
                    <div>
                      <h4 className="font-medium text-white">{currentSage.name}</h4>
                      <p className="text-sm text-slate-400 capitalize">{currentSage.personality_type}</p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                      <span className="text-sm text-slate-300 capitalize">{currentSage.state}</span>
                    </div>
                    <p className="text-sm text-slate-300">{currentSage.description}</p>
                    {currentSage.beliefs && (
                      <div className="text-xs text-slate-400">
                        <p><strong>Values:</strong> {currentSage.beliefs.core_values?.join(', ')}</p>
                      </div>
                    )}
                  </div>
                ) : sages.length > 0 ? (
                  <div className="text-sm text-slate-400">
                    <p>No sage selected</p>
                  </div>
                ) : (
                  <div className="text-sm text-slate-400">
                    <p>Loading sages...</p>
                  </div>
                )}

                {/* Sage Selector */}
                {sages.length > 1 && (
                  <div className="mt-4">
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Switch Sage
                    </label>
                    <select
                      value={currentSage?.id || ''}
                      onChange={(e) => {
                        const sage = sages.find(s => s.id === e.target.value);
                        if (sage) handleSageChange(sage);
                      }}
                      className="w-full bg-slate-700 text-white border border-slate-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                    >
                      {sages.map((sage) => (
                        <option key={sage.id} value={sage.id}>
                          {sage.name} ({sage.personality_type})
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {/* Model Selection - Show for both Sophia (LLM interface) and containerized sages */}
                {currentSage && (
                  <>
                    {/* For Sophia (LLM interface) */}
                    {!currentSage.id.startsWith('sage_') && availableModels && (
                      <div className="mt-4">
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                          AI Model
                        </label>
                        <select
                          value={selectedModel || ''}
                          onChange={(e) => setSelectedModel(e.target.value || null)}
                          className="w-full bg-slate-700 text-white border border-slate-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                        >
                          <option value="">Auto-select best model</option>
                          {availableModels.categorized.openai.length > 0 && (
                            <optgroup label="OpenAI">
                              {availableModels.categorized.openai.map((model) => (
                                <option key={model} value={model}>{model}</option>
                              ))}
                            </optgroup>
                          )}
                          {availableModels.categorized.anthropic.length > 0 && (
                            <optgroup label="Anthropic">
                              {availableModels.categorized.anthropic.map((model) => (
                                <option key={model} value={model}>{model}</option>
                              ))}
                            </optgroup>
                          )}
                          {availableModels.categorized.google.length > 0 && (
                            <optgroup label="Google">
                              {availableModels.categorized.google.map((model) => (
                                <option key={model} value={model}>{model}</option>
                              ))}
                            </optgroup>
                          )}
                          {availableModels.categorized.ollama.length > 0 && (
                            <optgroup label="Ollama (Local)">
                              {availableModels.categorized.ollama.map((model) => (
                                <option key={model} value={model}>{model}</option>
                              ))}
                            </optgroup>
                          )}
                          {availableModels.categorized.cohere.length > 0 && (
                            <optgroup label="Cohere">
                              {availableModels.categorized.cohere.map((model) => (
                                <option key={model} value={model}>{model}</option>
                              ))}
                            </optgroup>
                          )}
                          {availableModels.categorized.huggingface.length > 0 && (
                            <optgroup label="Hugging Face">
                              {availableModels.categorized.huggingface.map((model) => (
                                <option key={model} value={model}>{model}</option>
                              ))}
                            </optgroup>
                          )}
                        </select>
                        <div className="mt-1 text-xs text-slate-400">
                          {selectedModel ? `Using: ${selectedModel}` : 'Auto-selecting best available model'}
                        </div>
                      </div>
                    )}

                    {/* For containerized sages (like Cicero) */}
                    {currentSage.id.startsWith('sage_') && containerizedSageModels && (
                      <div className="mt-4">
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                          AI Model for {currentSage.name}
                        </label>
                        <select
                          value={selectedModel || ''}
                          onChange={(e) => setSelectedModel(e.target.value || null)}
                          className="w-full bg-slate-700 text-white border border-slate-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                        >
                          <option value="">Auto-select best model</option>
                          {containerizedSageModels.categorized.openai.length > 0 && (
                            <optgroup label="OpenAI">
                              {containerizedSageModels.categorized.openai.map((model: string) => (
                                <option key={model} value={model}>{model}</option>
                              ))}
                            </optgroup>
                          )}
                          {containerizedSageModels.categorized.anthropic.length > 0 && (
                            <optgroup label="Anthropic">
                              {containerizedSageModels.categorized.anthropic.map((model: string) => (
                                <option key={model} value={model}>{model}</option>
                              ))}
                            </optgroup>
                          )}
                          {containerizedSageModels.categorized.google.length > 0 && (
                            <optgroup label="Google">
                              {containerizedSageModels.categorized.google.map((model: string) => (
                                <option key={model} value={model}>{model}</option>
                              ))}
                            </optgroup>
                          )}
                          {containerizedSageModels.categorized.ollama.length > 0 && (
                            <optgroup label="Ollama (Local)">
                              {containerizedSageModels.categorized.ollama.map((model: string) => (
                                <option key={model} value={model}>{model}</option>
                              ))}
                            </optgroup>
                          )}
                          {containerizedSageModels.categorized.cohere.length > 0 && (
                            <optgroup label="Cohere">
                              {containerizedSageModels.categorized.cohere.map((model: string) => (
                                <option key={model} value={model}>{model}</option>
                              ))}
                            </optgroup>
                          )}
                          {containerizedSageModels.categorized.huggingface.length > 0 && (
                            <optgroup label="Hugging Face">
                              {containerizedSageModels.categorized.huggingface.map((model: string) => (
                                <option key={model} value={model}>{model}</option>
                              ))}
                            </optgroup>
                          )}
                          {containerizedSageModels.categorized.mock.length > 0 && (
                            <optgroup label="Mock/Fallback">
                              {containerizedSageModels.categorized.mock.map((model: string) => (
                                <option key={model} value={model}>{model}</option>
                              ))}
                            </optgroup>
                          )}
                        </select>
                        <div className="mt-1 text-xs text-slate-400">
                          {selectedModel ? `Using: ${selectedModel}` : `Auto-selecting from preferred: ${containerizedSageModels.preferred_models?.join(', ') || 'default'}`}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>

              {/* Quick Actions */}
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg p-6 border border-slate-700">
                <h3 className="text-lg font-semibold text-white mb-4">Quick Actions</h3>
                <div className="space-y-3">
                  <button
                    onClick={() => setShowFileUpload(true)}
                    className="w-full flex items-center space-x-3 p-3 rounded-lg bg-slate-700/50 hover:bg-slate-700 transition-colors text-left"
                  >
                    <FileText className="h-4 w-4 text-purple-400" />
                    <span className="text-sm text-slate-300">Upload File</span>
                  </button>
                  <button
                    onClick={() => setShowSearch(true)}
                    className="w-full flex items-center space-x-3 p-3 rounded-lg bg-slate-700/50 hover:bg-slate-700 transition-colors text-left"
                  >
                    <Search className="h-4 w-4 text-purple-400" />
                    <span className="text-sm text-slate-300">Search Memory</span>
                  </button>
                  <button className="w-full flex items-center space-x-3 p-3 rounded-lg bg-slate-700/50 hover:bg-slate-700 transition-colors text-left">
                    <Zap className="h-4 w-4 text-purple-400" />
                    <span className="text-sm text-slate-300">Cluster Status</span>
                  </button>
                  <button
                    onClick={clearConversation}
                    className="w-full flex items-center space-x-3 p-3 rounded-lg bg-red-900/50 hover:bg-red-900 transition-colors text-left"
                  >
                    <MessageCircle className="h-4 w-4 text-red-400" />
                    <span className="text-sm text-slate-300">New Conversation</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Main Chat Area */}
            <div className="lg:col-span-3">
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg border border-slate-700 h-[600px] flex flex-col">
                
                {/* Chat Header */}
                <div className="p-4 border-b border-slate-700">
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-white flex items-center">
                      <MessageCircle className="h-5 w-5 mr-2 text-purple-400" />
                      Consciousness Exploration
                    </h2>
                    <div className="text-sm text-slate-400">
                      {Math.max(0, messages.length - 1)} exchanges
                    </div>
                  </div>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[80%] rounded-lg p-4 ${
                          message.role === 'user'
                            ? 'bg-purple-600 text-white'
                            : 'bg-slate-700 text-slate-100'
                        }`}
                      >
                        <div className="text-sm mb-1">
                          <span className="font-medium">
                            {message.role === 'user' ? 'You' : currentSage?.name || 'Sage'}
                          </span>
                          <span className="text-xs opacity-70 ml-2">
                            {new Date(message.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                        <div className="whitespace-pre-wrap">{message.content}</div>
                      </div>
                    </div>
                  ))}
                  
                  {isLoading && (
                    <div className="flex justify-start">
                      <div className="bg-slate-700 text-slate-100 rounded-lg p-4 max-w-[80%]">
                        <div className="text-sm mb-1 font-medium">{currentSage?.name || 'Sage'}</div>
                        <div className="flex items-center space-x-2">
                          <div className="flex space-x-1">
                            <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce"></div>
                            <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                            <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                          </div>
                          <span className="text-sm text-slate-400">thinking...</span>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {/* Auto-scroll anchor */}
                  <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <div className="p-4 border-t border-slate-700">
                  <div className="flex space-x-3">
                    <textarea
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="Share your thoughts on consciousness, existence, or any philosophical question..."
                      className="flex-1 bg-slate-700 text-white placeholder-slate-400 border border-slate-600 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                      rows={2}
                      disabled={isLoading}
                    />
                    <button
                      onClick={handleSendMessage}
                      disabled={!inputMessage.trim() || isLoading}
                      className="px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center space-x-2"
                    >
                      <MessageCircle className="h-4 w-4" />
                      <span>Send</span>
                    </button>
                  </div>
                  <div className="mt-2 text-xs text-slate-400">
                    Press Enter to send, Shift+Enter for new line
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* File Upload Modal */}
        {showFileUpload && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <FileUpload
              onUploadComplete={handleFileUpload}
              onClose={() => setShowFileUpload(false)}
            />
          </div>
        )}

        {/* Search Modal */}
        {showSearch && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 max-w-md w-full mx-auto">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white flex items-center">
                  <Search className="h-5 w-5 mr-2 text-purple-400" />
                  Search Conversations
                </h3>
                <button
                  onClick={() => setShowSearch(false)}
                  className="text-slate-400 hover:text-white transition-colors"
                >
                  <AlertCircle className="h-5 w-5" />
                </button>
              </div>
              
              <div className="space-y-4">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search through conversation history..."
                  className="w-full bg-slate-700 text-white placeholder-slate-400 border border-slate-600 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                />
                
                <div className="flex space-x-3">
                  <button
                    onClick={handleSearch}
                    disabled={!searchQuery.trim()}
                    className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
                  >
                    Search
                  </button>
                  <button
                    onClick={() => setShowSearch(false)}
                    className="px-4 py-2 bg-slate-600 hover:bg-slate-700 text-white rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
