// SPDX-License-Identifier: MIT
/**
 * Deployment script for MNEE Nexus contracts
 * 
 * Deploys:
 * 1. MockMNEE token (for testing)
 * 2. MNEEServiceRegistry
 * 3. MNEEPaymentRouter
 * 4. Registers 4 service providers
 */

const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  console.log("====================================");
  console.log("MNEE Nexus Contract Deployment");
  console.log("====================================\n");

  const [deployer, imageGenProvider, priceOracleProvider, batchComputeProvider, logArchiveProvider] = await hre.ethers.getSigners();

  console.log("Deploying contracts with account:", deployer.address);
  console.log("Account balance:", (await hre.ethers.provider.getBalance(deployer.address)).toString(), "\n");

  // Deploy MockMNEE (or use existing MNEE on mainnet)
  const useMockMNEE = process.env.USE_MOCK_MNEE !== "false";
  let mneeAddress;

  if (useMockMNEE) {
    console.log("📝 Deploying MockMNEE token...");
    const MockMNEE = await hre.ethers.getContractFactory("MockMNEE");
    const mnee = await MockMNEE.deploy();
    await mnee.waitForDeployment();
    mneeAddress = await mnee.getAddress();
    console.log("✅ MockMNEE deployed to:", mneeAddress, "\n");
  } else {
    mneeAddress = process.env.MNEE_TOKEN_ADDRESS || "0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF";
    console.log("✅ Using existing MNEE token at:", mneeAddress, "\n");
  }

  // Deploy ServiceRegistry
  console.log("📝 Deploying MNEEServiceRegistry...");
  const ServiceRegistry = await hre.ethers.getContractFactory("MNEEServiceRegistry");
  const registry = await ServiceRegistry.deploy();
  await registry.waitForDeployment();
  const registryAddress = await registry.getAddress();
  console.log("✅ ServiceRegistry deployed to:", registryAddress, "\n");

  // Deploy PaymentRouter
  console.log("📝 Deploying MNEEPaymentRouter...");
  const PaymentRouter = await hre.ethers.getContractFactory("MNEEPaymentRouter");
  const router = await PaymentRouter.deploy(mneeAddress, registryAddress);
  await router.waitForDeployment();
  const routerAddress = await router.getAddress();
  console.log("✅ PaymentRouter deployed to:", routerAddress, "\n");

  // Register services
  console.log("📝 Registering services...\n");

  const services = [
    {
      name: "IMAGE_GEN_PREMIUM",
      provider: imageGenProvider,
      unitPrice: hre.ethers.parseUnits("1.0", 18) // 1.0 MNEE
    },
    {
      name: "PRICE_ORACLE",
      provider: priceOracleProvider,
      unitPrice: hre.ethers.parseUnits("0.05", 18) // 0.05 MNEE
    },
    {
      name: "BATCH_COMPUTE",
      provider: batchComputeProvider,
      unitPrice: hre.ethers.parseUnits("3.0", 18) // 3.0 MNEE
    },
    {
      name: "LOG_ARCHIVE",
      provider: logArchiveProvider,
      unitPrice: hre.ethers.parseUnits("0.01", 18) // 0.01 MNEE
    }
  ];

  for (const service of services) {
    const serviceId = hre.ethers.id(service.name);
    const tx = await registry.registerService(
      serviceId, 
      service.provider.address, 
      service.unitPrice,
      "ipfs://placeholder", // metadataURI
      true // isVerified
    );
    await tx.wait();
    
    console.log(`  ✅ ${service.name} registered`);
    console.log(`     Provider: ${service.provider.address}`);
    console.log(`     Price: ${hre.ethers.formatUnits(service.unitPrice, 18)} MNEE\n`);
  }

  // Save deployment addresses
  const deployment = {
    network: hre.network.name,
    timestamp: new Date().toISOString(),
    contracts: {
      mneeToken: mneeAddress,
      serviceRegistry: registryAddress,
      paymentRouter: routerAddress
    },
    accounts: {
      deployer: deployer.address,
      treasury: deployer.address, // In production, use a separate treasury
      providers: {
        imageGen: imageGenProvider.address,
        priceOracle: priceOracleProvider.address,
        batchCompute: batchComputeProvider.address,
        logArchive: logArchiveProvider.address
      }
    },
    services: services.map(s => ({
      name: s.name,
      id: hre.ethers.id(s.name),
      provider: s.provider.address,
      unitPrice: hre.ethers.formatUnits(s.unitPrice, 18)
    }))
  };

  const deploymentPath = path.join(__dirname, "../deployments.json");
  fs.writeFileSync(deploymentPath, JSON.stringify(deployment, null, 2));
  console.log("💾 Deployment info saved to:", deploymentPath, "\n");

  // Generate .env file content
  console.log("====================================");
  console.log("📋 Add these to your backend/.env:");
  console.log("====================================");
  console.log(`ETH_RPC_URL=${hre.network.config.url || "http://127.0.0.1:8545"}`);
  console.log(`MNEE_TOKEN_ADDRESS=${mneeAddress}`);
  console.log(`SERVICE_REGISTRY_ADDRESS=${registryAddress}`);
  console.log(`PAYMENT_ROUTER_ADDRESS=${routerAddress}`);
  console.log(`TREASURY_PRIVATE_KEY=${process.env.TREASURY_PRIVATE_KEY || deployer.privateKey || "YOUR_PRIVATE_KEY_HERE"}`);
  console.log("\n====================================");
  console.log("✅ Deployment Complete!");
  console.log("====================================\n");

  return deployment;
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
