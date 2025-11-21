import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";
import * as dotenv from "dotenv";

dotenv.config();

const config: HardhatUserConfig = {
    solidity: "0.8.24",
    networks: {
        hardhat: {
            chainId: 31337,
            forking: {
                // Fork Ethereum mainnet to use real MNEE contract
                url: process.env.ETH_MAINNET_RPC_URL || "https://eth-mainnet.g.alchemy.com/v2/demo",
                blockNumber: 21000000, // Recent block for consistent testing
                enabled: true,
            },
            accounts: {
                // Generate accounts with balance for testing
                count: 10,
                accountsBalance: "10000000000000000000000", // 10000 ETH each
            },
        },
        localhost: {
            url: "http://127.0.0.1:8545",
            timeout: 60000,
        },
    },
    mocha: {
        timeout: 60000,
    },
};

export default config;
