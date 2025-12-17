"""
Deployment Approval Workflow

Implements approval workflow for deployments to prevent unauthorized infrastructure changes.

Features:
- Multi-stage approval
- Approval history
- Configurable approval rules
- Email notifications (optional)
- Approval expiration
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from pathlib import Path
from app.auth.auth_provider import User, UserRole
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class ApprovalStatus(str, Enum):
    """Approval status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass
class ApprovalRequest:
    """Deployment approval request"""
    request_id: str
    deployment_id: str
    requester_user_id: str
    requester_email: str
    config: Dict[str, Any]
    estimated_cost: float
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "request_id": self.request_id,
            "deployment_id": self.deployment_id,
            "requester_user_id": self.requester_user_id,
            "requester_email": self.requester_email,
            "config": self.config,
            "estimated_cost": self.estimated_cost,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "rejection_reason": self.rejection_reason,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ApprovalRequest":
        """Create from dictionary"""
        return cls(
            request_id=data["request_id"],
            deployment_id=data["deployment_id"],
            requester_user_id=data["requester_user_id"],
            requester_email=data["requester_email"],
            config=data["config"],
            estimated_cost=data["estimated_cost"],
            status=ApprovalStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            approved_by=data.get("approved_by"),
            approved_at=datetime.fromisoformat(data["approved_at"]) if data.get("approved_at") else None,
            rejection_reason=data.get("rejection_reason"),
        )


