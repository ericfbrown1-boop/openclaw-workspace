#!/usr/bin/env python3
"""
test_parse_sdlc.py — Unit tests for parse_sdlc.py using mock data in a temp directory.
"""

import json
import os
import sys
import tempfile
import unittest

# Ensure parse_sdlc is importable
sys.path.insert(0, os.path.dirname(__file__))
from parse_sdlc import GraphBuilder, slug, extract_wikilinks, extract_skill_info


class TestHelpers(unittest.TestCase):
    def test_slug_basic(self):
        s = slug("/base/workspace/AGENTS.md", "/base")
        self.assertRegex(s, r"^[a-z0-9_-]+$")
        self.assertNotIn("/", s)

    def test_slug_deterministic(self):
        a = slug("/a/b/c.md", "/a")
        b = slug("/a/b/c.md", "/a")
        self.assertEqual(a, b)

    def test_extract_wikilinks(self):
        text = "See [[PIPELINE]] and [[DELEGATION|delegation rules]] for more."
        links = extract_wikilinks(text)
        self.assertEqual(sorted(links), ["DELEGATION", "PIPELINE"])

    def test_extract_wikilinks_empty(self):
        self.assertEqual(extract_wikilinks("no links here"), [])

    def test_extract_skill_info_frontmatter(self):
        text = "---\nname: MySkill\ndescription: Does cool stuff\n---\n# MySkill\nBody."
        info = extract_skill_info(text)
        self.assertEqual(info["name"], "MySkill")
        self.assertEqual(info["description"], "Does cool stuff")

    def test_extract_skill_info_heading_fallback(self):
        text = "# Weather Skill\nGet weather data from wttr.in."
        info = extract_skill_info(text)
        self.assertEqual(info["name"], "Weather Skill")
        self.assertIn("weather", info["description"].lower())


