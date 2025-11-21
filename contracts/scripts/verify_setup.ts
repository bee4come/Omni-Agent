import { ethers } from "hardhat";

const MNEE_ADDRESS = "0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF";
const REGISTRY_ADDRESS = "0xC1dC7a8379885676a6Ea08E67b7Defd9a235De71";
const ROUTER_ADDRESS = "0xf0F5e9b00b92f3999021fD8B88aC75c351D93fc7";
const TREASURY_ADDRESS = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8";

async function main() {
    console.log("🔍 Complete Setup Verification\n");
    console.log("=".repeat(60));

    // 1. MNEE Contract
    console.log("\n1️⃣ MNEE Contract");
    const mnee = await ethers.getContractAt(
        ["function name() view returns (string)", 
         "function symbol() view returns (string)",
         "function balanceOf(address) view returns (uint256)",
         "function allowance(address,address) view returns (uint256)"],
        MNEE_ADDRESS
    );
    
    const name = await mnee.name();
    const symbol = await mnee.symbol();
    console.log(`   Address: ${MNEE_ADDRESS}`);
    console.log(`   Name: ${name}`);
    console.log(`   Symbol: ${symbol}`);

    // 2. Treasury Balance & Allowance
    console.log("\n2️⃣ Treasury Status");
    const balance = await mnee.balanceOf(TREASURY_ADDRESS);
    const allowance = await mnee.allowance(TREASURY_ADDRESS, ROUTER_ADDRESS);
    console.log(`   Address: ${TREASURY_ADDRESS}`);
    console.log(`   Balance: ${ethers.formatEther(balance)} MNEE`);
    console.log(`   Router Allowance: ${allowance > ethers.parseEther("1000000") ? "UNLIMITED ✅" : ethers.formatEther(allowance)}`);

    // 3. Service Registry
    console.log("\n3️⃣ Service Registry");
    const registry = await ethers.getContractAt("MNEEServiceRegistry", REGISTRY_ADDRESS);
    console.log(`   Address: ${REGISTRY_ADDRESS}`);
    
    const services = ["IMAGE_GEN_PREMIUM", "PRICE_ORACLE", "BATCH_COMPUTE", "LOG_ARCHIVE"];
    let allActive = true;
    
    for (const serviceName of services) {
        const serviceId = ethers.keccak256(ethers.toUtf8Bytes(serviceName));
        const service = await registry.getService(serviceId);
        const status = service.active ? "✅ Active" : "❌ Inactive";
        console.log(`   ${serviceName}: ${status} (${ethers.formatEther(service.unitPrice)} MNEE)`);
        if (!service.active) allActive = false;
    }

    // 4. Payment Router
    console.log("\n4️⃣ Payment Router");
    const router = await ethers.getContractAt("MNEEPaymentRouter", ROUTER_ADDRESS);
    console.log(`   Address: ${ROUTER_ADDRESS}`);
    
    try {
        const routerMnee = await router.mneeToken();
        const routerRegistry = await router.serviceRegistry();
        console.log(`   MNEE Token: ${routerMnee === MNEE_ADDRESS ? "✅ Correct" : "❌ Mismatch"}`);
        console.log(`   Registry: ${routerRegistry === REGISTRY_ADDRESS ? "✅ Correct" : "❌ Mismatch"}`);
    } catch (error) {
        console.log(`   ⚠️  Could not verify router config`);
    }

    // 5. Overall Status
    console.log("\n" + "=".repeat(60));
    console.log("\n🎯 Overall Status:");
    
    const checks = [
        { name: "MNEE Contract Connected", status: true },
        { name: "Treasury Has MNEE", status: balance > 0n },
        { name: "Router Has Allowance", status: allowance > ethers.parseEther("1000") },
        { name: "Services Registered", status: allActive },
    ];
    
    let allGood = true;
    for (const check of checks) {
        console.log(`   ${check.status ? "✅" : "❌"} ${check.name}`);
        if (!check.status) allGood = false;
    }
    
    console.log("\n" + "=".repeat(60));
    
    if (allGood) {
        console.log("\n🎉 SETUP COMPLETE! Ready to process payments!\n");
        console.log("Next steps:");
        console.log("1. Start backend: cd backend && uvicorn app.main:app --reload");
        console.log("2. Test payment: curl -X POST http://localhost:8000/chat \\");
        console.log("   -H 'Content-Type: application/json' \\");
        console.log("   -d '{\"agent_id\":\"user-agent\",\"message\":\"Generate an avatar\"}'\n");
    } else {
        console.log("\n⚠️  Some issues found. Please review above.\n");
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
