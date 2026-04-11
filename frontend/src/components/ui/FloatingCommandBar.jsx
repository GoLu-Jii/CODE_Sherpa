import React, { useState } from 'react';
import { Search, ChevronRight, GitBranch, X } from 'lucide-react';
import useAppStore from '../../store/useAppStore';
import { ingestRepository } from '../../api/sherpaClient';

const STAGES = [
  '📥  Cloning repository...',
  '🔍  Running AST analysis...',
  '⚙️   Chunking & uploading to Chroma...',
  '🗺️   Building architecture graph...',
  '✅  Ready.',
];

const FloatingCommandBar = () => {
  const [inputValue, setInputValue] = useState('');
  const [stageIndex, setStageIndex] = useState(0);
  const [minimised, setMinimised] = useState(false);
  const { repo, setRepoUrl, setRepoStatus, setRepoData } = useAppStore();

  // Advance the fake terminal stages while waiting
  const startStageAnimation = () => {
    let idx = 0;
    const iv = setInterval(() => {
      idx = Math.min(idx + 1, STAGES.length - 2); // stay below "Ready" until done
      setStageIndex(idx);
    }, 7000);
    return () => clearInterval(iv);
  };

  const handleIngest = async (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    setRepoUrl(inputValue.trim());
    setRepoStatus('loading');
    setStageIndex(0);

    const stopAnimation = startStageAnimation();

    try {
      const data = await ingestRepository(inputValue.trim());
      stopAnimation();
      setStageIndex(STAGES.length - 1); // "Ready"
      setRepoData(data);
      // Auto-minimise after a short celebratory pause
      setTimeout(() => setMinimised(true), 1200);
    } catch (err) {
      stopAnimation();
      const errMsg =
        err?.response?.status === 403
          ? 'Access denied. Is the repository public?'
          : err?.response?.status === 404
          ? 'Repository not found. Check the URL.'
          : err?.code === 'ECONNABORTED'
          ? 'Request timed out — the repository may be too large.'
          : err?.message || 'Unknown error.';
      setRepoStatus('error', errMsg);
    }
  };

  // ---------------------------------------------------------------
  // MINIMISED PILL (after ingestion)
  // ---------------------------------------------------------------
  if (repo.status === 'ready' && minimised) {
    return (
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 px-4 py-2 font-[var(--font-jetbrains)] text-xs border border-[var(--color-telemetry-border)] bg-[var(--color-telemetry-bg)] shadow-md">
        <GitBranch size={12} className="text-[var(--color-telemetry-accent)]" />
        <span className="text-[var(--color-telemetry-muted)] max-w-[300px] truncate">{repo.url}</span>
        <span className="text-green-400 tracking-widest">STATUS:READY</span>
        <button
          onClick={() => setMinimised(false)}
          className="text-[var(--color-telemetry-muted)] hover:text-[var(--color-telemetry-text)] transition-colors"
        >
          <X size={12} />
        </button>
      </div>
    );
  }

  // ---------------------------------------------------------------
  // HIDDEN when ready but not minimised (user expanded it back)
  // ---------------------------------------------------------------

  return (
    <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-full max-w-2xl px-4 z-50">
      <div
        className="shadow-2xl p-6"
        style={{
          background: 'rgba(9,10,15,0.92)',
          border: '1px solid var(--color-telemetry-border)',
          backdropFilter: 'blur(12px)',
        }}
      >
        {/* Header label */}
        <div className="flex items-center gap-3 mb-5 font-[var(--font-jetbrains)] text-[10px] tracking-widest text-[var(--color-telemetry-muted)]">
          <GitBranch size={14} />
          SYSTEM.INITIALIZE — ENTER GITHUB TARGET
        </div>

        {/* ---- LOADING STATE ---- */}
        {repo.status === 'loading' && (
          <div className="font-[var(--font-jetbrains)] text-sm flex flex-col gap-3">
            <div className="flex items-center gap-2 text-[var(--color-telemetry-text)]">
              <ChevronRight size={14} className="text-[var(--color-telemetry-accent)] flex-shrink-0" />
              <span className="text-[var(--color-telemetry-muted)] text-[11px] truncate">{repo.url}</span>
            </div>

            {STAGES.map((stage, i) => (
              <div
                key={i}
                className={`flex items-center gap-2 transition-all duration-300 ${
                  i < stageIndex
                    ? 'opacity-40 line-through text-[var(--color-telemetry-muted)]'
                    : i === stageIndex
                    ? 'text-[var(--color-telemetry-text)]'
                    : 'opacity-20 text-[var(--color-telemetry-muted)]'
                }`}
              >
                <span>{stage}</span>
                {i === stageIndex && i < STAGES.length - 1 && (
                  <span className="w-2 h-4 bg-[var(--color-telemetry-accent)] animate-blink inline-block flex-shrink-0" />
                )}
              </div>
            ))}
          </div>
        )}

        {/* ---- INPUT STATE ---- */}
        {repo.status !== 'loading' && (
          <form onSubmit={handleIngest} className="flex gap-3">
            <div className="relative flex-1">
              <Search
                size={16}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-telemetry-muted)] pointer-events-none"
              />
              <input
                type="text"
                value={inputValue}
                onChange={e => setInputValue(e.target.value)}
                placeholder="https://github.com/username/repository"
                className="w-full bg-transparent text-[var(--color-telemetry-text)] font-[var(--font-jetbrains)] text-sm px-10 py-3 placeholder-[var(--color-telemetry-muted)] focus:outline-none transition-colors"
                style={{
                  border: '1px solid var(--color-telemetry-border)',
                }}
                onFocus={e =>
                  (e.currentTarget.style.borderColor = 'var(--color-telemetry-accent)')
                }
                onBlur={e =>
                  (e.currentTarget.style.borderColor = 'var(--color-telemetry-border)')
                }
              />
            </div>
            <button
              type="submit"
              disabled={!inputValue.trim()}
              className="font-[var(--font-jetbrains)] text-[11px] uppercase tracking-widest px-6 py-3 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
              style={{
                border: '1px solid var(--color-telemetry-accent)',
                color: 'var(--color-telemetry-accent)',
                background: 'transparent',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.background = 'var(--color-telemetry-accent)';
                e.currentTarget.style.color = '#090A0F';
              }}
              onMouseLeave={e => {
                e.currentTarget.style.background = 'transparent';
                e.currentTarget.style.color = 'var(--color-telemetry-accent)';
              }}
            >
              Ingest
            </button>
          </form>
        )}

        {/* Error message */}
        {repo.status === 'error' && (
          <div
            className="mt-4 pt-4 font-[var(--font-jetbrains)] text-[11px]"
            style={{
              borderTop: '1px solid var(--color-telemetry-border)',
              color: '#f87171',
            }}
          >
            ERR: {repo.error}
          </div>
        )}
      </div>
    </div>
  );
};

export default FloatingCommandBar;
