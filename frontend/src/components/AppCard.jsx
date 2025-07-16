import React from 'react';
import './AppCard.css';

// For the MVP, we assume the backend runs on localhost:8000
// and the deployed apps will be on localhost at their assigned host_port.
// A real reverse proxy would make this much cleaner.
const HOST_URL = 'http://backend';

// Skeleton loader component
const AppCardSkeleton = () => (
  <div className="app-card skeleton">
    <div className="skeleton-header">
      <div className="skeleton-title"></div>
      <div className="skeleton-status"></div>
    </div>
    <div className="skeleton-description">
      <div className="skeleton-line"></div>
      <div className="skeleton-line"></div>
      <div className="skeleton-line short"></div>
    </div>
    <div className="skeleton-button"></div>
  </div>
);

function AppCard({ app, loading }) {
  // If loading prop is true, render skeleton
  if (loading) {
    return <AppCardSkeleton />;
  }

  const getStatusClass = (status) => {
    switch (status) {
      case 'running':
        return 'status-running';
      case 'creating':
      case 'deploying':
        return 'status-creating';
      case 'error':
      case 'failed':
        return 'status-error';
      case 'stopped':
      case 'terminated':
        return 'status-stopped';
      default:
        return 'status-unknown';
    }
  };

  const getStatusLabel = (status) => {
    const statusMap = {
      'running': 'Running',
      'creating': 'Deploying',
      'deploying': 'Deploying',
      'error': 'Error',
      'failed': 'Failed',
      'stopped': 'Stopped',
      'terminated': 'Terminated',
    };
    return statusMap[status] || status.charAt(0).toUpperCase() + status.slice(1);
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'running':
        return (
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
          </svg>
        );
      case 'creating':
      case 'deploying':
        return (
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="2" x2="12" y2="6"></line>
            <line x1="12" y1="18" x2="12" y2="22"></line>
            <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line>
            <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line>
            <line x1="2" y1="12" x2="6" y2="12"></line>
            <line x1="18" y1="12" x2="22" y2="12"></line>
            <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line>
            <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line>
          </svg>
        );
      case 'error':
      case 'failed':
        return (
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="15" y1="9" x2="9" y2="15"></line>
            <line x1="9" y1="9" x2="15" y2="15"></line>
          </svg>
        );
      default:
        return (
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
        );
    }
  };

  const statusClass = getStatusClass(app.status);
  const statusLabel = getStatusLabel(app.status);
  const statusIcon = getStatusIcon(app.status);
  const isAppAvailable = app.status === 'running' && app.internal_port;

  return (
    <div className="app-card">
      <div className="card-header">
        <h3 title={app.name}>{app.name}</h3>
        <span className={`status-pill ${statusClass}`}>
          {statusIcon}
          <span>{statusLabel}</span>
        </span>
      </div>
      
      <div className="card-body">
        <div className="tooltip-container">
          <p className="description" data-tooltip={app.description || 'No description provided.'}>
            {app.description || 'No description provided.'}
          </p>
          {app.description && (
            <div className="tooltip">
              {app.description}
              <span className="tooltip-arrow"></span>
            </div>
          )}
        </div>
        
        {app.url && (
          <div className="app-url">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
              <polyline points="15 3 21 3 21 9"></polyline>
              <line x1="10" y1="14" x2="21" y2="3"></line>
            </svg>
            <a 
              href={app.url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="app-url-link"
            >
              {new URL(app.url).hostname}
            </a>
          </div>
        )}
      </div>
      
      <div className="card-footer">
        {isAppAvailable ? (
          <a
            href={`${HOST_URL}:${app.internal_port}`}
            target="_blank"
            rel="noopener noreferrer"
            className="view-button"
          >
            <span>Open App</span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
              <polyline points="15 3 21 3 21 9"></polyline>
              <line x1="10" y1="14" x2="21" y2="3"></line>
            </svg>
          </a>
        ) : (
          <button 
            className="view-button-disabled" 
            disabled
            title={app.status === 'creating' || app.status === 'deploying' ? 'Your app is being deployed...' : 'App is not running'}
          >
            <span>Open App</span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="12"></line>
              <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}

AppCard.defaultProps = {
  loading: false,
};

export default AppCard;
