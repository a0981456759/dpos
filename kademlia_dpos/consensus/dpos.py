import asyncio
import hashlib
import json
import random
import time
import uuid
from typing import Dict, List, Any, Optional, Tuple

class DPoSConsensus:
    """
    Implementation of the Delegated Proof of Stake consensus algorithm.
    """
    
    def __init__(self, network, node_id: str, stake: int = 0):
        """
        Initialize a DPoS consensus instance.
        
        Args:
            network: The network interface for communication
            node_id: Unique identifier for this node
            stake: The stake of this node (used for voting power)
        """
        self.network = network
        self.node_id = node_id
        self.stake = stake
        self.is_delegate = False
        self.delegates = []
        self.current_round = 0
        self.votes = {}  # {voter_id: delegate_id}
        
    async def register_node(self, address: str, port: int):
        """
        Register this node with the network.
        
        Args:
            address: IP address of this node
            port: Port this node is listening on
        """
        node_info = {
            "id": self.node_id,
            "address": address,
            "port": port,
            "stake": self.stake,
            "is_delegate": self.is_delegate,
            "registered_at": time.time()
        }
        
        # Directly store node information
        await self.network.set_value(f"node:{self.node_id}", node_info)
        
        # Get and update global node list
        all_nodes = await self.network.get_value("nodes:all") or []
        if self.node_id not in all_nodes:
            all_nodes.append(self.node_id)
            await self.network.set_value("nodes:all", all_nodes)
            print(f"Node added to global list: {self.node_id}")
        
        # The original method may not have been implemented correctly
        # await self.network.announce_node(node_info)
        
        print(f"Node registration complete: {self.node_id}, global node count: {len(all_nodes)}")
    
    async def update_stake(self, new_stake: int):
        """
        Update the stake of this node.
        
        Args:
            new_stake: New stake value
        """
        self.stake = new_stake
        # Re-register with updated stake
        node_info = await self.network.get_value(f"node:{self.node_id}")
        if node_info:
            node_info["stake"] = new_stake
            await self.network.set_value(f"node:{self.node_id}", node_info)
    
    async def get_all_nodes(self) -> List[Dict[str, Any]]:
        """
        Get information about all nodes in the network.
        
        Returns:
            List of node information dictionaries
        """
        return await self.network.get_nodes()
        
    async def start_delegate_election(self, num_delegates: int = 21, election_duration: int = 3600) -> str:
        """
        Start an election for delegates.
        
        Args:
            num_delegates: Number of delegates to elect
            election_duration: Duration of the election in seconds
            
        Returns:
            ID of the election
        """
        election_id = str(uuid.uuid4())
        
        election_info = {
            "id": election_id,
            "type": "delegate_election",
            "created_by": self.node_id,
            "created_at": time.time(),
            "ends_at": time.time() + election_duration,
            "num_delegates": num_delegates,
            "status": "active"
        }
        
        await self.network.announce_vote(election_id, election_info)
        return election_id
    
    async def vote_for_delegate(self, election_id: str, delegate_id: str):
        """
        Vote for a delegate in an election.
        
        Args:
            election_id: ID of the election
            delegate_id: ID of the delegate to vote for
        """
        await self.network.cast_vote(election_id, self.node_id, {
            "delegate": delegate_id,
            "weight": self.stake,
            "timestamp": time.time()
        })
        
        self.votes[election_id] = delegate_id
    
    async def count_votes(self, election_id: str) -> Dict[str, int]:
        """
        Count votes in a delegate election.
        
        Args:
            election_id: ID of the election
            
        Returns:
            Dictionary mapping delegate IDs to vote counts weighted by stake
        """
        results = await self.network.get_vote_results(election_id)
        
        # Count weighted votes
        weighted_votes = {}
        for voter_id, vote in results.items():
            delegate_id = vote.get("delegate")
            weight = vote.get("weight", 1)
            
            if delegate_id not in weighted_votes:
                weighted_votes[delegate_id] = 0
                
            weighted_votes[delegate_id] += weight
            
        return weighted_votes
    
    async def finalize_election(self, election_id: str) -> List[str]:
        """
        Finalize an election and select delegates.
        
        Args:
            election_id: ID of the election
            
        Returns:
            List of selected delegate IDs
        """
        vote_counts = await self.count_votes(election_id)
        
        # Sort delegates by vote count in descending order
        sorted_delegates = sorted(
            vote_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # Get election info
        election_info = await self.network.get_value(f"vote:{election_id}")
        num_delegates = election_info.get("num_delegates", 21)
        
        # Select top delegates
        selected_delegates = [d[0] for d in sorted_delegates[:num_delegates]]
        
        # Update election info
        election_info["status"] = "completed"
        election_info["completed_at"] = time.time()
        election_info["selected_delegates"] = selected_delegates
        await self.network.set_value(f"vote:{election_id}", election_info)
        
        # Store current delegates
        await self.network.set_value("consensus:delegates", selected_delegates)
        
        # Update local list
        self.delegates = selected_delegates
        self.is_delegate = self.node_id in selected_delegates
        
        # Update node info to reflect delegate status
        node_info = await self.network.get_value(f"node:{self.node_id}")
        if node_info:
            node_info["is_delegate"] = self.is_delegate
            await self.network.set_value(f"node:{self.node_id}", node_info)
        
        # Added: Send status update notifications to each delegate
        for delegate_id in selected_delegates:
            delegate_info = await self.network.get_value(f"node:{delegate_id}")
            if delegate_info:
                delegate_info["is_delegate"] = True
                await self.network.set_value(f"node:{delegate_id}", delegate_info)
        
        return selected_delegates
    
    async def sync_delegates(self):
        """
        Synchronize the list of delegates from the network.
        
        Returns:
            True if the node is a delegate, False otherwise
        """
        delegates = await self.network.get_value("consensus:delegates")
        if delegates:
            self.delegates = delegates
            was_delegate = self.is_delegate
            self.is_delegate = self.node_id in delegates
            
            # 如果代表狀態已變更，更新節點信息
            if was_delegate != self.is_delegate:
                node_info = await self.network.get_value(f"node:{self.node_id}")
                if node_info:
                    node_info["is_delegate"] = self.is_delegate
                    await self.network.set_value(f"node:{self.node_id}", node_info)
                    print(f"節點代表狀態已更新: {self.is_delegate}")
            
            # 從API模塊導入配置
            from kademlia_dpos.utils import config
            
            # 保存更新後的狀態到本地
            config.save_node_state(
                node_id=self.node_id,
                is_delegate=self.is_delegate,
                stake=self.stake,
                port=self.network.port
            )
        
        return self.is_delegate
    
    async def start_proposal_vote(self, title: str, description: str, options: List[str], 
                                 vote_duration: int = 3600) -> str:
        """
        Start a vote on a proposal.
        
        Args:
            title: Title of the proposal
            description: Description of the proposal
            options: List of voting options
            vote_duration: Duration of the vote in seconds
            
        Returns:
            ID of the vote
        """
        vote_id = str(uuid.uuid4())
        
        vote_info = {
            "id": vote_id,
            "type": "proposal",
            "title": title,
            "description": description,
            "options": options,
            "created_by": self.node_id,
            "created_at": time.time(),
            "ends_at": time.time() + vote_duration,
            "status": "active"
        }
        
        await self.network.announce_vote(vote_id, vote_info)
        return vote_id
    
    async def vote_on_proposal(self, vote_id: str, option: str):
        """
        Vote on a proposal.
        
        Args:
            vote_id: ID of the vote
            option: Selected option
        """
        vote_info = await self.network.get_vote(vote_id)
        if not vote_info or vote_info.get("status") != "active":
            raise ValueError("Vote not active or not found")
            
        if option not in vote_info.get("options", []):
            raise ValueError(f"Invalid option: {option}")
        
        await self.network.cast_vote(vote_id, self.node_id, {
            "option": option,
            "weight": self.stake,
            "timestamp": time.time()
        })
    
    async def get_proposal_results(self, vote_id: str) -> Dict[str, int]:
        """
        Get results of a proposal vote.
        
        Args:
            vote_id: ID of the vote
            
        Returns:
            Dictionary mapping options to vote counts weighted by stake
        """
        results = await self.network.get_vote_results(vote_id)
        
        # Count weighted votes for each option
        option_counts = {}
        for voter_id, vote in results.items():
            option = vote.get("option")
            weight = vote.get("weight", 1)
            
            if option not in option_counts:
                option_counts[option] = 0
                
            option_counts[option] += weight
            
        return option_counts
    
    async def finalize_proposal_vote(self, vote_id: str) -> Dict[str, Any]:
        """
        Finalize a proposal vote.
        
        Args:
            vote_id: ID of the vote
            
        Returns:
            Dictionary with vote results
        """
        vote_info = await self.network.get_vote(vote_id)
        if not vote_info:
            raise ValueError("Vote not found")
            
        results = await self.get_proposal_results(vote_id)
        
        # Find winning option (highest vote count)
        winning_option = max(results.items(), key=lambda x: x[1]) if results else (None, 0)
        
        # Update vote info
        vote_info["status"] = "completed"
        vote_info["completed_at"] = time.time()
        vote_info["results"] = results
        vote_info["winning_option"] = winning_option[0]
        vote_info["total_votes"] = sum(results.values())
        
        await self.network.set_value(f"vote:{vote_id}", vote_info)
        
        return vote_info
    
    async def get_active_votes(self) -> List[Dict[str, Any]]:
        """
        Get information about all active votes.
        
        Returns:
            List of active vote information dictionaries
        """
        active_vote_ids = await self.network.get_active_votes()
        
        active_votes = []
        for vote_id in active_vote_ids:
            vote_info = await self.network.get_vote(vote_id)
            if vote_info and vote_info.get("status") == "active":
                # Check if vote has expired
                if vote_info.get("ends_at", 0) < time.time():
                    # Automatically finalize expired votes
                    if vote_info.get("type") == "delegate_election":
                        await self.finalize_election(vote_id)
                    else:
                        await self.finalize_proposal_vote(vote_id)
                else:
                    active_votes.append(vote_info)
                    
        return active_votes