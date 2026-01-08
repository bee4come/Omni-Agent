/**
 * Setup Mainnet Fork for Testing with Real MNEE
 *
 * This script:
 * 1. Impersonates a MNEE holder to get test tokens
 * 2. Deploys our contracts
 * 3. Funds the treasury with MNEE
 *
 * Usage:
 *   npx hardhat run scripts/setup-mainnet-fork.js --network localhost
 */

const hre = require("hardhat");

// Real MNEE contract on Ethereum Mainnet
const MNEE_TOKEN_ADDRESS = "0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF";

// Known MNEE holder (from Etherscan - pick one with balance)
// You can find holders at: https://etherscan.io/token/0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF#balances
const MNEE_WHALE = "0x1234567890123456789012345678901234567890"; // Replace with actual holder

async function main() {
    console.log("=".repeat(60));
    console.log("MNEE Mainnet Fork Setup");
    console.log("=".repeat(60));

    const [deployer, treasury, provider1, provider2] = await hre.ethers.getSigners();

    console.log("\n[1/6] Network Info");
    console.log(`  Network: ${hre.network.name}`);
    console.log(`  Chain ID: ${(await hre.ethers.provider.getNetwork()).chainId}`);
    console.log(`  Deployer: ${deployer.address}`);
    console.log(`  Treasury: ${treasury.address}`);

    // Connect to real MNEE token
    console.log("\n[2/6] Connecting to Real MNEE Token");
    const mneeToken = await hre.ethers.getContractAt("IERC20", MNEE_TOKEN_ADDRESS);
    const totalSupply = await mneeToken.totalSupply();
    console.log(`  MNEE Address: ${MNEE_TOKEN_ADDRESS}`);
    console.log(`  Total Supply: ${hre.ethers.formatEther(totalSupply)} MNEE`);

    // Try to impersonate a whale and transfer MNEE
    console.log("\n[3/6] Getting Test MNEE via Impersonation");

    // First, let's find a holder by checking some known addresses
    // Or we can mint via impersonating the contract owner if it has mint function
    try {
        // Check if deployer has any MNEE
        const deployerBalance = await mneeToken.balanceOf(deployer.address);
        console.log(`  Deployer MNEE Balance: ${hre.ethers.formatEther(deployerBalance)} MNEE`);

        if (deployerBalance < hre.ethers.parseEther("100")) {
            console.log("  Attempting to get MNEE from whale...");

            // Try to find a whale address by checking top holders
            // This is a sample - replace with actual whale address from Etherscan
            const potentialWhales = [
                "0x40ec5b33f54e0e8a33a975908c5ba1c14e5bbbdf", // Polygon Bridge
                "0x8eb8a3b98659cce290402893d0123abb75e3ab28", // Avalanche Bridge
            ];

            for (const whaleAddress of potentialWhales) {
                try {
                    const whaleBalance = await mneeToken.balanceOf(whaleAddress);
                    console.log(`  Checking ${whaleAddress}: ${hre.ethers.formatEther(whaleBalance)} MNEE`);

                    if (whaleBalance > hre.ethers.parseEther("1000")) {
                        // Impersonate this whale
                        await hre.network.provider.request({
                            method: "hardhat_impersonateAccount",
                            params: [whaleAddress],
                        });

                        // Fund whale with ETH for gas
                        await deployer.sendTransaction({
                            to: whaleAddress,
                            value: hre.ethers.parseEther("1"),
                        });

                        const whale = await hre.ethers.getSigner(whaleAddress);

                        // Transfer MNEE to treasury
                        const transferAmount = hre.ethers.parseEther("10000");
                        await mneeToken.connect(whale).transfer(treasury.address, transferAmount);

                        console.log(`  Transferred ${hre.ethers.formatEther(transferAmount)} MNEE to treasury`);

                        // Stop impersonating
                        await hre.network.provider.request({
                            method: "hardhat_stopImpersonatingAccount",
                            params: [whaleAddress],
                        });

                        break;
                    }
                } catch (e) {
                    console.log(`  Failed with ${whaleAddress}: ${e.message}`);
                }
            }
        }
    } catch (e) {
        console.log(`  Warning: Could not impersonate whale: ${e.message}`);
        console.log("  Using MockMNEE instead...");
    }

    // Deploy our contracts
    console.log("\n[4/6] Deploying Contracts");

    // Deploy ServiceRegistry
    const ServiceRegistry = await hre.ethers.getContractFactory("MNEEServiceRegistry");
    const registry = await ServiceRegistry.deploy();
    await registry.waitForDeployment();
    console.log(`  ServiceRegistry: ${await registry.getAddress()}`);

    // Deploy PaymentRouter (using real MNEE)
    const PaymentRouter = await hre.ethers.getContractFactory("MNEEPaymentRouter");
    const router = await PaymentRouter.deploy(MNEE_TOKEN_ADDRESS, await registry.getAddress());
    await router.waitForDeployment();
    console.log(`  PaymentRouter: ${await router.getAddress()}`);

    // Deploy AgentWallet
    const AgentWallet = await hre.ethers.getContractFactory("MNEEAgentWallet");
    const wallet = await AgentWallet.deploy(MNEE_TOKEN_ADDRESS);
    await wallet.waitForDeployment();
    console.log(`  AgentWallet: ${await wallet.getAddress()}`);

    // Deploy Escrow
    const Escrow = await hre.ethers.getContractFactory("MNEEEscrow");
    const escrow = await Escrow.deploy(MNEE_TOKEN_ADDRESS);
    await escrow.waitForDeployment();
    console.log(`  Escrow: ${await escrow.getAddress()}`);

    // Register services
    console.log("\n[5/6] Registering Services");

    const services = [
        { id: "IMAGE_GEN_PREMIUM", price: "1.0", provider: provider1.address },
        { id: "PRICE_ORACLE", price: "0.05", provider: provider1.address },
        { id: "BATCH_COMPUTE", price: "3.0", provider: provider2.address },
        { id: "LOG_ARCHIVE", price: "0.01", provider: provider2.address },
    ];

    for (const svc of services) {
        const serviceId = hre.ethers.keccak256(hre.ethers.toUtf8Bytes(svc.id));
        await registry.registerService(
            serviceId,
            svc.provider,
            hre.ethers.parseEther(svc.price),
            `ipfs://mnee/${svc.id}`,
            true
        );
        console.log(`  Registered ${svc.id} @ ${svc.price} MNEE`);
    }

    // Register agents
    console.log("\n[6/6] Registering Agents");

    const agents = ["user-agent", "batch-agent", "ops-agent", "merchant-agent"];
    for (const agentId of agents) {
        await wallet.registerAgent(agentId, agentId);
        console.log(`  Registered ${agentId}`);
    }

    // Fund agents with MNEE
    const treasuryBalance = await mneeToken.balanceOf(treasury.address);
    if (treasuryBalance > 0) {
        console.log("\n  Funding agents with MNEE...");
        await mneeToken.connect(treasury).approve(await wallet.getAddress(), treasuryBalance);

        const fundAmount = hre.ethers.parseEther("100");
        for (const agentId of agents) {
            try {
                await wallet.connect(treasury).fundAgent(agentId, fundAmount);
                console.log(`  Funded ${agentId} with 100 MNEE`);
            } catch (e) {
                console.log(`  Could not fund ${agentId}: ${e.message}`);
            }
        }
    }

    // Print summary
    console.log("\n" + "=".repeat(60));
    console.log("DEPLOYMENT SUMMARY");
    console.log("=".repeat(60));
    console.log(`
# Add these to backend/.env:
ETH_RPC_URL=http://127.0.0.1:8545
MNEE_TOKEN_ADDRESS=${MNEE_TOKEN_ADDRESS}
PAYMENT_ROUTER_ADDRESS=${await router.getAddress()}
SERVICE_REGISTRY_ADDRESS=${await registry.getAddress()}
AGENT_WALLET_ADDRESS=${await wallet.getAddress()}
ESCROW_ADDRESS=${await escrow.getAddress()}
TREASURY_PRIVATE_KEY=${treasury.privateKey || "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"}
`);

    // Check final balances
    console.log("\nFinal Treasury MNEE Balance:", hre.ethers.formatEther(await mneeToken.balanceOf(treasury.address)));
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
