#!/usr/bin/env python3
"""
Configuration Validation Script for MNEE Nexus

This script validates all configuration files and environment variables
to ensure the system is properly configured before startup.

Usage:
    python scripts/validate_config.py
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, List, Tuple

# ANSI color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")

def print_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")

def print_header(msg: str):
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}{Colors.RESET}\n")

class ConfigValidator:
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.project_root = Path(__file__).parent.parent
        
    def validate_all(self) -> bool:
        """Run all validation checks"""
        print_header("MNEE Nexus Configuration Validation")
        
        self.check_directory_structure()
        self.check_env_file()
        self.check_yaml_configs()
        self.check_dependencies()
        self.check_contracts()
        
        return self.print_summary()
    
    def check_directory_structure(self):
        """Verify all required directories exist"""
        print_info("Checking directory structure...")
        
        required_dirs = [
            "backend",
            "backend/app",
            "backend/agents",
            "backend/agents/tools",
            "backend/payment",
            "backend/policy",
            "config",
            "contracts",
            "contracts/contracts",
            "contracts/scripts",
            "providers",
            "providers/imagegen",
            "providers/price_oracle",
            "providers/batch_compute",
            "providers/log_archive",
        ]
        
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if full_path.exists():
                print_success(f"Directory exists: {dir_path}")
            else:
                self.errors.append(f"Missing directory: {dir_path}")
                print_error(f"Missing directory: {dir_path}")
    
    def check_env_file(self):
        """Check backend .env file configuration"""
        print_info("Checking environment configuration...")
        
        env_file = self.project_root / "backend" / ".env"
        
        if not env_file.exists():
            self.warnings.append("backend/.env not found. Using .env.example as template")
            print_warning("backend/.env not found. Copy from .env.example")
            return
        
        # Parse .env file
        env_vars = {}
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
        
        # Required variables
        required_vars = [
            "ETH_RPC_URL",
            "MNEE_TOKEN_ADDRESS",
            "POLICY_CONFIG_PATH",
            "SERVICE_CONFIG_PATH",
        ]
        
        # Optional but recommended
        recommended_vars = [
            "PAYMENT_ROUTER_ADDRESS",
            "TREASURY_PRIVATE_KEY",
            "AWS_ACCESS_KEY_ID",
            "OPENAI_API_KEY",
        ]
        
        for var in required_vars:
            if var in env_vars and env_vars[var]:
                print_success(f"Required variable set: {var}")
            else:
                self.errors.append(f"Missing required variable: {var}")
                print_error(f"Missing required variable: {var}")
        
        for var in recommended_vars:
            if var in env_vars and env_vars[var]:
                print_success(f"Optional variable set: {var}")
            else:
                self.warnings.append(f"Optional variable not set: {var}")
                print_warning(f"Optional variable not set: {var} (system will work in mock mode)")
    
    def check_yaml_configs(self):
        """Validate YAML configuration files"""
        print_info("Checking YAML configurations...")
        
        # Check agents.yaml
        agents_file = self.project_root / "config" / "agents.yaml"
        if agents_file.exists():
            try:
                with open(agents_file) as f:
                    agents_config = yaml.safe_load(f)
                
                if 'agents' not in agents_config:
                    self.errors.append("agents.yaml missing 'agents' key")
                    print_error("agents.yaml missing 'agents' key")
                else:
                    num_agents = len(agents_config['agents'])
                    print_success(f"agents.yaml loaded successfully ({num_agents} agents)")
                    
                    # Validate each agent
                    for agent in agents_config['agents']:
                        required_fields = ['id', 'priority', 'dailyBudget', 'maxPerCall']
                        missing_fields = [f for f in required_fields if f not in agent]
                        if missing_fields:
                            self.errors.append(f"Agent {agent.get('id', 'unknown')} missing fields: {missing_fields}")
                            print_error(f"Agent missing fields: {missing_fields}")
            except Exception as e:
                self.errors.append(f"Error parsing agents.yaml: {e}")
                print_error(f"Error parsing agents.yaml: {e}")
        else:
            self.errors.append("config/agents.yaml not found")
            print_error("config/agents.yaml not found")
        
        # Check services.yaml
        services_file = self.project_root / "config" / "services.yaml"
        if services_file.exists():
            try:
                with open(services_file) as f:
                    services_config = yaml.safe_load(f)
                
                if 'services' not in services_config:
                    self.errors.append("services.yaml missing 'services' key")
                    print_error("services.yaml missing 'services' key")
                else:
                    num_services = len(services_config['services'])
                    print_success(f"services.yaml loaded successfully ({num_services} services)")
                    
                    # Validate each service
                    for service in services_config['services']:
                        required_fields = ['id', 'unitPrice', 'providerAddress', 'active']
                        missing_fields = [f for f in required_fields if f not in service]
                        if missing_fields:
                            self.errors.append(f"Service {service.get('id', 'unknown')} missing fields: {missing_fields}")
                            print_error(f"Service missing fields: {missing_fields}")
            except Exception as e:
                self.errors.append(f"Error parsing services.yaml: {e}")
                print_error(f"Error parsing services.yaml: {e}")
        else:
            self.errors.append("config/services.yaml not found")
            print_error("config/services.yaml not found")
    
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        print_info("Checking dependencies...")
        
        # Python dependencies
        backend_requirements = self.project_root / "backend" / "requirements.txt"
        if backend_requirements.exists():
            print_success("backend/requirements.txt found")
        else:
            self.errors.append("backend/requirements.txt not found")
            print_error("backend/requirements.txt not found")
        
        # Node dependencies
        contracts_package = self.project_root / "contracts" / "package.json"
        if contracts_package.exists():
            print_success("contracts/package.json found")
        else:
            self.errors.append("contracts/package.json not found")
            print_error("contracts/package.json not found")
    
    def check_contracts(self):
        """Verify smart contract files exist"""
        print_info("Checking smart contracts...")
        
        required_contracts = [
            "contracts/contracts/MNEEServiceRegistry.sol",
            "contracts/contracts/MNEEPaymentRouter.sol",
            "contracts/contracts/MockMNEE.sol",
        ]
        
        for contract_path in required_contracts:
            full_path = self.project_root / contract_path
            if full_path.exists():
                print_success(f"Contract exists: {contract_path}")
            else:
                self.errors.append(f"Missing contract: {contract_path}")
                print_error(f"Missing contract: {contract_path}")
        
        # Check for deployment script
        deploy_script = self.project_root / "contracts" / "scripts" / "deploy.js"
        if deploy_script.exists():
            print_success("Deployment script found")
        else:
            self.warnings.append("contracts/scripts/deploy.js not found")
            print_warning("Deployment script not found")
    
    def print_summary(self) -> bool:
        """Print validation summary"""
        print_header("Validation Summary")
        
        if not self.errors and not self.warnings:
            print_success("All checks passed! ✓")
            print_info("Your configuration is ready.")
            return True
        
        if self.warnings:
            print_warning(f"Found {len(self.warnings)} warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")
            print()
        
        if self.errors:
            print_error(f"Found {len(self.errors)} errors:")
            for error in self.errors:
                print(f"  - {error}")
            print()
            print_error("Please fix the errors above before starting the system.")
            return False
        
        print_warning("Configuration has warnings but should still work.")
        return True

def main():
    validator = ConfigValidator()
    success = validator.validate_all()
    
    if not success:
        print_info("\nNext steps:")
        print("  1. Review the errors above")
        print("  2. Fix missing files or configuration")
        print("  3. Run this script again")
        sys.exit(1)
    else:
        print_info("\nYou can now start the system:")
        print("  ./start_all.sh")
        sys.exit(0)

if __name__ == "__main__":
    main()
