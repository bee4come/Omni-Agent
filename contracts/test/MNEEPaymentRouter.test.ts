import { expect } from "chai";
import { ethers } from "hardhat";
import { MNEEPaymentRouter, MNEEServiceRegistry, MockMNEE } from "../typechain-types";
import { SignerWithAddress } from "@nomicfoundation/hardhat-ethers/signers";

describe("MNEEPaymentRouter", function () {
  let router: MNEEPaymentRouter;
  let registry: MNEEServiceRegistry;
  let mneeToken: MockMNEE;
  let owner: SignerWithAddress;
  let treasury: SignerWithAddress;
  let provider: SignerWithAddress;

  const SERVICE_ID = ethers.keccak256(ethers.toUtf8Bytes("IMAGE_GEN_PREMIUM"));
  const UNIT_PRICE = ethers.parseEther("1.0");
  const METADATA_URI = "ipfs://QmTest123";
  const INITIAL_BALANCE = ethers.parseEther("1000");

  beforeEach(async function () {
    [owner, treasury, provider] = await ethers.getSigners();

    // Deploy MockMNEE token
    const MockMNEEFactory = await ethers.getContractFactory("MockMNEE");
    mneeToken = await MockMNEEFactory.deploy();

    // Deploy ServiceRegistry
    const RegistryFactory = await ethers.getContractFactory("MNEEServiceRegistry");
    registry = await RegistryFactory.deploy();

    // Deploy PaymentRouter
    const RouterFactory = await ethers.getContractFactory("MNEEPaymentRouter");
    router = await RouterFactory.deploy(await mneeToken.getAddress(), await registry.getAddress());

    // Register a service
    await registry.registerService(SERVICE_ID, provider.address, UNIT_PRICE, METADATA_URI, true);

    // Fund treasury with MNEE tokens
    await mneeToken.mint(treasury.address, INITIAL_BALANCE);

    // Treasury approves router to spend MNEE
    await mneeToken.connect(treasury).approve(await router.getAddress(), INITIAL_BALANCE);
  });

  describe("Deployment", function () {
    it("Should set correct MNEE token address", async function () {
      expect(await router.mneeToken()).to.equal(await mneeToken.getAddress());
    });

    it("Should set correct registry address", async function () {
      expect(await router.registry()).to.equal(await registry.getAddress());
    });
  });

  describe("Pay for Service", function () {
    const AGENT_ID = "user-agent";
    const TASK_ID = "task-001";
    const QUANTITY = 1;
    const SERVICE_CALL_HASH = ethers.keccak256(ethers.toUtf8Bytes("test-call"));

    it("Should execute payment successfully", async function () {
      const providerBalanceBefore = await mneeToken.balanceOf(provider.address);
      const treasuryBalanceBefore = await mneeToken.balanceOf(treasury.address);

      const tx = await router.connect(treasury).payForService(
        SERVICE_ID,
        AGENT_ID,
        TASK_ID,
        QUANTITY,
        SERVICE_CALL_HASH
      );

      const receipt = await tx.wait();

      // Check balances changed correctly
      expect(await mneeToken.balanceOf(provider.address)).to.equal(
        providerBalanceBefore + UNIT_PRICE
      );
      expect(await mneeToken.balanceOf(treasury.address)).to.equal(
        treasuryBalanceBefore - UNIT_PRICE
      );
    });

    it("Should emit PaymentExecuted event", async function () {
      await expect(
        router.connect(treasury).payForService(SERVICE_ID, AGENT_ID, TASK_ID, QUANTITY, SERVICE_CALL_HASH)
      ).to.emit(router, "PaymentExecuted");
    });

    it("Should calculate correct amount for multiple quantities", async function () {
      const quantity = 3;
      const expectedAmount = UNIT_PRICE * BigInt(quantity);
      const providerBalanceBefore = await mneeToken.balanceOf(provider.address);

      await router.connect(treasury).payForService(
        SERVICE_ID,
        AGENT_ID,
        TASK_ID,
        quantity,
        SERVICE_CALL_HASH
      );

      expect(await mneeToken.balanceOf(provider.address)).to.equal(
        providerBalanceBefore + expectedAmount
      );
    });

    it("Should generate unique payment IDs", async function () {
      const tx1 = await router.connect(treasury).payForService(
        SERVICE_ID, AGENT_ID, "task-001", QUANTITY, SERVICE_CALL_HASH
      );
      const tx2 = await router.connect(treasury).payForService(
        SERVICE_ID, AGENT_ID, "task-002", QUANTITY, SERVICE_CALL_HASH
      );

      const receipt1 = await tx1.wait();
      const receipt2 = await tx2.wait();

      // Get payment IDs from events
      const event1 = receipt1?.logs.find(log => log.topics[0] === router.interface.getEvent("PaymentExecuted").topicHash);
      const event2 = receipt2?.logs.find(log => log.topics[0] === router.interface.getEvent("PaymentExecuted").topicHash);

      expect(event1).to.not.be.undefined;
      expect(event2).to.not.be.undefined;
      // Payment IDs should be different (topics[1] is paymentId)
      expect(event1?.topics[1]).to.not.equal(event2?.topics[1]);
    });

    it("Should revert if service is not active", async function () {
      // Deactivate service
      await registry.updateService(SERVICE_ID, provider.address, UNIT_PRICE, false, METADATA_URI, true);

      await expect(
        router.connect(treasury).payForService(SERVICE_ID, AGENT_ID, TASK_ID, QUANTITY, SERVICE_CALL_HASH)
      ).to.be.revertedWith("Service not active");
    });

    it("Should revert if service does not exist", async function () {
      const nonExistentService = ethers.keccak256(ethers.toUtf8Bytes("NON_EXISTENT"));

      await expect(
        router.connect(treasury).payForService(nonExistentService, AGENT_ID, TASK_ID, QUANTITY, SERVICE_CALL_HASH)
      ).to.be.revertedWith("Service not found");
    });

    it("Should revert if payer has insufficient balance", async function () {
      // Transfer all tokens away
      await mneeToken.connect(treasury).transfer(owner.address, INITIAL_BALANCE);

      await expect(
        router.connect(treasury).payForService(SERVICE_ID, AGENT_ID, TASK_ID, QUANTITY, SERVICE_CALL_HASH)
      ).to.be.reverted; // ERC20 insufficient balance
    });

    it("Should revert if payer has not approved router", async function () {
      // Revoke approval
      await mneeToken.connect(treasury).approve(await router.getAddress(), 0);

      await expect(
        router.connect(treasury).payForService(SERVICE_ID, AGENT_ID, TASK_ID, QUANTITY, SERVICE_CALL_HASH)
      ).to.be.reverted; // ERC20 insufficient allowance
    });
  });

  describe("Edge Cases", function () {
    it("Should handle zero unit price service", async function () {
      const freeServiceId = ethers.keccak256(ethers.toUtf8Bytes("FREE_SERVICE"));
      await registry.registerService(freeServiceId, provider.address, 0, METADATA_URI, true);

      // Zero amount should revert
      await expect(
        router.connect(treasury).payForService(freeServiceId, "agent", "task", 1, ethers.ZeroHash)
      ).to.be.revertedWith("Amount must be > 0");
    });

    it("Should handle large quantities", async function () {
      // Mint more tokens
      await mneeToken.mint(treasury.address, ethers.parseEther("10000"));
      await mneeToken.connect(treasury).approve(await router.getAddress(), ethers.parseEther("10000"));

      const largeQuantity = 100;
      const expectedAmount = UNIT_PRICE * BigInt(largeQuantity);

      await expect(
        router.connect(treasury).payForService(SERVICE_ID, "agent", "task", largeQuantity, ethers.ZeroHash)
      ).to.not.be.reverted;
    });
  });
});
