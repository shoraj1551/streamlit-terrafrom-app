import subprocess
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class TerraformCommand(str, Enum):
    INIT = "init"
    VALIDATE = "validate"
    PLAN = "plan"
    APPLY = "apply"
    DESTROY = "destroy"
    OUTPUT = "output"


class DeploymentStatus(str, Enum):
    PENDING = "pending"
    INITIALIZING = "initializing"
    PLANNING = "planning"
    APPLYING = "applying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TerraformResult:
    """Result of a Terraform operation"""
    success: bool
    command: str
    output: str
    error: Optional[str] = None
    return_code: int = 0
    duration_seconds: float = 0.0


@dataclass
class DeploymentState:
    """State of a deployment"""
    deployment_id: str
    status: DeploymentStatus
    current_step: str
    progress_percentage: int
    logs: List[str] = field(default_factory=list)
    result: Optional[TerraformResult] = None
    error: Optional[str] = None


class TerraformExecutor:
    """Execute Terraform commands safely with proper error handling"""
    
    # Whitelist of allowed Terraform resource types
    ALLOWED_RESOURCES = {
        "aws_instance",
        "aws_security_group",
        "aws_vpc",
        "aws_subnet",
        "aws_ebs_volume",
        "aws_key_pair",
    }
    
    # Blocked provisioners (security risk - can execute arbitrary commands)
    BLOCKED_PROVISIONERS = {
        "local-exec",
        "remote-exec",
    }
    
    # Blocked resource types (security risk)
    BLOCKED_RESOURCES = {
        "null_resource",  # Can execute arbitrary commands
        "external",  # Can execute external programs
        "local_file",  # Can write arbitrary files
    }
    
    def __init__(self, working_dir: str):
        """
        Initialize Terraform executor
        
        Args:
            working_dir: Directory containing Terraform files
        """
        self.working_dir = Path(working_dir)
        if not self.working_dir.exists():
            raise ValueError(f"Working directory does not exist: {working_dir}")
        
        logger.info(f"Initialized TerraformExecutor with working_dir: {working_dir}")
    
    def validate_variables(self, variables: Dict[str, str]) -> None:
        """
        Validate Terraform variables for security
        
        Args:
            variables: Dictionary of Terraform variables
            
        Raises:
            ValueError: If variables contain dangerous patterns
        """
        import re
        
        for key, value in variables.items():
            # Validate key format (alphanumeric, underscore, hyphen only)
            if not re.match(r'^[a-zA-Z0-9_-]+$', key):
                raise ValueError(f"Invalid variable name: {key}. Only alphanumeric, underscore, and hyphen allowed.")
            
            # Validate value (no shell metacharacters)
            if isinstance(value, str):
                dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '<', '>', '\n', '\r']
                for char in dangerous_chars:
                    if char in value:
                        raise ValueError(
                            f"Variable '{key}' contains dangerous character: '{char}'. "
                            f"This could lead to command injection."
                        )
                
                # Check for command substitution patterns
                dangerous_patterns = [
                    r'\$\(',  # $(command)
                    r'`.*`',  # `command`
                    r'\|\|',  # ||
                    r'&&',    # &&
                ]
                
                for pattern in dangerous_patterns:
                    if re.search(pattern, value):
                        raise ValueError(
                            f"Variable '{key}' contains dangerous pattern: {pattern}. "
                            f"This could lead to command injection."
                        )
        
        logger.info(f"Validated {len(variables)} Terraform variables - all safe")
    
    async def _run_command(
        self,
        command: List[str],
        env: Optional[Dict[str, str]] = None
    ) -> TerraformResult:
        """
        Run a Terraform command asynchronously
        
        Args:
            command: Command and arguments to run
            env: Optional environment variables
            
        Returns:
            TerraformResult with command output
        """
        import time
        start_time = time.time()
        
        # Prepare environment
        cmd_env = os.environ.copy()
        if env:
            cmd_env.update(env)
        
        # Add Terraform-specific env vars
        cmd_env['TF_IN_AUTOMATION'] = '1'
        cmd_env['TF_INPUT'] = '0'  # Disable interactive prompts
        
        logger.info(f"Executing command: {' '.join(command)}")
        
        try:
            # Run command asynchronously
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.working_dir),
                env=cmd_env
            )
            
            stdout, stderr = await process.communicate()
            
            duration = time.time() - start_time
            
            output = stdout.decode('utf-8')
            error = stderr.decode('utf-8')
            
            success = process.returncode == 0
            
            if success:
                logger.info(f"Command completed successfully in {duration:.2f}s")
            else:
                logger.error(f"Command failed with return code {process.returncode}")
            
            return TerraformResult(
                success=success,
                command=' '.join(command),
                output=output,
                error=error if error else None,
                return_code=process.returncode,
                duration_seconds=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            logger.exception(f"Command execution failed: {e}")
            
            return TerraformResult(
                success=False,
                command=' '.join(command),
                output="",
                error=str(e),
                return_code=-1,
                duration_seconds=duration
            )
    
    async def init(self) -> TerraformResult:
        """Initialize Terraform working directory"""
        logger.info("Running terraform init")
        return await self._run_command(['terraform', 'init', '-no-color'])
    
    async def validate(self) -> TerraformResult:
        """Validate Terraform configuration"""
        logger.info("Running terraform validate")
        return await self._run_command(['terraform', 'validate', '-json'])
    
    async def plan(
        self,
        var_file: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None
    ) -> TerraformResult:
        """
        Generate Terraform execution plan
        
        Args:
            var_file: Path to .tfvars file
            variables: Dictionary of variables to pass
            
        Returns:
            TerraformResult with plan output
        """
        logger.info("Running terraform plan")
        
        # SECURITY: Validate variables before execution
        if variables:
            self.validate_variables(variables)
        
        command = ['terraform', 'plan', '-no-color', '-input=false']
        
        if var_file:
            command.extend(['-var-file', var_file])
        
        if variables:
            for key, value in variables.items():
                command.extend(['-var', f'{key}={value}'])
        
        return await self._run_command(command)
    
    async def apply(
        self,
        var_file: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None,
        auto_approve: bool = False
    ) -> TerraformResult:
        """
        Apply Terraform configuration
        
        Args:
            var_file: Path to .tfvars file
            variables: Dictionary of variables to pass
            auto_approve: Skip interactive approval
            
        Returns:
            TerraformResult with apply output
        """
        logger.info("Running terraform apply")
        
        # SECURITY: Validate variables before execution
        if variables:
            self.validate_variables(variables)
        
        command = ['terraform', 'apply', '-no-color', '-input=false']
        
        if auto_approve:
            command.append('-auto-approve')
        
        if var_file:
            command.extend(['-var-file', var_file])
        
        if variables:
            for key, value in variables.items():
                command.extend(['-var', f'{key}={value}'])
        
        return await self._run_command(command)
    
    async def destroy(
        self,
        var_file: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None,
        auto_approve: bool = False
    ) -> TerraformResult:
        """
        Destroy Terraform-managed infrastructure
        
        Args:
            var_file: Path to .tfvars file
            variables: Dictionary of variables to pass
            auto_approve: Skip interactive approval
            
        Returns:
            TerraformResult with destroy output
        """
        logger.info("Running terraform destroy")
        
        command = ['terraform', 'destroy', '-no-color', '-input=false']
        
        if auto_approve:
            command.append('-auto-approve')
        
        if var_file:
            command.extend(['-var-file', var_file])
        
        if variables:
            for key, value in variables.items():
                command.extend(['-var', f'{key}={value}'])
        
        return await self._run_command(command)
    
    async def output(self, output_name: Optional[str] = None) -> TerraformResult:
        """
        Get Terraform outputs
        
        Args:
            output_name: Specific output to retrieve (optional)
            
        Returns:
            TerraformResult with output values
        """
        logger.info("Running terraform output")
        
        command = ['terraform', 'output', '-json']
        
        if output_name:
            command.append(output_name)
        
        return await self._run_command(command)
    
    def parse_outputs(self, result: TerraformResult) -> Dict[str, Any]:
        """
        Parse Terraform outputs from JSON
        
        Args:
            result: TerraformResult from output command
            
        Returns:
            Dictionary of output values
        """
        if not result.success:
            return {}
        
        try:
            outputs = json.loads(result.output)
            # Extract values from Terraform output format
            return {
                key: value.get('value')
                for key, value in outputs.items()
            }
        except json.JSONDecodeError:
            logger.error("Failed to parse Terraform outputs as JSON")
            return {}
    
    async def full_deployment(
        self,
        variables: Optional[Dict[str, str]] = None,
        deployment_state: Optional[DeploymentState] = None
    ) -> DeploymentState:
        """
        Run full deployment workflow: init -> validate -> plan -> apply
        
        Args:
            variables: Terraform variables
            deployment_state: Optional state object to update
            
        Returns:
            DeploymentState with final status
        """
        import uuid
        
        if deployment_state is None:
            deployment_state = DeploymentState(
                deployment_id=str(uuid.uuid4()),
                status=DeploymentStatus.PENDING,
                current_step="Starting deployment",
                progress_percentage=0,
                logs=[]
            )
        
        try:
            # Step 1: Initialize
            deployment_state.status = DeploymentStatus.INITIALIZING
            deployment_state.current_step = "Initializing Terraform"
            deployment_state.progress_percentage = 10
            deployment_state.logs.append("🔧 Initializing Terraform...")
            
            init_result = await self.init()
            if not init_result.success:
                raise Exception(f"Terraform init failed: {init_result.error}")
            
            deployment_state.logs.append("✅ Terraform initialized successfully")
            
            # Step 2: Validate
            deployment_state.current_step = "Validating configuration"
            deployment_state.progress_percentage = 30
            deployment_state.logs.append("🔍 Validating configuration...")
            
            validate_result = await self.validate()
            if not validate_result.success:
                raise Exception(f"Terraform validate failed: {validate_result.error}")
            
            deployment_state.logs.append("✅ Configuration is valid")
            
            # Step 3: Plan
            deployment_state.status = DeploymentStatus.PLANNING
            deployment_state.current_step = "Generating execution plan"
            deployment_state.progress_percentage = 50
            deployment_state.logs.append("📋 Generating execution plan...")
            
            plan_result = await self.plan(variables=variables)
            if not plan_result.success:
                raise Exception(f"Terraform plan failed: {plan_result.error}")
            
            deployment_state.logs.append("✅ Execution plan generated")
            
            # Step 4: Apply
            deployment_state.status = DeploymentStatus.APPLYING
            deployment_state.current_step = "Applying changes"
            deployment_state.progress_percentage = 70
            deployment_state.logs.append("🚀 Applying infrastructure changes...")
            
            apply_result = await self.apply(variables=variables, auto_approve=True)
            if not apply_result.success:
                raise Exception(f"Terraform apply failed: {apply_result.error}")
            
            deployment_state.logs.append("✅ Infrastructure deployed successfully")
            
            # Step 5: Get outputs
            deployment_state.current_step = "Retrieving outputs"
            deployment_state.progress_percentage = 90
            deployment_state.logs.append("📤 Retrieving deployment outputs...")
            
            output_result = await self.output()
            outputs = self.parse_outputs(output_result)
            
            # Success!
            deployment_state.status = DeploymentStatus.COMPLETED
            deployment_state.current_step = "Deployment complete"
            deployment_state.progress_percentage = 100
            deployment_state.result = apply_result
            deployment_state.logs.append("🎉 Deployment completed successfully!")
            
            if outputs:
                deployment_state.logs.append(f"📊 Outputs: {json.dumps(outputs, indent=2)}")
            
            return deployment_state
            
        except Exception as e:
            logger.exception(f"Deployment failed: {e}")
            deployment_state.status = DeploymentStatus.FAILED
            deployment_state.error = str(e)
            deployment_state.logs.append(f"❌ Deployment failed: {str(e)}")
            return deployment_state
