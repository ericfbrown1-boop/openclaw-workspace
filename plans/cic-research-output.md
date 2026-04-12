# CIC Spike — Research Output

**Date:** 2026-04-12
**Author:** Jarvis (subagent spike)

---

## Task 1 — PowerSpec Environment Verification

| Component | Version | Status |
|-----------|---------|--------|
| Python | 3.12.10 | ✅ (`python` not `python3` on Windows) |
| Node.js | v24.14.1 | ✅ |
| npm | 11.11.0 | ✅ |

**Note:** On Windows, use `python` (not `python3`). The `python3` alias is a Microsoft Store redirect.

---

## Task 2 — parse_sdlc.py

### Design Decisions
- **Zero external dependencies** — uses only Python stdlib (json, re, glob, os, pathlib, argparse)
- **Stable node IDs** — slugified relative paths (deterministic across runs)
- **Edge deduplication** — `source--type--target` composite keys in a dict
- **Graceful degradation** — `safe_read()` returns None on any I/O error; missing files are skipped with stderr warnings
- **Cytoscape.js native format** — `{ elements: { nodes: [{data:{...}}], edges: [{data:{...}}] }, meta: {...} }`

### What It Parses

| Source | Node Type | Edge Types |
|--------|-----------|------------|
| `openclaw.json` agents list | `agent` | `configures` (config→agent), `delegates_to` (agent→agent via allowAgents) |
| `DELEGATION.md` | `file` | `spawns` (main→agent via `→ AgentName (agentId: x)` pattern) |
| `skills/*/SKILL.md` | `skill` | `reads` (main→skill) |
| `workspace-*/AGENTS.md` | `file` | `reads` (agent→its AGENTS.md) |
| All `*.md` files | `file`, `memory`, `plan` | `references` (via `[[wikilink]]` extraction) |
| `memory/YYYY-MM-DD.md` (14d) | `memory` | `writes` (main→memory) |
| `scripts/*.py`, `*.sh` | `script` | `triggers` (main→script) |

### Real Run Results (against live SDLC tree)

```
Total nodes: 337
Total edges: 126
  agent: 8
  config: 1
  file: 169
  memory: 99
  plan: 3
  script: 30
  skill: 27
  edge.configures: 8
  edge.delegates_to: 7
  edge.reads: 35
  edge.spawns: 7
  edge.triggers: 30
  edge.writes: 39
```

### Full Script

See `parse_sdlc.py` in this directory. Key APIs:

```python
from parse_sdlc import GraphBuilder

builder = GraphBuilder("/Users/ericbrown/.openclaw")
graph = builder.build()
# graph["elements"]["nodes"] → list of {data: {id, label, type, path, metadata}}
# graph["elements"]["edges"] → list of {data: {id, source, target, type, label}}
```

---

## Task 3 — Test Results

**17/17 tests pass** on both MacBook (Python 3.x) and mock data.

Tests cover:
- Helper functions (slug determinism, wikilink extraction, YAML frontmatter parsing, heading fallback)
- Full graph build (structure, agent nodes, delegation edges, skill nodes, memory nodes, script nodes, wikilink edges)
- Schema validation (all required fields present, types within allowed set)
- Edge deduplication (no duplicate IDs)
- JSON serialization round-trip

See `test_parse_sdlc.py` for full test suite.

---

## Task 4 — Cytoscape.js Layout Recommendation

### Layout Comparison for ~337 Nodes

| Layout | Package | Pros | Cons | Verdict |
|--------|---------|------|------|---------|
| **cose** | Built-in | Zero deps, decent force-directed | No hierarchy awareness, slow >200 nodes | ❌ Too many nodes |
| **cose-bilkent** | `cytoscape-cose-bilkent` | Compound-aware, good clustering | Still force-directed, no clear top-down | 🟡 Decent |
| **dagre** | `cytoscape-dagre` | True hierarchical DAG, clean top→bottom | Poor with cross-links, rigid grid feel | 🟡 Good for pure DAG |
| **elk** | `cytoscape-elk` | Eclipse Layout Kernel — best-in-class hierarchical + layered, handles cross-edges well, configurable | Larger bundle (~100KB), WASM-based | ✅ **RECOMMENDED** |

