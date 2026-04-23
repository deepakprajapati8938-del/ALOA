"""
Test file for Llama integration
"""
import pytest
from llama_cli_integration import llama_cli
from optimized_llama import optimized_llama

def test_llama_cli_info():
    info = llama_cli.get_info()
    assert "integration_type" in info

def test_optimized_llama_config():
    stats = optimized_llama.get_performance_stats()
    assert "model_config" in stats
