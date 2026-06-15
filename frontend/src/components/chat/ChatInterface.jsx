import React, { useRef, useEffect } from 'react';
import useAppStore from '../../store/useAppStore';
import QueryInput from './QueryInput';
import CitationChip from './CitationChip';

/**
 * Parses the numbered response format from the backend into sections.
 * Input:  "1. Purpose: ...\n\n2. Steps: ...\n\n3. Key Details: ..."
 * Output: [{ heading: "Purpose", body: "..." }, ...]
 */
const parseResponseSections = (content) => {
  if (!content) return [];

  const sectionRegex = /^\d+\.\s+\*{0,2}([^:\n]+)\*{0,2}:\s*/gm;
  const sections = [];
  let lastIndex = 0;
  let lastHeading = null;
  let match;

  while ((match = sectionRegex.exec(content)) !== null) {
    if (lastHeading !== null) {
      sections.push({
        heading: lastHeading,
        body: content.slice(lastIndex, match.index).trim(),
      });
    }
    lastHeading = match[1].trim();
    lastIndex = match.index + match[0].length;
  }

  if (lastHeading !== null) {
    sections.push({
      heading: lastHeading,
      body: content.slice(lastIndex).trim(),
    });
  }

  // If parsing failed (no numbered sections), return raw content as one block
  if (sections.length === 0) {
    return [{ heading: null, body: content }];
  }

  return sections;
};

/**
 * Renders a body string, replacing [citation] patterns with CitationChip components.
 * Citations are collected and shown as a chip row at the bottom of each section.
 */
const renderBodyWithCitations = (body) => {
  if (!body) return null;

  // Split on [citation] patterns
  const parts = body.split(/(\[[^[\]]+\])/g);
  const citationIds = [];

  parts.forEach((part) => {
    if (part.startsWith('[') && part.endsWith(']')) {
      const nodeId = part.slice(1, -1);
      // Collect unique citation IDs
      if (!citationIds.includes(nodeId)) citationIds.push(nodeId);
    }
  });

  return { citationIds };
};

/**
 * Renders a single assistant message section.
 */
const ResponseSection = ({ heading, body }) => {
  const parsed = renderBodyWithCitations(body);
  if (!parsed) return null;
  const { citationIds } = parsed;

  return (
    <div
      style={{
        marginBottom: '16px',
        paddingBottom: '16px',
        borderBottom: '1px solid rgba(28,32,53,0.5)',
      }}
    >
      {heading && (
        <div
          style={{
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '10px',
            color: '#454B66',
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
            marginBottom: '8px',
          }}
        >
          {heading}
        </div>
      )}

      {/* Body lines — render bullet points cleanly */}
      <div
        style={{
          fontFamily: 'JetBrains Mono, monospace',
          fontSize: '13px',
          color: '#C8CAD8',
          lineHeight: '1.7',
        }}
      >
        {body.split('\n').map((line, i) => {
          const trimmed = line.trim();
          if (!trimmed) return null;

          // Strip inline citations from the line for clean rendering
          const cleanLine = trimmed.replace(/\[[^[\]]+\]/g, '').trim();
          if (!cleanLine || cleanLine === '.') return null;

          const isBullet = cleanLine.startsWith('- ') || cleanLine.startsWith('• ');
          const text = isBullet ? cleanLine.slice(2) : cleanLine;

          return (
            <div
              key={i}
              style={{
                display: 'flex',
                gap: '8px',
                marginBottom: isBullet ? '4px' : '2px',
              }}
            >
              {isBullet && (
                <span style={{ color: '#FF6240', flexShrink: 0 }}>▸</span>
              )}
              <span>{text}</span>
            </div>
          );
        })}
      </div>

      {/* Citation chips row at the bottom */}
      {citationIds.length > 0 && (
        <div
          style={{
            marginTop: '10px',
            display: 'flex',
            flexWrap: 'wrap',
            gap: '4px',
          }}
        >
          {citationIds.map((id) => (
            <CitationChip key={id} nodeId={id} />
          ))}
        </div>
      )}
    </div>
  );
};

/**
 * Full assistant message renderer.
 */
