"""
AI Requirements Agent

Uses self-hosted GPT-NeoX 20B model to extract infrastructure requirements
from natural language descriptions and documents.
"""

from typing import Dict, Any, Optional, List
import json
import re
from pathlib import Path
from datetime import datetime


class AIRequirementsAgent:
    """
    AI-powered requirements extraction using self-hosted LLM
    
    Supports:
    - Natural language descriptions
    - Document parsing (PDF, DOCX, TXT)
    - Structured requirement generation
    """
    
    def __init__(self, model_name: str = "EleutherAI/gpt-neox-20b"):
        """
        Initialize AI agent
        
        Args:
            model_name: Hugging Face model identifier
        """
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.loaded = False
        
        # Lazy loading - only load when needed
        print(f"AI Agent initialized with model: {model_name}")
        print("Model will be loaded on first use")
    
    def _load_model(self):
        """Load the LLM model (lazy loading)"""
        if self.loaded:
            return
        
        print("Loading GPT-NeoX 20B model... This may take a few minutes.")
        print("Model size: ~40GB, requires 64GB+ RAM or GPU with 40GB+ VRAM")
        
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # Load model with optimizations
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16,  # Use FP16 for memory efficiency
                device_map="auto",  # Automatic device placement
                low_cpu_mem_usage=True,
                offload_folder="offload"  # Offload to disk if needed
            )
            
            self.loaded = True
            print("✅ Model loaded successfully!")
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            print("\nFallback: Using rule-based extraction")
            self.loaded = False
    
    def extract_from_natural_language(
        self,
        description: str,
        industry: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract requirements from natural language description
        
        Args:
            description: User's natural language description
            industry: Industry type for context
            
        Returns:
            Structured requirements dictionary
        """
        # Try AI extraction first
        if not self.loaded:
            self._load_model()
        
        if self.loaded:
            try:
                return self._ai_extract(description, industry)
            except Exception as e:
                print(f"AI extraction failed: {e}")
                print("Falling back to rule-based extraction")
        
        # Fallback to rule-based extraction
        return self._rule_based_extract(description, industry)
    
    def _ai_extract(self, description: str, industry: Optional[str]) -> Dict[str, Any]:
        """Extract requirements using AI model"""
        
        # Build prompt
        prompt = self._build_extraction_prompt(description, industry)
        
        # Generate response
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=1024,
            temperature=0.7,
            do_sample=True,
            top_p=0.9,
            repetition_penalty=1.1
        )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract JSON from response
        requirements = self._parse_json_response(response)
        
        return requirements
    
    def _build_extraction_prompt(self, description: str, industry: Optional[str]) -> str:
        """Build prompt for LLM"""
        
        industry_context = f"\nIndustry: {industry}" if industry else ""
        
        prompt = f"""You are an expert cloud infrastructure architect. Extract infrastructure requirements from the user's description and output structured JSON.

User Description: {description}{industry_context}

Analyze and extract:
1. Compute requirements (CPU cores, RAM GB, GPU if needed)
2. Storage requirements (type: ssd/hdd, size in GB, IOPS)
3. Network requirements (bandwidth in Gbps, static IP, load balancer)
4. Security requirements (encryption, firewall, DDoS protection, compliance standards)
5. Availability requirements (uptime SLA %, multi-region deployment)
6. Estimated instance count (min, max for auto-scaling)

Output ONLY valid JSON in this exact format:
{{
  "compute": {{
    "cpu_cores": <number>,
    "ram_gb": <number>,
    "gpu_required": <true/false>
  }},
  "storage": {{
    "type": "ssd" or "hdd",
    "size_gb": <number>,
    "iops": <number>
  }},
  "network": {{
    "bandwidth_gbps": <number>,
    "static_ip": <true/false>,
    "load_balancer": <true/false>
  }},
  "security": {{
    "encryption": <true/false>,
    "firewall": <true/false>,
    "ddos_protection": <true/false>,
    "compliance": [<list of standards>]
  }},
  "availability": {{
    "uptime_sla": <percentage>,
    "multi_region": <true/false>
  }},
  "scaling": {{
    "min_instances": <number>,
    "max_instances": <number>,
    "auto_scaling": <true/false>
  }}
}}

JSON Output:"""
        
        return prompt
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response"""
        
        # Try to find JSON in response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        
        if json_match:
            try:
                json_str = json_match.group(0)
                requirements = json.loads(json_str)
                
                # Validate structure
                return self._validate_requirements(requirements)
            
            except json.JSONDecodeError:
                pass
        
        # If parsing fails, return default structure
        return self._get_default_requirements()
    
    def _rule_based_extract(self, description: str, industry: Optional[str]) -> Dict[str, Any]:
        """
        Fallback rule-based extraction
        
        Uses keyword matching and heuristics
        """
        desc_lower = description.lower()
        
        # Initialize with defaults
        requirements = self._get_default_requirements()
        
        # Compute detection
        if any(word in desc_lower for word in ['ml', 'ai', 'machine learning', 'deep learning', 'gpu']):
            requirements['compute']['cpu_cores'] = 16
            requirements['compute']['ram_gb'] = 64
            requirements['compute']['gpu_required'] = True
        elif any(word in desc_lower for word in ['high performance', 'gaming', 'video']):
            requirements['compute']['cpu_cores'] = 8
            requirements['compute']['ram_gb'] = 32
        elif any(word in desc_lower for word in ['small', 'startup', 'dev', 'test']):
            requirements['compute']['cpu_cores'] = 2
            requirements['compute']['ram_gb'] = 8
        else:
            requirements['compute']['cpu_cores'] = 4
            requirements['compute']['ram_gb'] = 16
        
        # Storage detection
        if any(word in desc_lower for word in ['database', 'data', 'analytics', 'big data']):
            requirements['storage']['size_gb'] = 1000
            requirements['storage']['type'] = 'ssd'
            requirements['storage']['iops'] = 5000
        elif any(word in desc_lower for word in ['media', 'video', 'streaming', 'content']):
            requirements['storage']['size_gb'] = 2000
            requirements['storage']['type'] = 'ssd'
        else:
            requirements['storage']['size_gb'] = 500
        
        # Network detection
        if any(word in desc_lower for word in ['cdn', 'global', 'worldwide', 'multi-region']):
            requirements['network']['bandwidth_gbps'] = 10
            requirements['network']['load_balancer'] = True
            requirements['availability']['multi_region'] = True
        elif any(word in desc_lower for word in ['api', 'web', 'application']):
            requirements['network']['load_balancer'] = True
        
        # Security detection
        if any(word in desc_lower for word in ['hipaa', 'healthcare', 'medical', 'health']):
            requirements['security']['compliance'] = ['HIPAA', 'HITECH']
            requirements['security']['encryption'] = True
        elif any(word in desc_lower for word in ['pci', 'payment', 'financial', 'banking']):
            requirements['security']['compliance'] = ['PCI-DSS', 'SOC 2']
            requirements['security']['encryption'] = True
        elif any(word in desc_lower for word in ['gdpr', 'privacy', 'eu']):
            requirements['security']['compliance'] = ['GDPR']
        
        if any(word in desc_lower for word in ['secure', 'security', 'encrypted']):
            requirements['security']['encryption'] = True
            requirements['security']['firewall'] = True
        
        # Availability detection
        if any(word in desc_lower for word in ['critical', 'production', 'enterprise', '99.9']):
            requirements['availability']['uptime_sla'] = 99.9
        elif any(word in desc_lower for word in ['high availability', 'ha', '99.99']):
            requirements['availability']['uptime_sla'] = 99.99
        
        # Scaling detection
        if any(word in desc_lower for word in ['scale', 'scalable', 'auto-scale', 'elastic']):
            requirements['scaling']['auto_scaling'] = True
            requirements['scaling']['max_instances'] = 10
        
        return requirements
    
    def _validate_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize requirements"""
        
        default = self._get_default_requirements()
        
        # Ensure all required keys exist
        for key in default:
            if key not in requirements:
                requirements[key] = default[key]
            elif isinstance(default[key], dict):
                for subkey in default[key]:
                    if subkey not in requirements[key]:
                        requirements[key][subkey] = default[key][subkey]
        
        return requirements
    
    def _get_default_requirements(self) -> Dict[str, Any]:
        """Get default requirements structure"""
        return {
            "compute": {
                "cpu_cores": 4,
                "ram_gb": 16,
                "gpu_required": False
            },
            "storage": {
                "type": "ssd",
                "size_gb": 500,
                "iops": 3000
            },
            "network": {
                "bandwidth_gbps": 1,
                "static_ip": True,
                "load_balancer": False
            },
            "security": {
                "encryption": True,
                "firewall": True,
                "ddos_protection": False,
                "compliance": []
            },
            "availability": {
                "uptime_sla": 99.9,
                "multi_region": False
            },
            "scaling": {
                "min_instances": 1,
                "max_instances": 3,
                "auto_scaling": False
            }
        }
    
    def extract_from_document(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract requirements from uploaded document
        
        Args:
            file_path: Path to document (PDF, DOCX, TXT)
            
        Returns:
            Structured requirements
        """
        # Read document
        text = self._read_document(file_path)
        
        # Extract using AI
        return self.extract_from_natural_language(text)
    
    def _read_document(self, file_path: Path) -> str:
        """Read text from document"""
        
        suffix = file_path.suffix.lower()
        
        if suffix == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        elif suffix == '.pdf':
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text()
                    return text
            except Exception as e:
                print(f"Error reading PDF: {e}")
                return ""
        
        elif suffix in ['.docx', '.doc']:
            try:
                import docx
                doc = docx.Document(file_path)
                text = "\n".join([para.text for para in doc.paragraphs])
                return text
            except Exception as e:
                print(f"Error reading DOCX: {e}")
                return ""
        
        else:
            raise ValueError(f"Unsupported file type: {suffix}")
    
    def save_requirements(
        self,
        requirements: Dict[str, Any],
        user_email: str,
        description: str = ""
    ) -> str:
        """
        Save extracted requirements
        
        Returns:
            Requirement ID
        """
        req_dir = Path("data/requirements")
        req_dir.mkdir(parents=True, exist_ok=True)
        
        req_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        req_data = {
            "requirement_id": req_id,
            "user_email": user_email,
            "description": description,
            "requirements": requirements,
            "created_at": datetime.utcnow().isoformat(),
            "model_used": self.model_name if self.loaded else "rule-based"
        }
        
        req_file = req_dir / f"{req_id}.json"
        with open(req_file, 'w') as f:
            json.dump(req_data, f, indent=2)
        
        return req_id
    
    def load_requirements(self, req_id: str) -> Optional[Dict[str, Any]]:
        """Load saved requirements"""
        req_file = Path(f"data/requirements/{req_id}.json")
        
        if not req_file.exists():
            return None
        
        with open(req_file, 'r') as f:
            return json.load(f)
