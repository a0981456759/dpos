@echo off
echo =========================
echo System Resilience Demo
echo =========================

echo This demo simulates a node failure scenario to demonstrate
echo the resilience of distributed systems.
echo.
echo The demo will:
echo 1. Create test data in the network (an election)
echo 2. Simulate node failure by stopping a node
echo 3. Show that data remains accessible from other nodes
echo 4. Restore the failed node and verify recovery
echo.
echo Make sure all three nodes are running before starting:
echo - Node 1: port 5000, node-port 8468
echo - Node 2: port 5001, node-port 8469
echo - Node 3: port 5002, node-port 8470
echo.
echo We will simulate the failure of Node 2.
echo.
echo Press any key to start the demo...
pause

python node_failure_simulator.py --api-port 5001 --node-port 8469

echo ===================================================
echo Node failure simulation completed!
echo.
echo Key concepts demonstrated:
echo - Fault tolerance: System continues to function when nodes fail
echo - Data replication: Data is accessible from multiple nodes
echo - Self-healing: Nodes can rejoin the network seamlessly
echo.
echo These properties make distributed systems superior to centralized
echo systems in terms of reliability and availability.
echo ===================================================
pause