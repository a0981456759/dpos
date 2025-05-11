#!/usr/bin/env python
"""
Basic example showing how to use the DPoS voting system.

This script demonstrates:
1. Starting a node
2. Setting a stake
3. Starting a delegate election
4. Voting for a delegate
5. Finalizing the election
6. Starting a proposal vote
7. Voting on the proposal
8. Finalizing the proposal vote

Run this script after starting multiple nodes with different ports.
"""

import asyncio
import json
import sys
import time
import requests

API_URL = "http://localhost:5000"  # Change this to your API URL

def make_request(method, endpoint, data=None):
    """Make an HTTP request to the API."""
    url = f"{API_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url)
        elif method.upper() == "POST":
            response = requests.post(url, json=data)
        else:
            print(f"Unsupported method: {method}")
            sys.exit(1)
            
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error making request: {e}")
        return None

def print_json(data):
    """Print data as formatted JSON."""
    print(json.dumps(data, indent=2))

def main():
    """Run the example."""
    # 1. Get node info
    print("\n===== Node Info =====")
    node_info = make_request("GET", "/node/info")
    print_json(node_info)
    
    # 2. Set stake
    print("\n===== Setting Stake =====")
    stake_response = make_request("POST", "/node/stake", {"stake": 100})
    print_json(stake_response)
    
    # 3. Start delegate election
    print("\n===== Starting Delegate Election =====")
    election_response = make_request("POST", "/delegates/election/start", {
        "num_delegates": 3,
        "duration": 60  # 1 minute for demonstration
    })
    print_json(election_response)
    
    election_id = election_response["election_id"]
    
    # 4. Vote for self as delegate
    print("\n===== Voting for Delegate =====")
    vote_response = make_request("POST", f"/delegates/election/{election_id}/vote", {
        "delegate_id": node_info["id"]
    })
    print_json(vote_response)
    
    # 5. Get election results
    print("\n===== Election Results =====")
    print("Waiting 10 seconds for other nodes to vote...")
    time.sleep(10)
    
    results = make_request("GET", f"/delegates/election/{election_id}/results")
    print_json(results)
    
    # 6. Finalize election
    print("\n===== Finalizing Election =====")
    finalize_response = make_request("POST", f"/delegates/election/{election_id}/finalize")
    print_json(finalize_response)
    
    # 7. Check if we're a delegate
    print("\n===== Checking Delegate Status =====")
    delegate_info = make_request("GET", "/delegates")
    print_json(delegate_info)
    
    # 8. Start a proposal vote
    print("\n===== Starting Proposal Vote =====")
    vote_start_response = make_request("POST", "/votes/start", {
        "title": "Example Proposal",
        "description": "This is an example proposal for demonstration purposes.",
        "options": ["Yes", "No", "Abstain"],
        "duration": 60  # 1 minute for demonstration
    })
    print_json(vote_start_response)
    
    vote_id = vote_start_response["vote_id"]
    
    # 9. Cast a vote
    print("\n===== Casting Vote =====")
    cast_vote_response = make_request("POST", f"/votes/{vote_id}/cast", {
        "option": "Yes"
    })
    print_json(cast_vote_response)
    
    # 10. Get vote results
    print("\n===== Vote Results =====")
    print("Waiting 10 seconds for other nodes to vote...")
    time.sleep(10)
    
    vote_results = make_request("GET", f"/votes/{vote_id}/results")
    print_json(vote_results)
    
    # 11. Finalize vote
    print("\n===== Finalizing Vote =====")
    finalize_vote_response = make_request("POST", f"/votes/{vote_id}/finalize")
    print_json(finalize_vote_response)
    
    # 12. Check active votes
    print("\n===== Active Votes =====")
    active_votes = make_request("GET", "/votes/active")
    print_json(active_votes)
    
    print("\nExample completed successfully!")

if __name__ == "__main__":
    main() 