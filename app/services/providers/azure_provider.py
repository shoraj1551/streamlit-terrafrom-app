"""
Azure Cloud Provider Implementation
"""

from typing import Dict, Any, List, Optional
from app.services.cloud_provider import CloudProvider


class AzureProvider(CloudProvider):
    """Microsoft Azure cloud provider"""
    
    REGIONS = [
        "eastus", "eastus2", "westus", "westus2", "westus3",
        "centralus", "northcentralus", "southcentralus",
        "northeurope", "westeurope", "uksouth", "ukwest",
        "francecentral", "germanywestcentral",
        "southeastasia", "eastasia", "japaneast", "japanwest",
        "australiaeast", "australiasoutheast",
        "brazilsouth", "canadacentral", "canadaeast",
        "southafricanorth", "uaenorth"
    ]
    
    VM_SIZES = {
        # B-series (Burstable)
        "Standard_B1s": {"vcpu": 1, "ram_gb": 1, "cost_hour": 0.0104},
        "Standard_B1ms": {"vcpu": 1, "ram_gb": 2, "cost_hour": 0.0207},
        "Standard_B2s": {"vcpu": 2, "ram_gb": 4, "cost_hour": 0.0416},
        "Standard_B2ms": {"vcpu": 2, "ram_gb": 8, "cost_hour": 0.0832},
        "Standard_B4ms": {"vcpu": 4, "ram_gb": 16, "cost_hour": 0.166},
        
        # D-series (General purpose)
        "Standard_D2s_v3": {"vcpu": 2, "ram_gb": 8, "cost_hour": 0.096},
        "Standard_D4s_v3": {"vcpu": 4, "ram_gb": 16, "cost_hour": 0.192},
        "Standard_D8s_v3": {"vcpu": 8, "ram_gb": 32, "cost_hour": 0.384},
        
        # E-series (Memory optimized)
        "Standard_E2s_v3": {"vcpu": 2, "ram_gb": 16, "cost_hour": 0.126},
        "Standard_E4s_v3": {"vcpu": 4, "ram_gb": 32, "cost_hour": 0.252},
    }
    
    @property
    def name(self) -> str:
        return "Azure"
    
    @property
    def regions(self) -> List[str]:
        return self.REGIONS
    
    def generate_terraform(self, config: Dict[str, Any]) -> str:
        """Generate Azure Terraform configuration"""
        vm_size = config.get('instance_type', 'Standard_B1s')
        region = config.get('region', 'eastus')
        resource_group = config.get('resource_group', 'terraform-rg')
        vm_name = config.get('name', 'terraform-vm')
        environment = config.get('environment', 'dev')
        tags = config.get('tags', {})
        
        # Add environment to tags
        all_tags = {
            'Environment': environment,
            'ManagedBy': 'Terraform-Streamlit',
            **tags
        }
        
        return f'''terraform {{
  required_providers {{
    azurerm = {{
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }}
  }}
}}

provider "azurerm" {{
  features {{}}
}}

resource "azurerm_resource_group" "main" {{
  name     = "{resource_group}"
  location = "{region}"
  
  tags = {{
{self._format_tags(all_tags)}
  }}
}}

resource "azurerm_virtual_network" "main" {{
  name                = "{vm_name}-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  
  tags = azurerm_resource_group.main.tags
}}

resource "azurerm_subnet" "main" {{
  name                 = "{vm_name}-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.1.0/24"]
}}

resource "azurerm_public_ip" "main" {{
  name                = "{vm_name}-pip"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  allocation_method   = "Static"
  sku                 = "Standard"
  
  tags = azurerm_resource_group.main.tags
}}

resource "azurerm_network_security_group" "main" {{
  name                = "{vm_name}-nsg"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  security_rule {{
    name                       = "SSH"
    priority                   = 1001
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }}
  
  tags = azurerm_resource_group.main.tags
}}

resource "azurerm_network_interface" "main" {{
  name                = "{vm_name}-nic"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  ip_configuration {{
    name                          = "internal"
    subnet_id                     = azurerm_subnet.main.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.main.id
  }}
  
  tags = azurerm_resource_group.main.tags
}}

resource "azurerm_network_interface_security_group_association" "main" {{
  network_interface_id      = azurerm_network_interface.main.id
  network_security_group_id = azurerm_network_security_group.main.id
}}

resource "azurerm_linux_virtual_machine" "main" {{
  name                = "{vm_name}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  size                = "{vm_size}"
  admin_username      = "azureuser"
  
  network_interface_ids = [
    azurerm_network_interface.main.id,
  ]

  admin_ssh_key {{
    username   = "azureuser"
    public_key = file("~/.ssh/id_rsa.pub")
  }}

  os_disk {{
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
    disk_size_gb         = 30
  }}

  source_image_reference {{
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }}
  
  tags = azurerm_resource_group.main.tags
}}

output "public_ip" {{
  value       = azurerm_public_ip.main.ip_address
  description = "Public IP address of the VM"
}}

output "vm_id" {{
  value       = azurerm_linux_virtual_machine.main.id
  description = "Azure VM ID"
}}

output "resource_group" {{
  value       = azurerm_resource_group.main.name
  description = "Resource group name"
}}
'''
    
    def estimate_cost(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate Azure deployment cost"""
        vm_size = config.get('instance_type', 'Standard_B1s')
        vm_info = self.VM_SIZES.get(vm_size, self.VM_SIZES['Standard_B1s'])
        
        # Compute cost
        hourly_compute = vm_info['cost_hour']
        monthly_compute = hourly_compute * 730  # Average hours per month
        yearly_compute = monthly_compute * 12
        
        # Storage cost (Standard LRS)
        storage_gb = 30
        storage_cost_per_gb_month = 0.05
        monthly_storage = storage_gb * storage_cost_per_gb_month
        yearly_storage = monthly_storage * 12
        
        # Network cost (minimal for basic usage)
        monthly_network = 5.0  # Estimated
        yearly_network = monthly_network * 12
        
        return {
            'provider': 'azure',
            'vm_size': vm_size,
            'compute': {
                'hourly': round(hourly_compute, 4),
                'monthly': round(monthly_compute, 2),
                'yearly': round(yearly_compute, 2)
            },
            'storage': {
                'monthly': round(monthly_storage, 2),
                'yearly': round(yearly_storage, 2),
                'details': f'{storage_gb}GB Standard LRS'
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
        """Validate Azure configuration"""
        required_fields = ['region', 'instance_type']
        
        for field in required_fields:
            if field not in config:
                return False, f"Missing required field: {field}"
        
        # Validate region
        if config['region'] not in self.REGIONS:
            return False, f"Invalid region: {config['region']}. Must be one of {', '.join(self.REGIONS[:5])}..."
        
        # Validate VM size
        if config['instance_type'] not in self.VM_SIZES:
            return False, f"Invalid VM size: {config['instance_type']}. Must be one of {', '.join(list(self.VM_SIZES.keys())[:5])}..."
        
        return True, None
    
    def get_instance_types(self) -> Dict[str, Dict[str, Any]]:
        """Get available Azure VM sizes"""
        return self.VM_SIZES
