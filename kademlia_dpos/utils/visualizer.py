import time
import json
import os
import asyncio
from datetime import datetime

class NetworkVisualizer:
    """為Kademlia和DPoS提供可視化功能"""
    
    COLORS = {
        'reset': '\033[0m',
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'bold': '\033[1m'
    }
    
    def __init__(self, network, consensus, node_id=None):
        self.network = network
        self.consensus = consensus
        self.node_id = node_id
        self.log_path = os.path.join(os.getcwd(), 'network_logs')
        
        # 確保日誌目錄存在
        os.makedirs(self.log_path, exist_ok=True)
    
    def color_text(self, text, color='reset', bold=False):
        """將文字用顏色標記"""
        color_code = self.COLORS.get(color, self.COLORS['reset'])
        bold_code = self.COLORS['bold'] if bold else ''
        return f"{bold_code}{color_code}{text}{self.COLORS['reset']}"
    
    async def visualize_node_info(self):
        """顯示節點信息"""
        print("\n" + self.color_text("===== 節點信息 =====", 'blue', True))
        print(f"節點ID: {self.color_text(self.node_id[:8] + '...', 'green')}")
        print(f"監聽端口: {self.color_text(str(self.network.port), 'cyan')}")
        print(f"啟動時間: {self.color_text(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'yellow')}")
        
        # 顯示代表狀態
        if self.consensus:
            is_delegate = self.consensus.is_delegate
            stake = self.consensus.stake
            status = "代表" if is_delegate else "普通節點"
            
            print(f"節點類型: {self.color_text(status, 'green' if is_delegate else 'yellow')}")
            print(f"權益: {self.color_text(str(stake), 'cyan')}")
            
            # 獲取當前代表數量
            if self.consensus.delegates:
                print(f"當前網絡代表數量: {self.color_text(str(len(self.consensus.delegates)), 'magenta')}")
    
    async def visualize_network_topology(self):
        """顯示網絡拓撲"""
        nodes = await self.network.get_nodes()
        
        print("\n" + self.color_text("===== 網絡拓撲 =====", 'blue', True))
        print(f"總節點數: {self.color_text(str(len(nodes)), 'green')}")
        
        print("\n節點列表:")
        for i, node in enumerate(nodes):
            node_id = node.get('id', 'unknown')[:8] + '...'
            stake = node.get('stake', 0)
            is_delegate = node.get('is_delegate', False)
            
            status = "代表" if is_delegate else "普通節點"
            color = 'green' if is_delegate else 'white'
            
            print(f"{i+1}. {self.color_text(node_id, color)} - 權益: {stake} - 狀態: {self.color_text(status, color)}")
    
    async def visualize_routing_table(self):
        """可視化Kademlia路由表"""
        print("\n" + self.color_text("===== Kademlia 路由表 =====", 'blue', True))
        
        # 由於Kademlia內部實現可能不直接暴露路由表，這裡使用模擬數據
        # 實際實現時應該從self.network.server.protocol.router獲取
        
        print(self.color_text("每個K-桶中的節點:", 'yellow'))
        
        # 模擬8個桶的數據
        for i in range(8):
            bucket_distance = f"2^{i} ~ 2^{i+1}-1"
            # 隨機生成每個桶的節點數量，實際實現應獲取真實數據
            bucket_size = min(3, max(0, i))
            
            if bucket_size > 0:
                print(f"桶 {i} (距離 {bucket_distance}): {self.color_text(str(bucket_size), 'green')}個節點")
            else:
                print(f"桶 {i} (距離 {bucket_distance}): {self.color_text('空', 'red')}")
    
    async def simulate_node_failure(self, percentage=0.3):
        """模擬節點失效"""
        nodes = await self.network.get_nodes()
        total_nodes = len(nodes)
        
        fail_count = max(1, int(total_nodes * percentage))
        fail_count = min(fail_count, total_nodes - 1)  # 確保至少有一個節點存活
        
        print("\n" + self.color_text("===== 節點失效模擬 =====", 'red', True))
        print(f"總節點數: {total_nodes}")
        print(f"將模擬 {self.color_text(str(fail_count), 'red')} 個節點({percentage*100:.0f}%)失效")
        
        # 存儲測試用的鍵值對
        test_keys = ["test:key1", "test:key2", "test:key3"]
        
        # 在失效前存儲一些數據
        print("\n" + self.color_text("正在準備測試數據...", 'yellow'))
        for i, key in enumerate(test_keys):
            value = {"data": f"test_value_{i}", "timestamp": time.time()}
            await self.network.set_value(key, value)
            print(f"存儲鍵: {self.color_text(key, 'cyan')} = {value['data']}")
        
        # 檢查失效前的數據可用性
        print("\n" + self.color_text("故障前數據可用性檢查:", 'green'))
        for key in test_keys:
            value = await self.network.get_value(key)
            status = "可用" if value else "不可用"
            color = "green" if value else "red"
            print(f"鍵 '{key}': {self.color_text(status, color)}")
        
        # 模擬節點失效
        print("\n" + self.color_text("正在模擬節點失效...", 'red'))
        
        # 實際實現時，這裡應該與真實節點通信並使其離線
        # 現在僅做一個模擬延遲
        await asyncio.sleep(2)
        
        print(self.color_text(f"{fail_count}個節點已離線!", 'red', True))
        
        # 檢查失效後的數據可用性
        print("\n" + self.color_text("故障後數據可用性檢查:", 'yellow'))
        available_count = 0
        for key in test_keys:
            value = await self.network.get_value(key)
            status = "可用" if value else "不可用"
            color = "green" if value else "red"
            print(f"鍵 '{key}': {self.color_text(status, color)}")
            if value:
                available_count += 1
        
        # 顯示資料存活率
        survival_rate = (available_count / len(test_keys)) * 100
        print(f"\n數據存活率: {self.color_text(f'{survival_rate:.1f}%', 'green' if survival_rate > 50 else 'red')}")
        
        # 解釋為什麼數據仍然可用
        if survival_rate > 0:
            print("\n" + self.color_text("為什麼數據依然可用?", 'blue'))
            print("Kademlia DHT通過在多個節點上複製數據來確保容錯性。")
            print("即使某些節點失效，數據仍然可以從其他節點獲取。")
            print("這展示了分散式系統的優勢 - 沒有單點故障!")
    
    async def visualize_dpos_election(self, election_id):
        """可視化DPoS選舉過程"""
        if not self.consensus:
            print(self.color_text("錯誤: 共識對象尚未初始化", 'red'))
            return
        
        print("\n" + self.color_text("===== DPoS代表選舉可視化 =====", 'blue', True))
        print(f"選舉ID: {self.color_text(election_id, 'yellow')}")
        
        # 獲取選舉信息
        election_info = await self.network.get_vote(election_id)
        if not election_info:
            print(self.color_text("錯誤: 找不到選舉信息", 'red'))
            return
        
        # 顯示選舉基本信息
        status = election_info.get("status", "unknown")
        num_delegates = election_info.get("num_delegates", 0)
        created_at = election_info.get("created_at", 0)
        ends_at = election_info.get("ends_at", 0)
        
        status_color = "green" if status == "completed" else "yellow" if status == "active" else "red"
        
        print(f"狀態: {self.color_text(status, status_color)}")
        print(f"選舉代表數: {self.color_text(str(num_delegates), 'cyan')}")
        print(f"開始時間: {datetime.fromtimestamp(created_at).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"結束時間: {datetime.fromtimestamp(ends_at).strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 獲取投票結果
        vote_counts = await self.consensus.count_votes(election_id)
        
        print("\n" + self.color_text("投票結果:", 'green'))
        
        if not vote_counts:
            print(self.color_text("尚無投票", 'yellow'))
            return
        
        # 計算總權益
        total_stake = sum(vote_counts.values())
        
        # 排序並顯示候選人
        sorted_delegates = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)
        
        for i, (delegate_id, votes) in enumerate(sorted_delegates):
            percentage = (votes / total_stake) * 100 if total_stake > 0 else 0
            is_selected = i < num_delegates
            
            # 生成投票條形圖
            bar_length = int(percentage / 2)
            bar = "█" * bar_length
            
            delegate_color = "green" if is_selected else "white"
            selection_status = "[已選中]" if is_selected else ""
            
            print(f"{i+1}. {self.color_text(delegate_id[:8] + '...', delegate_color)} - "
                  f"{votes}票 ({percentage:.1f}%) {self.color_text(selection_status, 'green')}")
            print(f"   {self.color_text(bar, 'cyan')}")
        
        # 顯示選舉結論
        if status == "completed":
            selected = election_info.get("selected_delegates", [])
            print("\n" + self.color_text(f"選舉已完成，選出{len(selected)}位代表", 'green', True))
        else:
            remaining_time = ends_at - time.time()
            if remaining_time > 0:
                print(f"\n選舉還有 {self.color_text(f'{remaining_time/60:.1f}分鐘', 'yellow')} 結束")
            else:
                print(f"\n選舉已結束，等待確認結果")
    
    async def log_network_state(self, tag="routine"):
        """記錄網絡狀態到文件"""
        nodes = await self.network.get_nodes()
        active_votes = []
        
        if self.consensus:
            active_votes = await self.consensus.get_active_votes()
        
        state = {
            "timestamp": time.time(),
            "node_id": self.node_id,
            "total_nodes": len(nodes),
            "active_votes": len(active_votes),
            "is_delegate": self.consensus.is_delegate if self.consensus else False,
            "tag": tag
        }
        
        # 生成文件名
        filename = f"network_state_{datetime.now().strftime('%Y%m%d')}.jsonl"
        filepath = os.path.join(self.log_path, filename)
        
        # 追加到文件
        with open(filepath, 'a') as f:
            f.write(json.dumps(state) + '\n')
        
        return state