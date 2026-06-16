import React, { useEffect, useRef, useState, useMemo } from 'react';
import hljs from 'highlight.js/lib/core';
import python from 'highlight.js/lib/languages/python';
import javascript from 'highlight.js/lib/languages/javascript';
import typescript from 'highlight.js/lib/languages/typescript';
import 'highlight.js/styles/github-dark.css';
import useAppStore from '../../store/useAppStore';
import { buildFileData } from './graphHelpers';

hljs.registerLanguage('python', python);
hljs.registerLanguage('javascript', javascript);
hljs.registerLanguage('typescript', typescript);

const mono = { fontFamily: 'JetBrains Mono, monospace' };

const getLanguage = (path = '') => {
  if (path.endsWith('.py')) return 'python';
  if (path.endsWith('.ts')) return 'typescript';
  return 'javascript';
};

const highlight = (code, lang) => {
  try { return hljs.highlight(code, { language: lang }).value; }
  catch { return hljs.highlightAuto(code).value; }
};

const nodeTypeLabel = (label = '') => {
  if (label.startsWith('src/')) return 'SOURCE';
  if (label.startsWith('tests/') || label.startsWith('test/')) return 'TESTS';
  return 'PROJECT';
};

const typeColor = (label = '') => {
  if (label.startsWith('src/')) return '#FF7B4B';
  if (label.startsWith('tests/') || label.startsWith('test/')) return '#3DD68C';
  return '#4D9EFF';
};

// Center-aligned top-down hierarchical layout
function computeLayout(nodes, edges, containerWidth) {
  const NODE_W = 190;
  const NODE_H = 60;
  const H_GAP = 230;
  const V_GAP = 125;

  const adj = {};
  const inDegree = {};
  nodes.forEach(n => {
    adj[n.id] = [];
    inDegree[n.id] = 0;
  });

  edges.forEach(e => {
    const s = typeof e.source === 'object' ? e.source.id : e.source;
    const t = typeof e.target === 'object' ? e.target.id : e.target;
    if (adj[s] && adj[t]) {
      adj[s].push(t);
      inDegree[t]++;
    }
  });

  const layers = {};
  const queue = [];
  
  nodes.forEach(n => {
    if (inDegree[n.id] === 0) {
      layers[n.id] = 0;
      queue.push(n.id);
    }
  });

  if (queue.length === 0 && nodes.length > 0) {
    const firstId = nodes[0].id;
    layers[firstId] = 0;
    queue.push(firstId);
  }

  const visited = new Set();
  while (queue.length > 0) {
    const curr = queue.shift();
    if (visited.has(curr)) continue;
    visited.add(curr);

    const currLayer = layers[curr] || 0;
    (adj[curr] || []).forEach(next => {
      const nextLayer = Math.max(layers[next] || 0, currLayer + 1);
      layers[next] = nextLayer;
      queue.push(next);
    });
  }

  nodes.forEach(n => {
    if (layers[n.id] === undefined) {
      layers[n.id] = 0;
    }
  });

  const layerGroups = {};
  nodes.forEach(n => {
    const l = layers[n.id];
    if (!layerGroups[l]) layerGroups[l] = [];
    layerGroups[l].push(n);
  });

  const maxLayer = Math.max(...Object.keys(layerGroups).map(Number), 0);
  for (let l = 0; l <= maxLayer; l++) {
    if (layerGroups[l]) {
      layerGroups[l].sort((a, b) => a.id.localeCompare(b.id));
    }
  }

  const positions = {};
  let totalHeight = 60;

  for (let l = 0; l <= maxLayer; l++) {
    const rowNodes = layerGroups[l] || [];
    const rowCount = rowNodes.length;
    if (rowCount === 0) continue;

    const rowWidth = (rowCount - 1) * H_GAP + NODE_W;
    const startX = Math.max(40, (containerWidth - rowWidth) / 2);
    const y = 50 + l * V_GAP;

    rowNodes.forEach((node, idx) => {
      positions[node.id] = {
        x: startX + idx * H_GAP,
        y: y
      };
    });

    totalHeight = Math.max(totalHeight, y + NODE_H + 60);
  }

  // Calculate actual bounds to prevent SVG line clipping
  let maxX = containerWidth;
  Object.values(positions).forEach(pos => {
    if (pos.x + NODE_W + 100 > maxX) {
      maxX = pos.x + NODE_W + 100;
    }
  });

  return {
    positions,
    width: maxX,
    height: totalHeight,
    nodeW: NODE_W,
    nodeH: NODE_H,
  };
}

