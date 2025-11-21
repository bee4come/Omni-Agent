import { ethers } from "hardhat";

const REGISTRY_ADDRESS = "0xC1dC7a8379885676a6Ea08E67b7Defd9a235De71";

async function main() {
    console.log("📝 Registering Services...\n");

    const [deployer] = await ethers.getSigners();
    console.log(`Deployer/Owner: ${deployer.address}\n`);

    const registry = await ethers.getContractAt("MNEEServiceRegistry", REGISTRY_ADDRESS);

    // 服务配置 - 和后端 config/services.yaml 保持一致
    const services = [
        {
            name: "IMAGE_GEN_PREMIUM",
            provider: deployer.address, // 使用 deployer 作为 provider
            unitPrice: ethers.parseEther("1.0"), // 1 MNEE per call
            metadataURI: "ipfs://QmImageGenMetadata",
            isVerified: true
        },
        {
            name: "PRICE_ORACLE",
            provider: deployer.address,
            unitPrice: ethers.parseEther("0.05"), // 0.05 MNEE per call
            metadataURI: "ipfs://QmPriceOracleMetadata",
            isVerified: true
        },
        {
            name: "BATCH_COMPUTE",
            provider: deployer.address,
            unitPrice: ethers.parseEther("3.0"), // 3 MNEE per call
            metadataURI: "ipfs://QmBatchComputeMetadata",
            isVerified: false
        },
        {
            name: "LOG_ARCHIVE",
            provider: deployer.address,
            unitPrice: ethers.parseEther("0.01"), // 0.01 MNEE per call
            metadataURI: "ipfs://QmLogArchiveMetadata",
            isVerified: true
        }
    ];

    for (const service of services) {
        const serviceId = ethers.keccak256(ethers.toUtf8Bytes(service.name));
        
        console.log(`Registering: ${service.name}`);
        console.log(`  Service ID: ${serviceId}`);
        console.log(`  Provider: ${service.provider}`);
        console.log(`  Unit Price: ${ethers.formatEther(service.unitPrice)} MNEE`);
        
        try {
            const tx = await registry.registerService(
                serviceId,
                service.provider,
                service.unitPrice,
                service.metadataURI,
                service.isVerified
            );
            
            const receipt = await tx.wait();
            console.log(`  ✅ Registered! TX: ${receipt?.hash}\n`);
        } catch (error: any) {
            console.log(`  ❌ Failed: ${error.message}\n`);
        }
    }

    console.log("🎉 Service registration complete!\n");
    console.log("Verifying registrations...\n");

    // 验证所有服务
    for (const service of services) {
        const serviceId = ethers.keccak256(ethers.toUtf8Bytes(service.name));
        const registered = await registry.getService(serviceId);
        
        if (registered.provider !== ethers.ZeroAddress) {
            console.log(`✅ ${service.name}: Active=${registered.active}, Price=${ethers.formatEther(registered.unitPrice)} MNEE`);
        } else {
            console.log(`❌ ${service.name}: NOT FOUND`);
        }
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
