"""
Workflow Service for Agricultural Document Processing
Purpose: Minimal but real workflow layer for status assignment and queue management
"""
from typing import Dict, Any, List, Optional
from enum import Enum


class WorkflowStatus(Enum):
    """Application workflow statuses"""
    AUTO_APPROVED = "AUTO_APPROVED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    PENDING_REVIEW = "PENDING_REVIEW"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"
    REJECTED = "REJECTED"
    APPROVED = "APPROVED"


class QueuePriority(Enum):
    """Queue priority levels"""
    HIGH_PRIORITY = "HIGH_PRIORITY"
    NORMAL = "NORMAL"
    LOW = "LOW"


class WorkflowService:
    """Minimal workflow service for status assignment and queue management"""
    
    def __init__(self):
        # Status transition rules
        self.status_rules = {
            "auto_approve": {
                "conditions": ["ml_insights.review_type == 'AUTO'", "decision == 'approve'"],
                "status": WorkflowStatus.AUTO_APPROVED
            },
            "high_priority": {
                "conditions": ["ml_insights.queue == 'HIGH_PRIORITY'"],
                "status": WorkflowStatus.PENDING_VERIFICATION
            },
            "manual_review": {
                "conditions": ["ml_insights.review_type == 'MANUAL'", "decision == 'review'"],
                "status": WorkflowStatus.MANUAL_REVIEW_REQUIRED
            },
            "default": {
                "conditions": [],
                "status": WorkflowStatus.PENDING_REVIEW
            }
        }
    
    def assign_status(self, application: Dict[str, Any]) -> str:
        """
        Assign workflow status based on ML insights and decision
        
        Args:
            application: Application data with ml_insights and decision
            
        Returns:
            Workflow status string
        """
        ml_insights = application.get("ml_insights", {})
        decision = application.get("decision", "review")
        
        # Check auto-approve conditions
        if (ml_insights.get("review_type") == "AUTO" and 
            decision == "approve" and 
            ml_insights.get("priority_score", 0) > 0.7):
            return WorkflowStatus.AUTO_APPROVED.value
        
        # Check high priority conditions
        if ml_insights.get("queue") == "HIGH_PRIORITY":
            return WorkflowStatus.PENDING_VERIFICATION.value
        
        # Check manual review conditions
        if (ml_insights.get("review_type") == "MANUAL" or 
            decision == "review" or 
            ml_insights.get("risk_level") == "High"):
            return WorkflowStatus.MANUAL_REVIEW_REQUIRED.value
        
        # Default status
        return WorkflowStatus.PENDING_REVIEW.value
    
    def build_queue(self, application: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build queue information for application
        
        Args:
            application: Application data
            
        Returns:
            Queue information dictionary
        """
        ml_insights = application.get("ml_insights", {})
        status = self.assign_status(application)
        
        return {
            "application_id": application.get("id"),
            "status": status,
            "priority": ml_insights.get("queue", "NORMAL"),
            "risk": ml_insights.get("risk_level", "Medium"),
            "review_type": ml_insights.get("review_type", "AUTO"),
            "estimated_processing_time": ml_insights.get("processing_time", "2 days"),
            "approval_likelihood": ml_insights.get("approval_likelihood", "50%")
        }
    
    def get_workflow_summary(self, application: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get complete workflow summary for application
        
        Args:
            application: Application data
            
        Returns:
            Complete workflow summary
        """
        queue_info = self.build_queue(application)
        
        return {
            "workflow": {
                "status": queue_info["status"],
                "queue": queue_info["priority"],
                "estimated_processing_time": queue_info["estimated_processing_time"],
                "requires_manual_review": queue_info["review_type"] == "MANUAL",
                "risk_level": queue_info["risk"]
            },
            "next_steps": self._get_next_steps(queue_info),
            "sla_timeline": self._get_sla_timeline(queue_info)
        }
    
    def _get_next_steps(self, queue_info: Dict[str, Any]) -> List[str]:
        """Get next steps based on queue information"""
        steps = []
        
        if queue_info["status"] == WorkflowStatus.AUTO_APPROVED.value:
            steps = ["Application automatically approved", "Generate approval letter", "Schedule payment processing"]
        elif queue_info["status"] == WorkflowStatus.PENDING_VERIFICATION.value:
            steps = ["Priority verification required", "Document authenticity check", "Cross-reference with databases"]
        elif queue_info["status"] == WorkflowStatus.MANUAL_REVIEW_REQUIRED.value:
            steps = ["Assign to reviewing officer", "Manual document verification", "Officer decision required"]
        else:
            steps = ["Standard processing queue", "Automated validation", "Routine review"]
        
        return steps
    
    def _get_sla_timeline(self, queue_info: Dict[str, Any]) -> Dict[str, str]:
        """Get SLA timeline based on queue information"""
        priority = queue_info["priority"]
        
        if priority == "HIGH_PRIORITY":
            return {
                "initial_review": "24 hours",
                "final_decision": "48 hours",
                "total_processing": "2-3 business days"
            }
        elif priority == "NORMAL":
            return {
                "initial_review": "3-5 business days",
                "final_decision": "7-10 business days",
                "total_processing": "2 weeks"
            }
        else:  # LOW
            return {
                "initial_review": "7-10 business days",
                "final_decision": "14-21 business days",
                "total_processing": "3-4 weeks"
            }
    
    def update_application_status(self, application: Dict[str, Any], new_status: str) -> Dict[str, Any]:
        """
        Update application status and return updated workflow
        
        Args:
            application: Current application data
            new_status: New status to assign
            
        Returns:
            Updated workflow information
        """
        # Update application status
        application["status"] = new_status
        
        # Recalculate workflow
        return self.get_workflow_summary(application)
    
    def get_queue_statistics(self, applications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get queue statistics for batch of applications
        
        Args:
            applications: List of applications
            
        Returns:
            Queue statistics
        """
        stats = {
            "total_applications": len(applications),
            "by_status": {},
            "by_priority": {},
            "by_risk": {},
            "processing_times": {}
        }
        
        for app in applications:
            workflow = self.get_workflow_summary(app)
            wf = workflow["workflow"]
            
            # Count by status
            status = wf["status"]
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # Count by priority
            priority = wf["queue"]
            stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1
            
            # Count by risk
            risk = wf["risk_level"]
            stats["by_risk"][risk] = stats["by_risk"].get(risk, 0) + 1
            
            # Processing time estimates
            time = wf["estimated_processing_time"]
            stats["processing_times"][time] = stats["processing_times"].get(time, 0) + 1
        
        return stats
