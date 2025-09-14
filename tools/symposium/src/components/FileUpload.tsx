/**
 * File Upload Component for The Symposium
 * Handles file uploads with drag-and-drop support
 */

import React, { useState, useCallback } from 'react';
import { Upload, File, X, AlertCircle, CheckCircle } from 'lucide-react';
import { apiClient } from '../lib/api';
import { FileUploadResponse } from '../types';

interface FileUploadProps {
  onUploadComplete?: (result: FileUploadResponse) => void;
  onClose?: () => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onUploadComplete, onClose }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<FileUploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      setSelectedFile(files[0]);
      setError(null);
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      setSelectedFile(files[0]);
      setError(null);
    }
  }, []);

  const handleUpload = useCallback(async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setError(null);

    try {
      const response = await apiClient.uploadFile(selectedFile);
      
      if (response.error) {
        // Handle error properly - convert object to string if needed
        const errorMessage = typeof response.error === 'string'
          ? response.error
          : JSON.stringify(response.error);
        setError(errorMessage);
      } else if (response.data) {
        setUploadResult(response.data);
        onUploadComplete?.(response.data);
      }
    } catch (err) {
      // Ensure error is always a string
      let errorMessage = 'Upload failed';
      if (err instanceof Error) {
        errorMessage = err.message;
      } else if (typeof err === 'object' && err !== null) {
        errorMessage = JSON.stringify(err);
      } else if (typeof err === 'string') {
        errorMessage = err;
      }
      setError(errorMessage);
    } finally {
      setIsUploading(false);
    }
  }, [selectedFile, onUploadComplete]);

  const handleReset = useCallback(() => {
    setSelectedFile(null);
    setUploadResult(null);
    setError(null);
  }, []);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 max-w-md mx-auto">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white flex items-center">
          <Upload className="h-5 w-5 mr-2 text-purple-400" />
          Upload File
        </h3>
        {onClose && (
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {!uploadResult ? (
        <>
          {/* File Drop Zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              isDragging
                ? 'border-purple-400 bg-purple-900/20'
                : 'border-slate-600 hover:border-slate-500'
            }`}
          >
            {selectedFile ? (
              <div className="space-y-3">
                <File className="h-12 w-12 text-purple-400 mx-auto" />
                <div>
                  <p className="text-white font-medium">{selectedFile.name}</p>
                  <p className="text-slate-400 text-sm">{formatFileSize(selectedFile.size)}</p>
                </div>
                <button
                  onClick={handleReset}
                  className="text-slate-400 hover:text-white text-sm"
                >
                  Choose different file
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                <Upload className="h-12 w-12 text-slate-400 mx-auto" />
                <div>
                  <p className="text-white">Drop your file here</p>
                  <p className="text-slate-400 text-sm">or click to browse</p>
                </div>
                <input
                  type="file"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="file-input"
                  accept=".txt,.pdf,.docx,.md,.json"
                />
                <label
                  htmlFor="file-input"
                  className="inline-block px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg cursor-pointer transition-colors"
                >
                  Browse Files
                </label>
              </div>
            )}
          </div>

          {/* Upload Button */}
          {selectedFile && (
            <div className="mt-4 space-y-3">
              <button
                onClick={handleUpload}
                disabled={isUploading}
                className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center justify-center space-x-2"
              >
                {isUploading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Uploading...</span>
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4" />
                    <span>Upload File</span>
                  </>
                )}
              </button>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="mt-4 p-3 bg-red-900/50 border border-red-700 rounded-lg flex items-center space-x-2">
              <AlertCircle className="h-4 w-4 text-red-400 flex-shrink-0" />
              <span className="text-red-200 text-sm">{error}</span>
            </div>
          )}
        </>
      ) : (
        /* Upload Success */
        <div className="space-y-4">
          <div className="flex items-center justify-center space-x-2 text-green-400">
            <CheckCircle className="h-8 w-8" />
            <span className="text-lg font-medium">Upload Successful!</span>
          </div>
          
          <div className="bg-slate-700 rounded-lg p-4 space-y-2">
            <div className="flex justify-between">
              <span className="text-slate-300">File:</span>
              <span className="text-white">{uploadResult.filename}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-300">Status:</span>
              <span className="text-green-400 capitalize">{uploadResult.status}</span>
            </div>
            {uploadResult.analysis && (
              <div className="mt-3">
                <span className="text-slate-300 text-sm">Analysis:</span>
                <div className="mt-1 text-slate-200 text-sm bg-slate-800 rounded p-2">
                  <pre className="whitespace-pre-wrap">
                    {typeof uploadResult.analysis === 'string'
                      ? uploadResult.analysis
                      : JSON.stringify(uploadResult.analysis, null, 2)
                    }
                  </pre>
                </div>
              </div>
            )}
          </div>

          <button
            onClick={handleReset}
            className="w-full px-4 py-2 bg-slate-600 hover:bg-slate-700 text-white rounded-lg transition-colors"
          >
            Upload Another File
          </button>
        </div>
      )}
    </div>
  );
};