import React, { useEffect, useRef } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  useReactFlow,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import useAppStore from '../../store/useAppStore';
import CustomNode from './CustomNode';

const nodeTypes = { custom: CustomNode };

/**
 * Converts the backend graph structure to React Flow format.
 * Backend `graph` has: { nodes: [{id, label, group}], edges: [{source, target, type}] }
 * Backend `files` has the raw per-file data (used as node metadata).
 */
function buildReactFlowData(raw_ast) {
  const rfNodes = [];
  const rfEdges = [];

  if (!raw_ast) return { rfNodes, rfEdges };

  const graphNodes = raw_ast.graph?.nodes || [];
  const graphEdges = raw_ast.graph?.edges || [];
  const filesData   = raw_ast.files   || {};

  // Map graph nodes into React Flow nodes with simple column layout
  graphNodes.forEach((node, index) => {
    const cols = 5;
    const colWidth = 260;
    const rowHeight = 130;
    const col = index % cols;
    const row = Math.floor(index / cols);

    rfNodes.push({
      id: node.id,           // already sanitised string like "backend__app__main_py"
      type: 'custom',
      position: { x: col * colWidth + 40, y: row * rowHeight + 40 },
      data: {
        label: node.label,   // original file path, e.g. "backend/app/main.py"
        group: node.group,
        // Attach the per-file metadata from raw_ast.files
        ...(filesData[node.label] || {}),
        entry: raw_ast.entry_point === node.label,
      },
    });
  });

  // Map graph edges into React Flow edges
  graphEdges.forEach((edge, index) => {
    rfEdges.push({
      id: `e-${edge.source}-${edge.target}-${index}`,
      source: edge.source,
      target: edge.target,
      label: edge.type === 'calls' ? 'calls' : undefined,
      animated: edge.type === 'calls',
      style: {
        stroke: edge.type === 'calls' ? '#FF7B4B' : '#1E2230',
        strokeWidth: 1.5,
      },
    });
  });

  return { rfNodes, rfEdges };
}

// Inner component that has access to useReactFlow() context
const GraphPanner = ({ selectedNode }) => {
  const { fitView, setCenter } = useReactFlow();
  const prevNodeId = useRef(null);

  useEffect(() => {
    if (selectedNode?.id && selectedNode.id !== prevNodeId.current) {
      prevNodeId.current = selectedNode.id;
      // Give the layout a tick to settle, then zoom-to-node
      setTimeout(() => {
        fitView({ nodes: [{ id: selectedNode.id }], duration: 600, padding: 0.3 });
      }, 50);
    }
  }, [selectedNode, fitView]);

  return null;
};

const ArchitectureGraph = () => {
  const { repo, selectedNode } = useAppStore();
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    if (repo.raw_ast) {
      const { rfNodes, rfEdges } = buildReactFlowData(repo.raw_ast);
      setNodes(rfNodes);
      setEdges(rfEdges);
    }
  }, [repo.raw_ast, setNodes, setEdges]);

  if (repo.status !== 'ready') return null;

  return (
    <div className="w-full h-full bg-[var(--color-telemetry-bg)] relative">
      {/* Graph label */}
      <div
        className="absolute top-4 left-4 z-10 font-[var(--font-jetbrains)] text-[10px] tracking-widest text-[var(--color-telemetry-muted)] pointer-events-none"
      >
        VIEW::ARCHITECTURE_GRAPH
      </div>

      {/* Legend */}
      <div
        className="absolute bottom-14 left-4 z-10 flex flex-col gap-1 font-[var(--font-jetbrains)] text-[10px] text-[var(--color-telemetry-muted)]"
      >
        <div className="flex items-center gap-2">
          <span className="w-6 h-px bg-[#1E2230] inline-block border border-[#1E2230]" />
          imports
        </div>
        <div className="flex items-center gap-2">
          <span className="w-6 h-px bg-[#FF7B4B] inline-block" />
          calls
        </div>
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.15 }}
        minZoom={0.1}
        maxZoom={2}
        style={{ background: '#090A0F' }}
      >
        <Background gap={32} size={1} color="#1E2230" />
        <Controls
          style={{
            background: '#090A0F',
            border: '1px solid #1E2230',
            borderRadius: 0,
          }}
        />
        {/* Pans to selected node when a citation chip is clicked */}
        <GraphPanner selectedNode={selectedNode} />
      </ReactFlow>
    </div>
  );
};

export default ArchitectureGraph;
