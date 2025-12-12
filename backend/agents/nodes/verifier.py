"""
Verifier Node - AI-Powered Task Verification

Implements the three-layer verification architecture:
1. Local Optimistic Verification - Fast, cheap, handles 95% of cases
2. Third-party AI Verification - For disputed cases (Autonolas Mech)
3. Human/Social Arbitration - Final appeal layer (UMA Oracle)

This node runs after Executor and before Escrow Release to determine
whether task outputs meet requirements.
"""

import os
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from ..state import GraphState, StepRecord


class VerificationResult:
    """Result of task verification."""
    def __init__(
        self,
        passed: bool,
        score: float,
        reason: str,
        layer: str = "local"
    ):
        self.passed = passed
        self.score = score  # 0.0 to 1.0
        self.reason = reason
        self.layer = layer  # "local", "ai_network", "oracle"
        self.timestamp = datetime.now().isoformat()


class LocalVerifier:
    """
    Layer 1: Local Optimistic Verification
    
    Fast, cheap verification using heuristics and lightweight AI.
    Handles ~95% of normal transactions.
    """
    
    def __init__(self, llm=None):
        self.llm = llm
        self.threshold = 0.7  # Minimum score to pass
    
    def verify(
        self,
        task_description: str,
        tool_name: str,
        output: Dict[str, Any]
    ) -> VerificationResult:
        """
        Verify task output locally.
        
        Checks:
        1. Output is non-empty
        2. No error messages
        3. Output format matches expected
        4. Basic semantic alignment with task
        """
        # Check 1: Non-empty output
        if not output:
            return VerificationResult(
                passed=False,
                score=0.0,
                reason="Empty output",
                layer="local"
            )
        
        # Check 2: No errors
        if output.get("error") or output.get("_error"):
            return VerificationResult(
                passed=False,
                score=0.1,
                reason=f"Output contains error: {output.get('error') or output.get('_error')}",
                layer="local"
            )
        
        # Check 3: Tool-specific validation
        score, reason = self._validate_tool_output(tool_name, output)
        
        # Check 4: Semantic alignment (if LLM available)
        if self.llm and score >= 0.5:
            semantic_score = self._semantic_check(task_description, output)
            score = (score + semantic_score) / 2
        
        passed = score >= self.threshold
        
        return VerificationResult(
            passed=passed,
            score=score,
            reason=reason if not passed else "Verification passed",
            layer="local"
        )
    
    def _validate_tool_output(self, tool_name: str, output: Dict[str, Any]) -> Tuple[float, str]:
        """Tool-specific output validation."""
        
        if tool_name == "image_gen":
            # Check for image URL or data
            if output.get("image_url") or output.get("url") or output.get("data"):
                return 0.9, "Valid image output"
            return 0.3, "Missing image URL/data"
        
        elif tool_name == "price_oracle":
            # Check for price data
            if output.get("price") is not None or output.get("prices"):
                return 0.9, "Valid price data"
            return 0.3, "Missing price information"
        
        elif tool_name == "batch_compute":
            # Check for computation results
            if output.get("results") or output.get("data") or output.get("output"):
                return 0.9, "Valid computation results"
            return 0.3, "Missing computation results"
        
        elif tool_name == "log_archive":
            # Check for archive confirmation
            if output.get("archived") or output.get("success") or output.get("cid"):
                return 0.9, "Archive confirmed"
            return 0.3, "Archive not confirmed"
        
        else:
            # Generic validation
            if len(output) > 0 and not output.get("error"):
                return 0.8, "Output present"
            return 0.4, "Generic validation"
    
    def _semantic_check(self, task_description: str, output: Dict[str, Any]) -> float:
        """
        Use LLM to check semantic alignment between task and output.
        
        This is a lightweight check - the full version would use
        embedding similarity or a dedicated critic model.
        """
        try:
            # Simple heuristic: check if output mentions key terms from task
            task_terms = set(task_description.lower().split())
            output_str = str(output).lower()
            
            matches = sum(1 for term in task_terms if term in output_str)
            return min(matches / max(len(task_terms), 1), 1.0)
        except:
            return 0.5


class AINetworkVerifier:
    """
    Layer 2: Third-party AI Verification Network
    
    For disputed cases, uses decentralized AI verification (e.g., Autonolas Mech).
    More expensive but provides neutral third-party judgment.
    """
    
    def __init__(self, mech_endpoint: str = None):
        self.mech_endpoint = mech_endpoint or os.getenv("AUTONOLAS_MECH_ENDPOINT")
    
    def verify(
        self,
        task_description: str,
        tool_name: str,
        output: Dict[str, Any],
        requirement_hash: str = None
    ) -> VerificationResult:
        """
        Request verification from AI network.
        
        In production, this would:
        1. Submit task + output to Mech market
        2. Wait for Mech nodes to run verification scripts
        3. Receive signed verification result
        """
        # Simulated AI network verification
        # In production: call Autonolas Mech API
        
        print(f"    [VERIFIER] Requesting AI network verification...")
        
        # Simulate network delay and verification
        import time
        time.sleep(0.5)  # Simulated delay
        
        # Simple heuristic for demo
        has_result = bool(output and not output.get("error"))
        score = 0.85 if has_result else 0.2
        
        return VerificationResult(
            passed=score >= 0.7,
            score=score,
            reason="AI network consensus" if score >= 0.7 else "AI network rejected",
            layer="ai_network"
        )


