# kademlia_dpos/sync/controller.py
import time
import asyncio
import logging
from typing import Dict, List, Any, Optional

class DataSyncController:
    """負責管理節點數據同步的控制器"""
    
    def __init__(self, network, node_id, consensus=None):
        """
        初始化同步控制器
        
        Args:
            network: 分佈式網絡接口
            node_id: 當前節點ID
            consensus: 共識機制實例
        """
        self.network = network
        self.node_id = node_id
        self.consensus = consensus
        self.last_sync_time = None
        self.sync_in_progress = False
        self.logger = logging.getLogger(__name__)
    
    def set_consensus(self, consensus):
        """設置共識機制實例 (可以後期設置)"""
        self.consensus = consensus
    
    async def perform_sync(self):
        """執行完整的數據同步流程"""
        if self.sync_in_progress:
            self.logger.info("同步已在進行中，跳過")
            return False
            
        self.sync_in_progress = True
        self.logger.info("開始執行數據同步")
        
        try:
            # 1. 獲取最新的全局時間戳或版本號
            network_state = await self.network.get_value("system:state")
            
            # 2. 按優先級順序同步數據
            delegates = await self.sync_delegates()
            active_votes = await self.sync_active_votes()
            nodes = await self.sync_nodes()
            
            # 3. 更新本地同步時間戳
            self.last_sync_time = time.time()
            
            self.logger.info(f"同步完成: {len(delegates)} 代表, {len(active_votes)} 活躍投票, {len(nodes)} 節點")
            return True
        except Exception as e:
            self.logger.error(f"同步過程中發生錯誤: {e}")
            return False
        finally:
            self.sync_in_progress = False
    
    async def sync_delegates(self):
        """同步代表列表"""
        self.logger.info("同步代表列表")
        delegates = await self.network.get_value("consensus:delegates") or []
        
        if self.consensus and delegates:
            # 更新本地共識機制中的代表列表
            self.consensus.delegates = delegates
            # 檢查當前節點是否為代表
            was_delegate = self.consensus.is_delegate
            self.consensus.is_delegate = self.node_id in delegates
            
            if was_delegate != self.consensus.is_delegate:
                self.logger.info(f"代表狀態已更新: {self.consensus.is_delegate}")
                
                # 更新節點信息中的代表狀態
                node_info = await self.network.get_value(f"node:{self.node_id}")
                if node_info:
                    node_info["is_delegate"] = self.consensus.is_delegate
                    await self.network.set_value(f"node:{self.node_id}", node_info)
        
        return delegates
    
    async def sync_active_votes(self):
        """同步活躍投票"""
        self.logger.info("同步活躍投票")
        active_votes = await self.network.get_value("votes:active") or []
        result = []
        
        for vote_id in active_votes:
            vote_info = await self.network.get_value(f"vote:{vote_id}")
            if vote_info:
                # 同步投票結果
                await self.sync_vote_results(vote_id)
                result.append(vote_info)
        
        return result
    
    async def sync_vote_results(self, vote_id):
        """同步特定投票的結果"""
        # 獲取投票者列表
        voters = await self.network.get_value(f"vote:{vote_id}:voters") or []
        
        # 獲取每個投票
        results = {}
        for voter_id in voters:
            ballot = await self.network.get_value(f"vote:{vote_id}:ballot:{voter_id}")
            if ballot:
                results[voter_id] = ballot
        
        return results
    
    async def sync_nodes(self):
        """同步節點列表"""
        self.logger.info("同步節點列表")
        node_ids = await self.network.get_value("nodes:all") or []
        nodes = []
        
        for node_id in node_ids:
            node_info = await self.network.get_value(f"node:{node_id}")
            if node_info:
                nodes.append(node_info)
        
        return nodes
    
    async def check_connectivity_and_sync(self):
        """檢查網絡連接並在恢復連接時同步"""
        # 檢查是否能訪問網絡
        try:
            value = await self.network.get_value("system:state")
            if value is not None:
                # 如果之前沒有同步過或同步時間較久，執行同步
                if not self.last_sync_time or time.time() - self.last_sync_time > 300:  # 5分鐘
                    await self.perform_sync()
        except Exception as e:
            self.logger.warning(f"連接檢查失敗: {e}")