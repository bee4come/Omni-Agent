// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract MNEEServiceRegistry {
    address public owner;

    struct Service {
        address provider;
        uint256 unitPrice;
        bool active;
        string metadataURI;
        bool isVerified;
    }

    mapping(bytes32 => Service) public services;

    event ServiceRegistered(
        bytes32 indexed serviceId, 
        address indexed provider, 
        uint256 unitPrice, 
        string metadataURI, 
        bool isVerified
    );
    event ServiceUpdated(
        bytes32 indexed serviceId, 
        uint256 unitPrice, 
        bool active, 
        string metadataURI, 
        bool isVerified
    );

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this");
        _;
    }

    function registerService(
        bytes32 serviceId,
        address provider,
        uint256 unitPrice,
        string calldata metadataURI,
        bool isVerified
    ) external onlyOwner {
        require(services[serviceId].provider == address(0), "Service already exists");
        require(provider != address(0), "Invalid provider address");
        
        services[serviceId] = Service({
            provider: provider,
            unitPrice: unitPrice,
            active: true,
            metadataURI: metadataURI,
            isVerified: isVerified
        });
        
        emit ServiceRegistered(serviceId, provider, unitPrice, metadataURI, isVerified);
    }

    function updateService(
        bytes32 serviceId,
        address provider,
        uint256 unitPrice,
        bool active,
        string calldata metadataURI,
        bool isVerified
    ) external onlyOwner {
        require(services[serviceId].provider != address(0), "Service does not exist");
        
        services[serviceId].provider = provider;
        services[serviceId].unitPrice = unitPrice;
        services[serviceId].active = active;
        services[serviceId].metadataURI = metadataURI;
        services[serviceId].isVerified = isVerified;
        
        emit ServiceUpdated(serviceId, unitPrice, active, metadataURI, isVerified);
    }

    function getService(bytes32 serviceId) external view returns (Service memory) {
        return services[serviceId];
    }
}
