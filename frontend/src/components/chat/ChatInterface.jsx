import React, { useRef, useEffect } from 'react';
import useAppStore from '../../store/useAppStore';
import QueryInput from './QueryInput';
import CitationChip from './CitationChip';

// Helper to parse citations like [src/main.py] and render CitationChips
const renderContentWithCitations = (content) => {
  if (!content) return null;
  // This simple regex looks for [text]. Note: could collide with regular markdown links if not careful,
  // but for the sake of the CODE Sherpa specific citations, it works.
  const parts = content.split(/(\[[^[\]]+\])/g);
  
  return parts.map((part, index) => {
    if (part.startsWith('[') && part.endsWith(']')) {
      const nodeId = part.slice(1, -1);
      // We assume it's a citation if it looks like a file path or module name e.g., src.main or main.py
      return <CitationChip key={index} nodeId={nodeId} />;
    }
    return <span key={index}>{part}</span>;
  });
};

const ChatInterface = () => {
  const { chatHistory, isLoadingChat, repo } = useAppStore();
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, isLoadingChat]);

  if (repo.status !== 'ready') return null;

  return (
    <div className="flex flex-col h-full bg-[var(--color-telemetry-bg)] border-l border-[var(--color-telemetry-border)]">
      <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6">
        {chatHistory.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center text-[var(--color-telemetry-muted)] font-[var(--font-jetbrains)] text-sm">
            <span className="mb-2">SYSTEM.READY</span>
            <span>Awaiting input...</span>
          </div>
        ) : (
          chatHistory.map((msg, idx) => (
            <div 
              key={idx} 
              className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
            >
              <div className="text-[10px] text-[var(--color-telemetry-muted)] font-[var(--font-jetbrains)] mb-1 uppercase">
                {msg.role === 'user' ? 'USER_QUERY' : 'SHERPA_RESPONSE'}
              </div>
              <div 
                className={`max-w-[85%] p-4 text-[14px] leading-relaxed whitespace-pre-wrap ${
                  msg.role === 'user' 
                    ? 'bg-[var(--color-telemetry-border)] text-[var(--color-telemetry-text)]' 
                    : msg.isError
                      ? 'bg-red-900/20 text-red-400 border border-red-500/50'
                      : 'bg-transparent text-[var(--color-telemetry-text)]'
                }`}
              >
                {renderContentWithCitations(msg.content)}
              </div>
            </div>
          ))
        )}

        {isLoadingChat && (
          <div className="flex flex-col items-start">
            <div className="text-[10px] text-[var(--color-telemetry-muted)] font-[var(--font-jetbrains)] mb-1 uppercase">
              SHERPA_PROCESSING
            </div>
            <div className="font-[var(--font-jetbrains)] text-[var(--color-telemetry-muted)] flex items-center gap-2">
              <span>Analyzing sources... [====&nbsp;&nbsp;&nbsp;&nbsp;]</span>
              <span className="w-2 h-4 bg-[var(--color-telemetry-accent)] animate-blink inline-block"></span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <QueryInput />
    </div>
  );
};

export default ChatInterface;
