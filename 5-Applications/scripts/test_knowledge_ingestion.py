#!/usr/bin/env python3
"""
Test script for knowledge ingestion with Wolfram Alpha API
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from infra.knowledge_ingestion import KnowledgeIngestion

def test_wolfram_alpha():
    """Test Wolfram Alpha API integration"""
    api_key = "HYJE3R3R63"
    
    print("Testing Wolfram Alpha API integration...")
    ingestion = KnowledgeIngestion(api_key)
    
    # Test a simple query
    print("\n1. Testing simple query: 'What is 2+2?'")
    result = ingestion.wolfram.query("What is 2+2?")
    if result:
        print(f"Result: {result}")
    else:
        print("Query failed")
    
    # Test domain knowledge retrieval
    print("\n2. Testing domain knowledge: 'mathematics'")
    domain_knowledge = ingestion.wolfram.get_domain_knowledge("mathematics")
    print(f"Domain knowledge: {domain_knowledge}")
    
    # Test OpenMath ingestion
    print("\n3. Testing OpenMath Content Dictionary ingestion...")
    openmath_result = ingestion.openmath.fetch_content_dictionary("arith1")
    print(f"OpenMath result: {openmath_result}")
    
    # Test nLab scraping
    print("\n4. Testing nLab wiki scraping...")
    nlab_result = ingestion.nlab.scrape_page("topological_space")
    print(f"nLab result: {nlab_result}")
    
    print("\nAll tests complete!")

if __name__ == "__main__":
    test_wolfram_alpha()
