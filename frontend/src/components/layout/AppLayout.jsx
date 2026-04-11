import React from 'react';
import useAppStore from '../../store/useAppStore';
import FloatingCommandBar from '../ui/FloatingCommandBar';
import ArchitectureGraph from '../graph/ArchitectureGraph';
import ChatInterface from '../chat/ChatInterface';

const AppLayout = () => {
  const { repo } = useAppStore();
  const isReady = repo.status === 'ready';

  return (
    <div
      className="relative flex w-full h-screen overflow-hidden"
      style={{ background: '#090A0F', color: '#FFFFFF' }}
    >
      {/* -------------------------------------------------------
          Floating Command Bar — always rendered above the canvas
          (shows minimised pill after ingestion)
       ------------------------------------------------------- */}
      <FloatingCommandBar />

      {/* -------------------------------------------------------
          Empty state: subtle grid pattern while waiting for repo
       ------------------------------------------------------- */}
      {!isReady && (
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            opacity: 0.15,
            backgroundImage:
              'linear-gradient(#1E2230 1px, transparent 1px), linear-gradient(90deg, #1E2230 1px, transparent 1px)',
            backgroundSize: '40px 40px',
          }}
        />
      )}

      {/* -------------------------------------------------------
          Main Split View — only shown when repo is ready
       ------------------------------------------------------- */}
      {isReady && (
        <>
          {/* Left 60% — interactive React Flow graph */}
          <div className="w-[60%] h-full">
            <ArchitectureGraph />
          </div>

          {/* Divider */}
          <div className="w-px bg-[#1E2230] flex-shrink-0" />

          {/* Right 40% — chat interface */}
          <div className="w-[40%] h-full flex flex-col">
            <ChatInterface />
          </div>
        </>
      )}
    </div>
  );
};

export default AppLayout;
