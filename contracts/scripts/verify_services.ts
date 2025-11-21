import { ethers } from "hardhat";

const REGISTRY_ADDRESS = "0xC1dC7a8379885676a6Ea08E67b7Defd9a235De71";

async function main() {
    console.log("🔍 Verifying Service Registration Status...\n");

    const registry = await ethers.getContractAt("MNEEServiceRegistry", REGISTRY_ADDRESS);

    // 这些是后端配置文件中使用的服务 ID
    const serviceNames = [
        "IMAGE_GEN_PREMIUM",
        "PRICE_ORACLE",
        "BATCH_COMPUTE",
        "LOG_ARCHIVE"
    ];

    console.log("📋 Checking services in registry:\n");

    for (const name of serviceNames) {
        // 用和后端一样的方式计算 serviceId
        const serviceId = ethers.keccak256(ethers.toUtf8Bytes(name));
        
        console.log(`Service: ${name}`);
        console.log(`  ID: ${serviceId}`);
        
        try {
            const service = await registry.getService(serviceId);
            
            if (service.provider === ethers.ZeroAddress) {
                console.log(`  ❌ NOT REGISTERED\n`);
            } else {
                console.log(`  ✅ REGISTERED`);
                console.log(`     Provider: ${service.provider}`);
                console.log(`     Unit Price: ${ethers.formatEther(service.unitPrice)} MNEE`);
                console.log(`     Active: ${service.active}`);
                console.log(`     Verified: ${service.isVerified}`);
                console.log(`     Metadata: ${service.metadataURI}\n`);
            }
        } catch (error: any) {
            console.log(`  ❌ ERROR: ${error.message}\n`);
        }
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
