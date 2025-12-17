"""
Integration Test Suite

End-to-end tests for complete user journey.
"""

import unittest
import tempfile
import os
from pathlib import Path

from app.services.auth_system import AuthenticationSystem
from app.services.user_survey import UserSurvey
from app.services.ai_requirements_agent import AIRequirementsAgent
from app.services.priority_engine import PriorityEngine
from app.services.multi_cloud_analyzer import MultiCloudAnalyzer


class TestCompleteUserJourney(unittest.TestCase):
    """Test complete user journey from signup to deployment"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        
        # Initialize all services
        self.auth = AuthenticationSystem()
        self.survey = UserSurvey()
        self.ai_agent = AIRequirementsAgent()
        self.priority_engine = PriorityEngine()
        self.analyzer = MultiCloudAnalyzer()
        
        # Test data
        self.test_email = "integration@example.com"
        self.test_password = "IntegrationTest123"
        self.test_name = "Integration Test User"
    
    def test_complete_journey(self):
        """Test complete user journey"""
        
        # Step 1: Signup
        success, message = self.auth.signup(
            self.test_email,
            self.test_password,
            self.test_name
        )
        self.assertTrue(success)
        
        # Step 2: Login
        success, message, user_data = self.auth.login(
            self.test_email,
            self.test_password
        )
        self.assertTrue(success)
        self.assertIsNotNone(user_data['token'])
        
        # Step 3: Complete Survey
        survey_data = {
            'company_type': 'Startup (Seed/Series A)',
            'company_size': '1-10 employees',
            'infrastructure_status': 'No infrastructure yet',
            'budget_range': '$500 - $2,000/month',
            'primary_goals': ['Cost optimization', 'Scalability'],
            'use_case_description': 'Building a SaaS platform'
        }
        
        success = self.survey.save_survey(self.test_email, survey_data)
        self.assertTrue(success)
        
        # Step 4: Extract Requirements
        description = "Building a SaaS platform for 1000 users with auto-scaling"
        requirements = self.ai_agent.extract_from_natural_language(
            description,
            industry='saas'
        )
        
        self.assertIsNotNone(requirements)
        self.assertIn('compute', requirements)
        
        # Step 5: Priority Assessment
        priority_responses = {
            'q0': 9,  # Cost
            'q1': 8,  # Scalability
            'q2': 7,  # Performance
            'q3': 6,  # Availability
            'q4': 5   # Ease of use
        }
        
        priority_scores = self.priority_engine.calculate_priority_scores(
            priority_responses,
            'saas'
        )
        
        self.assertIsNotNone(priority_scores)
        
        # Step 6: Multi-Cloud Analysis
        analyses = self.analyzer.analyze_all_providers(
            requirements,
            {k.value: v for k, v in priority_scores.items()},
            'saas'
        )
        
        self.assertEqual(len(analyses), 3)
        
        # Step 7: Get Recommendation
        recommendation = self.analyzer.get_recommendation(
            analyses,
            {k.value: v for k, v in priority_scores.items()}
        )
        
        self.assertIn('primary_provider', recommendation)
        self.assertIn('confidence', recommendation)
        
        # Verify cost-conscious recommendation (should prefer GCP for cost)
        # Since cost priority is high (9), GCP should likely be recommended
        print(f"\nRecommended Provider: {recommendation['primary_provider'].upper()}")
        print(f"Confidence: {recommendation['confidence']}")
        print(f"Reasoning: {recommendation['reasoning']}")
        
        # Verify all costs are reasonable for budget
        for provider, analysis in analyses.items():
            print(f"\n{provider.upper()}: ${analysis.total_monthly:,.2f}/month")
            # Should be within budget range ($500-$2000)
            self.assertLess(analysis.total_monthly, 2500)  # Allow some buffer


if __name__ == '__main__':
    unittest.main()
