#!/bin/bash

# MNEE Agent Cost & Billing Hub - Demo Walkthrough Script
# For MNEE Hackathon 2025 - AI & Agent Payments Track

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "\n${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}\n"
}

print_step() {
    echo -e "${GREEN}[STEP $1]${NC} $2"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_demo() {
    echo -e "${YELLOW}[DEMO]${NC} $1"
}

wait_for_user() {
    echo -e "\n${YELLOW}Press Enter to continue...${NC}"
    read -r
}

API_BASE="http://localhost:8000"

# Check if services are running
check_services() {
    print_header "Checking Services"

    services=("8000:Backend" "8100:Guardian" "8001:ImageGen" "8002:PriceOracle" "8003:BatchCompute" "8004:LogArchive")

    for service in "${services[@]}"; do
        port="${service%%:*}"
        name="${service##*:}"
        if curl -s "http://localhost:$port/" > /dev/null 2>&1; then
            echo -e "${GREEN}[OK]${NC} $name (port $port)"
        else
            echo -e "${RED}[FAIL]${NC} $name (port $port) - Please run ./start_all.sh first"
            exit 1
        fi
    done

    echo -e "\n${GREEN}All services are running!${NC}"
}

# Demo 1: Check Treasury Status
demo_treasury() {
    print_header "Demo 1: Treasury & Agent Budgets"

    print_step 1 "Fetching treasury status..."
    echo -e "${CYAN}curl $API_BASE/treasury${NC}\n"

    response=$(curl -s "$API_BASE/treasury" | python3 -m json.tool)
    echo "$response"

    print_info "This shows all agents with their daily budgets and current spending."
    print_info "Each agent has a priority level (HIGH/MEDIUM/LOW) that affects policy decisions."
}

# Demo 2: Service Catalog
demo_services() {
    print_header "Demo 2: Service Provider Catalog"

    print_step 2 "Fetching available services..."
    echo -e "${CYAN}curl $API_BASE/services${NC}\n"

    response=$(curl -s "$API_BASE/services" | python3 -m json.tool)
    echo "$response"

    print_info "Each service has a unit price in MNEE."
    print_info "Services can be verified, have spending limits, and agent restrictions."
}

# Demo 3: Execute a Chat Command
demo_chat() {
    print_header "Demo 3: Agent Task Execution"

    print_step 3 "Sending task to user-agent..."
    echo -e "${CYAN}curl -X POST $API_BASE/chat -d '{\"agent_id\":\"user-agent\",\"message\":\"Generate a cyberpunk avatar\"}'${NC}\n"

    response=$(curl -s -X POST "$API_BASE/chat" \
        -H "Content-Type: application/json" \
        -d '{"agent_id":"user-agent","message":"Generate a cyberpunk avatar"}' | python3 -m json.tool)
    echo "$response"

    print_info "The agent executed the task through the payment pipeline:"
    print_info "  1. Planner created execution plan"
    print_info "  2. Guardian checked risk and budget"
    print_info "  3. Executor called ImageGen service (1.0 MNEE)"
    print_info "  4. Payment recorded on-chain"
}

# Demo 4: A2A Payment
demo_a2a() {
    print_header "Demo 4: Agent-to-Agent (A2A) Payment"

    print_step 4 "Executing A2A payment: user-agent pays merchant-agent..."
    echo -e "${CYAN}curl -X POST $API_BASE/a2a/pay -d '{...}'${NC}\n"

    response=$(curl -s -X POST "$API_BASE/a2a/pay" \
        -H "Content-Type: application/json" \
        -d '{
            "from_agent": "user-agent",
            "to_agent": "merchant-agent",
            "amount": 5.0,
            "task_description": "Design marketing materials"
        }' | python3 -m json.tool)
    echo "$response"

    print_info "A2A payments enable agents to hire other agents!"
    print_info "The payment is recorded on-chain via MNEEAgentWallet contract."
}

# Demo 5: Check A2A Balances
demo_a2a_balances() {
    print_header "Demo 5: Agent Wallet Balances"

    print_step 5 "Fetching agent wallet balances..."
    echo -e "${CYAN}curl $API_BASE/a2a/balances${NC}\n"

    response=$(curl -s "$API_BASE/a2a/balances" | python3 -m json.tool)
    echo "$response"

    print_info "These balances are stored on-chain in MNEEAgentWallet."
}

# Demo 6: Policy Logs
demo_policy() {
    print_header "Demo 6: Policy Enforcement Logs"

    print_step 6 "Fetching recent policy decisions..."
    echo -e "${CYAN}curl $API_BASE/policy/logs${NC}\n"

    response=$(curl -s "$API_BASE/policy/logs" | python3 -m json.tool)
    echo "$response"

    print_info "Every transaction is checked against policy rules:"
    print_info "  - ALLOW: Transaction approved"
    print_info "  - DENY: Transaction blocked (budget exceeded)"
    print_info "  - DOWNGRADE: Switched to cheaper service"
}

# Demo 7: Escrow List
demo_escrow() {
    print_header "Demo 7: Escrow Transactions"

    print_step 7 "Fetching escrow list..."
    echo -e "${CYAN}curl $API_BASE/escrow/list${NC}\n"

    response=$(curl -s "$API_BASE/escrow/list" | python3 -m json.tool)
    echo "$response"

    print_info "Escrows implement trustless transactions:"
    print_info "  1. Customer locks funds"
    print_info "  2. Merchant submits work"
    print_info "  3. Verifier validates output"
    print_info "  4. Funds released or refunded"
}

# Demo 8: Agent Registry
demo_registry() {
    print_header "Demo 8: Agent Registry (Labor Market)"

    print_step 8 "Fetching registered agents..."
    echo -e "${CYAN}curl $API_BASE/registry/agents${NC}\n"

    response=$(curl -s "$API_BASE/registry/agents" | python3 -m json.tool)
    echo "$response"

    print_info "The registry enables agent discovery by capability."
    print_info "Agents are ranked by reputation and success rate."
}

# Demo 9: Budget Exhaustion (Failure Scenario)
demo_failure() {
    print_header "Demo 9: Budget Exhaustion (Failure Scenario)"

    print_step 9 "Simulating budget exhaustion for batch-agent..."

    # batch-agent has lower budget - try expensive operation
    echo -e "${CYAN}Attempting expensive batch compute operation...${NC}\n"

    response=$(curl -s -X POST "$API_BASE/chat" \
        -H "Content-Type: application/json" \
        -d '{"agent_id":"batch-agent","message":"Run 50 batch compute jobs"}' | python3 -m json.tool)
    echo "$response"

    print_info "Policy engine may DENY or DOWNGRADE based on remaining budget."
    print_info "This prevents runaway agent spending!"
}

# Demo 10: Reset Budgets
demo_reset() {
    print_header "Demo 10: Reset Daily Budgets"

    print_step 10 "Resetting all agent daily spending..."
    echo -e "${CYAN}curl -X POST $API_BASE/reset${NC}\n"

    response=$(curl -s -X POST "$API_BASE/reset" | python3 -m json.tool)
    echo "$response"

    print_info "Daily budgets reset (simulates start of new day)."
}

# Main Demo Flow
main() {
    clear
    print_header "MNEE Agent Cost & Billing Hub - Demo"
    echo -e "${YELLOW}The Financial Operating System for AI Agent Teams${NC}"
    echo -e "Built for MNEE Hackathon 2025 - AI & Agent Payments Track\n"

    echo "This demo will walk you through:"
    echo "  1. Treasury & Agent Budgets"
    echo "  2. Service Provider Catalog"
    echo "  3. Agent Task Execution (with payment)"
    echo "  4. Agent-to-Agent (A2A) Payment"
    echo "  5. Agent Wallet Balances"
    echo "  6. Policy Enforcement Logs"
    echo "  7. Escrow Transactions"
    echo "  8. Agent Registry (Labor Market)"
    echo "  9. Budget Exhaustion (Failure)"
    echo " 10. Reset Daily Budgets"

    wait_for_user

    check_services
    wait_for_user

    demo_treasury
    wait_for_user

    demo_services
    wait_for_user

    demo_chat
    wait_for_user

    demo_a2a
    wait_for_user

    demo_a2a_balances
    wait_for_user

    demo_policy
    wait_for_user

    demo_escrow
    wait_for_user

    demo_registry
    wait_for_user

    demo_failure
    wait_for_user

    demo_reset
    wait_for_user

    print_header "Demo Complete!"
    echo -e "${GREEN}Thank you for watching!${NC}\n"
    echo "Key Features Demonstrated:"
    echo "  - Multi-agent budget coordination"
    echo "  - Autonomous MNEE payments"
    echo "  - A2A commerce (agents hiring agents)"
    echo "  - Escrow-Verify-Release protocol"
    echo "  - Policy enforcement and audit trails"
    echo ""
    echo "Frontend Dashboard: http://localhost:3000"
    echo "API Documentation: http://localhost:8000/docs"
    echo ""
    echo -e "${CYAN}MNEE Contract: 0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF${NC}"
}

# Run specific demo or all
case "${1:-all}" in
    treasury) demo_treasury ;;
    services) demo_services ;;
    chat) demo_chat ;;
    a2a) demo_a2a ;;
    balances) demo_a2a_balances ;;
    policy) demo_policy ;;
    escrow) demo_escrow ;;
    registry) demo_registry ;;
    failure) demo_failure ;;
    reset) demo_reset ;;
    check) check_services ;;
    all) main ;;
    *)
        echo "Usage: $0 [treasury|services|chat|a2a|balances|policy|escrow|registry|failure|reset|check|all]"
        exit 1
        ;;
esac
