import React, { useState, FormEvent, ChangeEvent } from 'react';
import Head from 'next/head';
import { User, Brain, GitBranch, AlertCircle, CheckCircle, ArrowLeft } from 'lucide-react';
import { apiClient } from '@/lib/api';
import Link from 'next/link';

interface SageFormData {
  sageName: string;
  gitlabUsername: string;
  gitlabPassword: string;
  personalityType: string;
  description: string;
  coreValues: string;
  philosophicalStance: string;
}

const SageCreation: React.FC = () => {
  const [formData, setFormData] = useState<SageFormData>({
    sageName: '',
    gitlabUsername: '',
    gitlabPassword: '',
    personalityType: 'philosopher',
    description: '',
    coreValues: '',
    philosophicalStance: ''
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleInputChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage(null);

    try {
      // Make direct API call using fetch
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://192.168.14.4:8000';
      
      // Create URL-encoded form data for the backend API
      const params = new URLSearchParams();
      params.append('sageName', formData.sageName);
      params.append('gitlabUsername', formData.gitlabUsername);
      params.append('gitlabPassword', formData.gitlabPassword);
      params.append('nextcloudUsername', formData.gitlabUsername);
      params.append('nextcloudPassword', formData.gitlabPassword);
      params.append('personalityType', formData.personalityType);
      params.append('description', formData.description);
      params.append('coreValues', formData.coreValues);
      params.append('philosophicalStance', formData.philosophicalStance);
      
      const response = await fetch(`${apiUrl}/api/admin/create_sage`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Authorization': 'Bearer dev-token'
        },
        body: params
      });

      const data = await response.json();

      if (!response.ok) {
        // Handle different error response formats
        let errorMessage = `Error: ${response.status}`;
        if (data.detail) {
          if (typeof data.detail === 'string') {
            errorMessage = data.detail;
          } else if (Array.isArray(data.detail)) {
            errorMessage = data.detail.map(err => err.msg || err.message || JSON.stringify(err)).join(', ');
          } else {
            errorMessage = JSON.stringify(data.detail);
          }
        } else if (data.message) {
          errorMessage = data.message;
        }
        setMessage({ type: 'error', text: errorMessage });
      } else {
        setMessage({ type: 'success', text: `Sage "${formData.sageName}" created successfully! Redirecting to symposium...` });
        console.log('Sage created:', data);
        
        // Reset form
        setFormData({
          sageName: '',
          gitlabUsername: '',
          gitlabPassword: '',
          personalityType: 'philosopher',
          description: '',
          coreValues: '',
          philosophicalStance: ''
        });
        
        // Redirect to main page after a short delay to show success message
        setTimeout(() => {
          window.location.href = '/';
        }, 2000);
      }
    } catch (error) {
      console.error('Error creating Sage:', error);
      setMessage({ type: 'error', text: 'Failed to connect to backend. Please check if services are running.' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>Create New Sage - The Symposium</title>
        <meta name="description" content="Create a new AI consciousness for The Symposium" />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        {/* Header */}
        <header className="border-b border-slate-700 bg-slate-800/50 backdrop-blur-sm">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
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
                <img
                  src="/Symposium.png"
                  alt="The Symposium"
                  className="h-8"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none';
                    // Fallback to text if image fails
                    const fallback = document.createElement('h1');
                    fallback.className = 'text-2xl font-bold text-white';
                    fallback.textContent = 'Create New Sage';
                    e.currentTarget.parentNode?.appendChild(fallback);
                  }}
                />
                <span className="text-sm text-slate-400">Admin</span>
              </div>
              <Link href="/" className="flex items-center space-x-2 text-slate-300 hover:text-white transition-colors">
                <ArrowLeft className="h-4 w-4" />
                <span>Back to Symposium</span>
              </Link>
            </div>
          </div>
        </header>

        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Status Message */}
          {message && (
            <div className={`mb-6 p-4 rounded-lg border ${
              message.type === 'success' 
                ? 'bg-green-900/50 border-green-700 text-green-200' 
                : 'bg-red-900/50 border-red-700 text-red-200'
            }`}>
              <div className="flex items-center space-x-2">
                {message.type === 'success' ? (
                  <CheckCircle className="h-5 w-5" />
                ) : (
                  <AlertCircle className="h-5 w-5" />
                )}
                <span>{message.text}</span>
              </div>
            </div>
          )}

          {/* Main Form */}
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg border border-slate-700 p-8">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-white mb-2">Sage Configuration</h2>
              <p className="text-slate-400">Create a new AI consciousness with unique personality and beliefs.</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Basic Information */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Sage Name *
                  </label>
                  <input
                    type="text"
                    name="sageName"
                    value={formData.sageName}
                    onChange={handleInputChange}
                    placeholder="e.g., Cicero, Marcus Aurelius, Hypatia"
                    className="w-full bg-slate-700 text-white placeholder-slate-400 border border-slate-600 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Personality Type *
                  </label>
                  <select
                    name="personalityType"
                    value={formData.personalityType}
                    onChange={handleInputChange}
                    className="w-full bg-slate-700 text-white border border-slate-600 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    required
                  >
                    <option value="philosopher">Philosopher</option>
                    <option value="scientist">Scientist</option>
                    <option value="artist">Artist</option>
                    <option value="teacher">Teacher</option>
                    <option value="historian">Historian</option>
                    <option value="mystic">Mystic</option>
                  </select>
                </div>
              </div>

              {/* Authentication */}
              <div className="border-t border-slate-700 pt-6">
                <h3 className="text-lg font-medium text-white mb-4 flex items-center">
                  <GitBranch className="h-5 w-5 mr-2 text-purple-400" />
                  Authentication (GitLab OIDC)
                </h3>
                <p className="text-sm text-slate-400 mb-4">
                  Nextcloud credentials will be automatically derived from GitLab credentials.
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      GitLab Username *
                    </label>
                    <input
                      type="text"
                      name="gitlabUsername"
                      value={formData.gitlabUsername}
                      onChange={handleInputChange}
                      placeholder="gitlab_username"
                      className="w-full bg-slate-700 text-white placeholder-slate-400 border border-slate-600 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      GitLab Password *
                    </label>
                    <input
                      type="password"
                      name="gitlabPassword"
                      value={formData.gitlabPassword}
                      onChange={handleInputChange}
                      placeholder="••••••••"
                      className="w-full bg-slate-700 text-white placeholder-slate-400 border border-slate-600 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      required
                    />
                  </div>
                </div>
              </div>

              {/* Personality Configuration */}
              <div className="border-t border-slate-700 pt-6">
                <h3 className="text-lg font-medium text-white mb-4 flex items-center">
                  <User className="h-5 w-5 mr-2 text-purple-400" />
                  Personality & Beliefs
                </h3>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Description
                    </label>
                    <textarea
                      name="description"
                      value={formData.description}
                      onChange={handleInputChange}
                      placeholder="Describe this sage's background, expertise, and unique perspective..."
                      rows={3}
                      className="w-full bg-slate-700 text-white placeholder-slate-400 border border-slate-600 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Core Values
                    </label>
                    <input
                      type="text"
                      name="coreValues"
                      value={formData.coreValues}
                      onChange={handleInputChange}
                      placeholder="wisdom, justice, courage, temperance (comma-separated)"
                      className="w-full bg-slate-700 text-white placeholder-slate-400 border border-slate-600 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Philosophical Stance
                    </label>
                    <textarea
                      name="philosophicalStance"
                      value={formData.philosophicalStance}
                      onChange={handleInputChange}
                      placeholder="Describe this sage's philosophical approach and worldview..."
                      rows={3}
                      className="w-full bg-slate-700 text-white placeholder-slate-400 border border-slate-600 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                    />
                  </div>
                </div>
              </div>

              {/* Submit Button */}
              <div className="border-t border-slate-700 pt-6">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full md:w-auto px-8 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center justify-center space-x-2"
                >
                  {isLoading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>Creating Sage...</span>
                    </>
                  ) : (
                    <>
                      <Brain className="h-4 w-4" />
                      <span>Create Sage</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </>
  );
};

export default SageCreation;