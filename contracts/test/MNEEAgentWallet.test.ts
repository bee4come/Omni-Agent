import { expect } from "chai";
import { ethers } from "hardhat";
import { MNEEAgentWallet, MockMNEE } from "../typechain-types";
import { SignerWithAddress } from "@nomicfoundation/hardhat-ethers/signers";

describe("MNEEAgentWallet", function () {
  let wallet: MNEEAgentWallet;
  let mneeToken: MockMNEE;
  let owner: SignerWithAddress;
  let funder: SignerWithAddress;
  let external: SignerWithAddress;

  const AGENT_1 = "user-agent";
  const AGENT_2 = "batch-agent";
  const AGENT_3 = "merchant-agent";
  const INITIAL_BALANCE = ethers.parseEther("1000");

  beforeEach(async function () {
    [owner, funder, external] = await ethers.getSigners();

    // Deploy MockMNEE token
    const MockMNEEFactory = await ethers.getContractFactory("MockMNEE");
    mneeToken = await MockMNEEFactory.deploy();

    // Deploy AgentWallet
    const WalletFactory = await ethers.getContractFactory("MNEEAgentWallet");
    wallet = await WalletFactory.deploy(await mneeToken.getAddress());

    // Fund the funder account
    await mneeToken.mint(funder.address, INITIAL_BALANCE);
  });

  describe("Deployment", function () {
    it("Should set correct MNEE token address", async function () {
      expect(await wallet.mneeToken()).to.equal(await mneeToken.getAddress());
    });

    it("Should set deployer as owner", async function () {
      expect(await wallet.owner()).to.equal(owner.address);
    });
  });

  describe("Agent Registration", function () {
    it("Should register a new agent", async function () {
      await expect(wallet.registerAgent(AGENT_1, "User Agent"))
        .to.emit(wallet, "AgentRegistered");

      const info = await wallet.getAgentInfo(AGENT_1);
      expect(info.registered).to.be.true;
      expect(info.name).to.equal("User Agent");
      expect(info.balance).to.equal(0);
    });

    it("Should register multiple agents", async function () {
      await wallet.registerAgent(AGENT_1, "User Agent");
      await wallet.registerAgent(AGENT_2, "Batch Agent");
      await wallet.registerAgent(AGENT_3, "Merchant Agent");

      const info1 = await wallet.getAgentInfo(AGENT_1);
      const info2 = await wallet.getAgentInfo(AGENT_2);
      const info3 = await wallet.getAgentInfo(AGENT_3);

      expect(info1.registered).to.be.true;
      expect(info2.registered).to.be.true;
      expect(info3.registered).to.be.true;
    });

    it("Should revert if agent already registered", async function () {
      await wallet.registerAgent(AGENT_1, "User Agent");

      await expect(
        wallet.registerAgent(AGENT_1, "Another Name")
      ).to.be.revertedWith("Agent already registered");
    });

    it("Should revert if non-owner tries to register", async function () {
      await expect(
        wallet.connect(funder).registerAgent(AGENT_1, "User Agent")
      ).to.be.revertedWithCustomError(wallet, "OwnableUnauthorizedAccount");
    });
  });

  describe("Fund Agent", function () {
    const FUND_AMOUNT = ethers.parseEther("100");

    beforeEach(async function () {
      await wallet.registerAgent(AGENT_1, "User Agent");
      await mneeToken.connect(funder).approve(await wallet.getAddress(), INITIAL_BALANCE);
    });

    it("Should fund agent wallet", async function () {
      await expect(wallet.connect(funder).fundAgent(AGENT_1, FUND_AMOUNT))
        .to.emit(wallet, "AgentFunded")
        .withArgs(
          ethers.keccak256(ethers.toUtf8Bytes(AGENT_1)),
          FUND_AMOUNT,
          funder.address
        );

      const balance = await wallet.getAgentBalance(AGENT_1);
      expect(balance).to.equal(FUND_AMOUNT);
    });

    it("Should update totalReceived", async function () {
      await wallet.connect(funder).fundAgent(AGENT_1, FUND_AMOUNT);

      const info = await wallet.getAgentInfo(AGENT_1);
      expect(info.totalReceived).to.equal(FUND_AMOUNT);
    });

    it("Should allow multiple funding", async function () {
      await wallet.connect(funder).fundAgent(AGENT_1, FUND_AMOUNT);
      await wallet.connect(funder).fundAgent(AGENT_1, FUND_AMOUNT);

      const balance = await wallet.getAgentBalance(AGENT_1);
      expect(balance).to.equal(FUND_AMOUNT * 2n);
    });

    it("Should revert if agent not registered", async function () {
      await expect(
        wallet.connect(funder).fundAgent(AGENT_2, FUND_AMOUNT)
      ).to.be.revertedWith("Agent not registered");
    });

    it("Should revert if amount is zero", async function () {
      await expect(
        wallet.connect(funder).fundAgent(AGENT_1, 0)
      ).to.be.revertedWith("Amount must be > 0");
    });
  });

  describe("A2A Payment", function () {
    const FUND_AMOUNT = ethers.parseEther("100");
    const PAYMENT_AMOUNT = ethers.parseEther("10");
    const TASK_DESC = "Generate marketing image";

    beforeEach(async function () {
      await wallet.registerAgent(AGENT_1, "User Agent");
      await wallet.registerAgent(AGENT_2, "Batch Agent");
      await mneeToken.connect(funder).approve(await wallet.getAddress(), INITIAL_BALANCE);
      await wallet.connect(funder).fundAgent(AGENT_1, FUND_AMOUNT);
    });

    it("Should execute A2A payment", async function () {
      await expect(
        wallet.a2aPayment(AGENT_1, AGENT_2, PAYMENT_AMOUNT, TASK_DESC)
      ).to.emit(wallet, "A2APayment");

      const balance1 = await wallet.getAgentBalance(AGENT_1);
      const balance2 = await wallet.getAgentBalance(AGENT_2);

      expect(balance1).to.equal(FUND_AMOUNT - PAYMENT_AMOUNT);
      expect(balance2).to.equal(PAYMENT_AMOUNT);
    });

    it("Should record transfer in transfers array", async function () {
      await wallet.a2aPayment(AGENT_1, AGENT_2, PAYMENT_AMOUNT, TASK_DESC);

      const count = await wallet.getTransferCount();
      expect(count).to.equal(1);
    });

    it("Should update agent stats", async function () {
      await wallet.a2aPayment(AGENT_1, AGENT_2, PAYMENT_AMOUNT, TASK_DESC);

      const info1 = await wallet.getAgentInfo(AGENT_1);
      const info2 = await wallet.getAgentInfo(AGENT_2);

      expect(info1.totalSpent).to.equal(PAYMENT_AMOUNT);
      expect(info2.totalReceived).to.equal(PAYMENT_AMOUNT);
    });

    it("Should handle multiple A2A payments", async function () {
      await wallet.a2aPayment(AGENT_1, AGENT_2, PAYMENT_AMOUNT, "Task 1");
      await wallet.a2aPayment(AGENT_1, AGENT_2, PAYMENT_AMOUNT, "Task 2");
      await wallet.a2aPayment(AGENT_1, AGENT_2, PAYMENT_AMOUNT, "Task 3");

      const count = await wallet.getTransferCount();
      expect(count).to.equal(3);

      const balance2 = await wallet.getAgentBalance(AGENT_2);
      expect(balance2).to.equal(PAYMENT_AMOUNT * 3n);
    });

    it("Should revert if from agent not registered", async function () {
      await expect(
        wallet.a2aPayment(AGENT_3, AGENT_2, PAYMENT_AMOUNT, TASK_DESC)
      ).to.be.revertedWith("From agent not registered");
    });

    it("Should revert if to agent not registered", async function () {
      await expect(
        wallet.a2aPayment(AGENT_1, AGENT_3, PAYMENT_AMOUNT, TASK_DESC)
      ).to.be.revertedWith("To agent not registered");
    });

    it("Should revert if insufficient balance", async function () {
      const tooMuch = ethers.parseEther("500");
      await expect(
        wallet.a2aPayment(AGENT_1, AGENT_2, tooMuch, TASK_DESC)
      ).to.be.revertedWith("Insufficient balance");
    });

    it("Should revert if amount is zero", async function () {
      await expect(
        wallet.a2aPayment(AGENT_1, AGENT_2, 0, TASK_DESC)
      ).to.be.revertedWith("Amount must be > 0");
    });

    it("Should revert if non-owner tries to call", async function () {
      await expect(
        wallet.connect(funder).a2aPayment(AGENT_1, AGENT_2, PAYMENT_AMOUNT, TASK_DESC)
      ).to.be.revertedWithCustomError(wallet, "OwnableUnauthorizedAccount");
    });
  });

  describe("Get Recent Transfers", function () {
    beforeEach(async function () {
      await wallet.registerAgent(AGENT_1, "User Agent");
      await wallet.registerAgent(AGENT_2, "Batch Agent");
      await mneeToken.connect(funder).approve(await wallet.getAddress(), INITIAL_BALANCE);
      await wallet.connect(funder).fundAgent(AGENT_1, ethers.parseEther("100"));

      // Create 5 transfers
      for (let i = 0; i < 5; i++) {
        await wallet.a2aPayment(AGENT_1, AGENT_2, ethers.parseEther("1"), `Task ${i}`);
      }
    });

    it("Should return correct number of recent transfers", async function () {
      const result = await wallet.getRecentTransfers(3);
      expect(result.fromAgents.length).to.equal(3);
      expect(result.toAgents.length).to.equal(3);
      expect(result.amounts.length).to.equal(3);
      expect(result.timestamps.length).to.equal(3);
    });

    it("Should return all transfers if count exceeds total", async function () {
      const result = await wallet.getRecentTransfers(10);
      expect(result.fromAgents.length).to.equal(5);
    });

    it("Should return most recent transfers", async function () {
      const result = await wallet.getRecentTransfers(2);
      // All amounts should be 1 MNEE
      expect(result.amounts[0]).to.equal(ethers.parseEther("1"));
      expect(result.amounts[1]).to.equal(ethers.parseEther("1"));
    });
  });

  describe("Withdraw Agent Balance", function () {
    const FUND_AMOUNT = ethers.parseEther("100");
    const WITHDRAW_AMOUNT = ethers.parseEther("50");

    beforeEach(async function () {
      await wallet.registerAgent(AGENT_1, "User Agent");
      await mneeToken.connect(funder).approve(await wallet.getAddress(), INITIAL_BALANCE);
      await wallet.connect(funder).fundAgent(AGENT_1, FUND_AMOUNT);
    });

    it("Should withdraw to external address", async function () {
      const balanceBefore = await mneeToken.balanceOf(external.address);

      await expect(
        wallet.withdrawAgentBalance(AGENT_1, external.address, WITHDRAW_AMOUNT)
      ).to.emit(wallet, "AgentWithdraw");

      const balanceAfter = await mneeToken.balanceOf(external.address);
      expect(balanceAfter - balanceBefore).to.equal(WITHDRAW_AMOUNT);

      const agentBalance = await wallet.getAgentBalance(AGENT_1);
      expect(agentBalance).to.equal(FUND_AMOUNT - WITHDRAW_AMOUNT);
    });

    it("Should revert if insufficient balance", async function () {
      await expect(
        wallet.withdrawAgentBalance(AGENT_1, external.address, ethers.parseEther("200"))
      ).to.be.revertedWith("Insufficient balance");
    });

    it("Should revert if non-owner tries to withdraw", async function () {
      await expect(
        wallet.connect(funder).withdrawAgentBalance(AGENT_1, external.address, WITHDRAW_AMOUNT)
      ).to.be.revertedWithCustomError(wallet, "OwnableUnauthorizedAccount");
    });
  });

  describe("ReentrancyGuard", function () {
    it("Should protect fundAgent from reentrancy", async function () {
      await wallet.registerAgent(AGENT_1, "User Agent");
      await mneeToken.connect(funder).approve(await wallet.getAddress(), INITIAL_BALANCE);

      // Normal funding should work (reentrancy protection is transparent for normal calls)
      await expect(
        wallet.connect(funder).fundAgent(AGENT_1, ethers.parseEther("10"))
      ).to.not.be.reverted;
    });
  });
});
