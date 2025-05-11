# Kademlia DPoS Voting System

This project combines a Delegated Proof of Stake (DPoS) voting system with Kademlia P2P networking to create a decentralized voting platform. It allows nodes to elect delegates and participate in proposal votes, with the voting power determined by the stake of each node.

## Features

- **P2P Network**: Uses Kademlia DHT for decentralized peer-to-peer communication
- **DPoS Consensus**: Implements a Delegated Proof of Stake consensus mechanism
- **Delegate Elections**: Allows nodes to elect delegates based on stake-weighted voting
- **Proposal Voting**: Enables stake-weighted voting on proposals with customizable options
- **REST API**: Provides a RESTful API for interacting with the system
- **CLI**: Includes a command-line interface for easy interaction

## Requirements

- Python 3.8+
- Required packages (install via `pip install -r requirements.txt`):
  - kademlia
  - Flask
  - requests
  - cryptography
  - aiohttp
  - asyncio
  - pycryptodome

## Installation

1. Clone the repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Running a node

To start a node, run:

```bash
python run.py --port 5000 --node-port 8468 --stake 100
```

Options:
- `--host`: Host to bind the API server to (default: 0.0.0.0)
- `--port`: Port for the REST API (default: 5000)
- `--node-port`: Port for the Kademlia P2P network (default: 8468)
- `--stake`: Initial stake for this node (default: 0)
- `--bootstrap`: Bootstrap nodes to connect to, in the format `host:port`

To bootstrap with existing nodes:

```bash
python run.py --port 5001 --node-port 8469 --stake 50 --bootstrap 127.0.0.1:8468
```

## Using the CLI

The CLI provides various commands to interact with the system. 

Basic usage:
```bash
python -m kademlia_dpos.cli <command> [options]
```

Example commands:

1. Get node information:
   ```bash
   python -m kademlia_dpos.cli info --api http://localhost:5000
   ```

2. Update node stake:
   ```bash
   python -m kademlia_dpos.cli stake --amount 200 --api http://localhost:5000
   ```

3. Start a delegate election:
   ```bash
   python -m kademlia_dpos.cli start-election --delegates 5 --duration 3600 --api http://localhost:5000
   ```

4. Vote in delegate election:
   ```bash
   python -m kademlia_dpos.cli vote-delegate --election <election_id> --delegate <delegate_id> --api http://localhost:5000
   ```

5. Start a proposal vote:
   ```bash
   python -m kademlia_dpos.cli start-vote --title "Example Vote" --description "This is an example vote" --options "Yes" "No" "Abstain" --api http://localhost:5000
   ```

6. Cast a vote:
   ```bash
   python -m kademlia_dpos.cli cast-vote --vote <vote_id> --option "Yes" --api http://localhost:5000
   ```

7. Get vote results:
   ```bash
   python -m kademlia_dpos.cli vote-results --vote <vote_id> --api http://localhost:5000
   ```

Run `python -m kademlia_dpos.cli --help` to see all available commands.

## API Endpoints

The system exposes the following REST API endpoints:

### Node Management
- `GET /node/info`: Get information about this node
- `GET /nodes`: Get information about all nodes in the network
- `POST /node/stake`: Update the stake of this node

### Delegate Election
- `POST /delegates/election/start`: Start an election for delegates
- `POST /delegates/election/<election_id>/vote`: Vote for a delegate in an election
- `GET /delegates/election/<election_id>/results`: Get the results of a delegate election
- `POST /delegates/election/<election_id>/finalize`: Finalize a delegate election
- `GET /delegates`: Get the current list of delegates

### Proposal Voting
- `POST /votes/start`: Start a vote on a proposal
- `POST /votes/<vote_id>/cast`: Cast a vote on a proposal
- `GET /votes/<vote_id>/results`: Get the results of a proposal vote
- `POST /votes/<vote_id>/finalize`: Finalize a proposal vote
- `GET /votes/active`: Get all active votes

## Architecture

The system consists of several key components:

1. **Kademlia Network**: Provides P2P networking capabilities for node discovery and distributed data storage
2. **DPoS Consensus**: Implements the Delegated Proof of Stake consensus algorithm
3. **Cryptographic Utilities**: Handles key generation, signing, and verification
4. **REST API**: Exposes system functionality via HTTP endpoints
5. **CLI**: Provides a command-line interface for interacting with the system

## License

This project is licensed under the MIT License.

## Credits

This project combines concepts from:
- [Kademlia DHT](https://github.com/bmuller/kademlia) by bmuller
- [DPoS Consensus](https://github.com/VIVPM/Delegated-Proof-of-Stake-consensus-algorithm) by VIVPM 