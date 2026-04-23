import os
import json
import networkx as nx
from networkx.readwrite import json_graph
from datetime import datetime

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "..", "aloa_memory.json")

class ALOAMemory:
    """
    Knowledge Graph memory for ALOA.
    Stores facts as (subject, relation, object) triples.
    Example: ("User", "prefers", "Spotify")
    """
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.load()

    def add_fact(self, subject: str, relation: str, target: str, attributes: dict = None):
        """Adds a directed edge between subject and target with a relation type."""
        attr = attributes or {}
        attr["relation"] = relation
        attr["timestamp"] = datetime.now().isoformat()
        self.graph.add_edge(subject, target, **attr)
        self.save()

    def query_related(self, node: str) -> list:
        """Finds all facts related to a specific node."""
        if not self.graph.has_node(node):
            return []
        
        facts = []
        # Outgoing edges
        for _, target, data in self.graph.out_edges(node, data=True):
            facts.append(f"{node} {data['relation']} {target}")
        # Incoming edges
        for source, _, data in self.graph.in_edges(node, data=True):
            facts.append(f"{source} {data['relation']} {node}")
        
        return facts

    def get_semantic_context(self, user_input: str) -> str:
        """
        Heuristic: finds nodes mentioned in user_input and returns their relationships.
        Used to inject 'Long-term Memory' into LLM prompts.
        """
        words = user_input.lower().split()
        relevant_facts = []
        
        for node in self.graph.nodes():
            if str(node).lower() in words:
                relevant_facts.extend(self.query_related(node))
        
        if not relevant_facts:
            return ""
            
        return "\n[Long-term Memory Context]:\n" + "\n".join(list(set(relevant_facts))[:10])

    def save(self):
        """Serializes the graph to a JSON file."""
        try:
            data = json_graph.node_link_data(self.graph)
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Memory Save Error: {e}")

    def load(self):
        """Loads the graph from a JSON file."""
        if not os.path.exists(MEMORY_FILE):
            return
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.graph = json_graph.node_link_graph(data)
        except Exception as e:
            print(f"Memory Load Error: {e}")
            self.graph = nx.MultiDiGraph()

# Global Singleton
aloa_memory = ALOAMemory()