### Recommendation: **ELK (layered)**

ELK's `layered` algorithm is purpose-built for hierarchical graphs with cross-links — exactly our topology (Jarvis→agents→skills/files with wikilink cross-references). It produces clean, readable layouts with minimal edge crossings.

### Install

```bash
npm install cytoscape cytoscape-elk elkjs
```

### Cytoscape.js Init Config

```typescript
import cytoscape from 'cytoscape';
import elk from 'cytoscape-elk';

cytoscape.use(elk);

const cy = cytoscape({
  container: document.getElementById('cy'),
  elements: graphData.elements,  // from parse_sdlc.py output
  layout: {
    name: 'elk',
    elk: {
      algorithm: 'layered',
      'elk.direction': 'DOWN',
      'elk.layered.spacing.nodeNodeBetweenLayers': 80,
      'elk.layered.spacing.edgeNodeBetweenLayers': 40,
      'elk.spacing.nodeNode': 40,
      'elk.layered.crossingMinimization.strategy': 'LAYER_SWEEP',
      'elk.layered.nodePlacement.strategy': 'NETWORK_SIMPLEX',
    },
    padding: 40,
  },
  style: [
    {
      selector: 'node',
      style: {
        label: 'data(label)',
        'text-valign': 'bottom',
        'text-halign': 'center',
        'font-size': '11px',
        'text-max-width': '120px',
        'text-wrap': 'ellipsis',
        width: 40,
        height: 40,
      },
    },
    // Node type colors
    { selector: 'node[type="agent"]',  style: { 'background-color': '#FF6B6B', shape: 'hexagon', width: 60, height: 60 } },
    { selector: 'node[type="skill"]',  style: { 'background-color': '#4ECDC4', shape: 'round-rectangle' } },
    { selector: 'node[type="config"]', style: { 'background-color': '#FFE66D', shape: 'diamond' } },
    { selector: 'node[type="file"]',   style: { 'background-color': '#95E1D3', shape: 'rectangle' } },
    { selector: 'node[type="memory"]', style: { 'background-color': '#A8D8EA', shape: 'ellipse' } },
    { selector: 'node[type="script"]', style: { 'background-color': '#AA96DA', shape: 'barrel' } },
    { selector: 'node[type="plan"]',   style: { 'background-color': '#FCBAD3', shape: 'star' } },
    // Edge styles
    {
      selector: 'edge',
      style: {
        width: 1.5,
        'line-color': '#999',
        'target-arrow-color': '#999',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        'arrow-scale': 0.8,
      },
    },
    { selector: 'edge[type="delegates_to"]', style: { 'line-color': '#FF6B6B', 'target-arrow-color': '#FF6B6B', width: 3 } },
    { selector: 'edge[type="spawns"]',       style: { 'line-color': '#FF9F43', 'target-arrow-color': '#FF9F43', width: 2.5, 'line-style': 'dashed' } },
    { selector: 'edge[type="references"]',   style: { 'line-color': '#C8D6E5', width: 1, 'line-style': 'dotted' } },
  ],
});
```

### Performance Note
For 337 nodes, ELK layout computes in <500ms. For >500 nodes, consider:
- Web Worker offloading (`elkjs/lib/elk.bundled.js` runs in workers)
- Progressive rendering (show agents+skills first, lazy-load file/memory nodes)
- Filtering UI (toggle node types on/off)

---

## Task 5 — Next.js App Router + Cytoscape.js SSR-Safe Pattern

Cytoscape.js accesses `window` and `document` at import time, which crashes Next.js SSR. The solution is `next/dynamic` with `ssr: false`.

### Pattern: `app/(pages)/cic/page.tsx`

```tsx
// app/(pages)/cic/page.tsx
import { Suspense } from 'react';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'CIC — Command Information Center',
  description: 'Interactive graph of the Jarvis SDLC file tree',
};

// Dynamic import with SSR disabled — this is the key pattern
import dynamic from 'next/dynamic';

const CICGraph = dynamic(() => import('@/components/cic/CICGraph'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-[calc(100vh-64px)]">
      <div className="animate-pulse text-gray-400">Loading graph...</div>
    </div>
  ),
});

export default function CICPage() {
  return (
    <main className="h-screen w-full">
      <Suspense fallback={<div>Loading...</div>}>
        <CICGraph />
      </Suspense>
    </main>
  );
}
```

