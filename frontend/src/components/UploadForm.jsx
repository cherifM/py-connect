import React, { useState, useRef, useCallback } from 'react';
import axios from 'axios';
import './UploadForm.css';

// Inline SVG Icons
const UploadIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
    <polyline points="17 8 12 3 7 8"></polyline>
    <line x1="12" y1="3" x2="12" y2="15"></line>
  </svg>
);

const PackageIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="16.5" y1="9.4" x2="7.5" y2="4.21"></line>
    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
    <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
    <line x1="12" y1="22.08" x2="12" y2="12"></line>
  </svg>
);

const XIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="6" x2="6" y2="18"></line>
    <line x1="6" y1="6" x2="18" y2="18"></line>
  </svg>
);

const API_URL = 'http://backend:8000/api';

function UploadForm({ onUploadSuccess, onCancel }) {
  const [formData, setFormData] = useState({
    name: '',
    description: ''
  });
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState({ text: '', type: '', dismissible: false });
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);
  
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDragging) setIsDragging(true);
  }, [isDragging]);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    const files = e.dataTransfer.files;
    if (files && files[0]) {
      handleFileSelect(files[0]);
    }
  }, []);

  const handleFileSelect = (selectedFile) => {
    if (selectedFile.type === 'application/zip' || selectedFile.name.endsWith('.zip')) {
      setFile(selectedFile);
      setMessage({ text: '', type: '' });
    } else {
      setMessage({ 
        text: 'Please upload a valid ZIP file.', 
        type: 'error' 
      });
    }
  };

  const handleFileInputChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      handleFileSelect(selectedFile);
    }
  };

  const removeFile = (e) => {
    e.stopPropagation();
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!file || !formData.name.trim()) {
      setMessage({ 
        text: 'Please provide both app name and ZIP file', 
        type: 'error',
        dismissible: true 
      });
      return;
    }
    
    setIsUploading(true);
    setMessage({ 
      text: 'Uploading your app... This may take a moment.', 
      type: 'info',
      dismissible: false 
    });
    
    const formDataToSend = new FormData();
    formDataToSend.append('name', formData.name.trim());
    if (formData.description) {
      formDataToSend.append('description', formData.description.trim());
    }
    formDataToSend.append('file', file);
    
    try {
      const response = await axios.post(`${API_URL}/publish`, formDataToSend, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setMessage({ 
            text: `Uploading... ${progress}%`, 
            type: 'info',
            dismissible: false 
          });
        }
      });
      
      setMessage({ 
        text: 'App published successfully! Redirecting...', 
        type: 'success',
        dismissible: true 
      });
      
      // Reset form
      setFormData({
        name: '',
        description: ''
      });
      setFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
      if (onUploadSuccess) {
        // Small delay to show success message before redirecting
        setTimeout(() => onUploadSuccess(response.data), 1500);
      }
    } catch (error) {
      console.error('Error publishing app:', error);
      setMessage({ 
        text: error.response?.data?.detail || 'Failed to publish app. Please try again.', 
        type: 'error',
        dismissible: true 
      });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="upload-form">
      <div className="form-header">
        <h3>Publish New App</h3>
        <p className="form-subtitle">Fill in the details below to publish your application</p>
      </div>
      
      <div className="form-body">
        <div className="form-group">
          <label htmlFor="app-name">App Name <span className="required">*</span></label>
          <input
            type="text"
            id="app-name"
            value={formData.name}
            onChange={(e) => setFormData({...formData, name: e.target.value})}
            placeholder="My Awesome App"
            required
            disabled={isUploading}
            className={isUploading ? 'disabled' : ''}
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="app-description">Description <span className="optional">(Optional)</span></label>
          <div className="textarea-container">
            <textarea
              id="app-description"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              placeholder="A brief description of your app"
              rows="3"
              disabled={isUploading}
              className={isUploading ? 'disabled' : ''}
              maxLength="500"
            />
            <div className="character-count">
              {formData.description ? formData.description.length : 0}/500
            </div>
          </div>
        </div>
        
        <div className="form-group">
          <label>Upload App <span className="required">*</span></label>
          <div 
            className={`file-upload ${isDragging ? 'dragging' : ''} ${isUploading ? 'disabled' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => !isUploading && fileInputRef.current?.click()}
            aria-disabled={isUploading}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileInputChange}
              accept=".zip"
              className="file-input"
              required
              disabled={isUploading}
            />
            
            {isUploading ? (
              <div className="upload-loading">
                <div className="spinner"></div>
                <p>Uploading your app...</p>
              </div>
            ) : (
              <>
                <div className="upload-icon">
                  <UploadIcon />
                </div>
                <p className="upload-text">
                  {file ? (
                    <>
                      <span className="file-name">{file.name}</span>
                      <span className="file-size">({formatFileSize(file.size)})</span>
                    </>
                  ) : (
                    'Drag & drop your ZIP file here or click to browse'
                  )}
                </p>
                <p className="upload-hint">Supports: .zip (max 50MB)</p>
              </>
            )}
            
            {!isUploading && file && (
              <button 
                type="button" 
                className="remove-file"
                onClick={(e) => {
                  e.stopPropagation();
                  setFile(null);
                  if (fileInputRef.current) {
                    fileInputRef.current.value = '';
                  }
                }}
                disabled={isUploading}
                aria-label="Remove file"
              >
                <XIcon />
              </button>
            )}
          </div>
        </div>
        
        {message && (
          <div className={`message ${message.type} ${message.dismissible ? 'dismissible' : ''}`}>
            <div className="message-content">
              {message.type === 'success' ? (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                  <polyline points="22 4 12 14.01 9 11.01"></polyline>
                </svg>
              ) : message.type === 'error' ? (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="15" y1="9" x2="9" y2="15"></line>
                  <line x1="9" y1="9" x2="15" y2="15"></line>
                </svg>
              ) : (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="12" y1="16" x2="12" y2="12"></line>
                  <line x1="12" y1="8" x2="12.01" y2="8"></line>
                </svg>
              )}
              <span>{message.text}</span>
            </div>
            {message.dismissible && (
              <button 
                type="button" 
                className="dismiss-message"
                onClick={() => setMessage(null)}
                aria-label="Dismiss message"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            )}
          </div>
        )}
      </div>
      
      <div className="form-footer">
        <div className="form-actions">
          <button 
            type="button" 
            className="cancel-button"
            onClick={onCancel}
            disabled={isUploading}
          >
            Cancel
          </button>
          <button 
            type="submit" 
            className={`submit-button ${isUploading ? 'loading' : ''}`}
            disabled={!formData.name || !file || isUploading}
          >
            {isUploading ? (
              <>
                <span className="spinner"></span>
                <span>Publishing...</span>
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="17 8 12 3 7 8"></polyline>
                  <line x1="12" y1="3" x2="12" y2="15"></line>
                </svg>
                <span>Publish App</span>
              </>
            )}
          </button>
        </div>
        <p className="form-note">
          By publishing, you agree to our <a href="/terms" target="_blank" rel="noopener noreferrer">Terms of Service</a> and <a href="/privacy" target="_blank" rel="noopener noreferrer">Privacy Policy</a>.
        </p>
      </div>
      
      {message.text && (
        <div className={`message ${message.type} ${message.dismissible ? 'dismissible' : ''}`}>
          <div className="message-content">
            {message.type === 'success' ? (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                <polyline points="22 4 12 14.01 9 11.01"></polyline>
              </svg>
            ) : message.type === 'error' ? (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="15" y1="9" x2="9" y2="15"></line>
                <line x1="9" y1="9" x2="15" y2="15"></line>
              </svg>
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="16" x2="12" y2="12"></line>
                <line x1="12" y1="8" x2="12.01" y2="8"></line>
              </svg>
            )}
            <span>{message.text}</span>
          </div>
          {message.dismissible && (
            <button 
              type="button" 
              className="dismiss-message"
              onClick={() => setMessage({ ...message, text: '' })}
              aria-label="Dismiss message"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          )}
        </div>
      )}
    </form>
  );
}

export default UploadForm;
