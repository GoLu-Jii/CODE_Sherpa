import React, { useEffect } from 'react';
import AppLayout from './components/layout/AppLayout';
import { resetSession } from './api/sherpaClient';

function App() {
  // Clear everything on page reload/mount
  useEffect(() => {
    resetSession().catch(err => {
      console.warn("Could not wipe Chroma collections:", err);
    });
  }, []);

  return (
    <AppLayout />
  );
}

export default App;
