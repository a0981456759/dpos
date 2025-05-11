import time
import asyncio
import logging
from typing import Dict, List, Any, Optional

class DataSyncController:
    
    def __init__(self, network, node_id, consensus=None):
        self.network = network
        self.node_id = node_id
        self.consensus = consensus
        self.last_sync_time = None
        self.sync_in_progress = False
        self.logger = logging.getLogger(__name__)
    
    def set_consensus(self, consensus):
        self.consensus = consensus
    
    async def perform_sync(self):
        if self.sync_in_progress:
            self.logger.info("Synchronization already in progress, skipping")
            return False
            
        self.sync_in_progress = True
        self.logger.info("Starting data synchronization")
        
        try:
            # 1. Get the latest global timestamp or version number
            network_state = await self.network.get_value("system:state")
            
            # 2. Synchronize data in priority order
            delegates = await self.sync_delegates()
            active_votes = await self.sync_active_votes()
            nodes = await self.sync_nodes()
            
            # 3. Update local synchronization timestamp
            self.last_sync_time = time.time()
            
            self.logger.info(f"Synchronization completed: {len(delegates)} delegates, {len(active_votes)} active votes, {len(nodes)} nodes")
            return True
        except Exception as e:
            self.logger.error(f"Error during synchronization process: {e}")
            return False
        finally:
            self.sync_in_progress = False
    
    async def sync_delegates(self):
        self.logger.info("Synchronizing delegate list")
        delegates = await self.network.get_value("consensus:delegates") or []
        
        if self.consensus and delegates:
            # Update the delegate list in the local consensus mechanism
            self.consensus.delegates = delegates
            # Check if the current node is a delegate
            was_delegate = self.consensus.is_delegate
            self.consensus.is_delegate = self.node_id in delegates
            
            if was_delegate != self.consensus.is_delegate:
                self.logger.info(f"Delegate status updated: {self.consensus.is_delegate}")
                
                # Update delegate status in node information
                node_info = await self.network.get_value(f"node:{self.node_id}")
                if node_info:
                    node_info["is_delegate"] = self.consensus.is_delegate
                    await self.network.set_value(f"node:{self.node_id}", node_info)
        
        return delegates
    
    async def sync_active_votes(self):
        self.logger.info("Synchronizing active votes")
        active_votes = await self.network.get_value("votes:active") or []
        result = []
        
        for vote_id in active_votes:
            vote_info = await self.network.get_value(f"vote:{vote_id}")
            if vote_info:
                # Synchronize vote results
                await self.sync_vote_results(vote_id)
                result.append(vote_info)
        
        return result
    
    async def sync_vote_results(self, vote_id):
        # Get voter list
        voters = await self.network.get_value(f"vote:{vote_id}:voters") or []
        
        # Get each ballot
        results = {}
        for voter_id in voters:
            ballot = await self.network.get_value(f"vote:{vote_id}:ballot:{voter_id}")
            if ballot:
                results[voter_id] = ballot
        
        return results
    
    async def sync_nodes(self):
        self.logger.info("Synchronizing node list")
        node_ids = await self.network.get_value("nodes:all") or []
        nodes = []
        
        for node_id in node_ids:
            node_info = await self.network.get_value(f"node:{node_id}")
            if node_info:
                nodes.append(node_info)
        
        return nodes
    
    async def check_connectivity_and_sync(self):
        # Check if network can be accessed
        try:
            value = await self.network.get_value("system:state")
            if value is not None:
                # Perform synchronization if never synced before or if last sync was too long ago
                if not self.last_sync_time or time.time() - self.last_sync_time > 300:  # 5 minutes
                    await self.perform_sync()
        except Exception as e:
            self.logger.warning(f"Connection check failed: {e}")