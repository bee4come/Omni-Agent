// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract MNEEServiceRegistry {
    struct Service {
        address provider;
        uint256 unitPrice;
        bool active;
    }

    mapping(bytes32 => Service) public services;

    event ServiceRegistered(bytes32 indexed serviceId, address indexed provider, uint256 unitPrice);
    event ServiceUpdated(bytes32 indexed serviceId, uint256 unitPrice, bool active);

    function registerService(bytes32 serviceId, uint256 unitPrice) external {
        require(services[serviceId].provider == address(0), "Service already exists");
        services[serviceId] = Service({
            provider: msg.sender,
            unitPrice: unitPrice,
            active: true
        });
        emit ServiceRegistered(serviceId, msg.sender, unitPrice);
    }

    function updateService(bytes32 serviceId, uint256 unitPrice, bool active) external {
        require(services[serviceId].provider == msg.sender, "Not the provider");
        services[serviceId].unitPrice = unitPrice;
        services[serviceId].active = active;
        emit ServiceUpdated(serviceId, unitPrice, active);
    }

    function getService(bytes32 serviceId) external view returns (Service memory) {
        return services[serviceId];
    }
}
