"""
Priority Assessment Engine

Collects user priorities to make intelligent cloud provider recommendations.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
import json
from pathlib import Path
from datetime import datetime


class PriorityType(str, Enum):
    """Priority categories"""
    COST = "cost"
    SECURITY = "security"
    PERFORMANCE = "performance"
    SCALABILITY = "scalability"
    COMPLIANCE = "compliance"
    AVAILABILITY = "availability"
    SUPPORT = "support"
    EASE_OF_USE = "ease_of_use"


class PriorityEngine:
    """Assess user priorities for cloud selection"""
    
    # Industry-specific priority questions
    INDUSTRY_QUESTIONS = {
        "fintech": [
            {
                "question": "How critical is regulatory compliance (PCI-DSS, SOC 2)?",
                "priority": PriorityType.COMPLIANCE,
                "weight": 0.3
            },
            {
                "question": "How important is data encryption and security?",
                "priority": PriorityType.SECURITY,
                "weight": 0.25
            },
            {
                "question": "What's your priority: cost optimization or maximum uptime?",
                "priority": PriorityType.COST,
                "weight": 0.15
            },
            {
                "question": "How critical is 99.99% availability?",
                "priority": PriorityType.AVAILABILITY,
                "weight": 0.2
            },
            {
                "question": "Do you need 24/7 enterprise support?",
                "priority": PriorityType.SUPPORT,
                "weight": 0.1
            }
        ],
        "healthtech": [
            {
                "question": "How critical is HIPAA compliance?",
                "priority": PriorityType.COMPLIANCE,
                "weight": 0.35
            },
            {
                "question": "How important is data residency (keeping data in specific regions)?",
                "priority": PriorityType.COMPLIANCE,
                "weight": 0.2
            },
            {
                "question": "How critical is PHI encryption and access controls?",
                "priority": PriorityType.SECURITY,
                "weight": 0.25
            },
            {
                "question": "What's more important: cost or compliance?",
                "priority": PriorityType.COST,
                "weight": 0.1
            },
            {
                "question": "How critical is high availability for patient data?",
                "priority": PriorityType.AVAILABILITY,
                "weight": 0.1
            }
        ],
        "ecommerce": [
            {
                "question": "How important is handling traffic spikes (Black Friday, sales)?",
                "priority": PriorityType.SCALABILITY,
                "weight": 0.3
            },
            {
                "question": "How critical is page load speed (<2 seconds)?",
                "priority": PriorityType.PERFORMANCE,
                "weight": 0.25
            },
            {
                "question": "What's your priority: lowest cost or best performance?",
                "priority": PriorityType.COST,
                "weight": 0.2
            },
            {
                "question": "How important is global CDN coverage?",
                "priority": PriorityType.PERFORMANCE,
                "weight": 0.15
            },
            {
                "question": "How critical is PCI-DSS compliance for payments?",
                "priority": PriorityType.COMPLIANCE,
                "weight": 0.1
            }
        ],
        "saas": [
            {
                "question": "How important is cost per customer optimization?",
                "priority": PriorityType.COST,
                "weight": 0.25
            },
            {
                "question": "How critical is auto-scaling for user growth?",
                "priority": PriorityType.SCALABILITY,
                "weight": 0.25
            },
            {
                "question": "How important is API performance (<100ms response)?",
                "priority": PriorityType.PERFORMANCE,
                "weight": 0.2
            },
            {
                "question": "How critical is 99.9% uptime SLA?",
                "priority": PriorityType.AVAILABILITY,
                "weight": 0.2
            },
            {
                "question": "How important is ease of deployment and management?",
                "priority": PriorityType.EASE_OF_USE,
                "weight": 0.1
            }
        ],
        "gaming": [
            {
                "question": "How critical is low latency (<50ms)?",
                "priority": PriorityType.PERFORMANCE,
                "weight": 0.35
            },
            {
                "question": "How important is DDoS protection?",
                "priority": PriorityType.SECURITY,
                "weight": 0.2
            },
            {
                "question": "How critical is rapid scaling for player surges?",
                "priority": PriorityType.SCALABILITY,
                "weight": 0.25
            },
            {
                "question": "What's your priority: performance or cost?",
                "priority": PriorityType.COST,
                "weight": 0.1
            },
            {
                "question": "How important is global server distribution?",
                "priority": PriorityType.PERFORMANCE,
                "weight": 0.1
            }
        ],
        "ai_ml": [
            {
                "question": "How important is GPU availability and cost?",
                "priority": PriorityType.COST,
                "weight": 0.3
            },
            {
                "question": "How critical is training performance (TPU/GPU)?",
                "priority": PriorityType.PERFORMANCE,
                "weight": 0.3
            },
            {
                "question": "How important is large-scale storage (multi-TB)?",
                "priority": PriorityType.SCALABILITY,
                "weight": 0.2
            },
            {
                "question": "How critical is model deployment ease?",
                "priority": PriorityType.EASE_OF_USE,
                "weight": 0.1
            },
            {
                "question": "How important is data security for training data?",
                "priority": PriorityType.SECURITY,
                "weight": 0.1
            }
        ]
    }
    
    # Default questions for industries not listed
    DEFAULT_QUESTIONS = [
        {
            "question": "What's most important to you?",
            "options": ["Lowest cost", "Best performance", "Highest security", "Maximum scalability"],
            "priority": PriorityType.COST,
            "weight": 0.3
        },
        {
            "question": "How critical is high availability (99.9%+ uptime)?",
            "priority": PriorityType.AVAILABILITY,
            "weight": 0.25
        },
        {
            "question": "How important is compliance and security?",
            "priority": PriorityType.SECURITY,
            "weight": 0.2
        },
        {
            "question": "How critical is the ability to scale quickly?",
            "priority": PriorityType.SCALABILITY,
            "weight": 0.15
        },
        {
            "question": "How important is 24/7 support?",
            "priority": PriorityType.SUPPORT,
            "weight": 0.1
        }
    ]
    
    def __init__(self):
        self.assessments_file = Path("data/priority_assessments.json")
        self.assessments_file.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.assessments_file.exists():
            self._save_assessments({})
    
    def get_questions(self, industry: str) -> List[Dict[str, Any]]:
        """Get priority questions for industry"""
        return self.INDUSTRY_QUESTIONS.get(industry, self.DEFAULT_QUESTIONS)
    
    def calculate_priority_scores(
        self,
        responses: Dict[str, int],
        industry: str
    ) -> Dict[PriorityType, float]:
        """
        Calculate priority scores from user responses
        
        Args:
            responses: Question ID -> Rating (1-10)
            industry: Industry type
            
        Returns:
            Priority scores (0-10 scale)
        """
        questions = self.get_questions(industry)
        
        # Initialize scores
        scores = {priority: 0.0 for priority in PriorityType}
        
        # Calculate weighted scores
        for i, question in enumerate(questions):
            question_id = f"q{i}"
            if question_id in responses:
                rating = responses[question_id]
                priority = question['priority']
                weight = question['weight']
                
                scores[priority] += rating * weight
        
        # Normalize to 0-10 scale
        max_possible = max(scores.values()) if scores.values() else 1
        if max_possible > 0:
            scores = {k: (v / max_possible) * 10 for k, v in scores.items()}
        
        return scores
    
    def save_assessment(
        self,
        user_email: str,
        industry: str,
        responses: Dict[str, int],
        scores: Dict[PriorityType, float]
    ) -> str:
        """Save priority assessment"""
        assessments = self._load_assessments()
        
        assessment_id = f"assess_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        assessments[user_email] = {
            "assessment_id": assessment_id,
            "industry": industry,
            "responses": responses,
            "scores": {k.value: v for k, v in scores.items()},
            "created_at": datetime.utcnow().isoformat()
        }
        
        self._save_assessments(assessments)
        return assessment_id
    
    def get_assessment(self, user_email: str) -> Optional[Dict[str, Any]]:
        """Get user's priority assessment"""
        assessments = self._load_assessments()
        return assessments.get(user_email)
    
    def _load_assessments(self) -> Dict[str, Any]:
        """Load assessments from file"""
        try:
            with open(self.assessments_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_assessments(self, assessments: Dict[str, Any]):
        """Save assessments to file"""
        with open(self.assessments_file, 'w') as f:
            json.dump(assessments, f, indent=2)
    
    def get_top_priorities(
        self,
        scores: Dict[PriorityType, float],
        top_n: int = 3
    ) -> List[tuple[PriorityType, float]]:
        """Get top N priorities"""
        sorted_priorities = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_priorities[:top_n]
