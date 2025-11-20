import { ethers } from "hardhat";

async function main() {
    const [deployer] = await ethers.getSigners();

    // REPLACE THESE WITH YOUR DEPLOYED ADDRESSES IF RUNNING SEPARATELY
    // For now, we assume we might run this right after deploy or hardcode for local dev
    // This script expects environment variables or you can paste addresses here.
    const REGISTRY_ADDRESS = process.env.SERVICE_REGISTRY_ADDRESS;

    if (!REGISTRY_ADDRESS) {
        console.error("Please set SERVICE_REGISTRY_ADDRESS env var");
        return;
    }

    const registry = await ethers.getContractAt("MNEEServiceRegistry", REGISTRY_ADDRESS);

    const services = [
        {
            id: "IMAGE_GEN_PREMIUM",
            price: ethers.parseUnits("1.0", 18), // 1.0 MNEE
            provider: deployer.address // For demo, deployer is the provider
        },
        {
            id: "PRICE_ORACLE",
            price: ethers.parseUnits("0.05", 18), // 0.05 MNEE
            provider: deployer.address
        },
        {
            id: "BATCH_COMPUTE",
            price: ethers.parseUnits("3.0", 18), // 3.0 MNEE
            provider: deployer.address
        },
        {
            id: "LOG_ARCHIVE",
            price: ethers.parseUnits("0.01", 18), // 0.01 MNEE
            provider: deployer.address
        }
    ];

    for (const service of services) {
        const idBytes = ethers.keccak256(ethers.toUtf8Bytes(service.id));
        console.log(`Registering service: ${service.id} (${idBytes})`);

        // Check if exists (optional, simplified here)
        try {
            const tx = await registry.registerService(idBytes, service.price);
            await tx.wait();
            console.log(`Registered ${service.id}`);
        } catch (e) {
            console.log(`Service ${service.id} might already exist or failed:`, e);
        }
    }
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
