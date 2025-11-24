"""
Merchant Agent - Service Provider

Responsibilities:
- Provide quotes for services
- Verify payments
- Deliver services after payment confirmation
- Track service delivery metrics
"""

import uuid
import time
from typing import Dict, Optional
from datetime import datetime


class MerchantAgent:
    """
    Merchant Agent - Provides services and manages fulfillment

    The Merchant Agent acts as a service provider that:
    1. Provides quotes for requested services
    2. Verifies payment completion
    3. Delivers the actual service
    """

    def __init__(self, merchant_id: str = "merchant-1", services: Dict = None):
        self.merchant_id = merchant_id
        self.services = services or {
            "IMAGE_GEN_PREMIUM": {
                "unit_price_mnee": 1.0,
                "description": "Premium Cyberpunk Image Generation",
                "estimated_latency": "5s"
            },
            "PRICE_ORACLE": {
                "unit_price_mnee": 0.05,
                "description": "Real-time Price Data",
                "estimated_latency": "1s"
            },
            "BATCH_COMPUTE": {
                "unit_price_mnee": 3.0,
                "description": "Batch Computation Tasks",
                "estimated_latency": "30s"
            },
            "LOG_ARCHIVE": {
                "unit_price_mnee": 0.01,
                "description": "Log Storage and Archival",
                "estimated_latency": "2s"
            }
        }
        self.quotes_issued = []
        self.services_delivered = []

    def quote(self, service_id: str, payload: Dict) -> Dict:
        """
        Provide a quote for requested service

        Args:
            service_id: ID of service being requested
            payload: Service-specific parameters

        Returns:
            Quote details including price and terms
        """
        if service_id not in self.services:
            raise ValueError(f"Service {service_id} not offered by merchant {self.merchant_id}")

        service_info = self.services[service_id]
        quote_id = f"quote-{uuid.uuid4().hex[:8]}"

        quote = {
            "quote_id": quote_id,
            "merchant_id": self.merchant_id,
            "service_id": service_id,
            "unit_price_mnee": service_info["unit_price_mnee"],
            "estimated_latency": service_info["estimated_latency"],
            "terms": f"Valid for 5 minutes. {service_info['description']}",
            "expires_at": int(time.time()) + 300,  # 5 minutes
            "created_at": datetime.now().isoformat()
        }

        self.quotes_issued.append(quote)
        print(f"[MERCHANT-{self.merchant_id}] Issued quote {quote_id} for {service_id}: {service_info['unit_price_mnee']} MNEE")

        return quote

    def fulfill(
        self,
        service_id: str,
        task_id: str,
        payment_id: str,
        service_call_hash: str,
        payload: Dict
    ) -> Dict:
        """
        Deliver service after payment verification

        In production, this would:
        1. Verify payment on-chain
        2. Execute actual service (call Stable Diffusion, etc.)
        3. Return real results

        For MVP, we return mock data.

        Args:
            service_id: ID of service to deliver
            task_id: Task identifier
            payment_id: On-chain payment ID
            service_call_hash: Hash binding payment to service call
            payload: Service parameters

        Returns:
            Service delivery result
        """
        print(f"[MERCHANT-{self.merchant_id}] Fulfilling service {service_id} for task {task_id}")
        print(f"[MERCHANT-{self.merchant_id}] Payment ID: {payment_id}, Hash: {service_call_hash}")

        # TODO: Verify payment on-chain
        # For now, trust the customer
        time.sleep(0.5)  # Simulate service execution time

        # Generate service-specific results
        result_data = {}

        if service_id == "IMAGE_GEN_PREMIUM":
            result_data = {
                "image_url": f"https://ipfs.io/ipfs/Qm{uuid.uuid4().hex[:20]}",
                "prompt": payload.get("prompt", "cyberpunk avatar"),
                "style": payload.get("style", "cyberpunk"),
                "resolution": "1024x1024",
                "generated_at": datetime.now().isoformat()
            }

        elif service_id == "PRICE_ORACLE":
            base = payload.get("base", "ETH")
            quote = payload.get("quote", "MNEE")
            result_data = {
                "base": base,
                "quote": quote,
                "price": 1234.56,  # Mock price
                "timestamp": datetime.now().isoformat(),
                "source": "mock_oracle"
            }

        elif service_id == "BATCH_COMPUTE":
            job_size = payload.get("jobSize", 10)
            result_data = {
                "job_id": f"job-{uuid.uuid4().hex[:8]}",
                "status": "completed",
                "items_processed": job_size,
                "result_summary": f"Processed {job_size} items successfully",
                "completed_at": datetime.now().isoformat()
            }

        elif service_id == "LOG_ARCHIVE":
            result_data = {
                "archive_id": f"archive-{uuid.uuid4().hex[:8]}",
                "status": "archived",
                "storage_location": "s3://merchant-logs/...",
                "retention_days": 30,
                "archived_at": datetime.now().isoformat()
            }

        else:
            result_data = {
                "status": "completed",
                "message": f"Mock result for {service_id}"
            }

        delivery_record = {
            "task_id": task_id,
            "service_id": service_id,
            "payment_id": payment_id,
            "service_call_hash": service_call_hash,
            "status": "delivered",
            "data": result_data,
            "delivered_at": datetime.now().isoformat()
        }

        self.services_delivered.append(delivery_record)
        print(f"[MERCHANT-{self.merchant_id}] Service delivered successfully")

        return delivery_record

    def get_merchant_stats(self) -> Dict:
        """Get statistics about merchant activity"""
        return {
            "merchant_id": self.merchant_id,
            "services_offered": len(self.services),
            "quotes_issued": len(self.quotes_issued),
            "services_delivered": len(self.services_delivered),
            "total_revenue": sum(
                self.services[d["service_id"]]["unit_price_mnee"]
                for d in self.services_delivered
                if d["service_id"] in self.services
            )
        }
