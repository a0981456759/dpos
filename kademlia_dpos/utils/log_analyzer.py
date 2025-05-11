import os
import json
import argparse
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import time

class LogAnalyzer:
    """分析網絡日誌的工具"""
    
    def __init__(self, log_dir):
        self.log_dir = log_dir
        self.log_files = []
        self.log_entries = []
        
        # 查找所有日誌文件
        for filename in os.listdir(log_dir):
            if filename.startswith('network_state_') and filename.endswith('.jsonl'):
                self.log_files.append(os.path.join(log_dir, filename))
    
    def load_logs(self, days=1):
        """載入指定天數的日誌"""
        self.log_entries = []
        
        # 計算開始時間
        start_time = time.time() - (days * 86400)
        
        # 讀取並解析日誌
        for log_file in self.log_files:
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            if entry['timestamp'] >= start_time:
                                self.log_entries.append(entry)
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                print(f"警告: 讀取{log_file}時出錯: {e}")
        
        # 按時間戳排序
        self.log_entries.sort(key=lambda x: x['timestamp'])
        
        print(f"已載入{len(self.log_entries)}條日誌記錄")
    
    def plot_network_growth(self):
        """繪製網絡節點增長圖"""
        if not self.log_entries:
            print("錯誤: 沒有日誌記錄")
            return
        
        times = []
        node_counts = []
        
        # 提取數據
        for entry in self.log_entries:
            timestamp = entry['timestamp']
            node_count = entry.get('total_nodes', 0)
            
            times.append(datetime.fromtimestamp(timestamp))
            node_counts.append(node_count)
        
        # 創建圖表
        plt.figure(figsize=(10, 6))
        plt.plot(times, node_counts, 'b-', marker='o')
        plt.title('網絡節點數量變化')
        plt.xlabel('時間')
        plt.ylabel('節點數量')
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # 保存圖表
        output_file = os.path.join(self.log_dir, 'network_growth.png')
        plt.savefig(output_file)
        plt.close()
        
        print(f"網絡增長圖表已保存至: {output_file}")
    
    def plot_delegate_distribution(self):
        """繪製代表節點分佈圖"""
        if not self.log_entries:
            print("錯誤: 沒有日誌記錄")
            return
        
        # 統計代表節點和普通節點數量
        delegate_counts = []
        normal_counts = []
        times = []
        
        for entry in self.log_entries:
            if 'is_delegate' in entry:
                timestamp = entry['timestamp']
                times.append(datetime.fromtimestamp(timestamp))
                
                # 記數為1或0
                delegate_counts.append(1 if entry['is_delegate'] else 0)
                normal_counts.append(0 if entry['is_delegate'] else 1)
        
        # 創建圖表
        plt.figure(figsize=(10, 6))
        plt.stackplot(times, [delegate_counts, normal_counts], 
                     labels=['代表節點', '普通節點'],
                     colors=['green', 'gray'])
        plt.title('節點類型分佈')
        plt.xlabel('時間')
        plt.ylabel('節點數量')
        plt.legend(loc='upper left')
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # 保存圖表
        output_file = os.path.join(self.log_dir, 'delegate_distribution.png')
        plt.savefig(output_file)
        plt.close()
        
        print(f"代表分佈圖表已保存至: {output_file}")
    
    def generate_report(self, days=1):
        """生成網絡狀況報告"""
        self.load_logs(days)
        
        if not self.log_entries:
            print("錯誤: 沒有日誌記錄可供分析")
            return
        
        # 生成報告
        report = []
        report.append("===== Kademlia+DPoS網絡狀況報告 =====")
        report.append(f"報告生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"分析時間段: 最近{days}天")
        report.append(f"日誌記錄數: {len(self.log_entries)}")
        
        # 分析節點數據
        if self.log_entries:
            latest = self.log_entries[-1]
            earliest = self.log_entries[0]
            
            # 計算網絡增長
            initial_nodes = earliest.get('total_nodes', 0)
            current_nodes = latest.get('total_nodes', 0)
            growth_rate = ((current_nodes - initial_nodes) / max(1, initial_nodes)) * 100
            
            report.append("\n節點統計:")
            report.append(f"- 初始節點數: {initial_nodes}")
            report.append(f"- 當前節點數: {current_nodes}")
            report.append(f"- 增長率: {growth_rate:.1f}%")
            
            # 統計活躍投票
            active_votes = latest.get('active_votes', 0)
            report.append(f"- 當前活躍投票數: {active_votes}")
            
            # 分析代表狀態
            delegate_logs = [e for e in self.log_entries if e.get('is_delegate', False)]
            report.append(f"- 代表節點數: {len(delegate_logs)}")
        
        # 生成圖表
        try:
            self.plot_network_growth()
            self.plot_delegate_distribution()
            report.append("\n已生成以下可視化圖表:")
            report.append(f"- {os.path.join(self.log_dir, 'network_growth.png')}")
            report.append(f"- {os.path.join(self.log_dir, 'delegate_distribution.png')}")
        except Exception as e:
            report.append(f"\n生成圖表時出錯: {e}")
        
        # 寫入報告文件
        report_file = os.path.join(self.log_dir, f"network_report_{datetime.now().strftime('%Y%m%d')}.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        print(f"網絡報告已生成: {report_file}")
        return report_file

def main():
    parser = argparse.ArgumentParser(description='Kademlia+DPoS網絡日誌分析工具')
    parser.add_argument('--log-dir', default='./network_logs', help='日誌目錄路徑')
    parser.add_argument('--days', type=int, default=1, help='分析的天數')
    args = parser.parse_args()
    
    analyzer = LogAnalyzer(args.log_dir)
    analyzer.generate_report(args.days)

if __name__ == '__main__':
    main()