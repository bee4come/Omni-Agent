import { expect } from "chai";
import { ethers } from "hardhat";
import { MNEEServiceRegistry } from "../typechain-types";
import { SignerWithAddress } from "@nomicfoundation/hardhat-ethers/signers";

describe("MNEEServiceRegistry", function () {
  let registry: MNEEServiceRegistry;
  let owner: SignerWithAddress;
  let provider1: SignerWithAddress;
  let provider2: SignerWithAddress;
  let nonOwner: SignerWithAddress;

  const SERVICE_ID_1 = ethers.keccak256(ethers.toUtf8Bytes("IMAGE_GEN_PREMIUM"));
  const SERVICE_ID_2 = ethers.keccak256(ethers.toUtf8Bytes("PRICE_ORACLE"));
  const UNIT_PRICE = ethers.parseEther("1.0");
  const METADATA_URI = "ipfs://QmTest123";

  beforeEach(async function () {
    [owner, provider1, provider2, nonOwner] = await ethers.getSigners();

    const RegistryFactory = await ethers.getContractFactory("MNEEServiceRegistry");
    registry = await RegistryFactory.deploy();
  });

  describe("Deployment", function () {
    it("Should set the deployer as owner", async function () {
      expect(await registry.owner()).to.equal(owner.address);
    });
  });

  describe("Service Registration", function () {
    it("Should register a new service", async function () {
      await expect(
        registry.registerService(SERVICE_ID_1, provider1.address, UNIT_PRICE, METADATA_URI, true)
      )
        .to.emit(registry, "ServiceRegistered")
        .withArgs(SERVICE_ID_1, provider1.address, UNIT_PRICE, METADATA_URI, true);

      const service = await registry.getService(SERVICE_ID_1);
      expect(service.provider).to.equal(provider1.address);
      expect(service.unitPrice).to.equal(UNIT_PRICE);
      expect(service.active).to.be.true;
      expect(service.metadataURI).to.equal(METADATA_URI);
      expect(service.isVerified).to.be.true;
    });

    it("Should register multiple services", async function () {
      await registry.registerService(SERVICE_ID_1, provider1.address, UNIT_PRICE, METADATA_URI, true);
      await registry.registerService(SERVICE_ID_2, provider2.address, ethers.parseEther("0.05"), "ipfs://QmPrice", false);

      const service1 = await registry.getService(SERVICE_ID_1);
      const service2 = await registry.getService(SERVICE_ID_2);

      expect(service1.provider).to.equal(provider1.address);
      expect(service2.provider).to.equal(provider2.address);
    });

    it("Should revert if service already exists", async function () {
      await registry.registerService(SERVICE_ID_1, provider1.address, UNIT_PRICE, METADATA_URI, true);

      await expect(
        registry.registerService(SERVICE_ID_1, provider2.address, UNIT_PRICE, METADATA_URI, false)
      ).to.be.revertedWith("Service already exists");
    });

    it("Should revert if provider address is zero", async function () {
      await expect(
        registry.registerService(SERVICE_ID_1, ethers.ZeroAddress, UNIT_PRICE, METADATA_URI, true)
      ).to.be.revertedWith("Invalid provider address");
    });

    it("Should revert if non-owner tries to register", async function () {
      await expect(
        registry.connect(nonOwner).registerService(SERVICE_ID_1, provider1.address, UNIT_PRICE, METADATA_URI, true)
      ).to.be.revertedWith("Only owner can call this");
    });
  });

  describe("Service Update", function () {
    beforeEach(async function () {
      await registry.registerService(SERVICE_ID_1, provider1.address, UNIT_PRICE, METADATA_URI, true);
    });

    it("Should update service price", async function () {
      const newPrice = ethers.parseEther("2.0");
      await expect(
        registry.updateService(SERVICE_ID_1, provider1.address, newPrice, true, METADATA_URI, true)
      )
        .to.emit(registry, "ServiceUpdated")
        .withArgs(SERVICE_ID_1, newPrice, true, METADATA_URI, true);

      const service = await registry.getService(SERVICE_ID_1);
      expect(service.unitPrice).to.equal(newPrice);
    });

    it("Should deactivate service", async function () {
      await registry.updateService(SERVICE_ID_1, provider1.address, UNIT_PRICE, false, METADATA_URI, true);

      const service = await registry.getService(SERVICE_ID_1);
      expect(service.active).to.be.false;
    });

    it("Should update provider address", async function () {
      await registry.updateService(SERVICE_ID_1, provider2.address, UNIT_PRICE, true, METADATA_URI, true);

      const service = await registry.getService(SERVICE_ID_1);
      expect(service.provider).to.equal(provider2.address);
    });

    it("Should update verification status", async function () {
      await registry.updateService(SERVICE_ID_1, provider1.address, UNIT_PRICE, true, METADATA_URI, false);

      const service = await registry.getService(SERVICE_ID_1);
      expect(service.isVerified).to.be.false;
    });

    it("Should revert if service does not exist", async function () {
      await expect(
        registry.updateService(SERVICE_ID_2, provider1.address, UNIT_PRICE, true, METADATA_URI, true)
      ).to.be.revertedWith("Service does not exist");
    });

    it("Should revert if non-owner tries to update", async function () {
      await expect(
        registry.connect(nonOwner).updateService(SERVICE_ID_1, provider1.address, UNIT_PRICE, true, METADATA_URI, true)
      ).to.be.revertedWith("Only owner can call this");
    });
  });

  describe("Service Query", function () {
    it("Should return empty service for non-existent ID", async function () {
      const service = await registry.getService(SERVICE_ID_1);
      expect(service.provider).to.equal(ethers.ZeroAddress);
      expect(service.unitPrice).to.equal(0);
      expect(service.active).to.be.false;
    });
  });
});
