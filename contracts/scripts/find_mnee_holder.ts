import { ethers } from "hardhat";

const MNEE_ADDRESS = "0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF";

/**
 * This script helps find a real MNEE holder address from the mainnet fork.
 * We'll try some common DeFi protocol addresses and check their MNEE balance.
 */
async function main() {
    console.log("🔍 Searching for MNEE holders on mainnet fork...\n");

    const mneeAbi = [
        "function balanceOf(address) view returns (uint256)",
        "function decimals() view returns (uint8)",
    ];
    
    const mnee = await ethers.getContractAt(mneeAbi, MNEE_ADDRESS);
    
    // Common addresses that might hold MNEE
    // These are typically DEX contracts, treasury addresses, or large holders
    const candidateAddresses = [
        "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", // Example
        "0x0000000000000000000000000000000000000000", // Burn address (often has tokens)
        // Add more addresses from Etherscan token holders page
    ];

    console.log("Checking candidate addresses...\n");
    
    let foundHolder = null;
    let maxBalance = BigInt(0);

    for (const address of candidateAddresses) {
        try {
            const balance = await mnee.balanceOf(address);
            const balanceFormatted = ethers.formatEther(balance);
            
            if (balance > BigInt(0)) {
                console.log(`✅ ${address}: ${balanceFormatted} MNEE`);
                
                if (balance > maxBalance) {
                    maxBalance = balance;
                    foundHolder = address;
                }
            } else {
                console.log(`   ${address}: 0 MNEE`);
            }
        } catch (error) {
            console.log(`⚠️  ${address}: Could not check balance`);
        }
    }

    console.log("\n" + "─".repeat(60));
    if (foundHolder) {
        console.log(`\n🎯 Best holder found: ${foundHolder}`);
        console.log(`   Balance: ${ethers.formatEther(maxBalance)} MNEE`);
        console.log(`\n💡 Use this address in setup_fork.ts:`);
        console.log(`   const MNEE_HOLDER = "${foundHolder}";\n`);
    } else {
        console.log("\n⚠️  No holders found with balance > 0");
        console.log("\n📝 Manual steps:");
        console.log("1. Go to https://etherscan.io/token/0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF");
        console.log("2. Click 'Holders' tab");
        console.log("3. Copy any address with significant MNEE balance");
        console.log("4. Update MNEE_HOLDER in setup_fork.ts\n");
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
