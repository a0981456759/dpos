import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional

CONFIG_DIR = Path.home() / ".kademlia_dpos"
CONFIG_FILE = CONFIG_DIR / "config.json"
KEYS_FILE = CONFIG_DIR / "keys.json"

def ensure_config_dir():
    """Ensure the configuration directory exists."""
    os.makedirs(CONFIG_DIR, exist_ok=True)

def load_config() -> Dict[str, Any]:
    """
    Load configuration from the config file.
    
    Returns:
        Configuration dictionary
    """
    ensure_config_dir()
    
    if not CONFIG_FILE.exists():
        return {
            "port": 8468,
            "bootstrap_nodes": [],
            "stake": 0,
        }
    
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config: Dict[str, Any]):
    """
    Save configuration to the config file.
    
    Args:
        config: Configuration dictionary
    """
    ensure_config_dir()
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def get_config_dir(port=None):
    """Get configuration directory, creates a separate one for each port if specified"""
    base_dir = os.path.expanduser("~/.kademlia_dpos")
    if port:
        return os.path.join(base_dir, f"node_{port}")
    return base_dir

def load_keys(port=None):
    """
    Load node keys. If port is specified, load keys for that specific node.
    
    Args:
        port: Optional node port
        
    Returns:
        Dictionary containing keys, or None if not found
    """
    config_dir = get_config_dir(port)
    keys_file = os.path.join(config_dir, "keys.json")
    
    # Ensure directory exists
    os.makedirs(config_dir, exist_ok=True)
    
    # If keys file doesn't exist, return None
    if not os.path.exists(keys_file):
        return None
    
    # Load and return keys
    with open(keys_file, 'r') as f:
        return json.load(f)

def save_keys(keys, port=None):
    """
    Save node keys. If port is specified, save to that node's directory.
    
    Args:
        keys: Dictionary containing keys
        port: Optional node port
    """
    config_dir = get_config_dir(port)
    keys_file = os.path.join(config_dir, "keys.json")
    
    # Ensure directory exists
    os.makedirs(config_dir, exist_ok=True)
    
    # Save keys
    with open(keys_file, 'w') as f:
        json.dump(keys, f, indent=2)

def save_node_state(node_id, is_delegate, stake, port=None):
    """
    Save node state to configuration file.
    
    Args:
        node_id: Node ID
        is_delegate: Whether the node is a delegate
        stake: Node stake
        port: Optional node port
    """
    config_dir = get_config_dir(port)
    state_file = os.path.join(config_dir, "node_state.json")
    
    state = {
        "id": node_id,
        "is_delegate": is_delegate,
        "stake": stake,
        "last_update": time.time()
    }
    
    # Ensure directory exists
    os.makedirs(config_dir, exist_ok=True)
    
    # Save state
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)

def load_node_state(port=None):
    """
    Load node state.
    
    Args:
        port: Optional node port
        
    Returns:
        Dictionary containing node state, or None if not found
    """
    config_dir = get_config_dir(port)
    state_file = os.path.join(config_dir, "node_state.json")
    
    # If state file doesn't exist, return None
    if not os.path.exists(state_file):
        return None
    
    # Load and return state
    with open(state_file, 'r') as f:
        return json.load(f)

def get_bootstrap_nodes(config: Optional[Dict[str, Any]] = None) -> list:
    """
    Get the bootstrap nodes from the configuration.
    
    Args:
        config: Optional configuration dictionary (loads from file if not provided)
        
    Returns:
        List of (host, port) tuples for bootstrap nodes
    """
    if config is None:
        config = load_config()
    
    nodes = []
    for node in config.get("bootstrap_nodes", []):
        if isinstance(node, list) and len(node) == 2:
            nodes.append(tuple(node))
        elif isinstance(node, dict) and "host" in node and "port" in node:
            nodes.append((node["host"], node["port"]))
    
    return nodes