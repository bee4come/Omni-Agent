// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title MNEEAgentWallet
 * @dev Manages MNEE balances for AI Agents and enables A2A (Agent-to-Agent) payments
 * 
 * Key Features:
 * - Each agent has an on-chain balance
 * - Agents can transfer MNEE to other agents
 * - Treasury can fund agent wallets
 * - Complete audit trail of all A2A transfers
 */
contract MNEEAgentWallet is Ownable, ReentrancyGuard {
    IERC20 public mneeToken;
    
    // Agent balances
    mapping(bytes32 => uint256) public agentBalances;
    
    // Agent info
    struct AgentInfo {
        bool registered;
        string name;
        uint256 totalReceived;
        uint256 totalSpent;
    }
    mapping(bytes32 => AgentInfo) public agents;
    
    // A2A Transfer record
    struct A2ATransfer {
        bytes32 fromAgent;
        bytes32 toAgent;
        uint256 amount;
        string taskDescription;
        uint256 timestamp;
    }
    A2ATransfer[] public transfers;
    
    // Events
    event AgentRegistered(bytes32 indexed agentId, string name);
    event AgentFunded(bytes32 indexed agentId, uint256 amount, address funder);
    event A2APayment(
        bytes32 indexed fromAgent,
        bytes32 indexed toAgent,
        uint256 amount,
        string taskDescription,
        uint256 transferId
    );
    event AgentWithdraw(bytes32 indexed agentId, address to, uint256 amount);
    
    constructor(address _mneeToken) Ownable(msg.sender) {
        mneeToken = IERC20(_mneeToken);
    }
    
    /**
     * @dev Register a new agent
     */
    function registerAgent(string calldata agentId, string calldata name) external onlyOwner {
        bytes32 id = keccak256(abi.encodePacked(agentId));
        require(!agents[id].registered, "Agent already registered");
        
        agents[id] = AgentInfo({
            registered: true,
            name: name,
            totalReceived: 0,
            totalSpent: 0
        });
        
        emit AgentRegistered(id, name);
    }
    
    /**
     * @dev Fund an agent's wallet (Treasury deposits MNEE)
     */
    function fundAgent(string calldata agentId, uint256 amount) external nonReentrant {
        bytes32 id = keccak256(abi.encodePacked(agentId));
        require(agents[id].registered, "Agent not registered");
        require(amount > 0, "Amount must be > 0");
        
        require(mneeToken.transferFrom(msg.sender, address(this), amount), "Transfer failed");
        
        agentBalances[id] += amount;
        agents[id].totalReceived += amount;
        
        emit AgentFunded(id, amount, msg.sender);
    }
    
    /**
     * @dev Agent-to-Agent payment for task delegation
     * Called by backend when one agent hires another
     */
    function a2aPayment(
        string calldata fromAgentId,
        string calldata toAgentId,
        uint256 amount,
        string calldata taskDescription
    ) external onlyOwner nonReentrant returns (uint256 transferId) {
        bytes32 fromId = keccak256(abi.encodePacked(fromAgentId));
        bytes32 toId = keccak256(abi.encodePacked(toAgentId));
        
        require(agents[fromId].registered, "From agent not registered");
        require(agents[toId].registered, "To agent not registered");
        require(agentBalances[fromId] >= amount, "Insufficient balance");
        require(amount > 0, "Amount must be > 0");
        
        // Transfer between agents
        agentBalances[fromId] -= amount;
        agentBalances[toId] += amount;
        
        // Update stats
        agents[fromId].totalSpent += amount;
        agents[toId].totalReceived += amount;
        
        // Record transfer
        transferId = transfers.length;
        transfers.push(A2ATransfer({
            fromAgent: fromId,
            toAgent: toId,
            amount: amount,
            taskDescription: taskDescription,
            timestamp: block.timestamp
        }));
        
        emit A2APayment(fromId, toId, amount, taskDescription, transferId);
    }
    
    /**
     * @dev Get agent balance
     */
    function getAgentBalance(string calldata agentId) external view returns (uint256) {
        bytes32 id = keccak256(abi.encodePacked(agentId));
        return agentBalances[id];
    }
    
    /**
     * @dev Get agent info
     */
    function getAgentInfo(string calldata agentId) external view returns (
        bool registered,
        string memory name,
        uint256 balance,
        uint256 totalReceived,
        uint256 totalSpent
    ) {
        bytes32 id = keccak256(abi.encodePacked(agentId));
        AgentInfo storage info = agents[id];
        return (
            info.registered,
            info.name,
            agentBalances[id],
            info.totalReceived,
            info.totalSpent
        );
    }
    
    /**
     * @dev Get total transfer count
     */
    function getTransferCount() external view returns (uint256) {
        return transfers.length;
    }
    
    /**
     * @dev Get recent transfers (for visualization)
     */
    function getRecentTransfers(uint256 count) external view returns (
        bytes32[] memory fromAgents,
        bytes32[] memory toAgents,
        uint256[] memory amounts,
        uint256[] memory timestamps
    ) {
        uint256 total = transfers.length;
        uint256 start = total > count ? total - count : 0;
        uint256 resultCount = total - start;
        
        fromAgents = new bytes32[](resultCount);
        toAgents = new bytes32[](resultCount);
        amounts = new uint256[](resultCount);
        timestamps = new uint256[](resultCount);
        
        for (uint256 i = 0; i < resultCount; i++) {
            A2ATransfer storage t = transfers[start + i];
            fromAgents[i] = t.fromAgent;
            toAgents[i] = t.toAgent;
            amounts[i] = t.amount;
            timestamps[i] = t.timestamp;
        }
    }
    
    /**
     * @dev Withdraw agent balance to external address (for service providers)
     */
    function withdrawAgentBalance(
        string calldata agentId,
        address to,
        uint256 amount
    ) external onlyOwner nonReentrant {
        bytes32 id = keccak256(abi.encodePacked(agentId));
        require(agentBalances[id] >= amount, "Insufficient balance");
        
        agentBalances[id] -= amount;
        require(mneeToken.transfer(to, amount), "Transfer failed");
        
        emit AgentWithdraw(id, to, amount);
    }
}
