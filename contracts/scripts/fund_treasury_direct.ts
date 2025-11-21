import { ethers, network } from "hardhat";

const MNEE_ADDRESS = "0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF";
const TREASURY_ADDRESS = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"; // Account #1 from Hardhat
const ROUTER_ADDRESS = "0xf0F5e9b00b92f3999021fD8B88aC75c351D93fc7";

async function main() {
    console.log("💰 Funding Treasury with MNEE (Direct Storage Method)...\n");

    const mneeAbi = [
        "function balanceOf(address) view returns (uint256)",
        "function allowance(address,address) view returns (uint256)",
    ];
    
    const mnee = await ethers.getContractAt(mneeAbi, MNEE_ADDRESS);

    // Check current balance
    let balance = await mnee.balanceOf(TREASURY_ADDRESS);
    console.log(`📊 Current Treasury balance: ${ethers.formatEther(balance)} MNEE`);

    const desiredBalance = ethers.parseEther("100000"); // 100,000 MNEE
    console.log(`🎯 Target balance: ${ethers.formatEther(desiredBalance)} MNEE\n`);

    // ERC20 通常将 balances 存储在 mapping(address => uint256) 中
    // 存储位置 = keccak256(address + slot)
    // 我们尝试常见的 slot 位置

    console.log("🔧 Trying to set balance via storage manipulation...\n");

    const slots = [0, 1, 2, 3, 51, 52]; // 常见的 balance mapping slots
    
    for (const slot of slots) {
        try {
            // 计算存储位置
            const index = ethers.solidityPackedKeccak256(
                ["uint256", "uint256"],
                [TREASURY_ADDRESS, slot]
            );
            
            // 设置余额
            await network.provider.send("hardhat_setStorageAt", [
                MNEE_ADDRESS,
                index,
                ethers.zeroPadValue(ethers.toBeHex(desiredBalance), 32)
            ]);
            
            // 验证是否成功
            const newBalance = await mnee.balanceOf(TREASURY_ADDRESS);
            
            if (newBalance >= desiredBalance / 2n) { // 如果余额显著增加
                console.log(`✅ Success with slot ${slot}!`);
                console.log(`💰 New Treasury balance: ${ethers.formatEther(newBalance)} MNEE\n`);
                
                // 也设置 allowance for Router
                console.log(`🔓 Setting unlimited allowance for Router...\n`);
                
                // allowance 通常在 mapping(address => mapping(address => uint256))
                // 存储位置 = keccak256(spender + keccak256(owner + slot+1))
                const allowanceSlot = slot + 1;
                const innerHash = ethers.solidityPackedKeccak256(
                    ["uint256", "uint256"],
                    [TREASURY_ADDRESS, allowanceSlot]
                );
                const allowanceIndex = ethers.solidityPackedKeccak256(
                    ["uint256", "bytes32"],
                    [ROUTER_ADDRESS, innerHash]
                );
                
                const maxApproval = ethers.MaxUint256;
                await network.provider.send("hardhat_setStorageAt", [
                    MNEE_ADDRESS,
                    allowanceIndex,
                    ethers.zeroPadValue(ethers.toBeHex(maxApproval), 32)
                ]);
                
                const allowance = await mnee.allowance(TREASURY_ADDRESS, ROUTER_ADDRESS);
                console.log(`✅ Router allowance: ${ethers.formatEther(allowance)} MNEE\n`);
                
                return; // 成功，退出
            }
        } catch (error) {
            // 继续尝试下一个 slot
        }
    }
    
    console.log("⚠️  Could not set balance with common slots.");
    console.log("💡 Trying alternative: Use treasury signer to approve\n");
    
    // 备选方案：即使余额为 0，也先设置 approval
    // 这样至少合约调用不会因为 allowance 失败
    const [, treasury] = await ethers.getSigners();
    const mneeWithSigner = await ethers.getContractAt(
        ["function approve(address,uint256) returns (bool)"],
        MNEE_ADDRESS,
        treasury
    );
    
    try {
        console.log("Approving Router from Treasury...");
        const tx = await mneeWithSigner.approve(ROUTER_ADDRESS, ethers.MaxUint256);
        await tx.wait();
        console.log("✅ Approval set!\n");
    } catch (error: any) {
        console.log(`⚠️  Approval failed: ${error.message}\n`);
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
