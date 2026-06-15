import React, { useEffect, useRef, useState } from 'react';
import useAppStore from '../../store/useAppStore';
import { sendChatMessage } from '../../api/sherpaClient';

const MODES = ['ASK', 'FILE', 'FUNCTION'];

const QueryInput = () => {
  const [query, setQuery] = useState('');
  const [targetName, setTargetName] = useState('');
  const {
    addChatMessage,
    setLoadingChat,
    isLoadingChat,
    chatHistory,
    repo,
    chatMode,
    setChatMode,
    chatPrefill,
    prefillToken,
  } = useAppStore();

  const inputRef = useRef(null);

  useEffect(() => {
    if (prefillToken === 0) return;
    if (chatMode === 'ASK') {
      setQuery(chatPrefill.query || '');
      setTargetName('');
    } else {
      setTargetName(chatPrefill.targetName || '');
      setQuery('');
    }
    inputRef.current?.focus();
  }, [prefillToken, chatPrefill, chatMode]);

  const buildQuery = () => {
    if (chatMode === 'FILE') return `what does ${targetName.trim()} do`;
    if (chatMode === 'FUNCTION') return `what does the function ${targetName.trim()} do`;
    return query.trim();
  };

  const canSubmit = () => {
    if (isLoadingChat || repo.status !== 'ready') return false;
    if (chatMode === 'ASK') return query.trim().length > 0;
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

  const isDisabled = repo.status !== 'ready' || isLoadingChat;

  return (
    <div
      style={{
        borderTop: '1px solid #1C2035',
        background: 'rgba(14,16,24,0.92)',
        padding: '12px 16px',
        flexShrink: 0,
        fontFamily: 'JetBrains Mono, monospace',
        opacity: repo.status !== 'ready' ? 0.55 : 1,
      }}
    >
      <div style={{ display: 'flex', gap: '6px', marginBottom: '10px' }}>
        {MODES.map((m) => (
          <button
            key={m}
            onClick={() => setChatMode(m)}
            disabled={isDisabled}
            style={{
              padding: '3px 10px',
              fontSize: '10px',
              fontFamily: 'JetBrains Mono, monospace',
              background: 'transparent',
              border: chatMode === m ? '1px solid #FF6240' : '1px solid #1C2035',
              color: chatMode === m ? '#FF6240' : '#454B66',
              cursor: isDisabled ? 'not-allowed' : 'pointer',
              letterSpacing: '0.08em',
              transition: 'border-color 0.15s, color 0.15s',
            }}
          >
            {m}
          </button>
        ))}
      </div>

      {chatMode === 'ASK' && (
        <textarea
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={
            repo.status === 'ready'
              ? '> ask about the codebase...'
              : '> awaiting repository ingest...'
          }
          rows={2}
          disabled={isDisabled}
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

      {chatMode === 'FILE' && (
        <input
          ref={inputRef}
          value={targetName}
          onChange={(e) => setTargetName(e.target.value)}
          placeholder="> filename e.g. hooks.py"
          disabled={isDisabled}
          style={{ ...inputStyle }}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleSubmit();
          }}
        />
      )}

      {chatMode === 'FUNCTION' && (
        <input
          ref={inputRef}
          value={targetName}
          onChange={(e) => setTargetName(e.target.value)}
          placeholder="> function name e.g. Response.content"
          disabled={isDisabled}
          style={{ ...inputStyle }}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleSubmit();
          }}
        />
      )}

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
        <span>
          {repo.status === 'ready'
            ? 'Press Enter to send · Shift+Enter for newline'
            : 'Chat input locked until ingest completes'}
        </span>
        {chatMode !== 'ASK' && repo.status === 'ready' && (
          <span style={{ color: '#454B66', fontStyle: 'italic' }}>
            {chatMode === 'FILE'
              ? 'Searches by exact filename'
              : 'Searches by exact function name'}
          </span>
        )}
      </div>
    </div>
  );
};

export default QueryInput;
