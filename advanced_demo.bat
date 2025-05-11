@echo off
echo =========================
echo Advanced Kademlia + DPoS Demo
echo =========================

echo ========== Checking Node Status ==========
echo Getting info from all nodes...
python -m kademlia_dpos.cli info --api http://localhost:5000
python -m kademlia_dpos.cli info --api http://localhost:5001
python -m kademlia_dpos.cli info --api http://localhost:5002
timeout /T 2 /NOBREAK

echo ========== Part 1: Stake-weighted Voting Demonstration ==========
echo Setting up different stakes for each node...
python stake_manager.py --action set --node 1 --stake 100
python stake_manager.py --action set --node 2 --stake 200
python stake_manager.py --action set --node 3 --stake 50
timeout /T 2 /NOBREAK

echo Showing stake distribution...
python stake_manager.py --action show
timeout /T 3 /NOBREAK

echo Starting weighted election demonstration...
python stake_manager.py --action demo
timeout /T 5 /NOBREAK

echo ========== Part 2: Node Failure Simulation ==========
echo We will now demonstrate the system's resilience to node failures.
echo.
echo This will:
echo 1. Store test data in the network
echo 2. Simulate a node failure
echo 3. Check data availability after failure
echo 4. Restore the node and verify recovery
echo.

pause

echo Running node failure simulation...
python node_failure_simulator.py --action demo

echo ========== Demo Completed ==========
echo The advanced demonstration has successfully completed!
echo.
echo Key points demonstrated:
echo 1. Stake-weighted voting in DPoS consensus
echo 2. System resilience to node failures
echo 3. Decentralized data persistence
echo.
pause