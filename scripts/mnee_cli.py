#!/usr/bin/env python3
"""
MNEE Nexus Admin CLI Tool

Comprehensive command-line interface for managing the MNEE Nexus system.

Usage:
    python scripts/mnee_cli.py [command] [options]

Commands:
    agent       Agent management (list, show, update, pause, resume)
    service     Service provider management
    treasury    Treasury operations and monitoring
    policy      Policy configuration and testing
    logs        Log management and analysis
    backup      Backup and restore operations
    health      System health checks
    monitor     Real-time monitoring
"""

import sys
import argparse
import requests
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import time

# ANSI Colors
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class MNEECli:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.project_root = Path(__file__).parent.parent
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make HTTP request to backend API"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self._error(f"API request failed: {e}")
            sys.exit(1)
    
    def _success(self, msg: str):
        print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")
    
    def _error(self, msg: str):
        print(f"{Colors.RED}❌ {msg}{Colors.RESET}")
    
    def _warning(self, msg: str):
        print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")
    
    def _info(self, msg: str):
        print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")
    
    def _header(self, msg: str):
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}")
        print(f"  {msg}")
        print(f"{'='*60}{Colors.RESET}\n")
    
    # ==================== AGENT COMMANDS ====================
    
    def agent_list(self):
        """List all agents"""
        self._header("Agents Overview")
        data = self._request("GET", "/agents")
        
        for agent in data['agents']:
            print(f"\n{Colors.BOLD}{agent['id']}{Colors.RESET}")
            print(f"  Priority: {agent['priority']}")
            print(f"  Daily Budget: {agent['dailyBudget']} MNEE")
            print(f"  Current Spend: {agent['currentDailySpend']} MNEE")
            remaining = agent['dailyBudget'] - agent['currentDailySpend']
            print(f"  Remaining: {Colors.GREEN if remaining > 0 else Colors.RED}{remaining} MNEE{Colors.RESET}")
    
    def agent_show(self, agent_id: str):
        """Show detailed agent information"""
        self._header(f"Agent: {agent_id}")
        data = self._request("GET", f"/agents/{agent_id}")
        
        print(f"ID: {data['id']}")
        print(f"Priority: {data['priority']}")
        print(f"Daily Budget: {data['dailyBudget']} MNEE")
        print(f"Max Per Call: {data['maxPerCall']} MNEE")
        print(f"Current Daily Spend: {data['currentDailySpend']} MNEE")
        print(f"Remaining Budget: {data['remainingBudget']} MNEE")
        print(f"Total Spent (All Time): {data['totalSpent']} MNEE")
        
        print(f"\n{Colors.BOLD}Recent Transactions:{Colors.RESET}")
        for tx in data['transactions'][-5:]:
            print(f"  • {tx['service_id']}: {tx['amount']} MNEE - {tx['status']}")
    
    def agent_update_budget(self, agent_id: str, daily_budget: float = None, max_per_call: float = None):
        """Update agent budget"""
        data = {}
        if daily_budget is not None:
            data['daily_budget'] = daily_budget
        if max_per_call is not None:
            data['max_per_call'] = max_per_call
        
        result = self._request("PUT", f"/agents/{agent_id}/budget", json=data)
        self._success(f"Updated budget for {agent_id}")
        print(json.dumps(result, indent=2))
    
    # ==================== SERVICE COMMANDS ====================
    
    def service_list(self):
        """List all services"""
        self._header("Services Overview")
        data = self._request("GET", "/services")
        
        for service in data['services']:
            status = f"{Colors.GREEN}ACTIVE{Colors.RESET}" if service['active'] else f"{Colors.RED}INACTIVE{Colors.RESET}"
            print(f"\n{Colors.BOLD}{service['id']}{Colors.RESET} - {status}")
            print(f"  Unit Price: {service['unitPrice']} MNEE")
            print(f"  Provider: {service['providerAddress']}")
    
    def service_show(self, service_id: str):
        """Show detailed service information"""
        self._header(f"Service: {service_id}")
        data = self._request("GET", f"/services/{service_id}")
        
        print(f"ID: {data['id']}")
        print(f"Unit Price: {data['unitPrice']} MNEE")
        print(f"Provider Address: {data['providerAddress']}")
        print(f"Active: {data['active']}")
        print(f"Total Revenue: {data['totalRevenue']} MNEE")
        
        print(f"\n{Colors.BOLD}Recent Transactions:{Colors.RESET}")
        for tx in data['transactions'][-5:]:
            print(f"  • Agent: {tx['agent_id']}, Amount: {tx['amount']} MNEE")
    
    # ==================== TREASURY COMMANDS ====================
    
    def treasury_status(self):
        """Show treasury status"""
        self._header("Treasury Status")
        data = self._request("GET", "/treasury")
        
        print(f"Total Allocated Budget: {data['totalAllocated']} MNEE")
        print(f"Total Spent: {data['totalSpent']} MNEE")
        print(f"Remaining: {data['totalAllocated'] - data['totalSpent']} MNEE")
        
        print(f"\n{Colors.BOLD}Per-Agent Breakdown:{Colors.RESET}")
        for agent_id, agent_data in data['agents'].items():
            print(f"\n  {Colors.BOLD}{agent_id}{Colors.RESET}")
            print(f"    Budget: {agent_data['dailyBudget']} MNEE")
            print(f"    Spent: {agent_data['currentDailySpend']} MNEE")
            print(f"    Remaining: {agent_data['remainingBudget']} MNEE")
    
    def treasury_reset(self):
        """Reset daily budgets"""
        confirm = input(f"{Colors.YELLOW}⚠️  Reset all agents' daily spending? (yes/no): {Colors.RESET}")
        if confirm.lower() == 'yes':
            self._request("POST", "/reset")
            self._success("Daily budgets reset successfully")
        else:
            self._info("Reset cancelled")
    
    # ==================== LOGS COMMANDS ====================
    
    def logs_transactions(self, limit: int = 20):
        """Show recent transactions"""
        self._header(f"Recent Transactions (Last {limit})")
        data = self._request("GET", f"/transactions?limit={limit}")
        
        for tx in data['transactions']:
            timestamp = tx['timestamp'][:19]
            status_color = Colors.GREEN if tx['status'] == 'SUCCESS' else Colors.RED
            print(f"{timestamp} | {tx['agent_id']:15} | {tx['service_id']:20} | {status_color}{tx['amount']:6} MNEE{Colors.RESET}")
    
    def logs_policy(self, limit: int = 20):
        """Show recent policy decisions"""
        self._header(f"Recent Policy Decisions (Last {limit})")
        data = self._request("GET", f"/policy/logs?limit={limit}")
        
        for log in data['logs']:
            timestamp = log['timestamp'][:19]
            action_colors = {
                'ALLOWED': Colors.GREEN,
                'REJECTED': Colors.RED,
                'DOWNGRADED': Colors.YELLOW
            }
            color = action_colors.get(log['action'], Colors.RESET)
            print(f"{timestamp} | {color}{log['action']:12}{Colors.RESET} | {log['agent_id']:15} | {log['service_id']:20}")
            print(f"  Reason: {log['reason']}")
    
    # ==================== STATS COMMANDS ====================
    
    def stats_show(self):
        """Show system statistics"""
        self._header("System Statistics")
        data = self._request("GET", "/stats")
        
        print(f"{Colors.BOLD}Transactions:{Colors.RESET}")
        print(f"  Total: {data['transactions']['total']}")
        print(f"  Successful: {Colors.GREEN}{data['transactions']['successful']}{Colors.RESET}")
        print(f"  Failed: {Colors.RED}{data['transactions']['failed']}{Colors.RESET}")
        
        print(f"\n{Colors.BOLD}Policy Actions:{Colors.RESET}")
        for action, count in data['policyActions'].items():
            print(f"  {action}: {count}")
        
        print(f"\n{Colors.BOLD}Budget:{Colors.RESET}")
        print(f"  Total Allocated: {data['totalAllocatedBudget']} MNEE")
        print(f"  Total Spent: {data['totalSpent']} MNEE")
        
        print(f"\n{Colors.BOLD}System:{Colors.RESET}")
        print(f"  Agents: {data['agentCount']}")
        print(f"  Services: {data['serviceCount']}")
    
    # ==================== HEALTH COMMANDS ====================
    
    def health_check(self):
        """Perform health check"""
        self._header("System Health Check")
        
        services = {
            "Backend API": "http://localhost:8000/",
            "ImageGen": "http://localhost:8001/docs",
            "PriceOracle": "http://localhost:8002/docs",
            "BatchCompute": "http://localhost:8003/docs",
            "LogArchive": "http://localhost:8004/docs",
        }
        
        for name, url in services.items():
            try:
                response = requests.get(url, timeout=3)
                if response.status_code == 200:
                    self._success(f"{name:20} - OK")
                else:
                    self._warning(f"{name:20} - HTTP {response.status_code}")
            except requests.exceptions.RequestException:
                self._error(f"{name:20} - FAILED")
    
    # ==================== MONITOR COMMANDS ====================
    
    def monitor_realtime(self, interval: int = 5):
        """Real-time monitoring"""
        print(f"{Colors.CYAN}Real-time Monitoring (Refresh every {interval}s, Ctrl+C to exit){Colors.RESET}\n")
        
        try:
            while True:
                # Clear screen
                print("\033[2J\033[H")
                
                self._header(f"Real-time Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Treasury status
                treasury = self._request("GET", "/treasury")
                print(f"{Colors.BOLD}Treasury:{Colors.RESET}")
                print(f"  Allocated: {treasury['totalAllocated']} MNEE | Spent: {treasury['totalSpent']} MNEE")
                
                # Recent transactions
                print(f"\n{Colors.BOLD}Recent Transactions:{Colors.RESET}")
                txs = self._request("GET", "/transactions?limit=5")
                for tx in txs['transactions']:
                    print(f"  {tx['timestamp'][:19]} | {tx['agent_id']:12} | {tx['service_id']:18} | {tx['amount']} MNEE")
                
                # Recent policy decisions
                print(f"\n{Colors.BOLD}Recent Policy Decisions:{Colors.RESET}")
                policies = self._request("GET", "/policy/logs?limit=5")
                for log in policies['logs']:
                    print(f"  {log['timestamp'][:19]} | {log['action']:10} | {log['agent_id']:12} | {log['service_id']}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n{Colors.CYAN}Monitoring stopped.{Colors.RESET}")

def main():
    parser = argparse.ArgumentParser(
        description="MNEE Nexus Admin CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--url', default='http://localhost:8000', help='Backend API URL')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Agent commands
    agent_parser = subparsers.add_parser('agent', help='Agent management')
    agent_subparsers = agent_parser.add_subparsers(dest='subcommand')
    
    agent_subparsers.add_parser('list', help='List all agents')
    
    agent_show_parser = agent_subparsers.add_parser('show', help='Show agent details')
    agent_show_parser.add_argument('agent_id', help='Agent ID')
    
    agent_update_parser = agent_subparsers.add_parser('update', help='Update agent budget')
    agent_update_parser.add_argument('agent_id', help='Agent ID')
    agent_update_parser.add_argument('--daily-budget', type=float, help='Daily budget')
    agent_update_parser.add_argument('--max-per-call', type=float, help='Max per call')
    
    # Service commands
    service_parser = subparsers.add_parser('service', help='Service management')
    service_subparsers = service_parser.add_subparsers(dest='subcommand')
    
    service_subparsers.add_parser('list', help='List all services')
    
    service_show_parser = service_subparsers.add_parser('show', help='Show service details')
    service_show_parser.add_argument('service_id', help='Service ID')
    
    # Treasury commands
    treasury_parser = subparsers.add_parser('treasury', help='Treasury operations')
    treasury_subparsers = treasury_parser.add_subparsers(dest='subcommand')
    
    treasury_subparsers.add_parser('status', help='Show treasury status')
    treasury_subparsers.add_parser('reset', help='Reset daily budgets')
    
    # Logs commands
    logs_parser = subparsers.add_parser('logs', help='Log management')
    logs_subparsers = logs_parser.add_subparsers(dest='subcommand')
    
    logs_tx_parser = logs_subparsers.add_parser('transactions', help='Show transactions')
    logs_tx_parser.add_argument('--limit', type=int, default=20, help='Number of entries')
    
    logs_policy_parser = logs_subparsers.add_parser('policy', help='Show policy decisions')
    logs_policy_parser.add_argument('--limit', type=int, default=20, help='Number of entries')
    
    # Stats commands
    stats_parser = subparsers.add_parser('stats', help='System statistics')
    
    # Health commands
    health_parser = subparsers.add_parser('health', help='Health check')
    
    # Monitor commands
    monitor_parser = subparsers.add_parser('monitor', help='Real-time monitoring')
    monitor_parser.add_argument('--interval', type=int, default=5, help='Refresh interval (seconds)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    cli = MNEECli(base_url=args.url)
    
    # Route commands
    if args.command == 'agent':
        if args.subcommand == 'list':
            cli.agent_list()
        elif args.subcommand == 'show':
            cli.agent_show(args.agent_id)
        elif args.subcommand == 'update':
            cli.agent_update_budget(args.agent_id, args.daily_budget, args.max_per_call)
    
    elif args.command == 'service':
        if args.subcommand == 'list':
            cli.service_list()
        elif args.subcommand == 'show':
            cli.service_show(args.service_id)
    
    elif args.command == 'treasury':
        if args.subcommand == 'status':
            cli.treasury_status()
        elif args.subcommand == 'reset':
            cli.treasury_reset()
    
    elif args.command == 'logs':
        if args.subcommand == 'transactions':
            cli.logs_transactions(args.limit)
        elif args.subcommand == 'policy':
            cli.logs_policy(args.limit)
    
    elif args.command == 'stats':
        cli.stats_show()
    
    elif args.command == 'health':
        cli.health_check()
    
    elif args.command == 'monitor':
        cli.monitor_realtime(args.interval)

if __name__ == "__main__":
    main()
