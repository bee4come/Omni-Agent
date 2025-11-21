import { ethers } from "hardhat";

const MNEE_ADDRESS = "0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF";

// 从 Etherscan 上查到的一些可能的持有者地址
// https://etherscan.io/token/0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF#balances
const CANDIDATE_HOLDERS = [
    "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",  // Example holder
    "0x1234567890123456789012345678901234567890",  // Placeholder
    // 需要从 Etherscan 获取真实地址
];

async function main() {
    console.log("🔍 Finding MNEE holders on mainnet fork...\n");

    const mneeAbi = [
        "function balanceOf(address) view returns (uint256)",
        "function decimals() view returns (uint8)",
        "function symbol() view returns (string)",
    ];
    
    const mnee = await ethers.getContractAt(mneeAbi, MNEE_ADDRESS);
    
    try {
        const decimals = await mnee.decimals();
        const symbol = await mnee.symbol();
        console.log(`✅ Connected to ${symbol} (${decimals} decimals)\n`);
    } catch (error) {
        console.log("Could not fetch token info\n");
    }

    console.log("Checking candidate addresses...\n");
    
    let bestHolder = null;
    let maxBalance = 0n;

    for (const address of CANDIDATE_HOLDERS) {
        try {
            const balance = await mnee.balanceOf(address);
            const balanceFormatted = ethers.formatEther(balance);
            
            console.log(`${address}: ${balanceFormatted} MNEE`);
            
            if (balance > maxBalance) {
                maxBalance = balance;
                bestHolder = address;
            }
        } catch (error: any) {
            console.log(`${address}: Error - ${error.message}`);
        }
    }

    console.log("\n" + "=".repeat(60));
    
    if (bestHolder && maxBalance > 0n) {
        console.log(`\n✅ Best holder found: ${bestHolder}`);
        console.log(`   Balance: ${ethers.formatEther(maxBalance)} MNEE\n`);
    } else {
        console.log("\n⚠️  No holders found with balance > 0");
        console.log("\n📝 Manual steps:");
        console.log("1. Visit: https://etherscan.io/token/0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF#balances");
        console.log("2. Click 'Holders' tab");
        console.log("3. Copy any address with MNEE balance");
        console.log("4. Use it in fund_treasury_from_holder.ts\n");
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
