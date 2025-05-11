import argparse
import json
import sys
import requests
import time
from typing import Dict, List, Any

def create_parser():
    parser = argparse.ArgumentParser(description='DPoS Voting System CLI')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Node info
    info_parser = subparsers.add_parser('info', help='Get node information')
    info_parser.add_argument('--api', default='http://localhost:5000', help='API server URL')
    
    # List nodes
    nodes_parser = subparsers.add_parser('nodes', help='List all nodes in the network')
    nodes_parser.add_argument('--api', default='http://localhost:5000', help='API server URL')
    
    # Update stake
    stake_parser = subparsers.add_parser('stake', help='Update stake')
    stake_parser.add_argument('--api', default='http://localhost:5000', help='API server URL')
    stake_parser.add_argument('--amount', type=int, required=True, help='Stake amount')
    
    # Start delegate election
    start_election_parser = subparsers.add_parser('start-election', help='Start delegate election')
    start_election_parser.add_argument('--api', default='http://localhost:5000', help='API server URL')
    start_election_parser.add_argument('--delegates', type=int, default=21, help='Number of delegates to elect')
    start_election_parser.add_argument('--duration', type=int, default=3600, help='Election duration in seconds')
    
    # Vote in delegate election
    vote_delegate_parser = subparsers.add_parser('vote-delegate', help='Vote for a delegate')
    vote_delegate_parser.add_argument('--api', default='http://localhost:5000', help='API server URL')
    vote_delegate_parser.add_argument('--election', required=True, help='Election ID')
    vote_delegate_parser.add_argument('--delegate', required=True, help='Delegate ID to vote for')
    
    # Get election results
    election_results_parser = subparsers.add_parser('election-results', help='Get election results')
    election_results_parser.add_argument('--api', default='http://localhost:5000', help='API server URL')
    election_results_parser.add_argument('--election', required=True, help='Election ID')
    
    # Finalize election
    finalize_election_parser = subparsers.add_parser('finalize-election', help='Finalize delegate election')
    finalize_election_parser.add_argument('--api', default='http://localhost:5000', help='API server URL')
    finalize_election_parser.add_argument('--election', required=True, help='Election ID')
    
    # Get delegates
    delegates_parser = subparsers.add_parser('delegates', help='Get list of delegates')
    delegates_parser.add_argument('--api', default='http://localhost:5000', help='API server URL')
    
    # Start proposal vote
    start_vote_parser = subparsers.add_parser('start-vote', help='Start a proposal vote')
    start_vote_parser.add_argument('--api', default='http://localhost:5000', help='API server URL')
    start_vote_parser.add_argument('--title', required=True, help='Vote title')
    start_vote_parser.add_argument('--description', default='', help='Vote description')
    start_vote_parser.add_argument('--options', required=True, nargs='+', help='Voting options')
    start_vote_parser.add_argument('--duration', type=int, default=3600, help='Vote duration in seconds')
    
    # Cast vote
    cast_vote_parser = subparsers.add_parser('cast-vote', help='Cast a vote')
    cast_vote_parser.add_argument('--api', default='http://localhost:5000', help='API server URL')
    cast_vote_parser.add_argument('--vote', required=True, help='Vote ID')
    cast_vote_parser.add_argument('--option', required=True, help='Option to vote for')
    
    # Get vote results
    vote_results_parser = subparsers.add_parser('vote-results', help='Get vote results')
    vote_results_parser.add_argument('--api', default='http://localhost:5000', help='API server URL')
    vote_results_parser.add_argument('--vote', required=True, help='Vote ID')
    
    # Finalize vote
    finalize_vote_parser = subparsers.add_parser('finalize-vote', help='Finalize a vote')
    finalize_vote_parser.add_argument('--api', default='http://localhost:5000', help='API server URL')
    finalize_vote_parser.add_argument('--vote', required=True, help='Vote ID')
    
    # Get active votes
    active_votes_parser = subparsers.add_parser('active-votes', help='Get active votes')
    active_votes_parser.add_argument('--api', default='http://localhost:5000', help='API server URL')
    
    return parser


def make_request(method: str, url: str, data: Dict[str, Any] = None) -> Dict[str, Any]:

    try:
        if method.upper() == 'GET':
            response = requests.get(url)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error making request: {e}")
        sys.exit(1)


def print_json(data: Any):
    print(json.dumps(data, indent=2))


def main():
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    api_url = args.api.rstrip('/')
    
    # Execute the requested command
    if args.command == 'info':
        result = make_request('GET', f"{api_url}/node/info")
        print_json(result)
    
    elif args.command == 'nodes':
        result = make_request('GET', f"{api_url}/nodes")
        print_json(result)
    
    elif args.command == 'stake':
        result = make_request('POST', f"{api_url}/node/stake", {
            'stake': args.amount
        })
        print_json(result)
    
    elif args.command == 'start-election':
        result = make_request('POST', f"{api_url}/delegates/election/start", {
            'num_delegates': args.delegates,
            'duration': args.duration
        })
        print_json(result)
    
    elif args.command == 'vote-delegate':
        result = make_request('POST', f"{api_url}/delegates/election/{args.election}/vote", {
            'delegate_id': args.delegate
        })
        print_json(result)
    
    elif args.command == 'election-results':
        result = make_request('GET', f"{api_url}/delegates/election/{args.election}/results")
        print_json(result)
    
    elif args.command == 'finalize-election':
        result = make_request('POST', f"{api_url}/delegates/election/{args.election}/finalize")
        print_json(result)
    
    elif args.command == 'delegates':
        result = make_request('GET', f"{api_url}/delegates")
        print_json(result)
    
    elif args.command == 'start-vote':
        result = make_request('POST', f"{api_url}/votes/start", {
            'title': args.title,
            'description': args.description,
            'options': args.options,
            'duration': args.duration
        })
        print_json(result)
    
    elif args.command == 'cast-vote':
        result = make_request('POST', f"{api_url}/votes/{args.vote}/cast", {
            'option': args.option
        })
        print_json(result)
    
    elif args.command == 'vote-results':
        result = make_request('GET', f"{api_url}/votes/{args.vote}/results")
        print_json(result)
    
    elif args.command == 'finalize-vote':
        result = make_request('POST', f"{api_url}/votes/{args.vote}/finalize")
        print_json(result)
    
    elif args.command == 'active-votes':
        result = make_request('GET', f"{api_url}/votes/active")
        print_json(result)


if __name__ == '__main__':
    main() 