class TestGraphBuilder(unittest.TestCase):
    def setUp(self):
        """Create a mock .openclaw directory with realistic structure."""
        self.tmpdir = tempfile.mkdtemp()
        base = self.tmpdir

        # openclaw.json
        config = {
            "agents": {
                "list": [
                    {
                        "id": "main",
                        "name": "Jarvis",
                        "model": {"primary": "anthropic/claude-opus-4-6"},
                        "workspace": f"{base}/workspace",
                        "tools": {"allow": ["read", "write", "exec"]},
                        "subagents": {"allowAgents": ["coder", "researcher"]},
                    },
                    {
                        "id": "coder",
                        "name": "Coder",
                        "model": {"primary": "anthropic/claude-opus-4-6"},
                        "workspace": f"{base}/workspace-coder",
                    },
                    {
                        "id": "researcher",
                        "name": "Researcher",
                        "model": {"primary": "anthropic/claude-opus-4-6"},
                        "workspace": f"{base}/workspace-researcher",
                    },
                ]
            }
        }
        with open(os.path.join(base, "openclaw.json"), "w") as f:
            json.dump(config, f)

        # workspace/DELEGATION.md
        ws = os.path.join(base, "workspace")
        os.makedirs(ws, exist_ok=True)
        with open(os.path.join(ws, "DELEGATION.md"), "w") as f:
            f.write("# Delegation\n## → Coder Agent (agentId: coder)\nTrigger: code tasks\n## → Researcher (agentId: researcher)\nTrigger: research\n")

        # workspace/AGENTS.md
        with open(os.path.join(ws, "AGENTS.md"), "w") as f:
            f.write("# AGENTS.md\nRead [[DELEGATION]] and [[PIPELINE]] first.\n")

        # workspace/PIPELINE.md
        with open(os.path.join(ws, "PIPELINE.md"), "w") as f:
            f.write("# PIPELINE\nCode pipeline rules.\n")

        # workspace/skills/weather/SKILL.md
        skill_dir = os.path.join(ws, "skills", "weather")
        os.makedirs(skill_dir, exist_ok=True)
        with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
            f.write("# Weather Skill\nGet current weather via wttr.in.\n")

        # workspace/memory/2026-04-12.md
        mem_dir = os.path.join(ws, "memory")
        os.makedirs(mem_dir, exist_ok=True)
        with open(os.path.join(mem_dir, "2026-04-12.md"), "w") as f:
            f.write("# Daily Notes\nDid some work today.\n")

        # workspace/scripts/notify.sh
        scripts_dir = os.path.join(ws, "scripts")
        os.makedirs(scripts_dir, exist_ok=True)
        with open(os.path.join(scripts_dir, "notify.sh"), "w") as f:
            f.write("#!/bin/bash\necho 'hello'\n")

        # workspace-coder/AGENTS.md
        coder_ws = os.path.join(base, "workspace-coder")
        os.makedirs(coder_ws, exist_ok=True)
        with open(os.path.join(coder_ws, "AGENTS.md"), "w") as f:
            f.write("# Coder Agent\nRead PLAN.md before coding.\n")

    def test_full_build_structure(self):
        builder = GraphBuilder(self.tmpdir)
        graph = builder.build()

        # Validate top-level structure
        self.assertIn("elements", graph)
        self.assertIn("nodes", graph["elements"])
        self.assertIn("edges", graph["elements"])
        self.assertIn("meta", graph)
        self.assertGreater(graph["meta"]["node_count"], 0)
        self.assertGreater(graph["meta"]["edge_count"], 0)

    def test_agent_nodes_created(self):
        builder = GraphBuilder(self.tmpdir)
        graph = builder.build()
        node_ids = {n["data"]["id"] for n in graph["elements"]["nodes"]}
        self.assertIn("agent_main", node_ids)
        self.assertIn("agent_coder", node_ids)
        self.assertIn("agent_researcher", node_ids)

    def test_delegation_edges(self):
        builder = GraphBuilder(self.tmpdir)
        graph = builder.build()
        edge_pairs = {(e["data"]["source"], e["data"]["target"], e["data"]["type"]) for e in graph["elements"]["edges"]}
        self.assertIn(("agent_main", "agent_coder", "delegates_to"), edge_pairs)
        self.assertIn(("agent_main", "agent_researcher", "delegates_to"), edge_pairs)

    def test_skill_nodes(self):
        builder = GraphBuilder(self.tmpdir)
        graph = builder.build()
        skill_nodes = [n for n in graph["elements"]["nodes"] if n["data"]["type"] == "skill"]
        self.assertEqual(len(skill_nodes), 1)
        self.assertIn("Weather", skill_nodes[0]["data"]["label"])

    def test_memory_nodes(self):
        builder = GraphBuilder(self.tmpdir)
        graph = builder.build()
        mem_nodes = [n for n in graph["elements"]["nodes"] if n["data"]["type"] == "memory"]
        self.assertGreaterEqual(len(mem_nodes), 1)

    def test_script_nodes(self):
        builder = GraphBuilder(self.tmpdir)
        graph = builder.build()
        script_nodes = [n for n in graph["elements"]["nodes"] if n["data"]["type"] == "script"]
        self.assertEqual(len(script_nodes), 1)
        self.assertIn("notify.sh", script_nodes[0]["data"]["label"])

    def test_wikilink_edges(self):
        builder = GraphBuilder(self.tmpdir)
        graph = builder.build()
        ref_edges = [e for e in graph["elements"]["edges"] if e["data"]["type"] == "references"]
        # AGENTS.md references [[DELEGATION]] and [[PIPELINE]]
        self.assertGreaterEqual(len(ref_edges), 1)

    def test_node_schema(self):
        builder = GraphBuilder(self.tmpdir)
        graph = builder.build()
        for node in graph["elements"]["nodes"]:
            d = node["data"]
            self.assertIn("id", d)
            self.assertIn("label", d)
            self.assertIn("type", d)
            self.assertIn("path", d)
            self.assertIn("metadata", d)
            self.assertIn(d["type"], ("agent", "file", "skill", "config", "memory", "script", "plan"))

    def test_edge_schema(self):
        builder = GraphBuilder(self.tmpdir)
        graph = builder.build()
        for edge in graph["elements"]["edges"]:
            d = edge["data"]
            self.assertIn("id", d)
            self.assertIn("source", d)
            self.assertIn("target", d)
            self.assertIn("type", d)
            self.assertIn("label", d)
            self.assertIn(d["type"], ("reads", "delegates_to", "spawns", "references", "configures", "writes", "triggers"))

    def test_edge_deduplication(self):
        builder = GraphBuilder(self.tmpdir)
        graph = builder.build()
        edge_ids = [e["data"]["id"] for e in graph["elements"]["edges"]]
        self.assertEqual(len(edge_ids), len(set(edge_ids)), "Duplicate edge IDs found!")

    def test_json_serializable(self):
        builder = GraphBuilder(self.tmpdir)
        graph = builder.build()
        # Should not raise
        output = json.dumps(graph, indent=2, ensure_ascii=False)
        # And should parse back
        parsed = json.loads(output)
        self.assertEqual(parsed["meta"]["node_count"], graph["meta"]["node_count"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
