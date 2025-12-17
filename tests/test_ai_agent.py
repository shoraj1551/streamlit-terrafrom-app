"""
Test Suite for AI Requirements Agent

Unit tests for requirement extraction, document parsing, and validation.
"""

import unittest
from app.services.ai_requirements_agent import AIRequirementsAgent


class TestAIRequirementsAgent(unittest.TestCase):
    """Test AI requirements agent"""
    
    def setUp(self):
        """Set up test environment"""
        self.agent = AIRequirementsAgent()
    
    def test_rule_based_extraction_basic(self):
        """Test basic rule-based extraction"""
        description = "I need a small web application with 2 cores and 8GB RAM"
        
        requirements = self.agent.extract_from_natural_language(description)
        
        self.assertIsNotNone(requirements)
        self.assertIn('compute', requirements)
        self.assertEqual(requirements['compute']['cpu_cores'], 2)
        self.assertEqual(requirements['compute']['ram_gb'], 8)
    
    def test_rule_based_extraction_ml_workload(self):
        """Test ML workload detection"""
        description = "Building a machine learning platform for image recognition with GPU"
        
        requirements = self.agent.extract_from_natural_language(description)
        
        self.assertTrue(requirements['compute']['gpu_required'])
        self.assertGreaterEqual(requirements['compute']['cpu_cores'], 8)
        self.assertGreaterEqual(requirements['storage']['size_gb'], 1000)
    
    def test_rule_based_extraction_healthcare(self):
        """Test healthcare compliance detection"""
        description = "Healthcare platform with HIPAA compliance and patient data"
        
        requirements = self.agent.extract_from_natural_language(description)
        
        self.assertIn('HIPAA', requirements['security']['compliance'])
        self.assertTrue(requirements['security']['encryption'])
    
    def test_rule_based_extraction_fintech(self):
        """Test fintech compliance detection"""
        description = "Payment processing platform with PCI-DSS compliance"
        
        requirements = self.agent.extract_from_natural_language(description)
        
        self.assertIn('PCI-DSS', requirements['security']['compliance'])
        self.assertTrue(requirements['security']['encryption'])
    
    def test_rule_based_extraction_ecommerce(self):
        """Test e-commerce scalability detection"""
        description = "E-commerce platform handling Black Friday traffic spikes"
        
        requirements = self.agent.extract_from_natural_language(description)
        
        self.assertTrue(requirements['scaling']['auto_scaling'])
        self.assertGreater(requirements['scaling']['max_instances'], 1)
        self.assertTrue(requirements['network']['load_balancer'])
    
    def test_default_requirements_structure(self):
        """Test default requirements structure"""
        requirements = self.agent._get_default_requirements()
        
        # Verify all required keys exist
        self.assertIn('compute', requirements)
        self.assertIn('storage', requirements)
        self.assertIn('network', requirements)
        self.assertIn('security', requirements)
        self.assertIn('availability', requirements)
        self.assertIn('scaling', requirements)
        
        # Verify compute structure
        self.assertIn('cpu_cores', requirements['compute'])
        self.assertIn('ram_gb', requirements['compute'])
        self.assertIn('gpu_required', requirements['compute'])
    
    def test_requirement_validation(self):
        """Test requirement validation"""
        incomplete_requirements = {
            'compute': {'cpu_cores': 4}
        }
        
        validated = self.agent._validate_requirements(incomplete_requirements)
        
        # Should fill in missing fields
        self.assertIn('ram_gb', validated['compute'])
        self.assertIn('storage', validated)
        self.assertIn('network', validated)


if __name__ == '__main__':
    unittest.main()
