import asyncio
import json
import os
import threading
import time
from typing import Dict, List, Any, Optional, Tuple
import socket
import uuid

from flask import Flask, request, jsonify

from kademlia_dpos.network.kademlia_network import KademliaNetwork
from kademlia_dpos.consensus.dpos import DPoSConsensus
from kademlia_dpos.utils import crypto, config
from kademlia_dpos.utils.api_helpers import require_consensus
from kademlia_dpos.sync import DataSyncController

# Create Flask app
app = Flask(__name__)

# Global variables
network = None
consensus = None
node_id = None
loop = None
thread = None
sync_controller = None


def get_ip():
    """Get local IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't need to be reachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def initialize_node(port=8468, stake=0, bootstrap_nodes=None):
    """Initialize the node with network and consensus components."""
    global network, consensus, node_id, loop, thread, sync_controller
    
    # 加載先前的節點狀態
    prev_state = config.load_node_state(port)
    if prev_state:
        # 如果有先前的狀態，優先使用之前的權益值（除非當前提供的值更高）
        if prev_state.get("stake", 0) > stake:
            stake = prev_state.get("stake")
            print(f"Restored stake from persistent storage: {stake}")
    
    # 加載或生成與端口關聯的密鑰
    keys = config.load_keys(port)
    if not keys or 'private_key' not in keys or 'public_key' not in keys:
        private_key, public_key = crypto.generate_keys()
        keys = {
            'private_key': private_key,
            'public_key': public_key
        }
        config.save_keys(keys, port)  # 保存到特定端口的目錄
        print(f"Generated new keys for port {port}")
    else:
        print(f"Loaded existing keys for port {port}")
    
    # Create a new event loop for the thread
    loop = asyncio.new_event_loop()
    
    # Set node_id based on public key
    node_id = crypto.hash_data(keys['public_key'])
    
    # 保存節點配置
    node_config = {
        "port": port,
        "node_id": node_id,
        "stake": stake
    }
    config.save_config(node_config)
    
    # Define the bootstrap function
    async def bootstrap():
        global network, consensus, sync_controller
        # Initialize network
        network = KademliaNetwork(port=port)
        await network.start()
        
        # Initialize consensus
        consensus = DPoSConsensus(network, node_id, stake)
        
        # 初始化同步控制器
        sync_controller = DataSyncController(network, node_id, consensus)
        
        # Bootstrap with other nodes if specified
        if bootstrap_nodes:
            await network.bootstrap(bootstrap_nodes)
        
        # Register node
        ip = get_ip()
        await consensus.register_node(ip, port)
        
        # 執行初始數據同步
        await sync_controller.perform_sync()
        
        # Sync delegates
        await consensus.sync_delegates()
        
        print(f"Node initialized with ID: {node_id}")
        print(f"Listening on {ip}:{port}")
        print(f"Initial stake: {stake}")
        
        # Periodically sync delegate status and save node data
        while True:
            try:
                # Sync delegate status every 15 seconds
                await asyncio.sleep(15)
                
                # 檢查連接並同步 (如需要)
                await sync_controller.check_connectivity_and_sync()
                
                await consensus.sync_delegates()
                
                # Check and update local node information
                node_info = await network.get_value(f"node:{node_id}")
                if node_info and node_info.get("is_delegate") != consensus.is_delegate:
                    node_info["is_delegate"] = consensus.is_delegate
                    await network.set_value(f"node:{node_id}", node_info)
                    print(f"Node delegate status updated: is_delegate={consensus.is_delegate}")
                
                # 保存節點狀態到本地
                config.save_node_state(
                    node_id=node_id,
                    is_delegate=consensus.is_delegate,
                    stake=consensus.stake,
                    port=port
                )
            except Exception as e:
                print(f"Error during sync: {e}")
    
    # Run the bootstrap function in the event loop
    def run_loop():
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bootstrap())
    
    # Start the thread
    thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()
    
    # Give some time for initialization
    time.sleep(5)
    
    return node_id


def run_async(coro):
    """Run an async function in the event loop thread."""
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result()


# API Routes

@app.route('/node/info', methods=['GET'])
def get_node_info():
    """Get node information"""
    if consensus is None:
        return jsonify({
            'id': node_id,
            'is_delegate': False,
            'stake': 0,
            'status': 'Initializing'
        })
    return jsonify({
        'id': node_id,
        'is_delegate': consensus.is_delegate,
        'stake': consensus.stake,
        'status': 'Ready'
    })


@app.route('/nodes', methods=['GET'])
@require_consensus
def get_nodes():
    """Get information about all nodes in the network."""
    try:
        # First ensure the current node is registered
        node_info = {
            "id": node_id,
            "address": get_ip(),
            "port": network.port,
            "stake": consensus.stake,
            "is_delegate": consensus.is_delegate,
            "registered_at": time.time()
        }
        run_async(network.set_value(f"node:{node_id}", node_info))
        
        # Get or initialize nodes:all list
        all_nodes = run_async(network.get_value("nodes:all")) or []
        
        # Ensure current node is in the list
        if node_id not in all_nodes:
            all_nodes.append(node_id)
            run_async(network.set_value("nodes:all", all_nodes))
        
        # Get detailed information for all nodes
        nodes = []
        for n_id in all_nodes:
            node_data = run_async(network.get_value(f"node:{n_id}"))
            if node_data:
                nodes.append(node_data)
        
        return jsonify(nodes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/node/stake', methods=['POST'])
def update_stake():
    """Update the stake of this node."""
    data = request.get_json()
    if 'stake' not in data:
        return jsonify({'error': 'Missing stake value'}), 400
    
    new_stake = int(data['stake'])
    run_async(consensus.update_stake(new_stake))
    
    # 保存更新後的狀態到本地
    config.save_node_state(
        node_id=node_id,
        is_delegate=consensus.is_delegate,
        stake=consensus.stake,
        port=network.port
    )
    
    return jsonify({
        'id': node_id,
        'stake': consensus.stake,
    })

# 剩餘的API路由保持不變
@app.route('/delegates/election/start', methods=['POST'])
def start_delegate_election():
    """Start an election for delegates."""
    data = request.get_json()
    num_delegates = int(data.get('num_delegates', 21))
    duration = int(data.get('duration', 3600))
    
    election_id = run_async(consensus.start_delegate_election(num_delegates, duration))
    
    return jsonify({
        'election_id': election_id,
        'num_delegates': num_delegates,
        'duration': duration,
    })


@app.route('/delegates/election/<election_id>/vote', methods=['POST'])
def vote_for_delegate(election_id):
    """Vote for a delegate in an election."""
    data = request.get_json()
    if 'delegate_id' not in data:
        return jsonify({'error': 'Missing delegate_id'}), 400
    
    delegate_id = data['delegate_id']
    run_async(consensus.vote_for_delegate(election_id, delegate_id))
    
    return jsonify({
        'election_id': election_id,
        'delegate_id': delegate_id,
        'voter_id': node_id,
    })


@app.route('/delegates/election/<election_id>/results', methods=['GET'])
def get_election_results(election_id):
    """Get the results of a delegate election."""
    vote_counts = run_async(consensus.count_votes(election_id))
    return jsonify(vote_counts)


@app.route('/delegates/election/<election_id>/finalize', methods=['POST'])
def finalize_election(election_id):
    """Finalize a delegate election."""
    selected_delegates = run_async(consensus.finalize_election(election_id))
    
    # 選舉完成後保存狀態
    config.save_node_state(
        node_id=node_id,
        is_delegate=consensus.is_delegate,
        stake=consensus.stake,
        port=network.port
    )
    
    return jsonify({
        'election_id': election_id,
        'selected_delegates': selected_delegates,
        'is_delegate': consensus.is_delegate,
    })


@app.route('/delegates', methods=['GET'])
def get_delegates():
    """Get the current list of delegates."""
    return jsonify({
        'delegates': consensus.delegates,
        'is_delegate': consensus.is_delegate,
    })


@app.route('/votes/start', methods=['POST'])
def start_proposal_vote():
    """Start a vote on a proposal."""
    data = request.get_json()
    if 'title' not in data or 'options' not in data:
        return jsonify({'error': 'Missing title or options'}), 400
    
    title = data['title']
    description = data.get('description', '')
    options = data['options']
    duration = int(data.get('duration', 3600))
    
    vote_id = run_async(consensus.start_proposal_vote(title, description, options, duration))
    
    return jsonify({
        'vote_id': vote_id,
        'title': title,
        'options': options,
        'duration': duration,
    })


@app.route('/votes/<vote_id>/cast', methods=['POST'])
def cast_vote(vote_id):
    """Cast a vote on a proposal."""
    data = request.get_json()
    if 'option' not in data:
        return jsonify({'error': 'Missing option'}), 400
    
    option = data['option']
    try:
        run_async(consensus.vote_on_proposal(vote_id, option))
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    return jsonify({
        'vote_id': vote_id,
        'option': option,
        'voter_id': node_id,
    })


@app.route('/votes/<vote_id>/results', methods=['GET'])
def get_vote_results(vote_id):
    """Get the results of a proposal vote."""
    results = run_async(consensus.get_proposal_results(vote_id))
    return jsonify(results)


@app.route('/votes/<vote_id>/finalize', methods=['POST'])
def finalize_vote(vote_id):
    """Finalize a proposal vote."""
    try:
        vote_info = run_async(consensus.finalize_proposal_vote(vote_id))
        return jsonify(vote_info)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@app.route('/votes/active', methods=['GET'])
def get_active_votes():
    """Get all active votes."""
    active_votes = run_async(consensus.get_active_votes())
    return jsonify(active_votes)


@app.route('/store', methods=['POST'])
@require_consensus
def store_data():
    """Store key-value pair to the network"""
    data = request.get_json()
    if 'key' not in data or 'value' not in data:
        return jsonify({'error': 'Missing key or value'}), 400
    
    key = data['key']
    value = data['value']
    
    run_async(network.set_value(key, value))
    
    return jsonify({
        'status': 'success',
        'key': key,
        'value': value
    })


@app.route('/retrieve', methods=['GET'])
@require_consensus
def retrieve_data():
    """Retrieve key-value pair from the network"""
    key = request.args.get('key')
    if not key:
        return jsonify({'error': 'Missing key parameter'}), 400
    
    value = run_async(network.get_value(key))
    
    if value is None:
        return jsonify({'status': 'not_found', 'key': key}), 404
    
    return jsonify({
        'status': 'success',
        'key': key,
        'value': value
    })


@app.route('/proposals/create', methods=['POST'])
def create_proposal():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid request data"}), 400
    
    title = data.get('title')
    description = data.get('description')
    duration = data.get('duration', 24)  # Default 24 hours
    
    if not title or not description:
        return jsonify({"error": "Proposal title and content cannot be empty"}), 400
    
    # Generate proposal ID
    proposal_id = str(uuid.uuid4())
    
    # Create proposal object
    proposal = {
        "id": proposal_id,
        "title": title,
        "description": description,
        "creator": node_id,
        "created_at": time.time(),
        "duration": duration * 3600,  # Convert to seconds
        "status": "active",
        "votes": {"yes": 0, "no": 0, "abstain": 0},
        "voters": {}
    }
    
    # Store in DHT
    key = f"proposal:{proposal_id}"
    run_async(network.set_value(key, proposal))
    
    return jsonify({
        "proposal_id": proposal_id,
        "message": "Proposal created successfully"
    })


@app.route('/proposals/list', methods=['GET'])
def list_proposals():
    # Get all proposals from DHT
    proposals = []
    
    # Assume we have a method to list all keys starting with "proposal:"
    # Since Kademlia doesn't directly support this type of query, we might need to implement a centralized index
    # or maintain a proposal list in the actual application
    
    # Simulated data
    proposal_keys = run_async(network.get_all_values("proposal:*"))
    
    for key in proposal_keys:
        proposal_data = run_async(network.get_value(key))
        if proposal_data:
            proposals.append(proposal_data)
    
    return jsonify(proposals)


@app.route('/proposals/<proposal_id>', methods=['GET'])
def get_proposal(proposal_id):
    key = f"proposal:{proposal_id}"
    proposal_data = run_async(network.get_value(key))
    
    if not proposal_data:
        return jsonify({"error": "Proposal does not exist"}), 404
    
    return jsonify(proposal_data)


@app.route('/proposals/<proposal_id>/vote', methods=['POST'])
def vote_proposal(proposal_id):
    data = request.json
    if not data:
        return jsonify({"error": "Invalid request data"}), 400
    
    vote = data.get('vote')  # "yes", "no", "abstain"
    if vote not in ["yes", "no", "abstain"]:
        return jsonify({"error": "Invalid voting option"}), 400
    
    key = f"proposal:{proposal_id}"
    proposal_data = run_async(network.get_value(key))
    
    if not proposal_data:
        return jsonify({"error": "Proposal does not exist"}), 404
    
    proposal = proposal_data
    
    # Check if proposal is still active
    if proposal["status"] != "active":
        return jsonify({"error": "This proposal has ended, cannot vote"}), 400
    
    # Check if already voted
    if node_id in proposal["voters"]:
        return jsonify({"error": "You have already voted on this proposal"}), 400
    
    # Get user stake
    stake = consensus.stake
    
    # Record vote
    proposal["votes"][vote] += stake
    proposal["voters"][node_id] = vote
    
    # Update proposal
    run_async(network.set_value(key, proposal))
    
    return jsonify({
        "message": "Vote successful",
        "proposal_id": proposal_id,
        "vote": vote
    })


@app.route('/proposals/<proposal_id>/finalize', methods=['POST'])
def finalize_proposal(proposal_id):
    key = f"proposal:{proposal_id}"
    proposal_data = run_async(network.get_value(key))
    
    if not proposal_data:
        return jsonify({"error": "Proposal does not exist"}), 404
    
    proposal = proposal_data
    
    # Check if proposal has already ended
    if proposal["status"] != "active":
        return jsonify({"error": "This proposal has already ended"}), 400
    
    # Check if time has expired
    current_time = time.time()
    end_time = proposal["created_at"] + proposal["duration"]
    
    if current_time < end_time:
        return jsonify({"error": "Proposal voting period has not ended yet"}), 400
    
    # Calculate results
    yes_votes = proposal["votes"]["yes"]
    no_votes = proposal["votes"]["no"]
    abstain_votes = proposal["votes"]["abstain"]
    total_votes = yes_votes + no_votes + abstain_votes
    
    # Update status
    proposal["status"] = "completed"
    proposal["result"] = "passed" if yes_votes > no_votes else "rejected"
    proposal["finalized_at"] = current_time
    
    # Update proposal
    run_async(network.set_value(key, proposal))
    
    return jsonify({
        "message": "Proposal has ended",
        "proposal_id": proposal_id,
        "result": proposal["result"],
        "votes": proposal["votes"]
    })


@app.route('/data/store', methods=['POST'])
def store_data_endpoint():
    data = request.json
    if not data or 'data' not in data:
        return jsonify({"error": "Invalid data"}), 400
    
    data_content = data['data']
    data_id = str(uuid.uuid4())
    key = f"data:{data_id}"
    
    # Store in DHT
    run_async(network.set_value(key, {
        "id": data_id,
        "content": data_content,
        "created_at": time.time()
    }))
    
    return jsonify({
        "message": "Data stored successfully",
        "data_id": data_id
    })


@app.route('/data/retrieve/<data_id>', methods=['GET'])
def retrieve_data_endpoint(data_id):
    key = f"data:{data_id}"
    data = run_async(network.get_value(key))
    
    if not data:
        return jsonify({"error": "Data does not exist"}), 404
    
    return jsonify(data)


@app.route('/debug/shutdown', methods=['POST'])
def shutdown_node():
    # Use only in development environment
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        return jsonify({"error": "Unable to shut down server"}), 500
    
    func()
    return jsonify({"message": "Node is shutting down"})


@app.route('/sync', methods=['POST'])
def sync_node():
    """Manually sync node status"""
    if not consensus:
        return jsonify({'error': 'Node not initialized'}), 500
    
    # Sync delegate status
    is_delegate = run_async(consensus.sync_delegates())
    
    # 同步後保存狀態
    config.save_node_state(
        node_id=node_id,
        is_delegate=consensus.is_delegate,
        stake=consensus.stake,
        port=network.port
    )
    
    return jsonify({
        'id': node_id,
        'is_delegate': is_delegate,
        'stake': consensus.stake,
        'status': 'Synchronized'
    })


@app.route('/force-sync', methods=['POST'])
def force_sync():
    """強制執行數據同步"""
    if not sync_controller:
        return jsonify({'error': 'Sync controller not initialized'}), 500
    
    success = run_async(sync_controller.perform_sync())
    
    return jsonify({
        'success': success,
        'last_sync': sync_controller.last_sync_time,
        'message': 'Sync completed' if success else 'Sync failed'
    })


def start_api(host='0.0.0.0', port=5000, node_port=8468, stake=0, bootstrap_nodes=None):
    """
    Start the API server.
    
    Args:
        host: Host to bind the API server to
        port: Port for the API server
        node_port: Port for the Kademlia node
        stake: Initial stake for this node
        bootstrap_nodes: List of (host, port) tuples for bootstrap nodes
    """
    initialize_node(node_port, stake, bootstrap_nodes)
    app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Kademlia DPoS API Server')
    parser.add_argument('--host', default='0.0.0.0', help='API server host')
    parser.add_argument('--port', type=int, default=5000, help='API server port')
    parser.add_argument('--node-port', type=int, default=8468, help='Kademlia node port')
    parser.add_argument('--stake', type=int, default=0, help='Initial stake')
    parser.add_argument('--bootstrap', nargs='+', help='Bootstrap nodes (host:port)')
    
    args = parser.parse_args()
    
    # Parse bootstrap nodes
    bootstrap_nodes = None
    if args.bootstrap:
        bootstrap_nodes = []
        for node in args.bootstrap:
            host, port = node.split(':')
            bootstrap_nodes.append((host, int(port)))
    
    # Start the API server
    start_api(args.host, args.port, args.node_port, args.stake, bootstrap_nodes)