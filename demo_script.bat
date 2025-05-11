@echo off
echo =========================
echo Kademlia + DPoS Demo
echo =========================

echo ========== Starting Demo Network ==========
echo This script assumes you've already started these nodes:
echo - First node: port 5000, node-port 8468
echo - Second node: port 5001, node-port 8469
echo If not, please start them first and then restart this script.
echo.
echo Continuing in 5 seconds...
timeout /T 5 /NOBREAK

echo ========== Checking Node Status ==========
echo Getting info from Node 1...
python -m kademlia_dpos.cli info --api http://localhost:5000
timeout /T 2 /NOBREAK

echo Getting info from Node 2...
python -m kademlia_dpos.cli info --api http://localhost:5001
timeout /T 2 /NOBREAK

echo ========== Listing All Nodes ==========
python -m kademlia_dpos.cli nodes --api http://localhost:5000
timeout /T 2 /NOBREAK

echo ========== Starting Delegate Election ==========
echo Creating new election with 2 delegates...
python -m kademlia_dpos.cli start-election --api http://localhost:5000 --delegates 2 --duration 600

echo ====================================================================
echo Please enter the election ID from the output above
echo ====================================================================
SET /P ELECTION_ID="Election ID: "
echo You entered: %ELECTION_ID%

echo ====================================================================
echo The node ID from above should be your delegation target
echo Copy this ID: 1c0c9ae6fa08e68a9f07fcdd5a21476dd8293828192215be60dcdd0f3b2e4978
echo ====================================================================
SET NODE2_ID=1c0c9ae6fa08e68a9f07fcdd5a21476dd8293828192215be60dcdd0f3b2e4978
echo Using Node ID: %NODE2_ID%

echo ========== Voting Process ==========
echo Node 1 voting for Node 2...
python -m kademlia_dpos.cli vote-delegate --api http://localhost:5000 --election %ELECTION_ID% --delegate %NODE2_ID%
timeout /T 3 /NOBREAK

echo Node 2 voting for itself...
python -m kademlia_dpos.cli vote-delegate --api http://localhost:5001 --election %ELECTION_ID% --delegate %NODE2_ID%
timeout /T 3 /NOBREAK

echo ========== Viewing Election Results ==========
python -m kademlia_dpos.cli election-results --api http://localhost:5000 --election %ELECTION_ID%
timeout /T 3 /NOBREAK

echo ========== Finalizing Election ==========
python -m kademlia_dpos.cli finalize-election --api http://localhost:5000 --election %ELECTION_ID%
timeout /T 3 /NOBREAK

echo ========== Checking Updated Delegate Status ==========
python -m kademlia_dpos.cli delegates --api http://localhost:5000
timeout /T 2 /NOBREAK

echo ========== Demo Completed ==========
echo The demonstration has successfully completed!
echo.
echo This demo has shown:
echo 1. Kademlia DHT for node discovery and P2P communication
echo 2. DPoS consensus for stake-based voting
echo 3. Distributed network consensus and delegate election
echo.
echo Key advantages of distributed algorithms:
echo - No central point of failure
echo - Nodes can freely join and leave the network
echo - Transparent and verifiable voting process
echo - Energy efficient compared to proof-of-work
echo.
pause