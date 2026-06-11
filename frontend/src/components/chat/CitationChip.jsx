import React from 'react';
import useAppStore from '../../store/useAppStore';

// Shorten node ID to last 2 parts for display
// src.backend.app.engine_rag.vector_db.ChromaCloudDB.__init__ → ChromaCloudDB.__init__
const shortenNodeId = (nodeId) => {
  const parts = nodeId.split('.');
  if (parts.length <= 2) return nodeId;
  return parts.slice(-2).join('.');
};

// Map citation dot-notation to a React Flow node id (underscore notation)
// src.requests.hooks.default_hooks → find node whose label converted matches
const findGraphNodeId = (nodeId, rawAst) => {
  if (!rawAst?.graph?.nodes) return null;
  const nodes = rawAst.graph.nodes;

  // Try to match by converting node label to module path
  for (const node of nodes) {
    const modulePath = node.label
      .replace(/\\/g, '/')
      .replace('.py', '')
      .replace(/\//g, '.');
    if (nodeId.startsWith(modulePath)) return node.id;
  }
  return null;
};

const CitationChip = ({ nodeId }) => {
  const { repo, setSelectedNode } = useAppStore();
  const displayLabel = shortenNodeId(nodeId);

  const handleClick = () => {
    if (!repo.raw_ast) return;
    const graphNodeId = findGraphNodeId(nodeId, repo.raw_ast);
    if (graphNodeId) {
      const node = repo.raw_ast.graph.nodes.find((n) => n.id === graphNodeId);
      if (node) setSelectedNode(node);
    }
  };

  return (
    <span
      onClick={handleClick}
      title={nodeId}
      style={{
        fontFamily: 'JetBrains Mono, monospace',
        fontSize: '10px',
        padding: '2px 6px',
        background: '#1C2035',
        border: '1px solid #FF6240',
        color: '#FF6240',
        cursor: 'pointer',
        display: 'inline-block',
        margin: '0 2px',
        borderRadius: 0,
        verticalAlign: 'middle',
        lineHeight: '1.4',
        transition: 'background 0.15s, color 0.15s',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = '#FF6240';
        e.currentTarget.style.color = '#07080F';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = '#1C2035';
        e.currentTarget.style.color = '#FF6240';
      }}
    >
      {displayLabel}
    </span>
  );
};

export default CitationChip;