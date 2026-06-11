import React from 'react';
import useAppStore from '../../store/useAppStore';

/**
 * CitationChip renders a clickable [node_id] citation inline in chat.
 *
 * The LLM cites nodes by their module-path IDs like:
 *   backend.app.api.gitclone.ingest_github_repo
 *
 * The React Flow graph uses sanitised IDs like:
 *   backend__app__api__gitclone_py   (from flow_builder.node_id())
 *
 * We try to match by:
 *   1. Checking the nodeId against file paths stored in raw_ast.files (exact)
 *   2. Stripping the last dot-segment (function name) to get the module/file
 *   3. Falling back to just highlighting by nodeId as-is
 */
const CitationChip = ({ nodeId }) => {
  const { setSelectedNode, repo } = useAppStore();

  const handleClick = () => {
    const files = repo.raw_ast?.files || {};
    const graphNodes = repo.raw_ast?.graph?.nodes || [];

    // --- Try to find the matching graph node ---
    let matchedNode = null;

    // 1. Check if nodeId matches a file path key in files dict directly
    if (files[nodeId]) {
      // Find graph node whose label equals this file path
      matchedNode = graphNodes.find(n => n.label === nodeId);
    }

    // 2. nodeId is a function id like "backend.app.api.gitclone.ingest_github_repo"
    //    Convert it to a file path guess: drop last segment, replace . with /
    if (!matchedNode) {
      const parts = nodeId.split('.');
      // Try progressively shorter paths (to handle package depth)
      for (let len = parts.length - 1; len >= 1; len--) {
        const candidate = parts.slice(0, len).join('/') + '.py';
        if (files[candidate]) {
          matchedNode = graphNodes.find(n => n.label === candidate);
          if (matchedNode) break;
        }
        // Also try without .py (for __init__ packages)
        const candidatePkg = parts.slice(0, len).join('/') + '/__init__.py';
        if (files[candidatePkg]) {
          matchedNode = graphNodes.find(n => n.label === candidatePkg);
          if (matchedNode) break;
        }
      }
    }

    // 3. Fall back — just set selectedNode with the raw nodeId so the graph does its best
    if (matchedNode) {
      setSelectedNode({ id: matchedNode.id, label: matchedNode.label });
    } else {
      setSelectedNode({ id: nodeId, label: nodeId });
    }
  };

  return (
    <span
      onClick={handleClick}
      title={`Jump to ${nodeId} in the architecture graph`}
      className="inline-flex items-center mx-0.5 px-1.5 py-0.5 text-[11px] font-[var(--font-jetbrains)] rounded-none cursor-pointer transition-all"
      style={{
        background: 'rgba(255,123,75,0.08)',
        border: '1px solid rgba(255,123,75,0.35)',
        color: '#FF7B4B',
      }}
      onMouseEnter={e => {
        e.currentTarget.style.background = '#FF7B4B';
        e.currentTarget.style.color = '#090A0F';
      }}
      onMouseLeave={e => {
        e.currentTarget.style.background = 'rgba(255,123,75,0.08)';
        e.currentTarget.style.color = '#FF7B4B';
      }}
    >
      [{nodeId}]
    </span>
  );
};

export default CitationChip;
