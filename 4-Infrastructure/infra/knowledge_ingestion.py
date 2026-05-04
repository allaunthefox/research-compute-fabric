"""
Knowledge Ingestion Module for Swarm
Integrates multiple public domain knowledge sources:
- Wolfram Alpha API (computational knowledge)
- OpenMath Content Dictionaries (mathematical symbols)
- nLab wiki (research-level mathematics/physics)
"""

import requests
import json
import re
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class WolframAlphaKnowledge:
    """Wolfram Alpha API integration for computational knowledge retrieval"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.wolframalpha.com/v2/query"
        self.rate_limit_remaining = 2000  # Free tier: 2000 calls/month
        self.cache = {}  # Simple in-memory cache
        
    def query(self, question: str, format: str = "json") -> Optional[Dict[str, Any]]:
        """
        Query Wolfram Alpha API with caching and rate limiting
        
        Args:
            question: The question to ask
            format: Response format (json, xml, html)
            
        Returns:
            Parsed response or None if failed
        """
        # Check cache first
        cache_key = f"{question}_{format}"
        if cache_key in self.cache:
            logger.info(f"Cache hit for: {question[:50]}...")
            return self.cache[cache_key]
        
        # Rate limit check
        if self.rate_limit_remaining <= 0:
            logger.warning("Wolfram Alpha API rate limit reached")
            return None
        
        try:
            params = {
                "input": question,
                "format": "plaintext",
                "output": "JSON",
                "appid": self.api_key,
                "includepodid": "Result"
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            self.rate_limit_remaining -= 1
            
            if format == "json":
                result = response.json()
            else:
                result = {"raw": response.text}
            
            # Cache the result
            self.cache[cache_key] = result
            logger.info(f"Wolfram Alpha query successful: {question[:50]}...")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Wolfram Alpha API error: {e}")
            return None
    
    def get_domain_knowledge(self, domain: str) -> Dict[str, Any]:
        """
        Get comprehensive knowledge about a specific domain
        
        Args:
            domain: Domain name (mathematics, physics, geometry, topology, etc.)
            
        Returns:
            Structured domain knowledge
        """
        queries = [
            f"What are the main concepts in {domain}",
            f"List important theorems in {domain}",
            f"Key applications of {domain}"
        ]
        
        knowledge = {
            "domain": domain,
            "concepts": [],
            "theorems": [],
            "applications": []
        }
        
        for query in queries:
            result = self.query(query)
            if result and "queryresult" in result:
                pods = result["queryresult"].get("pods", [])
                for pod in pods:
                    if "subpods" in pod:
                        for subpod in pod["subpods"]:
                            if "plaintext" in subpod:
                                text = subpod["plaintext"]
                                if "concepts" in query:
                                    knowledge["concepts"].append(text)
                                elif "theorems" in query:
                                    knowledge["theorems"].append(text)
                                elif "applications" in query:
                                    knowledge["applications"].append(text)
        
        return knowledge


class OpenMathKnowledge:
    """OpenMath Content Dictionary ingestion"""
    
    def __init__(self):
        self.base_url = "https://openmath.org/cd"
        self.cache = {}
        
    def fetch_content_dictionary(self, cd_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch an OpenMath Content Dictionary
        
        Args:
            cd_name: Name of the content dictionary (e.g., "arith1", "alg1")
            
        Returns:
            Parsed content dictionary or None if failed
        """
        cache_key = f"openmath_{cd_name}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            url = f"{self.base_url}/{cd_name}.ocd"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse XML - remove namespace for easier parsing
            root = ET.fromstring(response.text)
            
            cd_data = {
                "name": cd_name,
                "symbols": []
            }
            
            # Try multiple namespace approaches
            namespaces = {
                'om': 'http://www.openmath.org/OpenMathCD',
                'm': 'http://www.w3.org/1998/Math/MathML',
                '': ''
            }
            
            for ns_prefix, ns_uri in namespaces.items():
                for symbol in root.findall(".//Symbol"):
                    if symbol.tag.endswith("Symbol"):
                        symbol_data = {
                            "name": symbol.get("name", ""),
                            "cd": symbol.get("cd", ""),
                            "role": symbol.get("role", ""),
                            "description": ""
                        }
                        
                        # Get description
                        for desc in symbol.findall(".//math"):
                            if desc.text:
                                symbol_data["description"] = desc.text
                        
                        if symbol_data["name"]:
                            cd_data["symbols"].append(symbol_data)
            
            # If no symbols found with namespace, try without
            if not cd_data["symbols"]:
                for elem in root.iter():
                    if elem.tag.endswith("Symbol"):
                        symbol_data = {
                            "name": elem.get("name", ""),
                            "cd": elem.get("cd", ""),
                            "role": elem.get("role", ""),
                            "description": ""
                        }
                        if symbol_data["name"]:
                            cd_data["symbols"].append(symbol_data)
            
            self.cache[cache_key] = cd_data
            logger.info(f"OpenMath CD fetched: {cd_name}")
            return cd_data
            
        except (requests.exceptions.RequestException, ET.ParseError) as e:
            logger.error(f"OpenMath CD fetch error for {cd_name}: {e}")
            return None
    
    def get_relevant_cds(self) -> List[str]:
        """
        Get list of relevant Content Dictionaries for this codebase
        
        Returns:
            List of CD names
        """
        # Relevant CDs for mathlib, physics, geometry, topology
        relevant_cds = [
            "arith1",  # Arithmetic
            "alg1",    # Algebra
            "relation1",  # Relations
            "set1",    # Sets
            "logic1",  # Logic
            "fns1",    # Functions
            "nums1",   # Numbers
            "calculus1",  # Calculus
            "complex1",  # Complex numbers
            "linalg1",  # Linear algebra
            "analysis1",  # Analysis
            "geometry",  # Geometry
            "topology",  # Topology
        ]
        return relevant_cds
    
    def ingest_all_relevant_cds(self) -> Dict[str, Dict[str, Any]]:
        """
        Ingest all relevant Content Dictionaries
        
        Returns:
            Dictionary mapping CD names to their data
        """
        all_cds = {}
        for cd_name in self.get_relevant_cds():
            cd_data = self.fetch_content_dictionary(cd_name)
            if cd_data:
                all_cds[cd_name] = cd_data
        
        logger.info(f"Ingested {len(all_cds)} OpenMath Content Dictionaries")
        return all_cds


