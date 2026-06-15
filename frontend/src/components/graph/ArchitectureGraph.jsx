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

// ─── helpers ────────────────────────────────────────────────────────────────

const getLanguage = (path = '') => {
  if (path.endsWith('.py')) return 'python';
  if (path.endsWith('.ts')) return 'typescript';
  return 'javascript';
};

const highlight = (code, lang) => {
  try { return hljs.highlight(code, { language: lang }).value; }
  catch { return hljs.highlightAuto(code).value; }
};

// Node type label derived from file path
const nodeTypeLabel = (label = '') => {
  if (label.startsWith('src/')) return 'SOURCE';
  if (label.startsWith('tests/') || label.startsWith('test/')) return 'TESTS';
  return 'PROJECT';
};

const typeColor = (label = '') => {
  if (label.startsWith('src/')) return '#FF6240';
  if (label.startsWith('tests/') || label.startsWith('test/')) return '#3DD68C';
  return '#4D9EFF';
};

// ─── Dagre-style layout using a simple topological sort ─────────────────────
// We don't want to add dagre as a dependency — instead we rank nodes by
// how many incoming edges they have (files depended upon rank lower/higher)
// and lay them out in rows.

function computeLayout(nodes, edges, containerWidth) {
  const NODE_W = 190;
  const NODE_H = 60;
  const H_GAP = 240;
  const V_GAP = 110;
  const COLS = Math.max(1, Math.floor((containerWidth - 60) / H_GAP));

  // Build incoming edge count
  const inDegree = {};
  nodes.forEach(n => { inDegree[n.id] = 0; });
  edges.forEach(e => {
    const t = typeof e.target === 'object' ? e.target.id : e.target;
    if (inDegree[t] !== undefined) inDegree[t]++;
  });

  // Sort: entry points first (lowest in-degree), then alphabetical
  const sorted = [...nodes].sort((a, b) => (inDegree[a.id] || 0) - (inDegree[b.id] || 0) || a.id.localeCompare(b.id));

  const positions = {};
  sorted.forEach((node, i) => {
    const col = i % COLS;
    const row = Math.floor(i / COLS);
    positions[node.id] = {
      x: 30 + col * H_GAP,
      y: 30 + row * V_GAP,
    };
  });

  const totalRows = Math.ceil(nodes.length / COLS);
  return {
    positions,
    width: Math.max(containerWidth, COLS * H_GAP + 60),
    height: totalRows * V_GAP + 60,
    nodeW: NODE_W,
    nodeH: NODE_H,
  };
}

// ─── Graph renderer ──────────────────────────────────────────────────────────

const DependencyGraph = ({ raw_ast, onNodeClick, highlightedNodeId }) => {
  const containerRef = useRef(null);
  const [containerWidth, setContainerWidth] = useState(900);
  const [hoveredId, setHoveredId] = useState(null);

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

  const graphNodes = raw_ast?.graph?.nodes || [];
  const graphEdges = raw_ast?.graph?.edges || [];

  if (!graphNodes.length) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', ...mono, color: '#454B66', fontSize: 12 }}>
        No graph data available.
      </div>
    );
  }

  // Build edge paths between node centers
  const edgePaths = graphEdges.map((edge, i) => {
    const srcId = typeof edge.source === 'object' ? edge.source.id : edge.source;
    const dstId = typeof edge.target === 'object' ? edge.target.id : edge.target;
    const s = positions[srcId];
    const d = positions[dstId];
    if (!s || !d) return null;

    const sx = s.x + nodeW / 2;
    const sy = s.y + nodeH;
    const dx = d.x + nodeW / 2;
    const dy = d.y;
    const cy = (sy + dy) / 2;

    return (
      <g key={i}>
        <path
          d={`M ${sx} ${sy} C ${sx} ${cy}, ${dx} ${cy}, ${dx} ${dy}`}
          fill="none"
          stroke={edge.type === 'calls' ? 'rgba(255,98,64,0.4)' : 'rgba(77,158,255,0.25)'}
          strokeWidth={1}
          strokeDasharray={edge.type === 'calls' ? '4 3' : undefined}
          markerEnd="url(#arrowhead)"
        />
      </g>
    );
  });

  return (
    <div
      ref={containerRef}
      style={{ width: '100%', height: '100%', overflow: 'auto', position: 'relative', background: '#07080F' }}
    >
      <svg
        width={width}
        height={height}
        style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}
      >
        <defs>
          <marker id="arrowhead" markerWidth="6" markerHeight="6" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L6,3 z" fill="rgba(77,158,255,0.4)" />
          </marker>
        </defs>
        {edgePaths}
      </svg>

      {/* Nodes rendered as DOM for crisp text and interaction */}
      <div style={{ position: 'relative', width, height }}>
        {graphNodes.map(node => {
          const pos = positions[node.id];
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
              onClick={() => onNodeClick?.(node)}
              onMouseEnter={() => setHoveredId(node.id)}
              onMouseLeave={() => setHoveredId(null)}
              style={{
                position: 'absolute',
                left: pos.x,
                top: pos.y,
                width: nodeW,
                height: nodeH,
                background: isHighlighted ? 'rgba(255,98,64,0.12)' : 'rgba(13,15,23,0.95)',
                border: isHighlighted
                  ? '1px solid #FF6240'
                  : isHovered
                  ? `1px solid ${color}`
                  : '1px solid #1C2035',
                borderLeft: `3px solid ${color}`,
                cursor: 'pointer',
                boxSizing: 'border-box',
                padding: '8px 10px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                gap: 3,
                transition: 'border-color 0.12s',
              }}
            >
              <div style={{ ...mono, fontSize: 9, color, letterSpacing: '0.12em' }}>{label}</div>
              <div style={{ ...mono, fontSize: 12, color: '#E8EAF2', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {fileName}
              </div>
              {dirPath && (
                <div style={{ ...mono, fontSize: 10, color: '#454B66', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {dirPath}/
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div style={{ position: 'fixed', bottom: 16, left: 16, display: 'flex', flexDirection: 'column', gap: 4, pointerEvents: 'none' }}>
        {[
          { color: 'rgba(77,158,255,0.5)', label: 'imports', dash: false },
          { color: 'rgba(255,98,64,0.5)', label: 'calls', dash: true },
        ].map(item => (
          <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 6, ...mono, fontSize: 10, color: '#454B66' }}>
            <svg width={20} height={2}>
              <line x1={0} y1={1} x2={20} y2={1} stroke={item.color} strokeWidth={1.5} strokeDasharray={item.dash ? '3 2' : undefined} />
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
            color: '#FF6240', cursor: 'pointer',
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

  // Find highlighted node from selected function's file
  const highlightedNodeId = useMemo(() => {
    if (!selectedFunction?.filePath || !repo.raw_ast?.graph?.nodes) return null;
    const node = repo.raw_ast.graph.nodes.find(n => n.label === selectedFunction.filePath);
    return node?.id || null;
  }, [selectedFunction, repo.raw_ast]);

  if (repo.status !== 'ready') return null;

  // Function selected → show code, graph stays in background via CSS
  if (selectedFunction) {
    return (
      <div style={{ width: '100%', height: '100%', position: 'relative' }}>
        {/* Graph faded in background */}
        <div style={{ position: 'absolute', inset: 0, opacity: 0.15, pointerEvents: 'none' }}>
          <DependencyGraph raw_ast={repo.raw_ast} highlightedNodeId={highlightedNodeId} />
        </div>
        {/* Function code on top */}
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
        // clicking a graph node asks about that file
        onAsk?.('FILE', node.label?.split('/').pop());
      }}
    />
  );
};

export default ArchitectureGraph;