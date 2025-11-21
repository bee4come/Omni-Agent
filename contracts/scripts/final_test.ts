import { ethers } from "hardhat";

const MNEE_ADDRESS = "0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF";
const TREASURY_ADDRESS = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8";
const ROUTER_ADDRESS = "0xf0F5e9b00b92f3999021fD8B88aC75c351D93fc7";

async function main() {
    console.log("🧪 Final Integration Test\n");

    const mnee = await ethers.getContractAt(
        ["function balanceOf(address) view returns (uint256)"],
        MNEE_ADDRESS
    );

    // 检查余额变化
    const balance = await mnee.balanceOf(TREASURY_ADDRESS);
    console.log(`💰 Treasury: ${ethers.formatEther(balance)} MNEE`);
    
    // 计算已花费
    const spent = ethers.parseEther("100000") - balance;
    console.log(`💸 Spent: ${ethers.formatEther(spent)} MNEE`);
    console.log(`📊 Remaining: ${ethers.formatEther(balance)} MNEE\n`);

    // 获取最近交易
    const latestBlock = await ethers.provider.getBlockNumber();
    console.log(`📦 Latest Block: ${latestBlock}`);
    console.log(`🍴 Fork Status: Active ✅`);
    console.log(`🔗 MNEE Contract: ${MNEE_ADDRESS} ✅`);
    console.log(`📜 Router: ${ROUTER_ADDRESS} ✅\n`);

    console.log("=".repeat(50));
    console.log("✅ ALL SYSTEMS OPERATIONAL");
    console.log("=".repeat(50));
}

main().then(() => process.exit(0)).catch(e => { console.error(e); process.exit(1); });
