import { expect } from "chai";
import { ethers } from "hardhat";
import { MNEEEscrow, MockMNEE } from "../typechain-types";
import { SignerWithAddress } from "@nomicfoundation/hardhat-ethers/signers";

describe("MNEEEscrow", function () {
  let escrow: MNEEEscrow;
  let mneeToken: MockMNEE;
  let owner: SignerWithAddress;
  let funder: SignerWithAddress;
  let feeCollector: SignerWithAddress;

  const CUSTOMER_AGENT = "customer-agent";
  const MERCHANT_AGENT = "merchant-agent";
  const VERIFIER_AGENT = "verifier-agent";
  const ESCROW_AMOUNT = ethers.parseEther("100");
  const TASK_DESC = "Generate marketing images";
  const REQ_HASH = "QmRequirements123";
  const WORK_HASH = "QmWorkProof456";
  const INITIAL_BALANCE = ethers.parseEther("10000");

  beforeEach(async function () {
    [owner, funder, feeCollector] = await ethers.getSigners();

    // Deploy MockMNEE token
    const MockMNEEFactory = await ethers.getContractFactory("MockMNEE");
    mneeToken = await MockMNEEFactory.deploy();

    // Deploy Escrow contract
    const EscrowFactory = await ethers.getContractFactory("MNEEEscrow");
    escrow = await EscrowFactory.deploy(await mneeToken.getAddress());

    // Fund the funder account
    await mneeToken.mint(funder.address, INITIAL_BALANCE);
    await mneeToken.connect(funder).approve(await escrow.getAddress(), INITIAL_BALANCE);
  });

  describe("Deployment", function () {
    it("Should set correct MNEE token address", async function () {
      expect(await escrow.mneeToken()).to.equal(await mneeToken.getAddress());
    });

    it("Should set deployer as owner and fee collector", async function () {
      expect(await escrow.owner()).to.equal(owner.address);
      expect(await escrow.feeCollector()).to.equal(owner.address);
    });

    it("Should set default platform fee to 1%", async function () {
      expect(await escrow.platformFeePercent()).to.equal(100);
    });
  });

  describe("Create Escrow", function () {
    it("Should create escrow and lock funds", async function () {
      const balanceBefore = await mneeToken.balanceOf(funder.address);

      const tx = await escrow.connect(funder).createEscrow(
        CUSTOMER_AGENT,
        MERCHANT_AGENT,
        ESCROW_AMOUNT,
        TASK_DESC,
        REQ_HASH
      );

      await expect(tx).to.emit(escrow, "EscrowCreated");

      const balanceAfter = await mneeToken.balanceOf(funder.address);
      expect(balanceBefore - balanceAfter).to.equal(ESCROW_AMOUNT);

      // Contract should hold the funds
      expect(await mneeToken.balanceOf(await escrow.getAddress())).to.equal(ESCROW_AMOUNT);
    });

    it("Should store escrow details correctly", async function () {
      const tx = await escrow.connect(funder).createEscrow(
        CUSTOMER_AGENT,
        MERCHANT_AGENT,
        ESCROW_AMOUNT,
        TASK_DESC,
        REQ_HASH
      );

      const receipt = await tx.wait();
      const event = receipt?.logs.find(log =>
        log.topics[0] === escrow.interface.getEvent("EscrowCreated").topicHash
      );
      const escrowId = event?.topics[1];

      const esc = await escrow.getEscrow(escrowId!);
      expect(esc.amount).to.equal(ESCROW_AMOUNT);
      expect(esc.taskDescription).to.equal(TASK_DESC);
      expect(esc.requirementHash).to.equal(REQ_HASH);
      expect(esc.state).to.equal(0); // Created
    });

    it("Should calculate correct platform fee", async function () {
      const tx = await escrow.connect(funder).createEscrow(
        CUSTOMER_AGENT,
        MERCHANT_AGENT,
        ESCROW_AMOUNT,
        TASK_DESC,
        REQ_HASH
      );

      const receipt = await tx.wait();
      const event = receipt?.logs.find(log =>
        log.topics[0] === escrow.interface.getEvent("EscrowCreated").topicHash
      );
      const escrowId = event?.topics[1];

      const esc = await escrow.getEscrow(escrowId!);
      // 1% of 100 MNEE = 1 MNEE
      expect(esc.platformFee).to.equal(ethers.parseEther("1"));
    });

    it("Should increment escrow count", async function () {
      expect(await escrow.getEscrowCount()).to.equal(0);

      await escrow.connect(funder).createEscrow(CUSTOMER_AGENT, MERCHANT_AGENT, ESCROW_AMOUNT, TASK_DESC, REQ_HASH);
      expect(await escrow.getEscrowCount()).to.equal(1);

      await escrow.connect(funder).createEscrow(CUSTOMER_AGENT, "other-merchant", ESCROW_AMOUNT, "Task 2", REQ_HASH);
      expect(await escrow.getEscrowCount()).to.equal(2);
    });

    it("Should revert if amount is zero", async function () {
      await expect(
        escrow.connect(funder).createEscrow(CUSTOMER_AGENT, MERCHANT_AGENT, 0, TASK_DESC, REQ_HASH)
      ).to.be.revertedWith("Amount must be > 0");
    });

    it("Should revert if customer and merchant are same", async function () {
      await expect(
        escrow.connect(funder).createEscrow(CUSTOMER_AGENT, CUSTOMER_AGENT, ESCROW_AMOUNT, TASK_DESC, REQ_HASH)
      ).to.be.revertedWith("Customer and merchant must differ");
    });
  });

  describe("Submit Work", function () {
    let escrowId: string;

    beforeEach(async function () {
      const tx = await escrow.connect(funder).createEscrow(
        CUSTOMER_AGENT,
        MERCHANT_AGENT,
        ESCROW_AMOUNT,
        TASK_DESC,
        REQ_HASH
      );
      const receipt = await tx.wait();
      const event = receipt?.logs.find(log =>
        log.topics[0] === escrow.interface.getEvent("EscrowCreated").topicHash
      );
      escrowId = event?.topics[1] as string;
    });

    it("Should submit work proof", async function () {
      await expect(escrow.submitWork(escrowId, WORK_HASH))
        .to.emit(escrow, "WorkSubmitted")
        .withArgs(escrowId, WORK_HASH);

      const esc = await escrow.getEscrow(escrowId);
      expect(esc.workProofHash).to.equal(WORK_HASH);
      expect(esc.state).to.equal(1); // Submitted
      expect(esc.submittedAt).to.be.greaterThan(0);
    });

    it("Should revert if escrow not found", async function () {
      const fakeId = ethers.keccak256(ethers.toUtf8Bytes("fake"));
      await expect(
        escrow.submitWork(fakeId, WORK_HASH)
      ).to.be.revertedWith("Escrow not found");
    });

    it("Should revert if work proof is empty", async function () {
      await expect(
        escrow.submitWork(escrowId, "")
      ).to.be.revertedWith("Work proof required");
    });

    it("Should revert if already submitted", async function () {
      await escrow.submitWork(escrowId, WORK_HASH);
      await expect(
        escrow.submitWork(escrowId, "QmAnotherProof")
      ).to.be.revertedWith("Invalid escrow state");
    });
  });

  describe("Verify and Release", function () {
    let escrowId: string;

    beforeEach(async function () {
      const tx = await escrow.connect(funder).createEscrow(
        CUSTOMER_AGENT,
        MERCHANT_AGENT,
        ESCROW_AMOUNT,
        TASK_DESC,
        REQ_HASH
      );
      const receipt = await tx.wait();
      const event = receipt?.logs.find(log =>
        log.topics[0] === escrow.interface.getEvent("EscrowCreated").topicHash
      );
      escrowId = event?.topics[1] as string;
      await escrow.submitWork(escrowId, WORK_HASH);
    });

    it("Should release to merchant if score >= 70", async function () {
      const ownerBalanceBefore = await mneeToken.balanceOf(owner.address);

      await expect(escrow.verifyAndRelease(escrowId, VERIFIER_AGENT, 85))
        .to.emit(escrow, "VerificationCompleted")
        .to.emit(escrow, "EscrowReleased");

      const esc = await escrow.getEscrow(escrowId);
      expect(esc.state).to.equal(3); // Released
      expect(esc.verificationScore).to.equal(85);

      // Owner should receive merchant amount (99 MNEE after 1% fee)
      const ownerBalanceAfter = await mneeToken.balanceOf(owner.address);
      expect(ownerBalanceAfter - ownerBalanceBefore).to.equal(ethers.parseEther("99"));
    });

    it("Should refund to customer if score < 70", async function () {
      const ownerBalanceBefore = await mneeToken.balanceOf(owner.address);

      await expect(escrow.verifyAndRelease(escrowId, VERIFIER_AGENT, 50))
        .to.emit(escrow, "VerificationCompleted")
        .to.emit(escrow, "EscrowRefunded");

      const esc = await escrow.getEscrow(escrowId);
      expect(esc.state).to.equal(4); // Refunded
      expect(esc.verificationScore).to.equal(50);

      // Owner should receive full refund (100 MNEE, no fee)
      const ownerBalanceAfter = await mneeToken.balanceOf(owner.address);
      expect(ownerBalanceAfter - ownerBalanceBefore).to.equal(ESCROW_AMOUNT);
    });

    it("Should handle edge case score of exactly 70", async function () {
      await escrow.verifyAndRelease(escrowId, VERIFIER_AGENT, 70);

      const esc = await escrow.getEscrow(escrowId);
      expect(esc.state).to.equal(3); // Released (passed threshold)
    });

    it("Should revert if score > 100", async function () {
      await expect(
        escrow.verifyAndRelease(escrowId, VERIFIER_AGENT, 101)
      ).to.be.revertedWith("Invalid score");
    });

    it("Should revert if work not submitted", async function () {
      // Create new escrow without submitting work
      const tx2 = await escrow.connect(funder).createEscrow(
        CUSTOMER_AGENT,
        "another-merchant",
        ESCROW_AMOUNT,
        "Another task",
        REQ_HASH
      );
      const receipt2 = await tx2.wait();
      const event2 = receipt2?.logs.find(log =>
        log.topics[0] === escrow.interface.getEvent("EscrowCreated").topicHash
      );
      const newEscrowId = event2?.topics[1] as string;

      await expect(
        escrow.verifyAndRelease(newEscrowId, VERIFIER_AGENT, 80)
      ).to.be.revertedWith("Work not submitted");
    });
  });

  describe("Dispute Resolution", function () {
    let escrowId: string;

    beforeEach(async function () {
      const tx = await escrow.connect(funder).createEscrow(
        CUSTOMER_AGENT,
        MERCHANT_AGENT,
        ESCROW_AMOUNT,
        TASK_DESC,
        REQ_HASH
      );
      const receipt = await tx.wait();
      const event = receipt?.logs.find(log =>
        log.topics[0] === escrow.interface.getEvent("EscrowCreated").topicHash
      );
      escrowId = event?.topics[1] as string;
    });

    it("Should raise dispute on created escrow", async function () {
      await expect(escrow.raiseDispute(escrowId, "Work not started"))
        .to.emit(escrow, "DisputeRaised")
        .withArgs(escrowId, "Work not started");

      const esc = await escrow.getEscrow(escrowId);
      expect(esc.state).to.equal(5); // Disputed
      expect(esc.disputeReason).to.equal("Work not started");
    });

    it("Should raise dispute on submitted escrow", async function () {
      await escrow.submitWork(escrowId, WORK_HASH);
      await escrow.raiseDispute(escrowId, "Quality issues");

      const esc = await escrow.getEscrow(escrowId);
      expect(esc.state).to.equal(5); // Disputed
    });

    it("Should resolve dispute in favor of merchant", async function () {
      await escrow.submitWork(escrowId, WORK_HASH);
      await escrow.raiseDispute(escrowId, "Quality issues");

      await expect(escrow.resolveDispute(escrowId, true))
        .to.emit(escrow, "DisputeResolved")
        .to.emit(escrow, "EscrowReleased");

      const esc = await escrow.getEscrow(escrowId);
      expect(esc.state).to.equal(3); // Released
    });

    it("Should resolve dispute in favor of customer", async function () {
      await escrow.submitWork(escrowId, WORK_HASH);
      await escrow.raiseDispute(escrowId, "Quality issues");

      await expect(escrow.resolveDispute(escrowId, false))
        .to.emit(escrow, "DisputeResolved")
        .to.emit(escrow, "EscrowRefunded");

      const esc = await escrow.getEscrow(escrowId);
      expect(esc.state).to.equal(4); // Refunded
    });

    it("Should revert dispute on already released escrow", async function () {
      await escrow.submitWork(escrowId, WORK_HASH);
      await escrow.verifyAndRelease(escrowId, VERIFIER_AGENT, 90);

      await expect(
        escrow.raiseDispute(escrowId, "Too late")
      ).to.be.revertedWith("Cannot dispute in current state");
    });
  });

  describe("View Functions", function () {
    beforeEach(async function () {
      // Create multiple escrows in different states
      await escrow.connect(funder).createEscrow(CUSTOMER_AGENT, MERCHANT_AGENT, ESCROW_AMOUNT, "Task 1", REQ_HASH);
      await escrow.connect(funder).createEscrow(CUSTOMER_AGENT, "merchant-2", ESCROW_AMOUNT, "Task 2", REQ_HASH);
      await escrow.connect(funder).createEscrow(CUSTOMER_AGENT, "merchant-3", ESCROW_AMOUNT, "Task 3", REQ_HASH);
    });

    it("Should return correct escrow count", async function () {
      expect(await escrow.getEscrowCount()).to.equal(3);
    });

    it("Should return recent escrows", async function () {
      const recent = await escrow.getRecentEscrows(2);
      expect(recent.length).to.equal(2);
    });

    it("Should filter by state", async function () {
      const created = await escrow.getEscrowsByState(0); // Created
      expect(created.length).to.equal(3);
    });
  });

  describe("Admin Functions", function () {
    it("Should update fee collector", async function () {
      await escrow.setFeeCollector(feeCollector.address);
      expect(await escrow.feeCollector()).to.equal(feeCollector.address);
    });

    it("Should update platform fee percent", async function () {
      await escrow.setPlatformFeePercent(200); // 2%
      expect(await escrow.platformFeePercent()).to.equal(200);
    });

    it("Should revert if fee too high", async function () {
      await expect(
        escrow.setPlatformFeePercent(1001) // > 10%
      ).to.be.revertedWith("Fee too high");
    });

    it("Should revert if non-owner calls admin functions", async function () {
      await expect(
        escrow.connect(funder).setFeeCollector(funder.address)
      ).to.be.revertedWithCustomError(escrow, "OwnableUnauthorizedAccount");
    });
  });
});
