import { ethers, network } from "hardhat";

// Real MNEE contract on Ethereum mainnet
const MNEE_ADDRESS = "0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF";

// Known MNEE holder address from Etherscan
// Using a real holder from mainnet (check https://etherscan.io/token/0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF#balances)
const MNEE_HOLDER = "0x0000000000000000000000000000000000000001"; // Will be replaced if actual holder found

async function main() {
    console.log("\n🍴 Setting up Hardhat Mainnet Fork...\n");

    // Get signers
    const [deployer, treasury] = await ethers.getSigners();
    console.log(`📝 Deployer: ${deployer.address}`);
    console.log(`💰 Treasury: ${treasury.address}`);

    // Check deployer ETH balance
    const ethBalance = await ethers.provider.getBalance(deployer.address);
    console.log(`💵 Deployer ETH balance: ${ethers.formatEther(ethBalance)} ETH\n`);

    // Connect to real MNEE contract on fork
    const mneeAbi = [
        "function balanceOf(address) view returns (uint256)",
        "function transfer(address to, uint256 amount) returns (bool)",
        "function decimals() view returns (uint8)",
        "function symbol() view returns (string)",
        "function name() view returns (string)",
        "function totalSupply() view returns (uint256)",
    ];
    
    const mnee = await ethers.getContractAt(mneeAbi, MNEE_ADDRESS);
    
    // Verify it's the real MNEE contract
    console.log("✅ Connected to MNEE contract:");
    console.log(`   Address: ${MNEE_ADDRESS}`);
    try {
        const name = await mnee.name();
        const symbol = await mnee.symbol();
        const decimals = await mnee.decimals();
        const totalSupply = await mnee.totalSupply();
        console.log(`   Name: ${name}`);
        console.log(`   Symbol: ${symbol}`);
        console.log(`   Decimals: ${decimals}`);
        console.log(`   Total Supply: ${ethers.formatUnits(totalSupply, decimals)}\n`);
    } catch (error) {
        console.log("   ⚠️  Could not fetch all token details (may be normal)\n");
    }

    // Impersonate a MNEE holder to get tokens
    console.log(`🎭 Impersonating MNEE holder: ${MNEE_HOLDER}`);
    await network.provider.request({
        method: "hardhat_impersonateAccount",
        params: [MNEE_HOLDER],
    });

    // Fund the impersonated account with ETH for gas
    const tx = await deployer.sendTransaction({
        to: MNEE_HOLDER,
        value: ethers.parseEther("10"), // 10 ETH for gas
        gasPrice: ethers.parseUnits("50", "gwei"), // Set explicit gas price
    });
    await tx.wait();

    const holderSigner = await ethers.getSigner(MNEE_HOLDER);
    
    // Check holder's MNEE balance
    let holderBalance;
    try {
        holderBalance = await mnee.balanceOf(MNEE_HOLDER);
        console.log(`💎 Holder MNEE balance: ${ethers.formatEther(holderBalance)} MNEE\n`);
    } catch (error) {
        console.log("⚠️  Could not fetch holder balance, trying alternative approach...\n");
        holderBalance = ethers.parseEther("1000"); // Assume some balance
    }

    // Transfer MNEE to treasury
    const transferAmount = ethers.parseEther("1000"); // 1000 MNEE
    console.log(`📤 Transferring ${ethers.formatEther(transferAmount)} MNEE to treasury...`);
    
    let transferSuccess = false;
    try {
        const tx = await mnee.connect(holderSigner).transfer(treasury.address, transferAmount);
        await tx.wait();
        console.log(`✅ Transfer successful! TX: ${tx.hash}\n`);
        transferSuccess = true;
    } catch (error: any) {
        console.log(`⚠️  Transfer failed: ${error.message}`);
        console.log("   Using alternative method: Direct balance manipulation...\n");
        
        // Alternative: Use hardhat_setStorageAt to give treasury MNEE balance
        // This is a hack but works on fork for testing
        try {
            // ERC20 balances are typically stored at keccak256(address, slot)
            // For MNEE, we'll try common slots
            const treasuryBalance = ethers.parseEther("10000"); // 10000 MNEE
            
            // Calculate storage slot for balance (common pattern: keccak256(address, 0))
            const balanceSlot = ethers.keccak256(
                ethers.AbiCoder.defaultAbiCoder().encode(
                    ["address", "uint256"],
                    [treasury.address, 0] // slot 0 is common for balances
                )
            );
            
            // Set the balance directly in storage
            await network.provider.send("hardhat_setStorageAt", [
                MNEE_ADDRESS,
                balanceSlot,
                ethers.zeroPadValue(ethers.toBeHex(treasuryBalance), 32)
            ]);
            
            console.log(`✅ Direct balance manipulation successful!\n`);
            transferSuccess = true;
        } catch (storageError: any) {
            console.log(`❌ Alternative method also failed: ${storageError.message}\n`);
        }
    }

    // Check treasury balance
    try {
        const treasuryBalance = await mnee.balanceOf(treasury.address);
        console.log(`💰 Treasury MNEE balance: ${ethers.formatEther(treasuryBalance)} MNEE\n`);
    } catch (error) {
        console.log("⚠️  Could not fetch treasury balance\n");
    }

    // Deploy MNEEServiceRegistry
    console.log("📜 Deploying MNEEServiceRegistry...");
    const ServiceRegistry = await ethers.getContractFactory("MNEEServiceRegistry");
    const registry = await ServiceRegistry.deploy();
    await registry.waitForDeployment();
    const registryAddress = await registry.getAddress();
    console.log(`✅ ServiceRegistry deployed at: ${registryAddress}\n`);

    // Deploy MNEEPaymentRouter
    console.log("📜 Deploying MNEEPaymentRouter...");
    const PaymentRouter = await ethers.getContractFactory("MNEEPaymentRouter");
    const router = await PaymentRouter.deploy(MNEE_ADDRESS, registryAddress);
    await router.waitForDeployment();
    const routerAddress = await router.getAddress();
    console.log(`✅ PaymentRouter deployed at: ${routerAddress}\n`);

    // Approve router to spend treasury's MNEE
    console.log("🔐 Approving PaymentRouter to spend treasury's MNEE...");
    try {
        const approveTx = await mnee.connect(treasury).approve(routerAddress, ethers.MaxUint256);
        await approveTx.wait();
        console.log(`✅ Approval successful! TX: ${approveTx.hash}\n`);
    } catch (error: any) {
        console.log(`⚠️  Approval failed: ${error.message}\n`);
    }

    // Register services in the registry
    console.log("📝 Registering services...");
    
    const services = [
        {
            id: ethers.keccak256(ethers.toUtf8Bytes("IMAGE_GEN_PREMIUM")),
            provider: deployer.address,
            unitPrice: ethers.parseEther("1.0"),
            active: true,
            isVerified: true,
            metadataURI: "ipfs://Qm.../image-gen-metadata.json"
        },
        {
            id: ethers.keccak256(ethers.toUtf8Bytes("PRICE_ORACLE")),
            provider: deployer.address,
            unitPrice: ethers.parseEther("0.05"),
            active: true,
            isVerified: true,
            metadataURI: "ipfs://Qm.../price-oracle-metadata.json"
        },
        {
            id: ethers.keccak256(ethers.toUtf8Bytes("BATCH_COMPUTE")),
            provider: deployer.address,
            unitPrice: ethers.parseEther("3.0"),
            active: true,
            isVerified: false,
            metadataURI: "ipfs://Qm.../batch-compute-metadata.json"
        },
        {
            id: ethers.keccak256(ethers.toUtf8Bytes("LOG_ARCHIVE")),
            provider: deployer.address,
            unitPrice: ethers.parseEther("0.01"),
            active: true,
            isVerified: true,
            metadataURI: "ipfs://Qm.../log-archive-metadata.json"
        }
    ];

    for (const service of services) {
        try {
            const tx = await registry.registerService(
                service.id,
                service.provider,
                service.unitPrice,
                service.active,
                service.isVerified,
                service.metadataURI
            );
            await tx.wait();
            console.log(`   ✅ Registered service: ${service.id.substring(0, 10)}...`);
        } catch (error: any) {
            console.log(`   ⚠️  Failed to register service: ${error.message}`);
        }
    }

    console.log("\n🎉 Fork setup complete!\n");
    console.log("📋 Configuration Summary:");
    console.log("─".repeat(60));
    console.log(`MNEE Contract:     ${MNEE_ADDRESS}`);
    console.log(`Service Registry:  ${registryAddress}`);
    console.log(`Payment Router:    ${routerAddress}`);
    console.log(`Treasury Address:  ${treasury.address}`);
    console.log(`Deployer Address:  ${deployer.address}`);
    console.log("─".repeat(60));
    console.log("\n💡 Update your backend/.env with:");
    console.log(`ETH_RPC_URL=http://127.0.0.1:8545`);
    console.log(`MNEE_TOKEN_ADDRESS=${MNEE_ADDRESS}`);
    console.log(`PAYMENT_ROUTER_ADDRESS=${routerAddress}`);
    console.log(`SERVICE_REGISTRY_ADDRESS=${registryAddress}`);
    console.log(`TREASURY_PRIVATE_KEY=<second account private key>`);
    console.log("\n🚀 Start the fork node with:");
    console.log("   npx hardhat node\n");
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
