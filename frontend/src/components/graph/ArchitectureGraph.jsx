import React, { useEffect, useRef, useState, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import useAppStore from '../../store/useAppStore';

// Folder colors — translucent, distinct but not dominating
const FOLDER_COLORS = [
  'rgba(255, 98, 64, 0.15)',   // orange
  'rgba(77, 158, 255, 0.15)',  // blue
  'rgba(61, 214, 140, 0.15)',  // green
  'rgba(168, 100, 255, 0.15)', // purple
  'rgba(255, 200, 60, 0.15)',  // yellow
  'rgba(255, 100, 160, 0.15)', // pink
  'rgba(60, 200, 220, 0.15)',  // cyan
];

const FOLDER_BORDER_COLORS = [
  'rgba(255, 98, 64, 0.5)',
  'rgba(77, 158, 255, 0.5)',
  'rgba(61, 214, 140, 0.5)',
  'rgba(168, 100, 255, 0.5)',
  'rgba(255, 200, 60, 0.5)',
  'rgba(255, 100, 160, 0.5)',
  'rgba(60, 200, 220, 0.5)',
];

/**
 * Builds the force graph data from raw_ast.
 * Structure: folder nodes → file nodes → function nodes
 * Expanded state controls which children are visible.
 */
function buildGraphData(raw_ast, expandedFolders, expandedFiles) {
  if (!raw_ast?.files) return { nodes: [], links: [] };

  const nodes = [];
  const links = [];
  const folderColorMap = {};
  let folderColorIndex = 0;

  const files = raw_ast.files;

  // Group files by their top-level folder
  const folderMap = {};
  Object.keys(files).forEach((filePath) => {
    const parts = filePath.split('/');
    const folder = parts.length > 1 ? parts[0] : '__root__';
    if (!folderMap[folder]) folderMap[folder] = [];
    folderMap[folder].push(filePath);
  });

  // Build folder nodes
  Object.keys(folderMap).forEach((folder) => {
    const colorIdx = folderColorIndex % FOLDER_COLORS.length;
    folderColorMap[folder] = colorIdx;
    folderColorIndex++;

    nodes.push({
      id: `folder::${folder}`,
      label: folder === '__root__' ? '/ (root)' : folder,
      type: 'folder',
      colorIdx,
      expanded: expandedFolders.has(folder),
      childCount: folderMap[folder].length,
    });

    // Build file nodes if folder is expanded
    if (expandedFolders.has(folder)) {
      folderMap[folder].forEach((filePath) => {
        const fileName = filePath.split('/').pop();
        const fileData = files[filePath];
        const isEntry = raw_ast.entry_point === filePath;

        nodes.push({
          id: `file::${filePath}`,
          label: fileName,
          fullPath: filePath,
          type: 'file',
          colorIdx: folderColorMap[folder],
          expanded: expandedFiles.has(filePath),
          isEntry,
          functionCount: Object.keys(fileData?.functions || {}).length,
        });

        links.push({
          source: `folder::${folder}`,
          target: `file::${filePath}`,
          type: 'contains',
        });

        // Build function nodes if file is expanded
        if (expandedFiles.has(filePath)) {
          Object.keys(fileData?.functions || {}).forEach((funcName) => {
            nodes.push({
              id: `func::${filePath}::${funcName}`,
              label: funcName,
              filePath,
              type: 'function',
              colorIdx: folderColorMap[folder],
            });

            links.push({
              source: `file::${filePath}`,
              target: `func::${filePath}::${funcName}`,
              type: 'contains',
            });
          });
        }
      });
    }
  });

  // Add dependency edges between files (only if both are visible)
  const visibleFileIds = new Set(
    nodes.filter((n) => n.type === 'file').map((n) => n.id)
  );

  Object.keys(files).forEach((filePath) => {
    const fileData = files[filePath];
    const srcId = `file::${filePath}`;
    if (!visibleFileIds.has(srcId)) return;

    (fileData.depends_on || []).forEach((dep) => {
      const dstId = `file::${dep}`;
      if (visibleFileIds.has(dstId)) {
        links.push({
          source: srcId,
          target: dstId,
          type: 'imports',
        });
      }
    });
  });

  return { nodes, links };
}

const ArchitectureGraph = () => {
  const { repo, sendNodeQuery } = useAppStore();
  const graphRef = useRef(null);
  const containerRef = useRef(null);

  const [expandedFolders, setExpandedFolders] = useState(new Set());
  const [expandedFiles, setExpandedFiles] = useState(new Set());
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [hoveredNode, setHoveredNode] = useState(null);
  const [clickedNode, setClickedNode] = useState(null); // for Ask About This popup

  // Track container size
  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect;
      setDimensions({ width, height });
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // Rebuild graph data when expansion state changes
  useEffect(() => {
    if (repo.raw_ast) {
      const data = buildGraphData(repo.raw_ast, expandedFolders, expandedFiles);
      setGraphData(data);
    }
  }, [repo.raw_ast, expandedFolders, expandedFiles]);

  const handleNodeClick = useCallback(
    (node) => {
      if (node.type === 'folder') {
        setExpandedFolders((prev) => {
          const next = new Set(prev);
          if (next.has(node.label === '/ (root)' ? '__root__' : node.label)) {
            next.delete(node.label === '/ (root)' ? '__root__' : node.label);
          } else {
            next.add(node.label === '/ (root)' ? '__root__' : node.label);
          }
          return next;
        });
        setClickedNode(null);
      } else if (node.type === 'file') {
        setExpandedFiles((prev) => {
          const next = new Set(prev);
          if (next.has(node.fullPath)) {
            next.delete(node.fullPath);
          } else {
            next.add(node.fullPath);
          }
          return next;
        });
        setClickedNode(node);
      } else if (node.type === 'function') {
        setClickedNode(node);
      }
    },
    []
  );

  const handleAskAboutThis = useCallback(() => {
    if (!clickedNode) return;
    const label =
      clickedNode.type === 'function' ? clickedNode.label : clickedNode.label;
    sendNodeQuery(label, clickedNode.type);
    setClickedNode(null);
  }, [clickedNode, sendNodeQuery]);

  // Canvas node painter
  const paintNode = useCallback(
    (node, ctx, globalScale) => {
      const isHovered = hoveredNode?.id === node.id;
      const isClicked = clickedNode?.id === node.id;
      const color = FOLDER_COLORS[node.colorIdx ?? 0];
      const borderColor = FOLDER_BORDER_COLORS[node.colorIdx ?? 0];

      if (node.type === 'folder') {
        const r = 28;
        ctx.beginPath();
        ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
        ctx.fillStyle = isHovered ? color.replace('0.15', '0.28') : color;
        ctx.fill();
        ctx.strokeStyle = isClicked ? '#ffffff' : borderColor;
        ctx.lineWidth = isHovered ? 1.5 : 1;
        ctx.stroke();

        // Label
        ctx.font = `${Math.max(8, 10 / globalScale)}px JetBrains Mono, monospace`;
        ctx.fillStyle = '#E8EAF2';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        const shortLabel =
          node.label.length > 10
            ? node.label.slice(0, 9) + '…'
            : node.label;
        ctx.fillText(shortLabel, node.x, node.y);

        // Child count badge
        if (!node.expanded) {
          ctx.font = `${Math.max(6, 8 / globalScale)}px JetBrains Mono, monospace`;
          ctx.fillStyle = borderColor;
          ctx.fillText(`+${node.childCount}`, node.x, node.y + 14);
        }
      } else if (node.type === 'file') {
        const w = 90;
        const h = 32;
        // Matte rectangle
        ctx.fillStyle = isHovered
          ? 'rgba(14,16,24,0.95)'
          : 'rgba(14,16,24,0.85)';
        ctx.fillRect(node.x - w / 2, node.y - h / 2, w, h);

        // Left color strip
        ctx.fillStyle = borderColor;
        ctx.fillRect(node.x - w / 2, node.y - h / 2, 3, h);

        // Border
        ctx.strokeStyle = isClicked ? '#ffffff' : isHovered ? borderColor : '#1C2035';
        ctx.lineWidth = 1;
        ctx.strokeRect(node.x - w / 2, node.y - h / 2, w, h);

        // Entry point indicator
        if (node.isEntry) {
          ctx.strokeStyle = '#E8EAF2';
          ctx.lineWidth = 1.5;
          ctx.strokeRect(node.x - w / 2 - 2, node.y - h / 2 - 2, w + 4, h + 4);
        }

        // Filename
        ctx.font = `${Math.max(7, 9 / globalScale)}px JetBrains Mono, monospace`;
        ctx.fillStyle = '#E8EAF2';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        const shortName =
          node.label.length > 14 ? node.label.slice(0, 13) + '…' : node.label;
        ctx.fillText(shortName, node.x + 2, node.y - 5);

        // Function count
        if (node.functionCount > 0) {
          ctx.font = `${Math.max(6, 7 / globalScale)}px JetBrains Mono, monospace`;
          ctx.fillStyle = '#454B66';
          ctx.fillText(
            node.expanded ? '▾ collapse' : `▸ ${node.functionCount} fn`,
            node.x + 2,
            node.y + 8
          );
        }
      } else if (node.type === 'function') {
        const r = 14;
        ctx.beginPath();
        ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
        ctx.fillStyle = isHovered
          ? color.replace('0.15', '0.25')
          : 'rgba(14,16,24,0.9)';
        ctx.fill();
        ctx.strokeStyle = isClicked ? '#ffffff' : borderColor;
        ctx.lineWidth = 1;
        ctx.stroke();

        ctx.font = `${Math.max(6, 8 / globalScale)}px JetBrains Mono, monospace`;
        ctx.fillStyle = '#E8EAF2';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        const shortFn =
          node.label.length > 10 ? node.label.slice(0, 9) + '…' : node.label;
        ctx.fillText(shortFn, node.x, node.y);
      }
    },
    [hoveredNode, clickedNode]
  );

  // Link painter
  const paintLink = useCallback((link, ctx) => {
    if (link.type === 'contains') {
      ctx.strokeStyle = 'rgba(28, 32, 53, 0.6)';
      ctx.lineWidth = 0.5;
    } else if (link.type === 'imports') {
      ctx.strokeStyle = 'rgba(77, 158, 255, 0.3)';
      ctx.lineWidth = 1;
      ctx.setLineDash([3, 3]);
    }
    ctx.stroke();
    ctx.setLineDash([]);
  }, []);

  if (repo.status !== 'ready') return null;

  return (
    <div ref={containerRef} className="w-full h-full relative" style={{ background: '#07080F' }}>
      {/* Label */}
      <div className="absolute top-4 left-4 z-10 text-[10px] tracking-widest text-[#454B66] pointer-events-none"
        style={{ fontFamily: 'JetBrains Mono, monospace' }}>
        VIEW::ARCHITECTURE_GRAPH
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-10 flex flex-col gap-1 text-[10px] text-[#454B66]"
        style={{ fontFamily: 'JetBrains Mono, monospace' }}>
        <div className="flex items-center gap-2">
          <span className="w-4 h-px" style={{ background: 'rgba(28,32,53,0.8)', display: 'inline-block' }} />
          contains
        </div>
        <div className="flex items-center gap-2">
          <span className="w-4 h-px" style={{ background: 'rgba(77,158,255,0.5)', display: 'inline-block' }} />
          imports
        </div>
      </div>

      {/* Hint when no folders expanded */}
      {expandedFolders.size === 0 && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
          <span className="text-[11px] text-[#454B66]" style={{ fontFamily: 'JetBrains Mono, monospace' }}>
            Click a folder node to expand
          </span>
        </div>
      )}

      {/* Ask About This popup */}
      {clickedNode && (clickedNode.type === 'file' || clickedNode.type === 'function') && (
        <div
          className="absolute z-20 flex flex-col"
          style={{
            top: 60,
            right: 16,
            background: 'rgba(14,16,24,0.95)',
            border: '1px solid #1C2035',
            backdropFilter: 'blur(12px)',
            fontFamily: 'JetBrains Mono, monospace',
          }}
        >
          <div className="px-3 py-2 text-[10px] text-[#454B66] border-b border-[#1C2035]">
            {clickedNode.type === 'file' ? clickedNode.label : clickedNode.label}
          </div>
          <button
            onClick={handleAskAboutThis}
            className="px-3 py-2 text-[11px] text-[#FF6240] hover:bg-[#FF6240] hover:text-[#07080F] transition-colors text-left"
          >
            ▸ ASK ABOUT THIS
          </button>
          <button
            onClick={() => setClickedNode(null)}
            className="px-3 py-2 text-[11px] text-[#454B66] hover:text-[#E8EAF2] transition-colors text-left"
          >
            ✕ CLOSE
          </button>
        </div>
      )}

      <ForceGraph2D
        ref={graphRef}
        width={dimensions.width}
        height={dimensions.height}
        graphData={graphData}
        nodeCanvasObject={paintNode}
        nodeCanvasObjectMode={() => 'replace'}
        linkCanvasObject={paintLink}
        linkCanvasObjectMode={() => 'replace'}
        onNodeClick={handleNodeClick}
        onNodeHover={(node) => setHoveredNode(node)}
        nodeRelSize={6}
        linkDirectionalArrowLength={3}
        linkDirectionalArrowRelPos={1}
        linkDirectionalArrowColor={() => 'rgba(77,158,255,0.4)'}
        cooldownTicks={120}
        d3AlphaDecay={0.02}
        d3VelocityDecay={0.3}
        backgroundColor="#07080F"
      />
    </div>
  );
};

export default ArchitectureGraph;