### Component: `components/cic/CICGraph.tsx`

```tsx
'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import cytoscape, { type Core } from 'cytoscape';
import elk from 'cytoscape-elk';

// Register ELK layout — safe here because this component never runs on server
cytoscape.use(elk);

// Type for our graph data
interface GraphData {
  elements: {
    nodes: Array<{ data: Record<string, any> }>;
    edges: Array<{ data: Record<string, any> }>;
  };
  meta: Record<string, any>;
}

const NODE_TYPE_COLORS: Record<string, string> = {
  agent: '#FF6B6B',
  skill: '#4ECDC4',
  config: '#FFE66D',
  file: '#95E1D3',
  memory: '#A8D8EA',
  script: '#AA96DA',
  plan: '#FCBAD3',
};

const LAYOUT_OPTIONS = {
  name: 'elk' as const,
  elk: {
    algorithm: 'layered',
    'elk.direction': 'DOWN',
    'elk.layered.spacing.nodeNodeBetweenLayers': 80,
    'elk.layered.spacing.edgeNodeBetweenLayers': 40,
    'elk.spacing.nodeNode': 40,
    'elk.layered.crossingMinimization.strategy': 'LAYER_SWEEP',
    'elk.layered.nodePlacement.strategy': 'NETWORK_SIMPLEX',
  },
  padding: 40,
};

export default function CICGraph() {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [selectedNode, setSelectedNode] = useState<Record<string, any> | null>(null);
  const [filter, setFilter] = useState<Set<string>>(new Set(['agent', 'skill', 'config', 'file', 'memory', 'script', 'plan']));

  // Fetch graph data
  useEffect(() => {
    fetch('/api/cic/graph')
      .then((r) => r.json())
      .then(setGraphData)
      .catch(console.error);
  }, []);

  // Initialize Cytoscape
  useEffect(() => {
    if (!containerRef.current || !graphData) return;

    // Filter elements by active node types
    const filteredNodes = graphData.elements.nodes.filter((n) => filter.has(n.data.type));
    const nodeIds = new Set(filteredNodes.map((n) => n.data.id));
    const filteredEdges = graphData.elements.edges.filter(
      (e) => nodeIds.has(e.data.source) && nodeIds.has(e.data.target)
    );

    const cy = cytoscape({
      container: containerRef.current,
      elements: { nodes: filteredNodes, edges: filteredEdges },
      layout: LAYOUT_OPTIONS,
      style: [
        {
          selector: 'node',
          style: {
            label: 'data(label)',
            'text-valign': 'bottom',
            'text-halign': 'center',
            'font-size': '11px',
            'text-max-width': '120px',
            'text-wrap': 'ellipsis',
            width: 40,
            height: 40,
            'background-color': '#ccc',
          } as any,
        },
        ...Object.entries(NODE_TYPE_COLORS).map(([type, color]) => ({
          selector: `node[type="${type}"]`,
          style: {
            'background-color': color,
            ...(type === 'agent' ? { shape: 'hexagon', width: 60, height: 60 } : {}),
          } as any,
        })),
        {
          selector: 'edge',
          style: {
            width: 1.5,
            'line-color': '#999',
            'target-arrow-color': '#999',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'arrow-scale': 0.8,
          } as any,
        },
        {
          selector: ':selected',
          style: {
            'border-width': 3,
            'border-color': '#333',
          } as any,
        },
      ],
      minZoom: 0.1,
      maxZoom: 5,
      wheelSensitivity: 0.3,
    });

    cy.on('tap', 'node', (evt) => {
      setSelectedNode(evt.target.data());
    });

    cy.on('tap', (evt) => {
      if (evt.target === cy) setSelectedNode(null);
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
      cyRef.current = null;
    };
  }, [graphData, filter]);

  const toggleFilter = useCallback((type: string) => {
    setFilter((prev) => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  }, []);

  return (
    <div className="relative h-full w-full">
      {/* Filter toolbar */}
      <div className="absolute top-4 left-4 z-10 flex gap-2 bg-white/90 backdrop-blur rounded-lg p-2 shadow">
        {Object.entries(NODE_TYPE_COLORS).map(([type, color]) => (
          <button
            key={type}
            onClick={() => toggleFilter(type)}
            className={`px-3 py-1 rounded text-xs font-medium transition-opacity ${
              filter.has(type) ? 'opacity-100' : 'opacity-30'
            }`}
            style={{ backgroundColor: color }}
          >
            {type}
          </button>
        ))}
      </div>

      {/* Graph container */}
      <div ref={containerRef} className="h-full w-full" />

      {/* Detail panel */}
      {selectedNode && (
        <div className="absolute bottom-4 right-4 z-10 w-80 bg-white/95 backdrop-blur rounded-lg p-4 shadow-lg">
          <h3 className="font-bold text-sm truncate">{selectedNode.label}</h3>
          <span
            className="inline-block px-2 py-0.5 rounded text-xs mt-1"
            style={{ backgroundColor: NODE_TYPE_COLORS[selectedNode.type] || '#ccc' }}
          >
            {selectedNode.type}
          </span>
          <pre className="mt-2 text-xs text-gray-600 overflow-auto max-h-40">
            {JSON.stringify(selectedNode.metadata, null, 2)}
          </pre>
        </div>
      )}

      {/* Stats */}
      {graphData && (
        <div className="absolute bottom-4 left-4 z-10 text-xs text-gray-500 bg-white/80 rounded px-2 py-1">
          {graphData.meta.node_count} nodes · {graphData.meta.edge_count} edges
        </div>
      )}
    </div>
  );
}
```

