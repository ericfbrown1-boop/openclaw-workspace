#!/usr/bin/env python3
"""
parse_sdlc.py — Walk the Jarvis SDLC file tree and generate a Cytoscape.js-compatible graph JSON.

Usage:
    python3 parse_sdlc.py --output graph_data.json
    python3 parse_sdlc.py --output /tmp/test.json --dry-run
    python3 parse_sdlc.py --output graph_data.json --base-dir /Users/ericbrown/.openclaw

Output format:
    {
        "elements": {
            "nodes": [ { "data": { "id", "label", "type", "path", "metadata": {...} } } ],
            "edges": [ { "data": { "id", "source", "target", "type", "label" } } ]
        },
        "meta": { "generated_at", "node_count", "edge_count", "base_dir" }
    }
"""

import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime, timedelta


# ─── Helpers ────────────────────────────────────────────────────────────────

def slug(path: str, base: str) -> str:
    """Generate a stable, unique node ID from a file path relative to base."""
    rel = os.path.relpath(path, base)
    return re.sub(r"[^a-zA-Z0-9_-]", "_", rel).strip("_").lower()


def safe_read(path: str) -> str | None:
    """Read a file, returning None on any error."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except (OSError, IOError):
        return None


def file_meta(path: str) -> dict:
    """Get file metadata (size, last modified)."""
    try:
        st = os.stat(path)
        return {
            "size": st.st_size,
            "lastModified": datetime.fromtimestamp(st.st_mtime).isoformat(),
        }
    except OSError:
        return {}


def extract_wikilinks(text: str) -> list[str]:
    """Extract [[wikilink]] references from markdown text."""
    return re.findall(r"\[\[([^\]|]+?)(?:\|[^\]]+?)?\]\]", text)


def extract_yaml_frontmatter(text: str) -> dict:
    """Extract key-value pairs from YAML frontmatter (simple parser, no PyYAML needed)."""
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    result = {}
    for line in m.group(1).splitlines():
        kv = line.split(":", 1)
        if len(kv) == 2:
            result[kv[0].strip()] = kv[1].strip().strip('"').strip("'")
    return result


def extract_skill_info(text: str) -> dict:
    """Extract skill name and description from SKILL.md — tries frontmatter then heading + first paragraph."""
    fm = extract_yaml_frontmatter(text)
    if fm.get("name"):
        return {"name": fm["name"], "description": fm.get("description", "")}
    # Fallback: first # heading = name, first paragraph = description
    name_match = re.search(r"^#\s+(.+)", text, re.MULTILINE)
    name = name_match.group(1).strip() if name_match else "Unknown Skill"
    # First non-empty, non-heading paragraph
    desc = ""
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("---"):
            desc = line[:200]
            break
    return {"name": name, "description": desc}


# ─── Node / Edge Builders ──────────────────────────────────────────────────

class GraphBuilder:
    def __init__(self, base_dir: str):
        self.base = base_dir
        self.workspace = os.path.join(base_dir, "workspace")
        self.nodes: dict[str, dict] = {}  # id → node data
        self.edges: dict[str, dict] = {}  # id → edge data

    def add_node(self, node_id: str, label: str, node_type: str, path: str, metadata: dict | None = None):
        if node_id not in self.nodes:
            self.nodes[node_id] = {
                "id": node_id,
                "label": label,
                "type": node_type,
                "path": path,
                "metadata": metadata or {},
            }

    def add_edge(self, source: str, target: str, edge_type: str, label: str = ""):
        edge_id = f"{source}--{edge_type}--{target}"
        if edge_id not in self.edges and source in self.nodes and target in self.nodes:
            self.edges[edge_id] = {
                "id": edge_id,
                "source": source,
                "target": target,
                "type": edge_type,
                "label": label or edge_type.replace("_", " "),
            }

    # ─── Step 1: Agent nodes from openclaw.json ─────────────────────────────

    def parse_agents(self):
        config_path = os.path.join(self.base, "openclaw.json")
        text = safe_read(config_path)
        if not text:
            print(f"  ⚠ Skipping agents — {config_path} not found", file=sys.stderr)
            return

        # Config node itself
        cfg_id = slug(config_path, self.base)
        self.add_node(cfg_id, "openclaw.json", "config", config_path, file_meta(config_path))

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            print(f"  ⚠ Could not parse {config_path}", file=sys.stderr)
            return

        agents = data.get("agents", {}).get("list", [])
        for agent in agents:
            aid = f"agent_{agent['id']}"
            meta = {
                "model": agent.get("model", {}).get("primary", ""),
                "description": f"Agent: {agent.get('name', agent['id'])}",
            }
            if "workspace" in agent:
                meta["workspace"] = agent["workspace"]
            tools = agent.get("tools", {})
            if "allow" in tools:
                meta["tools"] = tools["allow"]

            self.add_node(aid, agent.get("name", agent["id"]), "agent", agent.get("workspace", ""), meta)
            self.add_edge(cfg_id, aid, "configures", f"configures {agent['id']}")

        # Delegation edges: subagents.allowAgents
        for agent in agents:
            aid = f"agent_{agent['id']}"
            allowed = agent.get("subagents", {}).get("allowAgents", [])
            for target_id in allowed:
                target_node = f"agent_{target_id}"
                self.add_edge(aid, target_node, "delegates_to", f"can delegate to {target_id}")

    # ─── Step 2: DELEGATION.md parsing ───────────────────────────────────────

    def parse_delegation(self):
        deleg_path = os.path.join(self.workspace, "DELEGATION.md")
        text = safe_read(deleg_path)
        if not text:
            return

        deleg_id = slug(deleg_path, self.base)
        self.add_node(deleg_id, "DELEGATION.md", "file", deleg_path, file_meta(deleg_path))
        self.add_edge("agent_main", deleg_id, "reads", "reads delegation rules")

        # Extract "→ Agent Name (agentId: xyz)" patterns
        pattern = re.compile(r"→\s+(.+?)\s+(?:Agent\s+)?\(agentId:\s*(\w+)\)")
        for match in pattern.finditer(text):
            agent_name, agent_id = match.group(1).strip(), match.group(2)
            target = f"agent_{agent_id}"
            self.add_edge("agent_main", target, "spawns", f"Jarvis spawns {agent_name}")

    # ─── Step 3: Skill nodes ────────────────────────────────────────────────

    def parse_skills(self):
        skill_pattern = os.path.join(self.workspace, "skills", "*", "SKILL.md")
        for skill_path in sorted(glob.glob(skill_pattern)):
            text = safe_read(skill_path)
            if not text:
                continue
            info = extract_skill_info(text)
            sid = f"skill_{slug(skill_path, self.base)}"
            meta = {
                "description": info["description"],
                **file_meta(skill_path),
            }
            self.add_node(sid, info["name"], "skill", skill_path, meta)
            # All agents can potentially read skills; main is the primary consumer
            self.add_edge("agent_main", sid, "reads", f"uses skill: {info['name']}")

    # ─── Step 4: Per-agent workspace AGENTS.md ──────────────────────────────

    def parse_agent_workspaces(self):
        pattern = os.path.join(self.base, "workspace-*", "AGENTS.md")
        for agents_path in sorted(glob.glob(pattern)):
            text = safe_read(agents_path)
            if not text:
                continue
            workspace_name = os.path.basename(os.path.dirname(agents_path))
            # e.g. workspace-coder → coder
            agent_id_guess = workspace_name.replace("workspace-", "")
            fid = slug(agents_path, self.base)
            self.add_node(fid, f"{workspace_name}/AGENTS.md", "file", agents_path, file_meta(agents_path))

            target_agent = f"agent_{agent_id_guess}"
            self.add_edge(target_agent, fid, "reads", f"{agent_id_guess} reads its AGENTS.md")

    # ─── Step 5: All .md files → file nodes + wikilink edges ───────────────

    def parse_md_files(self):
        search_dirs = [self.workspace] + sorted(glob.glob(os.path.join(self.base, "workspace-*")))
        md_files: list[str] = []
        for d in search_dirs:
            for root, dirs, files in os.walk(d):
                # Skip node_modules, .git, etc.
                dirs[:] = [x for x in dirs if x not in (".git", "node_modules", "__pycache__", ".next")]
                for f in files:
                    if f.endswith(".md"):
                        md_files.append(os.path.join(root, f))

        # Index: filename (no ext, lowercased) → node_id for wikilink resolution
        name_index: dict[str, str] = {}

        for fpath in md_files:
            fid = slug(fpath, self.base)
            fname = os.path.basename(fpath)
            label = os.path.relpath(fpath, self.base)

            # Classify
            if "/memory/" in fpath:
                ftype = "memory"
            elif "/skills/" in fpath:
                continue  # Already handled in parse_skills
            elif fname in ("PLAN.md", "PIPELINE.md"):
                ftype = "plan"
            elif fname in ("openclaw.json",):
                ftype = "config"
            else:
                ftype = "file"

            self.add_node(fid, label, ftype, fpath, file_meta(fpath))
            name_index[os.path.splitext(fname)[0].lower()] = fid

        # Second pass: wikilink edges
        for fpath in md_files:
            text = safe_read(fpath)
            if not text:
                continue
            fid = slug(fpath, self.base)
            if fid not in self.nodes:
                continue
            links = extract_wikilinks(text)
            for link in links:
                target_key = link.strip().lower()
                target_id = name_index.get(target_key)
                if target_id and target_id != fid:
                    self.add_edge(fid, target_id, "references", f"[[{link}]]")

    # ─── Step 6: Memory nodes (last 14 days) ───────────────────────────────

    def parse_memory(self):
        mem_dir = os.path.join(self.workspace, "memory")
        if not os.path.isdir(mem_dir):
            return

        cutoff = datetime.now() - timedelta(days=14)
        date_pattern = re.compile(r"(\d{4}-\d{2}-\d{2})")

        for fname in sorted(os.listdir(mem_dir)):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(mem_dir, fname)
            m = date_pattern.search(fname)
            if m:
                try:
                    fdate = datetime.strptime(m.group(1), "%Y-%m-%d")
                    if fdate < cutoff:
                        continue
                except ValueError:
                    pass

            fid = slug(fpath, self.base)
            self.add_node(fid, f"memory/{fname}", "memory", fpath, file_meta(fpath))
            self.add_edge("agent_main", fid, "writes", f"Jarvis writes {fname}")

    # ─── Step 7: Script nodes ───────────────────────────────────────────────

    def parse_scripts(self):
        scripts_dir = os.path.join(self.workspace, "scripts")
        if not os.path.isdir(scripts_dir):
            return

        for fname in sorted(os.listdir(scripts_dir)):
            if not (fname.endswith(".py") or fname.endswith(".sh")):
                continue
            fpath = os.path.join(scripts_dir, fname)
            fid = slug(fpath, self.base)
            self.add_node(fid, f"scripts/{fname}", "script", fpath, file_meta(fpath))
            # Scripts are triggered by the main agent
            self.add_edge("agent_main", fid, "triggers", f"runs {fname}")

    # ─── Build all ──────────────────────────────────────────────────────────

    def build(self) -> dict:
        print("Parsing agents from openclaw.json...", file=sys.stderr)
        self.parse_agents()
        print(f"  → {len(self.nodes)} nodes, {len(self.edges)} edges", file=sys.stderr)

        print("Parsing DELEGATION.md...", file=sys.stderr)
        self.parse_delegation()
        print(f"  → {len(self.nodes)} nodes, {len(self.edges)} edges", file=sys.stderr)

        print("Parsing skills...", file=sys.stderr)
        self.parse_skills()
        print(f"  → {len(self.nodes)} nodes, {len(self.edges)} edges", file=sys.stderr)

        print("Parsing agent workspaces...", file=sys.stderr)
        self.parse_agent_workspaces()
        print(f"  → {len(self.nodes)} nodes, {len(self.edges)} edges", file=sys.stderr)

        print("Parsing .md files + wikilinks...", file=sys.stderr)
        self.parse_md_files()
        print(f"  → {len(self.nodes)} nodes, {len(self.edges)} edges", file=sys.stderr)

        print("Parsing memory (last 14 days)...", file=sys.stderr)
        self.parse_memory()
        print(f"  → {len(self.nodes)} nodes, {len(self.edges)} edges", file=sys.stderr)

        print("Parsing scripts...", file=sys.stderr)
        self.parse_scripts()
        print(f"  → {len(self.nodes)} nodes, {len(self.edges)} edges", file=sys.stderr)

        return {
            "elements": {
                "nodes": [{"data": n} for n in self.nodes.values()],
                "edges": [{"data": e} for e in self.edges.values()],
            },
            "meta": {
                "generated_at": datetime.now().isoformat(),
                "node_count": len(self.nodes),
                "edge_count": len(self.edges),
                "base_dir": self.base,
            },
        }


# ─── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate Cytoscape.js graph JSON from Jarvis SDLC file tree")
    parser.add_argument("--output", "-o", required=True, help="Output JSON file path")
    parser.add_argument("--base-dir", default="/Users/ericbrown/.openclaw", help="Base OpenClaw directory")
    parser.add_argument("--dry-run", action="store_true", help="Print counts without writing output file")
    args = parser.parse_args()

    if not os.path.isdir(args.base_dir):
        print(f"ERROR: Base directory not found: {args.base_dir}", file=sys.stderr)
        sys.exit(1)

    builder = GraphBuilder(args.base_dir)
    graph = builder.build()

    print(f"\n{'='*50}", file=sys.stderr)
    print(f"Total nodes: {graph['meta']['node_count']}", file=sys.stderr)
    print(f"Total edges: {graph['meta']['edge_count']}", file=sys.stderr)

    # Breakdown by type
    type_counts: dict[str, int] = {}
    for n in graph["elements"]["nodes"]:
        t = n["data"]["type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    for t, c in sorted(type_counts.items()):
        print(f"  {t}: {c}", file=sys.stderr)

    edge_type_counts: dict[str, int] = {}
    for e in graph["elements"]["edges"]:
        t = e["data"]["type"]
        edge_type_counts[t] = edge_type_counts.get(t, 0) + 1
    for t, c in sorted(edge_type_counts.items()):
        print(f"  edge.{t}: {c}", file=sys.stderr)
    print(f"{'='*50}", file=sys.stderr)

    if args.dry_run:
        print("Dry run — no file written.", file=sys.stderr)
    else:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(graph, f, indent=2, ensure_ascii=False)
        print(f"Written to: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
