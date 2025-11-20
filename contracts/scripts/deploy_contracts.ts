import { ethers } from "hardhat";

async function main() {
    const [deployer] = await ethers.getSigners();
    console.log("Deploying contracts with the account:", deployer.address);

    // 1. Deploy MNEE Token (Mock) OR use existing
    // For local testing, we always deploy a mock.
    // For production, we would use the address provided: 0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF
    let mneeAddress;
    const network = await ethers.provider.getNetwork();

    if (network.chainId === 31337n) { // Hardhat Network
        console.log("Local network detected. Deploying MockMNEE...");
        const MockMNEE = await ethers.getContractFactory("MockMNEE");
        const mockMNEE = await MockMNEE.deploy();
        await mockMNEE.waitForDeployment();
        mneeAddress = await mockMNEE.getAddress();
        console.log("MockMNEE deployed to:", mneeAddress);
    } else {
        // Assume mainnet or testnet where we use the real token
        mneeAddress = "0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF";
        console.log("Using existing MNEE Token at:", mneeAddress);
    }

    // 2. Deploy ServiceRegistry
    const ServiceRegistry = await ethers.getContractFactory("MNEEServiceRegistry");
    const registry = await ServiceRegistry.deploy();
    await registry.waitForDeployment();
    const registryAddress = await registry.getAddress();
    console.log("MNEEServiceRegistry deployed to:", registryAddress);

    // 3. Deploy PaymentRouter
    const PaymentRouter = await ethers.getContractFactory("MNEEPaymentRouter");
    const router = await PaymentRouter.deploy(mneeAddress, registryAddress);
    await router.waitForDeployment();
    const routerAddress = await router.getAddress();
    console.log("MNEEPaymentRouter deployed to:", routerAddress);

    // Output for frontend/backend
    console.log("\n--- Deployment Summary ---");
    console.log("MNEE_TOKEN_ADDRESS=" + mneeAddress);
    console.log("SERVICE_REGISTRY_ADDRESS=" + registryAddress);
    console.log("PAYMENT_ROUTER_ADDRESS=" + routerAddress);
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
