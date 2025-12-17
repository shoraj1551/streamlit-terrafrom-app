"""
Google Cloud Platform Provider Implementation
"""

from typing import Dict, Any, List, Optional
from app.services.cloud_provider import CloudProvider


class GCPProvider(CloudProvider):
    """Google Cloud Platform provider"""
    
    REGIONS = [
        "us-central1", "us-east1", "us-east4", "us-west1", "us-west2", "us-west3", "us-west4",
        "europe-west1", "europe-west2", "europe-west3", "europe-west4", "europe-west6",
        "europe-north1", "europe-central2",
        "asia-east1", "asia-east2", "asia-northeast1", "asia-northeast2", "asia-northeast3",
        "asia-south1", "asia-southeast1", "asia-southeast2",
        "australia-southeast1", "australia-southeast2",
        "southamerica-east1", "northamerica-northeast1"
    ]
    
    MACHINE_TYPES = {
        # E2 series (Cost-optimized)
        "e2-micro": {"vcpu": 0.25, "ram_gb": 1, "cost_hour": 0.0084},
        "e2-small": {"vcpu": 0.5, "ram_gb": 2, "cost_hour": 0.0168},
        "e2-medium": {"vcpu": 1, "ram_gb": 4, "cost_hour": 0.0336},
        "e2-standard-2": {"vcpu": 2, "ram_gb": 8, "cost_hour": 0.0672},
        "e2-standard-4": {"vcpu": 4, "ram_gb": 16, "cost_hour": 0.1344},
        
        # N1 series (General purpose)
        "n1-standard-1": {"vcpu": 1, "ram_gb": 3.75, "cost_hour": 0.0475},
        "n1-standard-2": {"vcpu": 2, "ram_gb": 7.5, "cost_hour": 0.095},
        "n1-standard-4": {"vcpu": 4, "ram_gb": 15, "cost_hour": 0.19},
        
        # N2 series (Balanced)
        "n2-standard-2": {"vcpu": 2, "ram_gb": 8, "cost_hour": 0.0971},
        "n2-standard-4": {"vcpu": 4, "ram_gb": 16, "cost_hour": 0.1942},
    }
    
    @property
    def name(self) -> str:
        return "GCP"
    
    @property
    def regions(self) -> List[str]:
        return self.REGIONS
    
    def generate_terraform(self, config: Dict[str, Any]) -> str:
        """Generate GCP Terraform configuration"""
        machine_type = config.get('instance_type', 'e2-medium')
        region = config.get('region', 'us-central1')
        zone = f"{region}-a"  # Default to zone 'a'
        project_id = config.get('project_id', 'my-project')
        instance_name = config.get('name', 'terraform-instance')
        environment = config.get('environment', 'dev')
        tags = config.get('tags', {})
        
        # Convert tags to GCP labels format (lowercase, no spaces)
        labels = {
            'environment': environment.lower().replace(' ', '-'),
            'managed_by': 'terraform-streamlit',
        }
        for key, value in tags.items():
            labels[key.lower().replace(' ', '-')] = value.lower().replace(' ', '-')
        
        labels_str = self._format_labels(labels)
        
        return f'''terraform {{
  required_providers {{
    google = {{
      source  = "hashicorp/google"
      version = "~> 5.0"
    }}
  }}
}}

provider "google" {{
  project = "{project_id}"
  region  = "{region}"
}}

resource "google_compute_network" "main" {{
  name                    = "{instance_name}-network"
  auto_create_subnetworks = false
}}

resource "google_compute_subnetwork" "main" {{
  name          = "{instance_name}-subnet"
  ip_cidr_range = "10.0.1.0/24"
  region        = "{region}"
  network       = google_compute_network.main.id
}}

resource "google_compute_firewall" "ssh" {{
  name    = "{instance_name}-allow-ssh"
  network = google_compute_network.main.name

  allow {{
    protocol = "tcp"
    ports    = ["22"]
  }}

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["ssh"]
}}

resource "google_compute_address" "main" {{
  name   = "{instance_name}-ip"
  region = "{region}"
}}

resource "google_compute_instance" "main" {{
  name         = "{instance_name}"
  machine_type = "{machine_type}"
  zone         = "{zone}"

  boot_disk {{
    initialize_params {{
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 30
      type  = "pd-standard"
    }}
  }}

  network_interface {{
    subnetwork = google_compute_subnetwork.main.id
    
    access_config {{
      nat_ip = google_compute_address.main.address
    }}
  }}

  metadata = {{
    ssh-keys = "ubuntu:${{file("~/.ssh/id_rsa.pub")}}"
  }}

  tags = ["ssh"]
  
  labels = {{
{labels_str}
  }}
}}

output "public_ip" {{
  value       = google_compute_address.main.address
  description = "Public IP address of the instance"
}}

output "instance_id" {{
  value       = google_compute_instance.main.id
  description = "GCP instance ID"
}}

output "instance_name" {{
  value       = google_compute_instance.main.name
  description = "Instance name"
}}
'''
    
    def estimate_cost(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate GCP deployment cost"""
        machine_type = config.get('instance_type', 'e2-medium')
        machine_info = self.MACHINE_TYPES.get(machine_type, self.MACHINE_TYPES['e2-medium'])
        
        # Compute cost
        hourly_compute = machine_info['cost_hour']
        monthly_compute = hourly_compute * 730
        yearly_compute = monthly_compute * 12
        
        # Storage cost (Standard persistent disk)
        storage_gb = 30
        storage_cost_per_gb_month = 0.04  # $0.04/GB/month for standard PD
        monthly_storage = storage_gb * storage_cost_per_gb_month
        yearly_storage = monthly_storage * 12
        
        # Network cost (egress)
        monthly_network = 3.0  # Estimated for basic usage
        yearly_network = monthly_network * 12
        
        return {
            'provider': 'gcp',
            'machine_type': machine_type,
            'compute': {
                'hourly': round(hourly_compute, 4),
                'monthly': round(monthly_compute, 2),
                'yearly': round(yearly_compute, 2)
            },
            'storage': {
                'monthly': round(monthly_storage, 2),
                'yearly': round(yearly_storage, 2),
                'details': f'{storage_gb}GB Standard Persistent Disk'
            },
            'network': {
                'monthly': round(monthly_network, 2),
                'yearly': round(yearly_network, 2)
            },
            'total': {
                'hourly': round(hourly_compute, 4),
                'monthly': round(monthly_compute + monthly_storage + monthly_network, 2),
                'yearly': round(yearly_compute + yearly_storage + yearly_network, 2)
            },
            'assumptions': {
                'uptime_percentage': 100,
                'storage_gb': storage_gb,
                'network_usage': 'Basic'
            }
        }
    
    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate GCP configuration"""
        required_fields = ['region', 'instance_type', 'project_id']
        
        for field in required_fields:
            if field not in config:
                return False, f"Missing required field: {field}"
        
        # Validate region
        if config['region'] not in self.REGIONS:
            return False, f"Invalid region: {config['region']}. Must be one of {', '.join(self.REGIONS[:5])}..."
        
        # Validate machine type
        if config['instance_type'] not in self.MACHINE_TYPES:
            return False, f"Invalid machine type: {config['instance_type']}. Must be one of {', '.join(list(self.MACHINE_TYPES.keys())[:5])}..."
        
        return True, None
    
    def get_instance_types(self) -> Dict[str, Dict[str, Any]]:
        """Get available GCP machine types"""
        return self.MACHINE_TYPES
    
    def _format_labels(self, labels: Dict[str, str]) -> str:
        """Format labels for GCP Terraform"""
        if not labels:
            return ""
        
        formatted = []
        for key, value in labels.items():
            formatted.append(f'    {key} = "{value}"')
        return "\n".join(formatted)
