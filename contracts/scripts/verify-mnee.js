/**
 * Verify Real MNEE Token on Mainnet Fork
 *
 * Run: npx hardhat run scripts/verify-mnee.js --network localhost
 */

const hre = require("hardhat");

const MNEE_ADDRESS = "0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF";

async function main() {
    console.log("=".repeat(50));
    console.log("Verifying Real MNEE Token on Mainnet Fork");
    console.log("=".repeat(50));

    // Connect to MNEE token
    const mnee = await hre.ethers.getContractAt(
        ["function name() view returns (string)",
         "function symbol() view returns (string)",
         "function decimals() view returns (uint8)",
         "function totalSupply() view returns (uint256)",
         "function balanceOf(address) view returns (uint256)"],
        MNEE_ADDRESS
    );

    // Get token info
    console.log("\nMNEE Token Info:");
    console.log(`  Address: ${MNEE_ADDRESS}`);

    try {
        const name = await mnee.name();
        const symbol = await mnee.symbol();
        const decimals = await mnee.decimals();
        const totalSupply = await mnee.totalSupply();

        console.log(`  Name: ${name}`);
        console.log(`  Symbol: ${symbol}`);
        console.log(`  Decimals: ${decimals}`);
        console.log(`  Total Supply: ${hre.ethers.formatUnits(totalSupply, decimals)} ${symbol}`);

        console.log("\n✅ SUCCESS: Connected to real MNEE token on mainnet fork!");
        console.log("\nYou can now deploy contracts that interact with real MNEE.");

    } catch (e) {
        console.log("\n❌ FAILED: Could not connect to MNEE token");
        console.log("Error:", e.message);
        console.log("\nMake sure:");
        console.log("1. You have ETH_MAINNET_RPC_URL set in contracts/.env");
        console.log("2. Hardhat node is running with fork enabled");
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
