// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "./MNEEServiceRegistry.sol";

contract MNEEPaymentRouter {
    IERC20 public mneeToken;
    MNEEServiceRegistry public registry;

    event PaymentExecuted(
        bytes32 indexed paymentId,
        address indexed payer,
        address indexed provider,
        bytes32 serviceId,
        string agentId,
        string taskId,
        uint256 amount,
        uint256 quantity,
        uint256 timestamp
    );

    constructor(address _mneeToken, address _registry) {
        mneeToken = IERC20(_mneeToken);
        registry = MNEEServiceRegistry(_registry);
    }

    function payForService(
        bytes32 serviceId,
        string calldata agentId,
        string calldata taskId,
        uint256 quantity
    ) external {
        MNEEServiceRegistry.Service memory service = registry.getService(serviceId);
        require(service.active, "Service not active");
        require(service.provider != address(0), "Service not found");

        uint256 totalAmount = service.unitPrice * quantity;
        require(totalAmount > 0, "Amount must be > 0");

        // Transfer MNEE from payer (Agent Treasury) to Provider
        require(
            mneeToken.transferFrom(msg.sender, service.provider, totalAmount),
            "Transfer failed"
        );

        // Generate a unique payment ID (hash of params + timestamp)
        bytes32 paymentId = keccak256(
            abi.encodePacked(msg.sender, serviceId, agentId, taskId, block.timestamp)
        );

        emit PaymentExecuted(
            paymentId,
            msg.sender,
            service.provider,
            serviceId,
            agentId,
            taskId,
            totalAmount,
            quantity,
            block.timestamp
        );
    }
}
