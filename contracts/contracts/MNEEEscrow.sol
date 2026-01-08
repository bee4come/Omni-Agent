// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title MNEEEscrow
 * @dev Implements trustless escrow for Agent-to-Agent commerce
 *
 * Protocol: Escrow-Verify-Release
 * 1. Customer locks funds in escrow
 * 2. Merchant performs work and submits proof
 * 3. Verifier validates output
 * 4. Funds released to merchant OR refunded to customer
 *
 * Key Features:
 * - Trustless transactions between AI Agents
 * - On-chain verification scores
 * - Dispute resolution mechanism
 * - Platform fee collection
 */
contract MNEEEscrow is Ownable, ReentrancyGuard {
    IERC20 public mneeToken;

    // Escrow states
    enum EscrowState {
        Created,    // Funds locked, waiting for work
        Submitted,  // Work submitted by merchant
        Verifying,  // Under verification
        Released,   // Funds released to merchant
        Refunded,   // Funds returned to customer
        Disputed    // In dispute resolution
    }

    struct Escrow {
        bytes32 escrowId;
        bytes32 customerAgentId;
        bytes32 merchantAgentId;
        bytes32 verifierAgentId;
        uint256 amount;
        uint256 platformFee;
        EscrowState state;
        string taskDescription;
        string requirementHash;  // IPFS CID of task requirements
        string workProofHash;    // IPFS CID of submitted work
        uint256 verificationScore;  // 0-100 scale
        uint256 createdAt;
        uint256 submittedAt;
        uint256 releasedAt;
        string disputeReason;
    }

    // Storage
    mapping(bytes32 => Escrow) public escrows;
    bytes32[] public escrowIds;

    // Platform settings
    uint256 public platformFeePercent = 100;  // 1% = 100 basis points
    uint256 public constant FEE_DENOMINATOR = 10000;
    uint256 public constant MIN_VERIFICATION_SCORE = 70;  // Minimum score to release

    address public feeCollector;

    // Events
    event EscrowCreated(
        bytes32 indexed escrowId,
        bytes32 indexed customerAgentId,
        bytes32 indexed merchantAgentId,
        uint256 amount,
        string taskDescription
    );

    event WorkSubmitted(
        bytes32 indexed escrowId,
        string workProofHash
    );

    event VerificationCompleted(
        bytes32 indexed escrowId,
        bytes32 indexed verifierAgentId,
        uint256 score,
        bool passed
    );

    event EscrowReleased(
        bytes32 indexed escrowId,
        bytes32 indexed merchantAgentId,
        uint256 amount,
        uint256 fee
    );

    event EscrowRefunded(
        bytes32 indexed escrowId,
        bytes32 indexed customerAgentId,
        uint256 amount
    );

    event DisputeRaised(
        bytes32 indexed escrowId,
        string reason
    );

    event DisputeResolved(
        bytes32 indexed escrowId,
        bool releasedToMerchant
    );

    constructor(address _mneeToken) Ownable(msg.sender) {
        mneeToken = IERC20(_mneeToken);
        feeCollector = msg.sender;
    }

    /**
     * @dev Create a new escrow (Customer locks funds)
     * @param customerAgentId ID of the customer agent
     * @param merchantAgentId ID of the merchant agent
     * @param amount Amount to lock in escrow
     * @param taskDescription Description of the task
     * @param requirementHash IPFS CID of detailed requirements
     */
    function createEscrow(
        string calldata customerAgentId,
        string calldata merchantAgentId,
        uint256 amount,
        string calldata taskDescription,
        string calldata requirementHash
    ) external nonReentrant returns (bytes32 escrowId) {
        require(amount > 0, "Amount must be > 0");

        bytes32 custId = keccak256(abi.encodePacked(customerAgentId));
        bytes32 merchId = keccak256(abi.encodePacked(merchantAgentId));
        require(custId != merchId, "Customer and merchant must differ");

        // Calculate platform fee
        uint256 fee = (amount * platformFeePercent) / FEE_DENOMINATOR;

        // Generate unique escrow ID
        escrowId = keccak256(abi.encodePacked(
            custId,
            merchId,
            amount,
            block.timestamp,
            escrowIds.length
        ));

        require(escrows[escrowId].createdAt == 0, "Escrow already exists");

        // Transfer MNEE from sender to contract
        require(
            mneeToken.transferFrom(msg.sender, address(this), amount),
            "Transfer failed"
        );

        // Create escrow record
        escrows[escrowId] = Escrow({
            escrowId: escrowId,
            customerAgentId: custId,
            merchantAgentId: merchId,
            verifierAgentId: bytes32(0),
            amount: amount,
            platformFee: fee,
            state: EscrowState.Created,
            taskDescription: taskDescription,
            requirementHash: requirementHash,
            workProofHash: "",
            verificationScore: 0,
            createdAt: block.timestamp,
            submittedAt: 0,
            releasedAt: 0,
            disputeReason: ""
        });

        escrowIds.push(escrowId);

        emit EscrowCreated(escrowId, custId, merchId, amount, taskDescription);
    }

    /**
     * @dev Submit work proof (Merchant submits completed work)
     * @param escrowId ID of the escrow
     * @param workProofHash IPFS CID of the work evidence
     */
    function submitWork(
        bytes32 escrowId,
        string calldata workProofHash
    ) external onlyOwner {
        Escrow storage esc = escrows[escrowId];
        require(esc.createdAt > 0, "Escrow not found");
        require(esc.state == EscrowState.Created, "Invalid escrow state");
        require(bytes(workProofHash).length > 0, "Work proof required");

        esc.workProofHash = workProofHash;
        esc.submittedAt = block.timestamp;
        esc.state = EscrowState.Submitted;

        emit WorkSubmitted(escrowId, workProofHash);
    }

    /**
     * @dev Verify work and potentially release funds
     * @param escrowId ID of the escrow
     * @param verifierAgentId ID of the verifier agent
     * @param score Verification score (0-100)
     */
    function verifyAndRelease(
        bytes32 escrowId,
        string calldata verifierAgentId,
        uint256 score
    ) external onlyOwner nonReentrant {
        Escrow storage esc = escrows[escrowId];
        require(esc.createdAt > 0, "Escrow not found");
        require(esc.state == EscrowState.Submitted, "Work not submitted");
        require(score <= 100, "Invalid score");

        bytes32 verId = keccak256(abi.encodePacked(verifierAgentId));
        esc.verifierAgentId = verId;
        esc.verificationScore = score;
        esc.state = EscrowState.Verifying;

        bool passed = score >= MIN_VERIFICATION_SCORE;

        emit VerificationCompleted(escrowId, verId, score, passed);

        if (passed) {
            _releaseToMerchant(escrowId);
        } else {
            _refundToCustomer(escrowId);
        }
    }

    /**
     * @dev Raise a dispute
     * @param escrowId ID of the escrow
     * @param reason Reason for dispute
     */
    function raiseDispute(
        bytes32 escrowId,
        string calldata reason
    ) external onlyOwner {
        Escrow storage esc = escrows[escrowId];
        require(esc.createdAt > 0, "Escrow not found");
        require(
            esc.state == EscrowState.Created ||
            esc.state == EscrowState.Submitted ||
            esc.state == EscrowState.Verifying,
            "Cannot dispute in current state"
        );

        esc.state = EscrowState.Disputed;
        esc.disputeReason = reason;

        emit DisputeRaised(escrowId, reason);
    }

    /**
     * @dev Resolve a dispute (Admin decision)
     * @param escrowId ID of the escrow
     * @param releaseToMerchant True to release to merchant, false to refund customer
     */
    function resolveDispute(
        bytes32 escrowId,
        bool releaseToMerchant
    ) external onlyOwner nonReentrant {
        Escrow storage esc = escrows[escrowId];
        require(esc.createdAt > 0, "Escrow not found");
        require(esc.state == EscrowState.Disputed, "Not in dispute");

        emit DisputeResolved(escrowId, releaseToMerchant);

        if (releaseToMerchant) {
            _releaseToMerchant(escrowId);
        } else {
            _refundToCustomer(escrowId);
        }
    }

    /**
     * @dev Internal: Release funds to merchant
     */
    function _releaseToMerchant(bytes32 escrowId) internal {
        Escrow storage esc = escrows[escrowId];

        uint256 merchantAmount = esc.amount - esc.platformFee;

        // Transfer to merchant (via owner who manages agent wallets)
        require(mneeToken.transfer(owner(), merchantAmount), "Merchant transfer failed");

        // Transfer fee to collector
        if (esc.platformFee > 0) {
            require(mneeToken.transfer(feeCollector, esc.platformFee), "Fee transfer failed");
        }

        esc.state = EscrowState.Released;
        esc.releasedAt = block.timestamp;

        emit EscrowReleased(escrowId, esc.merchantAgentId, merchantAmount, esc.platformFee);
    }

    /**
     * @dev Internal: Refund to customer
     */
    function _refundToCustomer(bytes32 escrowId) internal {
        Escrow storage esc = escrows[escrowId];

        // Full refund (no fee on failed work)
        require(mneeToken.transfer(owner(), esc.amount), "Refund transfer failed");

        esc.state = EscrowState.Refunded;
        esc.releasedAt = block.timestamp;

        emit EscrowRefunded(escrowId, esc.customerAgentId, esc.amount);
    }

    // ============================================================
    // View Functions
    // ============================================================

    function getEscrow(bytes32 escrowId) external view returns (Escrow memory) {
        return escrows[escrowId];
    }

    function getEscrowCount() external view returns (uint256) {
        return escrowIds.length;
    }

    function getEscrowsByState(EscrowState state) external view returns (bytes32[] memory) {
        uint256 count = 0;
        for (uint256 i = 0; i < escrowIds.length; i++) {
            if (escrows[escrowIds[i]].state == state) {
                count++;
            }
        }

        bytes32[] memory result = new bytes32[](count);
        uint256 idx = 0;
        for (uint256 i = 0; i < escrowIds.length; i++) {
            if (escrows[escrowIds[i]].state == state) {
                result[idx] = escrowIds[i];
                idx++;
            }
        }

        return result;
    }

    function getRecentEscrows(uint256 count) external view returns (bytes32[] memory) {
        uint256 total = escrowIds.length;
        uint256 start = total > count ? total - count : 0;
        uint256 resultCount = total - start;

        bytes32[] memory result = new bytes32[](resultCount);
        for (uint256 i = 0; i < resultCount; i++) {
            result[i] = escrowIds[start + i];
        }

        return result;
    }

    // ============================================================
    // Admin Functions
    // ============================================================

    function setFeeCollector(address _feeCollector) external onlyOwner {
        require(_feeCollector != address(0), "Invalid address");
        feeCollector = _feeCollector;
    }

    function setPlatformFeePercent(uint256 _feePercent) external onlyOwner {
        require(_feePercent <= 1000, "Fee too high");  // Max 10%
        platformFeePercent = _feePercent;
    }
}