class NLabKnowledge:
    """nLab local Git mirror ingestion for research-level mathematics/physics"""
    
    def __init__(self, nlab_path="docs/nlab"):
        self.nlab_path = nlab_path
        self.cache = {}
        
    def read_local_page(self, page_name: str) -> Optional[Dict[str, Any]]:
        """
        Read an nLab page from local Git mirror
        
        Args:
            page_name: Name of the nLab page (e.g., "topological_space", "category_theory")
            
        Returns:
            Parsed page data or None if failed
        """
        cache_key = f"nlab_{page_name}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Try multiple file paths
            possible_paths = [
                os.path.join(self.nlab_path, page_name),
                os.path.join(self.nlab_path, f"{page_name}.md"),
                os.path.join(self.nlab_path, f"{page_name}.html"),
                os.path.join(self.nlab_path, page_name, "index.md"),
                os.path.join(self.nlab_path, page_name, "index.html")
            ]
            
            content = None
            file_path = None
            
            for path in possible_paths:
                if os.path.exists(path):
                    file_path = path
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    break
            
            if not content:
                # Try searching for files that contain the page name
                for root, dirs, files in os.walk(self.nlab_path):
                    for file in files:
                        if page_name.lower() in file.lower():
                            full_path = os.path.join(root, file)
                            try:
                                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                file_path = full_path
                                break
                            except:
                                continue
                    if content:
                        break
            
            if not content:
                logger.warning(f"nLab page not found: {page_name}")
                return None
            
            page_data = {
                "name": page_name,
                "title": page_name,
                "content": content[:5000],  # Limit content for efficiency
                "file_path": file_path,
                "categories": [],
                "links": []
            }
            
            # Extract title from content
            if "# " in content:
                lines = content.split('\n')
                for line in lines:
                    if line.startswith("# "):
                        page_data["title"] = line[2:].strip()
                        break
            
            # Extract links (markdown format)
            import re
            links = re.findall(r'\[([^\]]+)\]\([^\)]+\)', content)
            page_data["links"] = links[:20]  # Limit links
            
            self.cache[cache_key] = page_data
            logger.info(f"nLab page read from local: {page_name} ({file_path})")
            return page_data
            
        except Exception as e:
            logger.error(f"nLab local read error for {page_name}: {e}")
            return None
    
    def get_relevant_pages(self) -> List[str]:
        """
        Get list of relevant nLab pages for this codebase
        
        Returns:
            List of page names
        """
        relevant_pages = [
            "topological_space",
            "manifold",
            "category_theory",
            "homotopy_type_theory",
            "higher_category_theory",
            "simplicial_set",
            "cohomology",
            "homology",
            "fiber_bundle",
            "vector_bundle",
            "symplectic_manifold",
            "Riemannian_manifold",
            "Lie_group",
            "Lie_algebra",
            "sheaf",
            "topos"
        ]
        return relevant_pages
    
    def ingest_all_relevant_pages(self) -> Dict[str, Dict[str, Any]]:
        """
        Ingest all relevant nLab pages from local Git mirror
        
        Returns:
            Dictionary mapping page names to their data
        """
        all_pages = {}
        for page_name in self.get_relevant_pages():
            page_data = self.read_local_page(page_name)
            if page_data:
                all_pages[page_name] = page_data
        
        logger.info(f"Ingested {len(all_pages)} nLab pages from local Git mirror")
        return all_pages


