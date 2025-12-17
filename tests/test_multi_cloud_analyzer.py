"""
Test Suite for Multi-Cloud Analyzer

Unit tests for cost calculations, scoring, and recommendations.
"""

import unittest
from app.services.multi_cloud_analyzer import MultiCloudAnalyzer
from app.services.priority_engine import PriorityType


class TestMultiCloudAnalyzer(unittest.TestCase):
    """Test multi-cloud analyzer"""
    
    def setUp(self):
        """Set up test environment"""
        self.analyzer = MultiCloudAnalyzer()
        
        # Sample requirements
        self.requirements = {
            'compute': {'cpu_cores': 4, 'ram_gb': 16, 'gpu_required': False},
            'storage': {'type': 'ssd', 'size_gb': 500, 'iops': 3000},
            'network': {'bandwidth_gbps': 1, 'static_ip': True, 'load_balancer': False},
            'security': {'encryption': True, 'firewall': True, 'ddos_protection': False, 'compliance': []},
            'availability': {'uptime_sla': 99.9, 'multi_region': False},
            'scaling': {'min_instances': 1, 'max_instances': 3, 'auto_scaling': False}
        }
        
        # Sample priority scores
        self.priority_scores = {
            'cost': 8.0,
            'performance': 6.0,
            'security': 7.0,
            'scalability': 5.0,
            'compliance': 4.0,
            'support': 5.0
        }
    
    def test_environment_cost_calculation(self):
        """Test environment-specific cost calculation"""
        dev_cost = self.analyzer._calculate_environment_cost(
            'aws',
            self.requirements,
            'dev'
        )
        
        staging_cost = self.analyzer._calculate_environment_cost(
            'aws',
            self.requirements,
            'staging'
        )
        
        prod_cost = self.analyzer._calculate_environment_cost(
            'aws',
            self.requirements,
            'prod'
        )
        
        # Dev should be cheapest
        self.assertLess(dev_cost.monthly_cost, staging_cost.monthly_cost)
        self.assertLess(staging_cost.monthly_cost, prod_cost.monthly_cost)
        
        # Dev should have 1 instance
        self.assertEqual(dev_cost.instance_count, 1)
        
        # Prod should have max instances
        self.assertEqual(prod_cost.instance_count, self.requirements['scaling']['max_instances'])
    
    def test_cost_score_calculation(self):
        """Test cost score calculation"""
        # Lower cost should have higher score
        score_low = self.analyzer._calculate_cost_score(400)
        score_high = self.analyzer._calculate_cost_score(6000)
        
        self.assertGreater(score_low, score_high)
        
        # Verify score range
        self.assertGreaterEqual(score_low, 0)
        self.assertLessEqual(score_low, 10)
    
    def test_analyze_all_providers(self):
        """Test analysis of all providers"""
        analyses = self.analyzer.analyze_all_providers(
            self.requirements,
            self.priority_scores,
            'default'
        )
        
        # Should have all 3 providers
        self.assertEqual(len(analyses), 3)
        self.assertIn('aws', analyses)
        self.assertIn('azure', analyses)
        self.assertIn('gcp', analyses)
        
        # Each should have required fields
        for provider, analysis in analyses.items():
            self.assertIsNotNone(analysis.total_monthly)
            self.assertIsNotNone(analysis.total_yearly)
            self.assertIsNotNone(analysis.three_year_tco)
            self.assertIsNotNone(analysis.overall_score)
            
            # Verify score range
            self.assertGreaterEqual(analysis.overall_score, 0)
            self.assertLessEqual(analysis.overall_score, 10)
    
    def test_recommendation_generation(self):
        """Test recommendation generation"""
        analyses = self.analyzer.analyze_all_providers(
            self.requirements,
            self.priority_scores,
            'default'
        )
        
        recommendation = self.analyzer.get_recommendation(
            analyses,
            self.priority_scores
        )
        
        # Should have primary provider
        self.assertIn('primary_provider', recommendation)
        self.assertIn(recommendation['primary_provider'], ['aws', 'azure', 'gcp'])
        
        # Should have confidence level
        self.assertIn('confidence', recommendation)
        self.assertIn(recommendation['confidence'], ['high', 'medium'])
        
        # Should have reasoning
        self.assertIn('reasoning', recommendation)
        self.assertIsInstance(recommendation['reasoning'], str)
    
    def test_gcp_cost_advantage(self):
        """Test that GCP is typically cheaper"""
        # GCP should generally be 20-30% cheaper
        aws_cost = self.analyzer._get_base_compute_cost('aws', 4, 16, False)
        gcp_cost = self.analyzer._get_base_compute_cost('gcp', 4, 16, False)
        
        self.assertLess(gcp_cost, aws_cost)
        
        # Verify approximately 20-30% cheaper
        savings_pct = ((aws_cost - gcp_cost) / aws_cost) * 100
        self.assertGreater(savings_pct, 15)  # At least 15% cheaper


if __name__ == '__main__':
    unittest.main()
