import { ethers, network } from "hardhat";

const MNEE_ADDRESS = "0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF";
const TREASURY_ADDRESS = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"; // Account #1

async function main() {
    console.log("💰 Funding Treasury with MNEE...\n");

    const mneeAbi = [
        "function balanceOf(address) view returns (uint256)",
        "function totalSupply() view returns (uint256)",
    ];
    
    const mnee = await ethers.getContractAt(mneeAbi, MNEE_ADDRESS);

    // Check current balance
    let balance = await mnee.balanceOf(TREASURY_ADDRESS);
    console.log(`📊 Current Treasury balance: ${ethers.formatEther(balance)} MNEE`);

    // Set a large balance using storage manipulation
    const desiredBalance = ethers.parseEther("100000"); // 100,000 MNEE
    
    console.log(`🔧 Setting Treasury balance to ${ethers.formatEther(desiredBalance)} MNEE...\n`);

    // Try different common storage slot patterns for ERC20 balances
    const slots = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
    
    for (const slot of slots) {
        try {
            // Calculate storage slot: keccak256(abi.encode(address, slot))
            const balanceSlot = ethers.keccak256(
                ethers.AbiCoder.defaultAbiCoder().encode(
                    ["address", "uint256"],
                    [TREASURY_ADDRESS, slot]
                )
            );
            
            // Set the balance
            await network.provider.send("hardhat_setStorageAt", [
                MNEE_ADDRESS,
                balanceSlot,
                ethers.zeroPadValue(ethers.toBeHex(desiredBalance), 32)
            ]);
            
            // Check if it worked
            const newBalance = await mnee.balanceOf(TREASURY_ADDRESS);
            
            if (newBalance > balance) {
                console.log(`✅ Success! Balance set via slot ${slot}`);
                console.log(`💰 New Treasury balance: ${ethers.formatEther(newBalance)} MNEE\n`);
                
                // Also approve the router
                const ROUTER_ADDRESS = "0xf0F5e9b00b92f3999021fD8B88aC75c351D93fc7";
                const approveSlot = ethers.keccak256(
                    ethers.AbiCoder.defaultAbiCoder().encode(
                        ["address", "uint256"],
                        [ROUTER_ADDRESS, slot]
                    )
                );
                
                // Create nested mapping slot: mapping(owner => mapping(spender => amount))
                // This might be slot+1 for allowances
                const allowanceSlot = ethers.keccak256(
                    ethers.AbiCoder.defaultAbiCoder().encode(
                        ["address", "bytes32"],
                        [ROUTER_ADDRESS, ethers.keccak256(
                            ethers.AbiCoder.defaultAbiCoder().encode(
                                ["address", "uint256"],
                                [TREASURY_ADDRESS, slot + 1]
                            )
                        )]
                    )
                );
                
                console.log(`🔓 Setting Router approval...\n`);
                return;
            }
        } catch (error) {
            // Continue to next slot
        }
    }
    
    console.log("⚠️  Could not set balance automatically.");
    console.log("💡 Alternative: Use MNEE SDK to transfer from a real holder\n");
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
