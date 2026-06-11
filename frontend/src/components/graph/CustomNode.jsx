import React from 'react';
import { Handle, Position } from '@xyflow/react';
import useAppStore from '../../store/useAppStore';

const groupColors = {
  source:  '#FF7B4B',
  project: '#8A91A6',
  tests:   '#70D6B7',
  docs:    '#F9E4B7',
};

const CustomNode = ({ data, id }) => {
  const { selectedNode, setSelectedNode } = useAppStore();
  const isSelected = selectedNode?.id === id;
  const accentColor = groupColors[data.group] || groupColors.project;

  return (
    <div
      className="min-w-[170px] max-w-[220px] cursor-pointer transition-all duration-200"
      style={{
        background: isSelected ? 'rgba(255,123,75,0.07)' : 'rgba(9,10,15,0.85)',
        border: `1px solid ${isSelected ? '#FF7B4B' : '#1E2230'}`,
        boxShadow: isSelected ? '0 0 16px rgba(255,123,75,0.35)' : 'none',
        padding: '8px 12px',
      }}
      onClick={() => setSelectedNode({ id, label: data.label, ...data })}
    >
      <Handle type="target" position={Position.Top} style={{ background: '#1E2230', border: 'none' }} />

      {/* Group badge */}
      <span
        className="block text-[9px] font-[var(--font-jetbrains)] uppercase tracking-widest mb-1"
        style={{ color: accentColor }}
      >
        {data.group || 'MODULE'}
        {data.entry && (
          <span className="ml-2 text-[var(--color-telemetry-accent)]">● ENTRY</span>
        )}
      </span>

      {/* File path label */}
      <span
        className="block text-[11px] font-[var(--font-jetbrains)] leading-tight break-all"
        style={{ color: isSelected ? '#FF7B4B' : '#E6E9F2' }}
      >
        {data.label}
      </span>

      <Handle type="source" position={Position.Bottom} style={{ background: '#1E2230', border: 'none' }} />
    </div>
  );
};

export default CustomNode;
