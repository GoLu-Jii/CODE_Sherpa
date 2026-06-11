import React, { useState } from 'react';
import useAppStore from '../../store/useAppStore';
import { sendChatMessage } from '../../api/sherpaClient';

const MODES = ['ASK', 'FILE', 'FUNCTION'];

const QueryInput = () => {
  const [query, setQuery] = useState('');
  const [targetName, setTargetName] = useState('');
  const [mode, setMode] = useState('ASK');
  const { addChatMessage, setLoadingChat, isLoadingChat, chatHistory } = useAppStore();

  const buildQuery = () => {
    if (mode === 'FILE') return `what does ${targetName.trim()} do`;
    if (mode === 'FUNCTION') return `what does the function ${targetName.trim()} do`;
    return query.trim();
  };

  const canSubmit = () => {
    if (isLoadingChat) return false;
    if (mode === 'ASK') return query.trim().length > 0;
    return targetName.trim().length > 0;
  };

  const handleSubmit = async () => {
    if (!canSubmit()) return;

    const finalQuery = buildQuery();
    setQuery('');
    setTargetName('');

    addChatMessage({ role: 'user', content: finalQuery, timestamp: new Date() });
    setLoadingChat(true);

    try {
      const historyForApi = chatHistory.map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));

      const response = await sendChatMessage(finalQuery, historyForApi);
      const answerPayload = response?.data;

      addChatMessage({
        role: 'assistant',
        content: answerPayload?.answer ?? 'No answer returned.',
        sources: answerPayload?.sources || [],
        timestamp: new Date(),
      });
    } catch (error) {
      addChatMessage({
        role: 'assistant',
        content: `Error: Failed to communicate with the Sherpa engine. (${error.message || 'Unknown error'})`,
        isError: true,
        timestamp: new Date(),
      });
    } finally {
      setLoadingChat(false);
    }
  };

  const inputStyle = {
    width: '100%',
    background: 'transparent',
    border: 'none',
    outline: 'none',
    color: '#E8EAF2',
    fontFamily: 'JetBrains Mono, monospace',
    fontSize: '13px',
    resize: 'none',
    lineHeight: '1.6',
  };

  const secondaryInputStyle = {
    ...inputStyle,
    fontSize: '12px',
    borderTop: '1px solid #1C2035',
    paddingTop: '8px',
    marginTop: '8px',
    color: '#C8CAD8',
  };

  return (
    <div
      style={{
        borderTop: '1px solid #1C2035',
        background: 'rgba(14,16,24,0.92)',
        padding: '12px 16px',
        flexShrink: 0,
        fontFamily: 'JetBrains Mono, monospace',
      }}
    >
      {/* Mode toggles */}
      <div style={{ display: 'flex', gap: '6px', marginBottom: '10px' }}>
        {MODES.map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            style={{
              padding: '3px 10px',
              fontSize: '10px',
              fontFamily: 'JetBrains Mono, monospace',
              background: 'transparent',
              border: mode === m ? '1px solid #FF6240' : '1px solid #1C2035',
              color: mode === m ? '#FF6240' : '#454B66',
              cursor: 'pointer',
              letterSpacing: '0.08em',
              transition: 'border-color 0.15s, color 0.15s',
            }}
          >
            {m}
          </button>
        ))}
      </div>

      {/* Main input */}
      {mode === 'ASK' && (
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="> ask about the codebase..."
          rows={2}
          style={{
            ...inputStyle,
            maxHeight: '120px',
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit();
            }
          }}
        />
      )}

      {mode === 'FILE' && (
        <input
          value={targetName}
          onChange={(e) => setTargetName(e.target.value)}
          placeholder="> filename e.g. hooks.py"
          style={{ ...inputStyle }}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleSubmit();
          }}
        />
      )}

      {mode === 'FUNCTION' && (
        <input
          value={targetName}
          onChange={(e) => setTargetName(e.target.value)}
          placeholder="> function name e.g. Response.content"
          style={{ ...inputStyle }}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleSubmit();
          }}
        />
      )}

      {/* Hint */}
      <div
        style={{
          marginTop: '8px',
          fontSize: '10px',
          color: '#454B66',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <span>Press Enter to send · Shift+Enter for newline</span>
        {mode !== 'ASK' && (
          <span style={{ color: '#454B66', fontStyle: 'italic' }}>
            {mode === 'FILE'
              ? 'Searches by exact filename'
              : 'Searches by exact function name'}
          </span>
        )}
      </div>
    </div>
  );
};

export default QueryInput;