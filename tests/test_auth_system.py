"""
Test Suite for Authentication System

Unit tests for login, signup, session management, and password security.
"""

import unittest
import tempfile
import os
from pathlib import Path
import json

from app.services.auth_system import AuthenticationSystem


class TestAuthenticationSystem(unittest.TestCase):
    """Test authentication system"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        self.users_file = Path(self.test_dir) / "users.json"
        
        # Initialize auth system with test file
        self.auth = AuthenticationSystem()
        self.auth.users_file = self.users_file
        self.auth._save_users({})
        
        # Test user data
        self.test_email = "test@example.com"
        self.test_password = "TestPassword123"
        self.test_name = "Test User"
    
    def tearDown(self):
        """Clean up test environment"""
        if self.users_file.exists():
            self.users_file.unlink()
        os.rmdir(self.test_dir)
    
    def test_signup_success(self):
        """Test successful user signup"""
        success, message = self.auth.signup(
            self.test_email,
            self.test_password,
            self.test_name
        )
        
        self.assertTrue(success)
        self.assertEqual(message, "Account created successfully")
        
        # Verify user was created
        users = self.auth._load_users()
        self.assertIn(self.test_email, users)
        self.assertEqual(users[self.test_email]['full_name'], self.test_name)
    
    def test_signup_duplicate_email(self):
        """Test signup with duplicate email"""
        # Create first user
        self.auth.signup(self.test_email, self.test_password, self.test_name)
        
        # Try to create duplicate
        success, message = self.auth.signup(
            self.test_email,
            "AnotherPassword123",
            "Another User"
        )
        
        self.assertFalse(success)
        self.assertEqual(message, "Email already registered")
    
    def test_signup_weak_password(self):
        """Test signup with weak password"""
        success, message = self.auth.signup(
            self.test_email,
            "weak",
            self.test_name
        )
        
        self.assertFalse(success)
        self.assertIn("at least 8 characters", message)
    
    def test_login_success(self):
        """Test successful login"""
        # Create user
        self.auth.signup(self.test_email, self.test_password, self.test_name)
        
        # Login
        success, message, user_data = self.auth.login(
            self.test_email,
            self.test_password
        )
        
        self.assertTrue(success)
        self.assertEqual(message, "Login successful")
        self.assertIsNotNone(user_data)
        self.assertEqual(user_data['email'], self.test_email)
        self.assertIn('token', user_data)
    
    def test_login_wrong_password(self):
        """Test login with wrong password"""
        # Create user
        self.auth.signup(self.test_email, self.test_password, self.test_name)
        
        # Try wrong password
        success, message, user_data = self.auth.login(
            self.test_email,
            "WrongPassword123"
        )
        
        self.assertFalse(success)
        self.assertEqual(message, "Invalid email or password")
        self.assertIsNone(user_data)
    
    def test_login_nonexistent_user(self):
        """Test login with nonexistent user"""
        success, message, user_data = self.auth.login(
            "nonexistent@example.com",
            self.test_password
        )
        
        self.assertFalse(success)
        self.assertEqual(message, "Invalid email or password")
        self.assertIsNone(user_data)
    
    def test_token_generation_and_verification(self):
        """Test JWT token generation and verification"""
        # Create and login user
        self.auth.signup(self.test_email, self.test_password, self.test_name)
        success, message, user_data = self.auth.login(self.test_email, self.test_password)
        
        token = user_data['token']
        
        # Verify token
        email = self.auth.verify_token(token)
        self.assertEqual(email, self.test_email)
    
    def test_password_change(self):
        """Test password change"""
        # Create user
        self.auth.signup(self.test_email, self.test_password, self.test_name)
        
        # Change password
        new_password = "NewPassword123"
        success, message = self.auth.change_password(
            self.test_email,
            self.test_password,
            new_password
        )
        
        self.assertTrue(success)
        self.assertEqual(message, "Password changed successfully")
        
        # Verify can login with new password
        success, _, _ = self.auth.login(self.test_email, new_password)
        self.assertTrue(success)
        
        # Verify cannot login with old password
        success, _, _ = self.auth.login(self.test_email, self.test_password)
        self.assertFalse(success)


if __name__ == '__main__':
    unittest.main()