const DependencyGraph = ({ raw_ast, onNodeClick, highlightedNodeId }) => {
  const containerRef = useRef(null);
  const [containerWidth, setContainerWidth] = useState(900);
  const [hoveredId, setHoveredId] = useState(null);

  // Stateful node positions for drag support
  const [nodePositions, setNodePositions] = useState({});
  const dragInfo = useRef({ nodeId: null, startX: 0, startY: 0, initialX: 0, initialY: 0, hasMoved: false });

  // Pan and Zoom states
  const [zoom, setZoom] = useState(0.95);
  const [pan, setPan] = useState({ x: 30, y: 10 });
  const [isPanning, setIsPanning] = useState(false);
  const panStart = useRef({ x: 0, y: 0 });

  useEffect(() => {
    if (!containerRef.current) return;
    const ro = new ResizeObserver(entries => {
      setContainerWidth(entries[0].contentRect.width);
    });
    ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, []);

  const { positions, width, height, nodeW, nodeH } = useMemo(() => {
    const nodes = raw_ast?.graph?.nodes || [];
    const edges = raw_ast?.graph?.edges || [];
    return computeLayout(nodes, edges, containerWidth);
  }, [raw_ast, containerWidth]);

  // Sync positions from computed layout to state
  useEffect(() => {
    if (positions) {
      setNodePositions(positions);
    }
  }, [positions]);

  const handleMouseDown = (nodeId, e) => {
    if (e.button !== 0) return; // Left click only
    e.stopPropagation(); // Prevent background panning
    const startX = e.clientX;
    const startY = e.clientY;
    const currentPos = nodePositions[nodeId] || positions[nodeId] || { x: 0, y: 0 };
    
    dragInfo.current = {
      nodeId,
      startX,
      startY,
      initialX: currentPos.x,
      initialY: currentPos.y,
      hasMoved: false
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
  };

  const handleMouseMove = (e) => {
    const { nodeId, startX, startY, initialX, initialY } = dragInfo.current;
    if (!nodeId) return;

    const dx = (e.clientX - startX) / zoom; 
    const dy = (e.clientY - startY) / zoom;

    if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
      dragInfo.current.hasMoved = true;
    }

    setNodePositions(prev => ({
      ...prev,
      [nodeId]: {
        x: initialX + dx,
        y: initialY + dy
      }
    }));
  };

  const handleMouseUp = (e) => {
    const { nodeId, hasMoved } = dragInfo.current;
    dragInfo.current = { nodeId: null, startX: 0, startY: 0, initialX: 0, initialY: 0, hasMoved: false };
    window.removeEventListener('mousemove', handleMouseMove);
    window.removeEventListener('mouseup', handleMouseUp);
  };

  // Background panning mouse handlers
  const handleBgMouseDown = (e) => {
    if (e.button !== 0) return; // Left click only
    setIsPanning(true);
    panStart.current = { x: e.clientX - pan.x, y: e.clientY - pan.y };
  };

  const handleBgMouseMove = (e) => {
    if (!isPanning) return;
    setPan({
      x: e.clientX - panStart.current.x,
      y: e.clientY - panStart.current.y
    });
  };

  const handleBgMouseUp = () => {
    setIsPanning(false);
  };

  // Wheel zoom handler
  const handleWheel = (e) => {
    e.preventDefault();
    const zoomFactor = 0.05;
    const direction = e.deltaY < 0 ? 1 : -1;
    setZoom(prev => Math.max(0.25, Math.min(2.5, prev + direction * zoomFactor)));
  };

  const resetView = () => {
    setZoom(0.95);
    setPan({ x: 30, y: 10 });
  };

  // Clean up listeners on unmount
  useEffect(() => {
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  const graphNodes = raw_ast?.graph?.nodes || [];
  const graphEdges = raw_ast?.graph?.edges || [];

  if (!graphNodes.length) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', ...mono, color: '#8A91A6', fontSize: 12 }}>
        No graph data available.
      </div>
    );
  }

  // Build edge paths between node centers
  const edgePaths = graphEdges.map((edge, i) => {
    const srcId = typeof edge.source === 'object' ? edge.source.id : edge.source;
    const dstId = typeof edge.target === 'object' ? edge.target.id : edge.target;
    const s = nodePositions[srcId] || positions[srcId];
    const d = nodePositions[dstId] || positions[dstId];
    if (!s || !d) return null;

    const sx = s.x + nodeW / 2;
    const sy = s.y + nodeH;
    const dx = d.x + nodeW / 2;
    const dy = d.y;
    const cy = (sy + dy) / 2;

    const isHovered = hoveredId === srcId || hoveredId === dstId;

    return (
      <g key={i}>
        <path
          d={`M ${sx} ${sy} C ${sx} ${cy}, ${dx} ${cy}, ${dx} ${dy}`}
          fill="none"
          stroke={edge.type === 'calls' ? '#FF7B4B' : '#4D9EFF'}
          strokeWidth={isHovered ? 1.8 : 1.2}
          strokeOpacity={isHovered ? 0.9 : 0.35}
          strokeDasharray={edge.type === 'calls' ? '4 3' : undefined}
          markerEnd="url(#arrowhead)"
        />
      </g>
    );
  });

  return (
    <div
      ref={containerRef}
      onWheel={handleWheel}
      onMouseDown={handleBgMouseDown}
      onMouseMove={handleBgMouseMove}
      onMouseUp={handleBgMouseUp}
      onMouseLeave={handleBgMouseUp}
      style={{ 
        width: '100%', 
        height: '100%', 
        overflow: 'hidden', 
        position: 'relative', 
        background: '#090A0F', 
        cursor: isPanning ? 'grabbing' : 'grab' 
      }}
    >
      {/* Zoomable, Pannable Content Wrapper */}
      <div
        style={{
          transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
          transformOrigin: '0 0',
          position: 'absolute',
          left: 0,
          top: 0,
          width: width,
          height: height,
        }}
      >
        <svg
          width={width}
          height={height}
          style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}
        >
          <defs>
            <marker id="arrowhead" markerWidth="6" markerHeight="6" refX="6" refY="3" orient="auto">
              <path d="M0,0 L0,6 L6,3 z" fill="#8A91A6" fillOpacity="0.5" />
            </marker>
          </defs>
          {edgePaths}
        </svg>

        {/* Nodes rendered as DOM for crisp text and interaction */}
        <div style={{ position: 'relative', width, height }}>
          {graphNodes.map(node => {
            const pos = nodePositions[node.id] || positions[node.id];
            if (!pos) return null;
            const isHovered = hoveredId === node.id;
            const isHighlighted = highlightedNodeId === node.id;
            const color = typeColor(node.label);
            const label = nodeTypeLabel(node.label);
            const fileName = (node.label || '').split('/').pop();
            const dirPath = (node.label || '').split('/').slice(0, -1).join('/');

            return (
              <div
                key={node.id}
                onClick={(e) => {
                  if (!dragInfo.current.hasMoved) {
                    onNodeClick?.(node);
                  }
                }}
                onMouseEnter={() => setHoveredId(node.id)}
                onMouseLeave={() => setHoveredId(null)}
                onMouseDown={(e) => handleMouseDown(node.id, e)}
                style={{
                  position: 'absolute',
                  left: pos.x,
                  top: pos.y,
                  width: nodeW,
                  height: nodeH,
                  background: isHighlighted ? 'rgba(255,123,75,0.08)' : '#090A0F',
                  border: isHighlighted
                    ? '1px solid #FF7B4B'
                    : isHovered
                    ? `1px solid ${color}`
                    : '1px solid #1E2230',
                  borderLeft: `3px solid ${color}`,
                  cursor: 'grab',
                  boxSizing: 'border-box',
                  padding: '8px 10px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                  gap: 3,
                  transition: 'border-color 0.12s, box-shadow 0.12s',
                  boxShadow: isHighlighted
                    ? '0 0 15px rgba(255,123,75,0.25)'
                    : isHovered
                    ? `0 0 12px ${color}35`
                    : 'none',
                  userSelect: 'none',
                }}
              >
                <div style={{ ...mono, fontSize: 9, color, letterSpacing: '0.12em', fontWeight: 600 }}>{label}</div>
                <div style={{ ...mono, fontSize: 12, color: '#FFFFFF', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {fileName}
                </div>
                {dirPath && (
                  <div style={{ ...mono, fontSize: 10, color: '#8A91A6', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {dirPath}/
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Viewport Control Panel */}
      <div style={{ position: 'fixed', bottom: 16, right: 16, display: 'flex', gap: 6, zIndex: 10 }}>
        <button
          onClick={() => setZoom(prev => Math.min(2.5, prev + 0.15))}
          style={{ ...mono, background: 'rgba(9,10,15,0.9)', border: '1px solid #1E2230', color: '#FFFFFF', width: 28, height: 28, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: 13 }}
          title="Zoom In"
        >
          +
        </button>
        <button
          onClick={() => setZoom(prev => Math.max(0.25, prev - 0.15))}
          style={{ ...mono, background: 'rgba(9,10,15,0.9)', border: '1px solid #1E2230', color: '#FFFFFF', width: 28, height: 28, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: 13 }}
          title="Zoom Out"
        >
          -
        </button>
        <button
          onClick={resetView}
          style={{ ...mono, background: 'rgba(9,10,15,0.9)', border: '1px solid #1E2230', color: '#8A91A6', padding: '0 8px', height: 28, cursor: 'pointer', fontSize: 10, letterSpacing: '0.05em' }}
          title="Reset View"
        >
          RESET
        </button>
      </div>

      {/* Legend */}
      <div style={{ position: 'fixed', bottom: 16, left: 16, display: 'flex', flexDirection: 'column', gap: 4, pointerEvents: 'none' }}>
        {[
          { color: '#4D9EFF', label: 'imports', dash: false },
          { color: '#FF7B4B', label: 'calls', dash: true },
        ].map(item => (
          <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 6, ...mono, fontSize: 10, color: '#8A91A6' }}>
            <svg width={20} height={2}>
              <line x1={0} y1={1} x2={20} y2={1} stroke={item.color} strokeWidth={1.5} strokeDasharray={item.dash ? '3 2' : undefined} strokeOpacity={0.7} />
            </svg>
            {item.label}
          </div>
        ))}
      </div>
    </div>
  );
};

// ─── Function code view ──────────────────────────────────────────────────────

const FunctionView = ({ selectedFunction, fileMap, onAsk }) => {
  const functionFile = fileMap[selectedFunction?.filePath] || null;
  if (!selectedFunction || !functionFile) return null;

  const meta = functionFile.functions?.[selectedFunction.functionName];
  const source = functionFile.source || '';
  const lines = source.split('\n');
  const start = Math.max(0, (meta?.lineno || 1) - 1);
  const end = Math.min(lines.length, meta?.end_lineno || start + 1);
  const snippet = lines.slice(start, end).join('\n') || 'Source unavailable.';
  const highlighted = highlight(snippet, getLanguage(functionFile.path));

  return (
    <div style={{ width: '100%', height: '100%', overflow: 'auto', background: '#07080F', padding: 24, boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
        <div>
          <div style={{ ...mono, fontSize: 10, color: '#454B66', letterSpacing: '0.12em', marginBottom: 6 }}>FUNCTION VIEW</div>
          <div style={{ ...mono, fontSize: 16, color: '#E8EAF2' }}>{selectedFunction.functionName}</div>
          <div style={{ ...mono, fontSize: 11, color: '#454B66', marginTop: 4 }}>{functionFile.path}</div>
        </div>
        <button
          type="button"
          onClick={() => onAsk?.('FUNCTION', selectedFunction.functionName)}
          style={{
            ...mono, fontSize: 11, padding: '8px 14px',
            border: '1px solid rgba(255,98,64,0.4)',
            background: 'rgba(255,98,64,0.08)',
            color: '#FF7B4B', cursor: 'pointer',
          }}
        >
          Ask ↗
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '44px 1fr' }}>
        <pre style={{ ...mono, margin: 0, padding: '14px 8px 14px 0', color: '#454B66', textAlign: 'right', userSelect: 'none', lineHeight: 1.6, fontSize: 12 }}>
          {snippet.split('\n').map((_, i) => <div key={i}>{start + i + 1}</div>)}
        </pre>
        <pre style={{ margin: 0, padding: 14, overflowX: 'auto', background: '#0D0F17', lineHeight: 1.6, border: '1px solid #1C2035' }}>
          <code className="hljs" dangerouslySetInnerHTML={{ __html: highlighted }} />
        </pre>
      </div>
    </div>
  );
};

// ─── Main component ──────────────────────────────────────────────────────────

const ArchitectureGraph = ({ selectedFunction, onAsk }) => {
  const { repo } = useAppStore();

  const files = useMemo(() => buildFileData(repo.raw_ast), [repo.raw_ast]);
  const fileMap = useMemo(() => Object.fromEntries(files.map(f => [f.path, f])), [files]);

  const highlightedNodeId = useMemo(() => {
    if (!selectedFunction?.filePath || !repo.raw_ast?.graph?.nodes) return null;
    const node = repo.raw_ast.graph.nodes.find(n => n.label === selectedFunction.filePath);
    return node?.id || null;
  }, [selectedFunction, repo.raw_ast]);

  if (repo.status !== 'ready') return null;

  if (selectedFunction) {
    return (
      <div style={{ width: '100%', height: '100%', position: 'relative' }}>
        <div style={{ position: 'absolute', inset: 0, opacity: 0.15, pointerEvents: 'none' }}>
          <DependencyGraph raw_ast={repo.raw_ast} highlightedNodeId={highlightedNodeId} />
        </div>
        <div style={{ position: 'absolute', inset: 0 }}>
          <FunctionView selectedFunction={selectedFunction} fileMap={fileMap} onAsk={onAsk} />
        </div>
      </div>
    );
  }

  return (
    <DependencyGraph
      raw_ast={repo.raw_ast}
      highlightedNodeId={highlightedNodeId}
      onNodeClick={(node) => {
        onAsk?.('FILE', node.label?.split('/').pop());
      }}
    />
  );
};

export default ArchitectureGraph;