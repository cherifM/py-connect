import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import UploadForm from './components/UploadForm';
import AppCard from './components/AppCard';
import axios from 'axios';

// For the MVP, we assume the backend runs on localhost:8000
const API_BASE_URL = 'http://backend:8000/api';

// Skeleton loader for the apps grid
const AppsGridSkeleton = ({ count = 6 }) => (
  <div className="apps-grid">
    {Array.from({ length: count }).map((_, index) => (
      <AppCard key={`skeleton-${index}`} loading={true} />
    ))}
  </div>
);

function App() {
  const [apps, setApps] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [error, setError] = useState(null);

  const fetchApps = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE_URL}/apps`);
      setApps(response.data);
    } catch (error) {
      console.error('Error fetching apps:', error);
      setError('Failed to load apps. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchApps();
  }, [fetchApps]);

  const handleAppPublished = (newApp) => {
    setApps(prevApps => [newApp, ...prevApps]);
    setShowUploadForm(false);
  };

  const handleRetry = () => {
    fetchApps();
  };

  const renderContent = () => {
    if (isLoading) {
      return <AppsGridSkeleton />;
    }

    if (error) {
      return (
        <div className="error-state">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
          <h3>Something went wrong</h3>
          <p>{error}</p>
          <button 
            className="retry-button"
            onClick={handleRetry}
          >
            Retry
          </button>
        </div>
      );
    }

    if (apps.length === 0 && !showUploadForm) {
      return (
        <div className="empty-state">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <circle cx="10" cy="13" r="2"></circle>
            <path d="m20 17-1.09-1.09a2 2 0 0 0-2.82 0L10 22l-1-1"></path>
          </svg>
          <h3>No apps published yet</h3>
          <p>Get started by publishing your first app</p>
          <button 
            className="publish-button"
            onClick={() => setShowUploadForm(true)}
          >
            Publish New App
          </button>
        </div>
      );
    }

    return (
      <div className="apps-grid">
        {apps.map((app) => (
          <AppCard key={app.id} app={app} />
        ))}
      </div>
    );
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="logo">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
              <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
              <line x1="12" y1="22.08" x2="12" y2="12"></line>
            </svg>
            <h1>Posit Connect</h1>
          </div>
          <button 
            className={`publish-button ${showUploadForm ? 'cancel' : ''}`}
            onClick={() => setShowUploadForm(!showUploadForm)}
            disabled={isLoading}
          >
            {showUploadForm ? (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
                <span>Cancel</span>
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="12" y1="5" x2="12" y2="19"></line>
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                </svg>
                <span>Publish New App</span>
              </>
            )}
          </button>
        </div>
      </header>

      <main className="main-content">
        {showUploadForm && (
          <div className="upload-form-container">
            <UploadForm 
              onAppPublished={handleAppPublished} 
              onCancel={() => setShowUploadForm(false)}
            />
          </div>
        )}

        <div className="dashboard">
          <div className="dashboard-header">
            <h2>My Published Content</h2>
            {!isLoading && !error && apps.length > 0 && (
              <p className="app-count">
                {apps.length} {apps.length === 1 ? 'app' : 'apps'} published
              </p>
            )}
          </div>

          {renderContent()}
        </div>
      </main>
    </div>
  );
}

export default App;
