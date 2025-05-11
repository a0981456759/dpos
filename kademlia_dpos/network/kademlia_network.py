import asyncio
import json
import logging
from kademlia.network import Server
from typing import Dict, List, Any, Optional, Tuple

class KademliaNetwork:
    """
    A wrapper around the Kademlia DHT providing P2P networking capabilities
    for the DPoS voting system.
    """
    
    def __init__(self, node_id: Optional[bytes] = None, port: int = 8468):
        """
        Initialize a KademliaNetwork instance.
        
        Args:
            node_id: Optional node ID. If not provided, a random one will be generated.
            port: Port to listen on for connections
        """
        self.server = Server(node_id=node_id)
        self.port = port
        self.bootstrap_nodes = []
        
        # Set up logging
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        log = logging.getLogger('kademlia')
        log.addHandler(handler)
        log.setLevel(logging.INFO)
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)
    
    async def start(self):
        """Start the Kademlia server and listen for connections."""
        await self.server.listen(self.port)
        self.logger.info(f"Node listening on port {self.port}")
        
        # Fix: Properly handle node ID
        node_id = self.server.node.long_id
        node_id_hex = hex(node_id)[2:] if isinstance(node_id, int) else node_id
        
        return node_id_hex  # Return node ID in hexadecimal format
    
    async def bootstrap(self, bootstrap_nodes: List[Tuple[str, int]]):
        """
        Bootstrap the node by connecting to existing nodes in the network.
        
        Args:
            bootstrap_nodes: List of (host, port) tuples of bootstrap nodes
        """
        self.bootstrap_nodes = bootstrap_nodes
        if bootstrap_nodes:
            self.logger.info(f"Bootstrapping with nodes: {bootstrap_nodes}")
            await self.server.bootstrap(bootstrap_nodes)
            self.logger.info("Bootstrap completed")
    
    async def set_value(self, key: str, value: Any):
        """
        Store a key-value pair in the DHT.
        
        Args:
            key: Key to store the value under
            value: Value to store (will be JSON serialized)
        """
        json_value = json.dumps(value)
        self.logger.info(f"Setting {key}: {json_value}")
        await self.server.set(key, json_value)
    
    async def get_value(self, key: str) -> Any:
        """
        Retrieve a value from the DHT.
        
        Args:
            key: Key to retrieve
            
        Returns:
            The value if found and valid JSON, None otherwise
        """
        result = await self.server.get(key)
        if result is not None:
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                self.logger.error(f"Failed to decode result for key {key}: {result}")
                return result
        return None
    
    async def announce_node(self, node_info: Dict[str, Any]):
        """
        Announce this node's information to the network.
        
        Args:
            node_info: Information about this node (address, stake, etc.)
        """
        node_id = node_info.get("id")
        if not node_id:
            self.logger.error("Node info missing ID")
            return
        
        # Store node information
        key = f"node:{node_id}"
        await self.set_value(key, node_info)
        
        # Get and update global node list
        all_nodes = await self.get_value("nodes:all") or []
        if node_id not in all_nodes:
            all_nodes.append(node_id)
            await self.set_value("nodes:all", all_nodes)
            self.logger.info(f"Added node {node_id} to global list. Total nodes: {len(all_nodes)}")
    
    async def get_nodes(self) -> List[Dict[str, Any]]:
        """
        Get information about all nodes in the network.
        
        Returns:
            List of node information dictionaries
        """
        node_ids = await self.get_value("nodes:all")
        if not node_ids:
            return []
            
        nodes = []
        for node_id in node_ids:
            node_info = await self.get_value(f"node:{node_id}")
            if node_info:
                nodes.append(node_info)
                
        return nodes
    
    async def announce_vote(self, vote_id: str, vote_info: Dict[str, Any]):
        """
        Announce a new vote to the network.
        
        Args:
            vote_id: Unique identifier for the vote
            vote_info: Information about the vote
        """
        await self.set_value(f"vote:{vote_id}", vote_info)
        
        # Add to list of active votes
        active_votes = await self.get_value("votes:active") or []
        if vote_id not in active_votes:
            active_votes.append(vote_id)
            await self.set_value("votes:active", active_votes)
    
    async def get_vote(self, vote_id: str) -> Dict[str, Any]:
        """
        Get information about a specific vote.
        
        Args:
            vote_id: ID of the vote to retrieve
            
        Returns:
            Vote information dictionary or None if not found
        """
        return await self.get_value(f"vote:{vote_id}")
    
    async def get_active_votes(self) -> List[str]:
        """
        Get IDs of all active votes.
        
        Returns:
            List of active vote IDs
        """
        return await self.get_value("votes:active") or []
    
    async def cast_vote(self, vote_id: str, voter_id: str, choice: Any):
        """
        Cast a vote in an active voting process.
        
        Args:
            vote_id: ID of the vote
            voter_id: ID of the voter
            choice: The voter's choice
        """
        vote_key = f"vote:{vote_id}:ballot:{voter_id}"
        await self.set_value(vote_key, choice)
        
        # Add to list of voters for this vote
        voters_key = f"vote:{vote_id}:voters"
        voters = await self.get_value(voters_key) or []
        if voter_id not in voters:
            voters.append(voter_id)
            await self.set_value(voters_key, voters)
    
    async def get_vote_results(self, vote_id: str) -> Dict[str, Any]:
        """
        Get the results of a vote.
        
        Args:
            vote_id: ID of the vote
            
        Returns:
            Dictionary mapping voter IDs to their choices
        """
        voters_key = f"vote:{vote_id}:voters"
        voters = await self.get_value(voters_key) or []
        
        results = {}
        for voter_id in voters:
            vote_key = f"vote:{vote_id}:ballot:{voter_id}"
            choice = await self.get_value(vote_key)
            if choice is not None:
                results[voter_id] = choice
                
        return results
    
    async def stop(self):
        """Stop the Kademlia server."""
        self.server.stop()
        self.logger.info("Node stopped") 