class OracleVerifier:
    """
    Layer 3: Human/Social Arbitration (UMA Oracle)
    
    Final appeal layer for high-stakes disputes.
    Uses human voters to determine outcome.
    """
    
    def __init__(self, uma_endpoint: str = None):
        self.uma_endpoint = uma_endpoint or os.getenv("UMA_ORACLE_ENDPOINT")
    
    def submit_dispute(
        self,
        escrow_id: str,
        task_description: str,
        output: Dict[str, Any],
        dispute_reason: str
    ) -> str:
        """
        Submit dispute to UMA Optimistic Oracle.
        
        Returns a dispute ID for tracking resolution.
        """
        # In production: call UMA DVM API
        dispute_id = f"DISPUTE-{escrow_id}"
        print(f"    [VERIFIER] Submitted to oracle: {dispute_id}")
        return dispute_id
    
    def check_resolution(self, dispute_id: str) -> Optional[VerificationResult]:
        """
        Check if oracle has resolved the dispute.
        
        Returns None if still pending, or VerificationResult if resolved.
        """
        # In production: query UMA for resolution
        # For demo: return simulated result
        return VerificationResult(
            passed=True,
            score=1.0,
            reason="Oracle resolution: approved",
            layer="oracle"
        )


class HybridVerifier:
    """
    Main verifier that implements the three-layer verification funnel.
    
    95% of cases resolve at Layer 1 (local)
    4% escalate to Layer 2 (AI network)
    1% escalate to Layer 3 (oracle)
    """
    
    def __init__(self, llm=None):
        self.local = LocalVerifier(llm)
        self.ai_network = AINetworkVerifier()
        self.oracle = OracleVerifier()
    
    def verify(
        self,
        task_description: str,
        tool_name: str,
        output: Dict[str, Any],
        force_layer: str = None
    ) -> VerificationResult:
        """
        Run verification through the funnel.
        
        Starts with local verification, escalates if needed.
        """
        # Layer 1: Local verification
        result = self.local.verify(task_description, tool_name, output)
        
        if force_layer == "ai_network" or (not result.passed and result.score >= 0.3):
            # Escalate to AI network for borderline cases
            result = self.ai_network.verify(
                task_description, tool_name, output
            )
        
        # Layer 3 is triggered manually through dispute process
        
        return result


# Singleton instance
_verifier: Optional[HybridVerifier] = None


def get_verifier(llm=None) -> HybridVerifier:
    global _verifier
    if _verifier is None:
        _verifier = HybridVerifier(llm)
    return _verifier


def verifier_node(state: GraphState, verifier: HybridVerifier = None) -> GraphState:
    """
    LangGraph node: Verify task outputs before escrow release.
    
    This node runs after Executor and before Escrow Release.
    It determines whether each step's output meets requirements.
    """
    print(f"\n[VERIFIER_NODE] Verifying {len(state.steps)} step outputs")
    
    if verifier is None:
        verifier = get_verifier()
    
    verification_summary = {
        "total": len(state.steps),
        "passed": 0,
        "failed": 0,
        "skipped": 0
    }
    
    for step in state.steps:
        # Skip already finalized steps
        if step.status in ["denied"]:
            verification_summary["skipped"] += 1
            continue
        
        # Get task description from plan
        task_desc = step.description or ""
        for plan_step in state.plan:
            if plan_step.step_id == step.step_id:
                task_desc = plan_step.description
                break
        
        # Run verification
        result = verifier.verify(
            task_description=task_desc,
            tool_name=step.tool_name or "",
            output=step.output or {}
        )
        
        # Update step with verification results
        # Store in output metadata
        if step.output is None:
            step.output = {}
        
        step.output["_verification"] = {
            "passed": result.passed,
            "score": result.score,
            "reason": result.reason,
            "layer": result.layer,
            "timestamp": result.timestamp
        }
        
        if result.passed:
            verification_summary["passed"] += 1
            print(f"  > Step {step.step_id}: PASSED (score={result.score:.2f})")
        else:
            verification_summary["failed"] += 1
            # Don't change status to failed - let escrow handle refund
            print(f"  > Step {step.step_id}: FAILED (score={result.score:.2f}, reason={result.reason})")
    
    # Store summary in state
    if not hasattr(state, 'verification_summary'):
        state.messages.append({
            "role": "system",
            "content": f"Verification complete: {verification_summary['passed']}/{verification_summary['total']} passed"
        })
    
    print(f"\n[VERIFIER_NODE] Summary: {verification_summary['passed']}/{verification_summary['total']} passed")
    
    return state