### API Route: `app/api/cic/graph/route.ts`

```typescript
import { NextResponse } from 'next/server';
import { readFile } from 'fs/promises';
import path from 'path';

export async function GET() {
  // In production, run parse_sdlc.py on-demand or read cached JSON
  const graphPath = path.join(process.cwd(), 'data', 'graph_data.json');
  try {
    const data = await readFile(graphPath, 'utf-8');
    return NextResponse.json(JSON.parse(data));
  } catch {
    return NextResponse.json({ error: 'Graph data not found' }, { status: 404 });
  }
}
```

### Key SSR Safety Rules

1. **Never import `cytoscape` at the top level of a server component** — it accesses `window` on import
2. **Use `next/dynamic` with `ssr: false`** for the graph component
3. **Register extensions (`cytoscape.use(elk)`) inside the client component**, not in a shared module
4. **The `'use client'` directive** is necessary on the graph component but NOT sufficient alone — you still need dynamic import at the page level
5. **Cleanup:** Always `cy.destroy()` in the useEffect cleanup to prevent memory leaks on re-renders

---

## Summary & Next Steps

| Item | Status | Location |
|------|--------|----------|
| parse_sdlc.py | ✅ Complete, tested | `C:/Users/Eric Brown/cic_spike/parse_sdlc.py` + MacBook `/tmp/cic_spike/` |
| test_parse_sdlc.py | ✅ 17/17 pass | `C:/Users/Eric Brown/cic_spike/test_parse_sdlc.py` |
| graph_data.json (real) | ✅ 337 nodes, 126 edges | `C:/Users/Eric Brown/cic_spike/graph_data.json` |
| Layout recommendation | ✅ ELK layered | See Task 4 above |
| Next.js SSR pattern | ✅ Complete | See Task 5 above |

### Recommended Next Steps
1. **Set up the Next.js project** with `npx create-next-app@latest cic --typescript --tailwind --app`
2. **Install deps:** `npm install cytoscape cytoscape-elk elkjs @types/cytoscape`
3. **Copy `graph_data.json`** into `data/` directory
4. **Create the components** from the patterns above
5. **Add search/filter** — the filter toolbar is already in the component
6. **Add live refresh** — run `parse_sdlc.py` as a cron/watcher and serve fresh JSON
7. **Consider grouping** — use Cytoscape compound nodes to group files by workspace
