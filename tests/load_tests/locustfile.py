"""
Load Testing Script using Locust

Tests concurrent users, deployments, and API endpoints.
"""

from locust import HttpUser, task, between, events
import json
import random
import os


class TerraformAppUser(HttpUser):
    """
    Simulated user for load testing
    """
    
    # Wait between 1-3 seconds between tasks
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a user starts"""
        # Login (simulated)
        self.auth_token = self._login()
    
    def _login(self):
        """Simulate login and get auth token"""
        response = self.client.post("/api/auth/login", json={
            "email": f"test_user_{random.randint(1, 100)}@example.com",
            "password": "Test123!@#"
        })
        
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    @task(3)
    def view_deployments(self):
        """View deployment list (most common action)"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        self.client.get("/api/deployments", headers=headers)
    
    @task(2)
    def view_deployment_detail(self):
        """View specific deployment"""
        deployment_id = f"deploy_{random.randint(1, 1000)}"
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        self.client.get(f"/api/deployments/{deployment_id}", headers=headers)
    
    @task(1)
    def create_deployment(self):
        """Create new deployment (less frequent)"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        deployment_data = {
            "provider": random.choice(["aws", "azure", "gcp"]),
            "region": random.choice(["us-east-1", "us-west-2", "eu-west-1"]),
            "instance_type": random.choice(["t2.micro", "t2.small", "t3.micro"]),
            "variables": {
                "environment": "test",
                "app_name": f"test_app_{random.randint(1, 100)}"
            }
        }
        
        self.client.post("/api/deployments", json=deployment_data, headers=headers)
    
    @task(1)
    def view_audit_logs(self):
        """View audit logs"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        self.client.get("/api/audit/logs?limit=50", headers=headers)
    
    @task(1)
    def check_queue_status(self):
        """Check deployment queue status"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        self.client.get("/api/queue/status", headers=headers)


class AdminUser(HttpUser):
    """
    Simulated admin user with different behavior
    """
    
    wait_time = between(2, 5)
    
    def on_start(self):
        """Called when admin starts"""
        self.auth_token = self._admin_login()
    
    def _admin_login(self):
        """Admin login"""
        response = self.client.post("/api/auth/login", json={
            "email": "admin@example.com",
            "password": "Admin123!@#"
        })
        
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    @task(5)
    def view_all_deployments(self):
        """View all deployments (admin)"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        self.client.get("/api/admin/deployments?limit=100", headers=headers)
    
    @task(3)
    def view_metrics(self):
        """View system metrics"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        self.client.get("/api/admin/metrics", headers=headers)
    
    @task(2)
    def view_queue_details(self):
        """View detailed queue information"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        self.client.get("/api/admin/queue/details", headers=headers)


# Event handlers for custom metrics
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Custom request handler"""
    if exception:
        print(f"Request failed: {name} - {exception}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    print("=" * 60)
    print("Load Test Started")
    print(f"Target: {environment.host}")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops"""
    print("=" * 60)
    print("Load Test Completed")
    print("=" * 60)
