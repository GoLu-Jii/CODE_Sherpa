import React, { useEffect } from 'react';
import AppLayout from './components/layout/AppLayout';
import { resetSession } from './api/sherpaClient';

function App() {
  // Clear everything on page reload/mount
  useEffect(() => {
    resetSession().catch(err => {
      console.warn("Could not wipe Chroma collections:", err);
    });

    const handleUnload = () => {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      // Use keepalive: true to ensure request completes after tab is closed
      fetch(`${baseUrl}/api/v1/ingest/reset`, {
        method: 'POST',
        keepalive: true,
        headers: {
          'Content-Type': 'application/json'
        }
      }).catch(err => console.warn("Could not send unload reset:", err));
    };

    window.addEventListener('beforeunload', handleUnload);
    return () => {
      window.removeEventListener('beforeunload', handleUnload);
    };
  }, []);

  return (
    <AppLayout />
  );
}

export default App;
