import argparse
import asyncio
from kademlia_dpos.api import start_api
from kademlia_dpos.utils.visualizer import NetworkVisualizer
import threading
import time

# Global visualizer object
visualizer = None

def run_visualizer(network, consensus, node_id):

    global visualizer
    visualizer = NetworkVisualizer(network, consensus, node_id)
    
    # Create event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Display welcome message
    welcome_task = loop.create_task(visualizer.visualize_node_info())
    loop.run_until_complete(welcome_task)
    
    # Regularly log network state
    async def log_regularly():
        while True:
            await visualizer.log_network_state()
            await asyncio.sleep(300)  # Log every 5 minutes
    
    loop.create_task(log_regularly())
    loop.run_forever()

def main():

    parser = argparse.ArgumentParser(description='Start DPoS voting server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind the API server to')
    parser.add_argument('--port', type=int, default=5000, help='Port for the API server')
    parser.add_argument('--node-port', type=int, default=8468, help='Port for the Kademlia node')
    parser.add_argument('--stake', type=int, default=0, help='Initial stake for this node')
    parser.add_argument('--bootstrap', nargs='+', help='Bootstrap nodes (host:port)')
    parser.add_argument('--visual', action='store_true', help='Enable visualization')
    
    args = parser.parse_args()
    
    # Parse bootstrap nodes
    bootstrap_nodes = None
    if args.bootstrap:
        bootstrap_nodes = []
        for node in args.bootstrap:
            host, port = node.split(':')
            bootstrap_nodes.append((host, int(port)))
    
    # Start the API server
    from kademlia_dpos.api import network, consensus, node_id
    start_api_thread = threading.Thread(
        target=start_api,
        args=(args.host, args.port, args.node_port, args.stake, bootstrap_nodes),
        daemon=True
    )
    start_api_thread.start()
    
    # Wait for API initialization
    time.sleep(5)
    
    # If visualization is enabled, start the visualizer
    if args.visual:
        visualizer_thread = threading.Thread(
            target=run_visualizer,
            args=(network, consensus, node_id),
            daemon=True
        )
        visualizer_thread.start()
    
    print(f"Node started:")
    print(f"- API: http://{args.host}:{args.port}")
    print(f"- P2P: {args.node_port}")
    print(f"- Node ID: {node_id}")
    
    # Keep the main program running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down node...")

if __name__ == '__main__':
    main()