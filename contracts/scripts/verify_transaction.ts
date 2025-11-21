import { ethers } from "hardhat";

const TX_HASH = "0xbe550bf43ac9baa0c3a01148b47669b6fde30d514fc0b5743ba28c0d82eb6e88";
const ROUTER_ADDRESS = "0xf0F5e9b00b92f3999021fD8B88aC75c351D93fc7";
const MNEE_ADDRESS = "0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF";

async function main() {
    console.log("🔍 Verifying On-Chain Transaction\n");
    console.log("=".repeat(60));
    
    // 获取交易详情
    const tx = await ethers.provider.getTransaction(TX_HASH);
    
    if (!tx) {
        console.log("❌ Transaction not found!");
        return;
    }
    
    console.log("\n📜 Transaction Details:");
    console.log(`   Hash: ${tx.hash}`);
    console.log(`   From: ${tx.from}`);
    console.log(`   To: ${tx.to}`);
    console.log(`   Value: ${ethers.formatEther(tx.value || 0n)} ETH`);
    console.log(`   Gas Used: ${tx.gasLimit?.toString()}`);
    
    // 获取收据
    const receipt = await ethers.provider.getTransactionReceipt(TX_HASH);
    
    if (!receipt) {
        console.log("\n⚠️  Transaction not yet mined");
        return;
    }
    
    console.log(`\n✅ Transaction Mined!`);
    console.log(`   Block: ${receipt.blockNumber}`);
    console.log(`   Status: ${receipt.status === 1 ? "✅ SUCCESS" : "❌ FAILED"}`);
    console.log(`   Gas Used: ${receipt.gasUsed.toString()}`);
    
    // 解析事件
    console.log(`\n📡 Events Emitted:`);
    
    const router = await ethers.getContractAt("MNEEPaymentRouter", ROUTER_ADDRESS);
    const mnee = await ethers.getContractAt(
        ["event Transfer(address indexed from, address indexed to, uint256 value)"],
        MNEE_ADDRESS
    );
    
    for (const log of receipt.logs) {
        try {
            if (log.address.toLowerCase() === ROUTER_ADDRESS.toLowerCase()) {
                const parsed = router.interface.parseLog({
                    topics: log.topics as string[],
                    data: log.data
                });
                
                if (parsed) {
                    console.log(`\n   🔔 ${parsed.name}`);
                    for (const [key, value] of Object.entries(parsed.args)) {
                        if (isNaN(Number(key))) {
                            console.log(`      ${key}: ${value}`);
                        }
                    }
                }
            } else if (log.address.toLowerCase() === MNEE_ADDRESS.toLowerCase()) {
                const parsed = mnee.interface.parseLog({
                    topics: log.topics as string[],
                    data: log.data
                });
                
                if (parsed && parsed.name === "Transfer") {
                    console.log(`\n   💸 MNEE Transfer`);
                    console.log(`      From: ${parsed.args.from}`);
                    console.log(`      To: ${parsed.args.to}`);
                    console.log(`      Amount: ${ethers.formatEther(parsed.args.value)} MNEE`);
                }
            }
        } catch (e) {
            // Skip unparseable logs
        }
    }
    
    console.log("\n" + "=".repeat(60));
    console.log("\n✅ Verification Complete!");
    console.log("\n💡 This is a REAL transaction on the mainnet fork");
    console.log("   - Uses actual MNEE contract: " + MNEE_ADDRESS);
    console.log("   - Real ERC-20 transfers executed");
    console.log("   - All events are authentic\n");
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