class KnowledgeIngestion:
    """Main knowledge ingestion orchestrator"""
    
    def __init__(self, wolfram_api_key: Optional[str] = None):
        self.wolfram = WolframAlphaKnowledge(wolfram_api_key) if wolfram_api_key else None
        self.openmath = OpenMathKnowledge()
        self.nlab = NLabKnowledge()
        self.knowledge_base = {
            "wolfram": {},
            "openmath": {},
            "nlab": {}
        }
        
    def ingest_all(self) -> Dict[str, Any]:
        """
        Ingest knowledge from all sources
        
        Returns:
            Combined knowledge base
        """
        logger.info("Starting knowledge ingestion from all sources")
        
        # Ingest from Wolfram Alpha if API key provided
        if self.wolfram:
            domains = ["mathematics", "physics", "geometry", "topology", "category_theory"]
            for domain in domains:
                knowledge = self.wolfram.get_domain_knowledge(domain)
                self.knowledge_base["wolfram"][domain] = knowledge
            logger.info("Wolfram Alpha ingestion complete")
        
        # Ingest from OpenMath
        self.knowledge_base["openmath"] = self.openmath.ingest_all_relevant_cds()
        
        # Ingest from nLab
        self.knowledge_base["nlab"] = self.nlab.ingest_all_relevant_pages()
        
        logger.info("Knowledge ingestion complete")
        return self.knowledge_base
    
    def query_knowledge_base(self, question: str) -> Dict[str, Any]:
        """
        Query the knowledge base with a question
        
        Args:
            question: The question to answer
            
        Returns:
            Relevant knowledge from all sources
        """
        results = {
            "question": question,
            "sources": []
        }
        
        # Try Wolfram Alpha first if available
        if self.wolfram:
            wolfram_result = self.wolfram.query(question)
            if wolfram_result:
                results["sources"].append({
                    "name": "Wolfram Alpha",
                    "data": wolfram_result
                })
        
        # Search OpenMath for relevant symbols
        question_lower = question.lower()
        for cd_name, cd_data in self.knowledge_base["openmath"].items():
            for symbol in cd_data.get("symbols", []):
                if any(keyword in symbol.get("name", "").lower() for keyword in question_lower.split()):
                    results["sources"].append({
                        "name": f"OpenMath: {cd_name}",
                        "data": symbol
                    })
        
        # Search nLab for relevant pages
        for page_name, page_data in self.knowledge_base["nlab"].items():
            if any(keyword in page_data.get("title", "").lower() for keyword in question_lower.split()):
                results["sources"].append({
                    "name": f"nLab: {page_name}",
                    "data": page_data
                })
        
        return results
    
    def export_knowledge_base(self, output_path: str):
        """
        Export knowledge base to JSON file
        
        Args:
            output_path: Path to output JSON file
        """
        with open(output_path, 'w') as f:
            json.dump(self.knowledge_base, f, indent=2)
        logger.info(f"Knowledge base exported to {output_path}")
    
    def load_knowledge_base(self, input_path: str):
        """
        Load knowledge base from JSON file
        
        Args:
            input_path: Path to input JSON file
        """
        with open(input_path, 'r') as f:
            self.knowledge_base = json.load(f)
        logger.info(f"Knowledge base loaded from {input_path}")
