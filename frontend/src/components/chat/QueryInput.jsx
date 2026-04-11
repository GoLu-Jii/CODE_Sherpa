import React, { useState } from 'react';
import { Send } from 'lucide-react';
import useAppStore from '../../store/useAppStore';
import { sendChatMessage } from '../../api/sherpaClient';

const QueryInput = () => {
  const [query, setQuery] = useState('');
  const { addChatMessage, setLoadingChat, isLoadingChat, chatHistory } = useAppStore();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim() || isLoadingChat) return;

    const userMsg = query;
    setQuery('');
    addChatMessage({ role: 'user', content: userMsg, timestamp: new Date() });
    setLoadingChat(true);

    try {
      // Map Zustand history to array of objects backend expects
      const historyForApi = chatHistory.map(msg => ({
        role: msg.role,
        content: msg.content
      }));
      
      const response = await sendChatMessage(userMsg, historyForApi);
      // Backend returns { status, data: { answer, sources, retrieved_chunks } }
      const assistantMsg = {
        role: 'assistant',
        content: response.data.answer,
        sources: response.data.sources || [],
        timestamp: new Date()
      };
      
      addChatMessage(assistantMsg);
    } catch (error) {
      addChatMessage({
        role: 'assistant',
        content: `**Error:** Failed to communicate with the Sherpa engine. (${error.message || 'Unknown error'})`,
        isError: true,
        timestamp: new Date()
      });
    } finally {
      setLoadingChat(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 border-t border-[var(--color-telemetry-border)] bg-[var(--color-telemetry-bg)]">
      <div className="relative flex items-end">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask about a specific file or function (e.g. 'what does vector_db.py do?')..."
          className="w-full bg-transparent border border-[var(--color-telemetry-border)] rounded-none text-[var(--color-telemetry-text)] px-4 py-3 pr-12 focus:outline-none focus:border-[var(--color-telemetry-accent)] transition-colors min-h-[50px] max-h-[200px] resize-y placeholder-[var(--color-telemetry-muted)] font-[var(--font-inter)]"
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
        />
        <button
          type="submit"
          disabled={!query.trim() || isLoadingChat}
          className="absolute right-2 bottom-2 p-2 text-[var(--color-telemetry-accent)] disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[var(--color-telemetry-border)]"
        >
          <Send size={18} />
        </button>
      </div>
      <div className="text-xs text-[var(--color-telemetry-muted)] mt-2 font-[var(--font-jetbrains)] flex flex-col sm:flex-row justify-between gap-1 items-start sm:items-center">
        <span>Press Enter to send, Shift+Enter for new line</span>
        <span className="text-yellow-500/80 italic">Note: Please include the exact file or function name in your query.</span>
      </div>
    </form>
  );
};

export default QueryInput;