const AssistantMessage = ({ content }) => {
  const sections = parseResponseSections(content);

  return (
    <div
      style={{
        background: 'rgba(14,16,24,0.6)',
        backdropFilter: 'blur(12px)',
        border: '1px solid #1C2035',
        borderLeft: '3px solid #FF6240',
        padding: '16px',
      }}
    >
      {sections.map((section, i) => (
        <ResponseSection key={i} heading={section.heading} body={section.body} />
      ))}
    </div>
  );
};

const ChatInterface = ({ selectedFile }) => {
  const { chatHistory, isLoadingChat, repo } = useAppStore();
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, isLoadingChat]);

  const exchangeCount = Math.floor(
    chatHistory.filter((m) => m.role === 'user').length
  );

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        background: 'rgba(7,8,15,0.65)',
        backdropFilter: 'blur(12px) saturate(180%)',
        borderLeft: '1px solid #1C2035',
      }}
    >
      {/* Header */}
      <div
        style={{
          height: '36px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 16px',
          borderBottom: '1px solid #1C2035',
          background: 'rgba(14,16,24,0.8)',
          flexShrink: 0,
          fontFamily: 'JetBrains Mono, monospace',
        }}
      >
        <div>
          <div style={{ fontSize: '10px', color: '#454B66', letterSpacing: '0.1em' }}>
            SHERPA_INTERFACE
          </div>
          {selectedFile && (
            <div style={{ fontSize: '10px', color: '#A8B4D0', marginTop: '2px' }}>
              selected: {selectedFile.name}
            </div>
          )}
        </div>
        <span style={{ fontSize: '10px', color: '#454B66' }}>
          {exchangeCount} EXCHANGES
        </span>
      </div>

      {/* Message history */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px',
        }}
      >
        {chatHistory.length === 0 ? (
          <div
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              fontFamily: 'JetBrains Mono, monospace',
              color: '#454B66',
              fontSize: '12px',
              gap: '6px',
            }}
          >
            <span>{repo.status === 'ready' ? 'SYSTEM.READY' : 'SYSTEM.INITIALIZING'}</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              {repo.status === 'ready' ? '> awaiting query...' : '> awaiting repository ingest...'}
              <span
                style={{
                  width: '8px',
                  height: '14px',
                  background: '#FF6240',
                  display: 'inline-block',
                  animation: 'blink 1s step-end infinite',
                }}
              />
            </span>
          </div>
        ) : (
          chatHistory.map((msg, idx) => (
            <div
              key={idx}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start',
              }}
            >
              {/* Role label */}
              <div
                style={{
                  fontSize: '10px',
                  color: '#454B66',
                  fontFamily: 'JetBrains Mono, monospace',
                  marginBottom: '6px',
                  letterSpacing: '0.08em',
                }}
              >
                {msg.role === 'user' ? 'USER_QUERY' : 'SHERPA_RESPONSE'}
              </div>

              {msg.role === 'user' ? (
                <div
                  style={{
                    maxWidth: '85%',
                    padding: '10px 14px',
                    background: '#1C2035',
                    borderTop: '1px solid #252840',
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: '13px',
                    color: '#E8EAF2',
                    lineHeight: '1.6',
                  }}
                >
                  {msg.content}
                </div>
              ) : msg.isError ? (
                <div
                  style={{
                    maxWidth: '85%',
                    padding: '10px 14px',
                    background: 'rgba(240,68,56,0.08)',
                    border: '1px solid rgba(240,68,56,0.3)',
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: '13px',
                    color: '#F04438',
                    lineHeight: '1.6',
                  }}
                >
                  <div style={{ fontSize: '10px', marginBottom: '4px', letterSpacing: '0.08em' }}>
                    SHERPA_ERROR
                  </div>
                  {msg.content}
                </div>
              ) : (
                <div style={{ maxWidth: '90%', width: '100%' }}>
                  <AssistantMessage content={msg.content} />
                </div>
              )}
            </div>
          ))
        )}

        {isLoadingChat && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'flex-start',
            }}
          >
            <div
              style={{
                fontSize: '10px',
                color: '#454B66',
                fontFamily: 'JetBrains Mono, monospace',
                marginBottom: '6px',
                letterSpacing: '0.08em',
              }}
            >
              SHERPA_PROCESSING
            </div>
            <div
              style={{
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '13px',
                color: '#454B66',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              {'> analyzing sources...'}
              <span
                style={{
                  width: '8px',
                  height: '14px',
                  background: '#FF6240',
                  display: 'inline-block',
                  animation: 'blink 1s step-end infinite',
                }}
              />
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