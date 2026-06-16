import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import useAppStore from '../../store/useAppStore';
import FloatingCommandBar from '../ui/FloatingCommandBar';
import ArchitectureGraph from '../graph/ArchitectureGraph';
import { buildFileData, buildFolderData } from '../graph/graphHelpers';
import ChatInterface from '../chat/ChatInterface';

const mono = { fontFamily: 'JetBrains Mono, monospace' };

const AppLayout = () => {
  const { repo, prefillChatInput } = useAppStore();
  const [selectedFilePath, setSelectedFilePath] = useState(null);
  const [selectedFunction, setSelectedFunction] = useState(null);
  const [folderOpenState, setFolderOpenState] = useState({});
  const [fileOpenState, setFileOpenState] = useState({});
  const [hoveredFilePath, setHoveredFilePath] = useState(null);
  const [leftWidth, setLeftWidth] = useState(260);
  const [rightWidth, setRightWidth] = useState(500);
  const dragStartX = useRef(0);
  const dragStartWidth = useRef(0);
  const activeResizer = useRef(null);

  const folders = useMemo(() => buildFolderData(repo.raw_ast), [repo.raw_ast]);
  const files = useMemo(() => buildFileData(repo.raw_ast), [repo.raw_ast]);


  const toggleFolder = useCallback((key) => {
    setFolderOpenState(prev => ({ ...prev, [key]: !prev[key] }));
  }, []);

  const toggleFile = useCallback((path) => {
    setFileOpenState(prev => ({ ...prev, [path]: !prev[path] }));
    setSelectedFilePath(path);
    setSelectedFunction(null);
  }, []);

  const handleFunctionSelect = useCallback((filePath, functionName) => {
    setSelectedFilePath(filePath);
    setSelectedFunction({ filePath, functionName });
  }, []);

  const clearFunction = useCallback(() => {
    setSelectedFunction(null);
  }, []);

  // Drag resize
  const startResize = useCallback((side, e) => {
    e.preventDefault();
    activeResizer.current = side;
    dragStartX.current = e.clientX;
    dragStartWidth.current = side === 'left' ? leftWidth : rightWidth;
  }, [leftWidth, rightWidth]);

  useEffect(() => {
    const onMove = (e) => {
      if (!activeResizer.current) return;
      const delta = e.clientX - dragStartX.current;
      if (activeResizer.current === 'left') {
        setLeftWidth(Math.max(200, Math.min(380, dragStartWidth.current + delta)));
      } else {
        setRightWidth(Math.max(360, Math.min(700, dragStartWidth.current - delta)));
      }
    };
    const onUp = () => { activeResizer.current = null; };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    return () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp); };
  }, []);

  const handleAsk = useCallback((mode, target) => {
    if (!prefillChatInput) return;
    if (mode === 'FUNCTION') prefillChatInput({ mode: 'FUNCTION', targetName: target });
    else if (mode === 'FILE') prefillChatInput({ mode: 'FILE', targetName: target });
    else prefillChatInput({ mode: 'ASK', query: target });
  }, [prefillChatInput]);

  if (repo.status !== 'ready') {
    return (
      <div style={{ position: 'relative', width: '100%', height: '100vh', background: '#090A0F', overflow: 'hidden' }}>
        <FloatingCommandBar />
        <div style={{
          position: 'absolute', inset: 0, pointerEvents: 'none', opacity: 0.12,
          backgroundImage: 'linear-gradient(#1E2230 1px, transparent 1px), linear-gradient(90deg, #1E2230 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }} />
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', width: '100%', height: '100vh', overflow: 'hidden', background: '#090A0F', color: '#E8EAF2' }}>
      <FloatingCommandBar />

      {/* ── Left panel: file browser ── */}
      <div style={{ width: leftWidth, minWidth: 200, maxWidth: 380, background: '#090A0F', borderRight: '1px solid #1E2230', display: 'flex', flexDirection: 'column', overflow: 'hidden', flexShrink: 0 }}>
        <div style={{ padding: '10px 12px', borderBottom: '1px solid #1E2230', background: '#090A0F', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0 }}>
          <div style={{ ...mono, fontSize: 10, color: '#8A91A6', letterSpacing: '0.12em', fontWeight: 600 }}>[SYSTEM::FILE_BROWSER]</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: '#22c55e', display: 'inline-block', boxShadow: '0 0 8px #22c55e' }} />
            <span style={{ ...mono, fontSize: 9, color: '#22c55e', fontWeight: 600 }}>ONLINE</span>
          </div>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '2px 0' }}>
          {folders.map(folder => {
            const isOpen = folderOpenState[folder.key];
            return (
              <div key={folder.key} style={{ borderBottom: '1px solid rgba(30, 34, 48, 0.4)' }}>
                {/* Folder row */}
                <button
                  type="button"
                  onClick={() => toggleFolder(folder.key)}
                  style={{
                    width: '100%', display: 'flex', alignItems: 'center', gap: 6,
                    padding: '6px 10px', background: 'transparent', border: 'none',
                    color: '#FFFFFF', cursor: 'pointer', textAlign: 'left',
                    ...mono, fontSize: 11, fontWeight: 600,
                    transition: 'background 0.1s',
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,123,75,0.04)'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                >
                  <span style={{ color: '#FF7B4B', fontSize: 10, width: 10, flexShrink: 0 }}>
                    {isOpen ? '▼' : '▶'}
                  </span>
                  <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {folder.label}
                  </span>
                  <span style={{ ...mono, fontSize: 9, color: '#8A91A6', background: 'rgba(30, 34, 48, 0.5)', padding: '1px 4px', borderRadius: 2, flexShrink: 0 }}>
                    {folder.files.length}
                  </span>
                </button>

                {/* Files inside folder */}
                {isOpen && (
                  <div style={{ paddingLeft: 12, borderLeft: '1px dotted #1E2230', marginLeft: 14, marginY: 2 }}>
                    {folder.files.map(file => {
                      const isFileOpen = fileOpenState[file.path];
                      const isActive = selectedFilePath === file.path;
                      return (
                        <div key={file.path} style={{ borderBottom: '1px solid rgba(30, 34, 48, 0.2)' }}>
                          {/* File row */}
                          <div
                            onMouseEnter={() => setHoveredFilePath(file.path)}
                            onMouseLeave={() => setHoveredFilePath(null)}
                            style={{
                              display: 'flex', alignItems: 'center', gap: 6,
                              padding: '4px 8px',
                              background: isActive ? 'rgba(255,123,75,0.08)' : 'transparent',
                              borderLeft: isActive ? '2px solid #FF7B4B' : '2px solid transparent',
                              cursor: 'pointer',
                              transition: 'background 0.1s',
                            }}
                            onClick={() => toggleFile(file.path)}
                          >
                            {/* Toggle arrow for functions */}
                            <span
                              style={{ color: '#8A91A6', fontSize: 9, width: 8, flexShrink: 0, cursor: 'pointer' }}
                            >
                              {file.functionCount > 0 ? (isFileOpen ? '▼' : '▶') : ' '}
                            </span>
                            {/* Filename */}
                            <span
                              style={{ ...mono, fontSize: 11, color: isActive ? '#FF7B4B' : '#E8EAF2', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                            >
                              {file.name}
                            </span>
                            {/* fn count or ask button */}
                            {hoveredFilePath === file.path ? (
                              <button
                                type="button"
                                onClick={e => { e.stopPropagation(); handleAsk('FILE', file.name); }}
                                style={{
                                  ...mono, fontSize: 9, padding: '1px 5px', flexShrink: 0,
                                  border: '1px solid #FF7B4B', background: 'rgba(255,123,75,0.1)',
                                  color: '#FF7B4B', cursor: 'pointer',
                                }}
                              >
                                Ask ↗
                              </button>
                            ) : (
                              <span style={{ ...mono, fontSize: 9, color: '#8A91A6', flexShrink: 0 }}>
                                {file.functionCount > 0 ? `${file.functionCount} fn` : ''}
                              </span>
                            )}
                          </div>

                          {/* Functions list */}
                          {isFileOpen && file.functionCount > 0 && (
                            <div style={{ paddingLeft: 10, borderLeft: '1px dotted #1E2230', marginLeft: 8, paddingBottom: 2, paddingTop: 2 }}>
                              {Object.keys(file.functions).map(fnName => {
                                const isFnSelected = selectedFunction?.filePath === file.path && selectedFunction?.functionName === fnName;
                                return (
                                  <div
                                    key={fnName}
                                    style={{
                                      display: 'flex', alignItems: 'center', gap: 6,
                                      padding: '3px 6px',
                                      background: isFnSelected ? 'rgba(77,158,255,0.08)' : 'transparent',
                                      borderLeft: isFnSelected ? '2px solid #4D9EFF' : '2px solid transparent',
                                      cursor: 'pointer',
                                    }}
                                  >
                                    <span style={{ ...mono, fontSize: 10, color: '#8A91A6', flexShrink: 0 }}>├</span>
                                    <button
                                      type="button"
                                      onClick={() => handleFunctionSelect(file.path, fnName)}
                                      style={{
                                        ...mono, fontSize: 10, color: isFnSelected ? '#4D9EFF' : '#8A91A6',
                                        background: 'none', border: 'none', cursor: 'pointer',
                                        textAlign: 'left', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', padding: 0,
                                      }}
                                    >
                                      {fnName}
                                    </button>
                                    <button
                                      type="button"
                                      onClick={e => { e.stopPropagation(); handleAsk('FUNCTION', fnName); }}
                                      style={{
                                        ...mono, fontSize: 8, padding: '1px 4px', flexShrink: 0,
                                        border: '1px solid rgba(255,123,75,0.3)', background: 'transparent',
                                        color: '#FF7B4B', cursor: 'pointer',
                                      }}
                                    >
                                      Ask
                                    </button>
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Left resize handle */}
      <div
        onMouseDown={e => startResize('left', e)}
        style={{ width: 6, cursor: 'col-resize', background: 'transparent', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
      >
        <div style={{ width: 1, height: '100%', background: '#1C2035' }} />
      </div>

      {/* ── Middle panel: graph / function code ── */}
      <div style={{ flex: 1, minWidth: 0, height: '100%', overflow: 'hidden', position: 'relative' }}>
        {/* Label */}
        <div style={{
          position: 'absolute', top: 12, left: 14, zIndex: 10, pointerEvents: 'none',
          ...mono, fontSize: 10, color: '#454B66', letterSpacing: '0.14em',
        }}>
          {selectedFunction ? 'VIEW::FUNCTION_CODE' : 'VIEW::DEPENDENCY_GRAPH'}
        </div>

        {/* Back button when function is open */}
        {selectedFunction && (
          <button
            type="button"
            onClick={clearFunction}
            style={{
              position: 'absolute', top: 8, right: 14, zIndex: 10,
              ...mono, fontSize: 10, color: '#454B66', padding: '4px 10px',
              border: '1px solid #1C2035', background: 'rgba(13,15,23,0.9)', cursor: 'pointer',
            }}
          >
            ← GRAPH
          </button>
        )}

        <ArchitectureGraph
          selectedFunction={selectedFunction}
          onAsk={handleAsk}
        />
      </div>

      {/* Right resize handle */}
      <div
        onMouseDown={e => startResize('right', e)}
        style={{ width: 6, cursor: 'col-resize', background: 'transparent', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
      >
        <div style={{ width: 1, height: '100%', background: '#1C2035' }} />
      </div>

      {/* ── Right panel: chat ── */}
      <div style={{ width: rightWidth, minWidth: 360, maxWidth: 700, display: 'flex', flexDirection: 'column', overflow: 'hidden', background: '#0A0E17', flexShrink: 0 }}>
        <ChatInterface selectedFile={files.find(f => f.path === selectedFilePath) || null} />
      </div>
    </div>
  );
};

export default AppLayout;