class ApprovalWorkflow:
    """
    Deployment approval workflow manager
    
    Manages approval requests for deployments with configurable rules.
    """
    
    def __init__(self, storage_path: str = "./data/approvals"):
        """
        Initialize approval workflow
        
        Args:
            storage_path: Path to store approval requests
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Approval rules
        self.rules = {
            "require_approval_for_all": False,  # Require approval for all deployments
            "require_approval_above_cost": 100.0,  # Require approval if cost > $100/month
            "approval_expiry_hours": 24,  # Approval requests expire after 24 hours
            "auto_approve_admins": True,  # Admins don't need approval
            "required_approvers": 1,  # Number of approvers required
        }
        
        logger.info(f"Initialized ApprovalWorkflow at {storage_path}")
    
    def requires_approval(self, user: User, estimated_cost: float) -> bool:
        """
        Check if deployment requires approval
        
        Args:
            user: User requesting deployment
            estimated_cost: Estimated monthly cost
            
        Returns:
            True if approval required
        """
        # Admins auto-approved if configured
        if self.rules["auto_approve_admins"] and user.role == UserRole.ADMIN:
            return False
        
        # Check if approval required for all
        if self.rules["require_approval_for_all"]:
            return True
        
        # Check cost threshold
        if estimated_cost > self.rules["require_approval_above_cost"]:
            return True
        
        return False
    
    def create_approval_request(
        self,
        deployment_id: str,
        requester: User,
        config: Dict[str, Any],
        estimated_cost: float,
    ) -> ApprovalRequest:
        """
        Create new approval request
        
        Args:
            deployment_id: Deployment ID
            requester: User requesting deployment
            config: Deployment configuration
            estimated_cost: Estimated monthly cost
            
        Returns:
            ApprovalRequest object
        """
        import secrets
        
        # Generate request ID
        request_id = f"apr_{secrets.token_hex(8)}"
        
        # Calculate expiry
        expires_at = datetime.now() + timedelta(hours=self.rules["approval_expiry_hours"])
        
        # Create request
        request = ApprovalRequest(
            request_id=request_id,
            deployment_id=deployment_id,
            requester_user_id=requester.user_id,
            requester_email=requester.email,
            config=config,
            estimated_cost=estimated_cost,
            expires_at=expires_at,
        )
        
        # Save request
        self._save_request(request)
        
        logger.info(f"Created approval request: {request_id} for deployment: {deployment_id}")
        
        # TODO: Send notification to approvers (Phase 1.4)
        
        return request
    
    def approve_request(self, request_id: str, approver: User) -> bool:
        """
        Approve deployment request
        
        Args:
            request_id: Request ID to approve
            approver: User approving the request
            
        Returns:
            True if approved successfully
        """
        request = self.get_request(request_id)
        
        if not request:
            logger.error(f"Approval request not found: {request_id}")
            return False
        
        # Check if already processed
        if request.status != ApprovalStatus.PENDING:
            logger.warning(f"Request already processed: {request_id} (status: {request.status})")
            return False
        
        # Check if expired
        if request.expires_at and datetime.now() > request.expires_at:
            request.status = ApprovalStatus.EXPIRED
            self._save_request(request)
            logger.warning(f"Request expired: {request_id}")
            return False
        
        # Check if approver has permission
        if approver.role not in [UserRole.ADMIN, UserRole.DEPLOYER]:
            logger.warning(f"User {approver.email} not authorized to approve")
            return False
        
        # Approve request
        request.status = ApprovalStatus.APPROVED
        request.approved_by = approver.user_id
        request.approved_at = datetime.now()
        
        self._save_request(request)
        
        logger.info(f"Approved request: {request_id} by {approver.email}")
        
        # TODO: Send notification to requester (Phase 1.4)
        
        return True
    
    def reject_request(self, request_id: str, approver: User, reason: str) -> bool:
        """
        Reject deployment request
        
        Args:
            request_id: Request ID to reject
            approver: User rejecting the request
            reason: Rejection reason
            
        Returns:
            True if rejected successfully
        """
        request = self.get_request(request_id)
        
        if not request:
            return False
        
        # Check if already processed
        if request.status != ApprovalStatus.PENDING:
            return False
        
        # Reject request
        request.status = ApprovalStatus.REJECTED
        request.approved_by = approver.user_id
        request.approved_at = datetime.now()
        request.rejection_reason = reason
        
        self._save_request(request)
        
        logger.info(f"Rejected request: {request_id} by {approver.email}")
        
        # TODO: Send notification to requester (Phase 1.4)
        
        return True
    
    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get approval request by ID"""
        request_file = self.storage_path / f"{request_id}.json"
        
        if not request_file.exists():
            return None
        
        with open(request_file, "r") as f:
            data = json.load(f)
        
        return ApprovalRequest.from_dict(data)
    
    def list_pending_requests(self) -> List[ApprovalRequest]:
        """List all pending approval requests"""
        requests = []
        
        for request_file in self.storage_path.glob("apr_*.json"):
            with open(request_file, "r") as f:
                data = json.load(f)
            
            request = ApprovalRequest.from_dict(data)
            
            # Check if expired
            if request.status == ApprovalStatus.PENDING:
                if request.expires_at and datetime.now() > request.expires_at:
                    request.status = ApprovalStatus.EXPIRED
                    self._save_request(request)
                else:
                    requests.append(request)
        
        # Sort by creation time (oldest first)
        requests.sort(key=lambda r: r.created_at)
        
        return requests
    
    def list_user_requests(self, user_id: str) -> List[ApprovalRequest]:
        """List all requests by a specific user"""
        requests = []
        
        for request_file in self.storage_path.glob("apr_*.json"):
            with open(request_file, "r") as f:
                data = json.load(f)
            
            request = ApprovalRequest.from_dict(data)
            
            if request.requester_user_id == user_id:
                requests.append(request)
        
        # Sort by creation time (newest first)
        requests.sort(key=lambda r: r.created_at, reverse=True)
        
        return requests
    
    def _save_request(self, request: ApprovalRequest):
        """Save approval request to disk"""
        request_file = self.storage_path / f"{request.request_id}.json"
        
        with open(request_file, "w") as f:
            json.dump(request.to_dict(), f, indent=2)
    
    def update_rules(self, rules: Dict[str, Any]):
        """Update approval rules"""
        self.rules.update(rules)
        logger.info(f"Updated approval rules: {rules}")
