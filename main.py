#!/usr/bin/env python3
"""
Zoho CRM MCP Server

A Model Context Protocol server that provides tools for interacting with Zoho CRM.
Uses Nango for authentication and provides comprehensive CRM operations.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Sequence
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv

# MCP imports
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    TextContent,
    Tool,
)

# Load environment variables
load_dotenv(override=True)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("zoho-crm-mcp")


class ZohoCRMError(Exception):
    """Custom exception for Zoho CRM API errors"""
    pass


def get_connection_credentials() -> dict[str, Any]:
    """Get credentials from Nango"""
    
    id = os.environ.get("NANGO_CONNECTION_ID")
    integration_id = os.environ.get("NANGO_INTEGRATION_ID")
    base_url = os.environ.get("NANGO_BASE_URL")
    secret_key = os.environ.get("NANGO_SECRET_KEY")
    
    if not all([id, integration_id, base_url, secret_key]):
        raise ZohoCRMError("Missing required Nango environment variables")
    
    url = f"{base_url}/connection/{id}"
    params = {
        "provider_config_key": integration_id,
        "refresh_token": "true",
    }
    headers = {"Authorization": f"Bearer {secret_key}"}
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    return response.json()


class ZohoCRMClient:
    """Zoho CRM API client"""
    
    def __init__(self, region: str = 'in'):
        self.region = region
        self.api_url = f"https://www.zohoapis.{region}/crm/v2"
        
        self.access_token = None
        self._load_credentials()
    
    def _load_credentials(self):
        """Load credentials from Nango"""
        try:
            credentials = get_connection_credentials()
            
            if 'credentials' in credentials:
                creds = credentials['credentials']
                self.access_token = creds.get('access_token')
            else:
                raise ZohoCRMError("Invalid credentials format from Nango")
                
        except Exception as e:
            raise ZohoCRMError(f"Failed to load Nango credentials: {str(e)}")
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated API request"""
        
        url = f"{self.api_url}/{endpoint}"
        
        headers = {
            'Authorization': f'Zoho-oauthtoken {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))
        
        response = requests.request(method, url, headers=headers, **kwargs)
        
        if response.status_code >= 400:
            try:
                error_data = response.json()
                error_msg = error_data.get('message', response.text)
            except:
                error_msg = response.text
            raise ZohoCRMError(f"API request failed ({response.status_code}): {error_msg}")
        
        try:
            return response.json()
        except:
            return {'raw_response': response.text}
    
    # CRM Operations
    def get_records(self, module: str, **params) -> Dict[str, Any]:
        """Get records from a module"""
        endpoint = f"{module}"
        if params:
            endpoint += f"?{urlencode(params)}"
        return self._make_request('GET', endpoint)
    
    def get_record(self, module: str, record_id: str) -> Dict[str, Any]:
        """Get a specific record by ID"""
        return self._make_request('GET', f"{module}/{record_id}")
    
    def create_record(self, module: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record"""
        payload = {'data': [data]}
        return self._make_request('POST', module, json=payload)
    
    def update_record(self, module: str, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing record"""
        payload = {'data': [data]}
        return self._make_request('PUT', f"{module}/{record_id}", json=payload)
    
    def delete_record(self, module: str, record_id: str) -> Dict[str, Any]:
        """Delete a record"""
        return self._make_request('DELETE', f"{module}/{record_id}")
    
    def search_records(self, module: str, criteria: str, **params) -> Dict[str, Any]:
        """Search records using criteria"""
        params['criteria'] = criteria
        endpoint = f"{module}/search?{urlencode(params)}"
        return self._make_request('GET', endpoint)
    
    def get_modules(self) -> List[Dict[str, Any]]:
        """Get list of available modules"""
        response = self._make_request('GET', 'settings/modules')
        return response.get('modules', [])
    
    def get_fields(self, module: str) -> Dict[str, Any]:
        """Get field metadata for a module"""
        return self._make_request('GET', f"settings/fields?module={module}")
    
    def get_users(self) -> Dict[str, Any]:
        """Get list of CRM users"""
        return self._make_request('GET', 'users')
    
    def get_org(self) -> Dict[str, Any]:
        """Get organization information"""
        return self._make_request('GET', 'org')


# Initialize the CRM client
try:
    crm_client = ZohoCRMClient(
        region=os.environ.get("ZOHO_REGION", "in"),
    )
except Exception as e:
    logger.error(f"Failed to initialize Zoho CRM client: {e}")
    crm_client = None

# Create the MCP server
server = Server("zoho-crm")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available Zoho CRM tools"""
    return [
        Tool(
            name="get_crm_records",
            description="Get records from a Zoho CRM module (Leads, Contacts, Accounts, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "module": {
                        "type": "string",
                        "description": "CRM module name (e.g., Leads, Contacts, Accounts, Deals)"
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number for pagination",
                        "default": 1
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "Number of records per page (max 200)",
                        "default": 20,
                        "maximum": 200
                    },
                    "sort_by": {
                        "type": "string",
                        "description": "Field to sort by"
                    },
                    "sort_order": {
                        "type": "string",
                        "enum": ["asc", "desc"],
                        "description": "Sort order"
                    }
                },
                "required": ["module"]
            }
        ),
        Tool(
            name="get_crm_record",
            description="Get a specific record by ID from Zoho CRM",
            inputSchema={
                "type": "object",
                "properties": {
                    "module": {
                        "type": "string",
                        "description": "CRM module name"
                    },
                    "record_id": {
                        "type": "string",
                        "description": "Record ID"
                    }
                },
                "required": ["module", "record_id"]
            }
        ),
        Tool(
            name="create_crm_record",
            description="Create a new record in Zoho CRM",
            inputSchema={
                "type": "object",
                "properties": {
                    "module": {
                        "type": "string",
                        "description": "CRM module name"
                    },
                    "data": {
                        "type": "object",
                        "description": "Record data as key-value pairs",
                        "additionalProperties": True
                    }
                },
                "required": ["module", "data"]
            }
        ),
        Tool(
            name="update_crm_record",
            description="Update an existing record in Zoho CRM",
            inputSchema={
                "type": "object",
                "properties": {
                    "module": {
                        "type": "string",
                        "description": "CRM module name"
                    },
                    "record_id": {
                        "type": "string",
                        "description": "Record ID to update"
                    },
                    "data": {
                        "type": "object",
                        "description": "Updated record data as key-value pairs",
                        "additionalProperties": True
                    }
                },
                "required": ["module", "record_id", "data"]
            }
        ),
        Tool(
            name="delete_crm_record",
            description="Delete a record from Zoho CRM",
            inputSchema={
                "type": "object",
                "properties": {
                    "module": {
                        "type": "string",
                        "description": "CRM module name"
                    },
                    "record_id": {
                        "type": "string",
                        "description": "Record ID to delete"
                    }
                },
                "required": ["module", "record_id"]
            }
        ),
        Tool(
            name="search_crm_records",
            description="Search records in Zoho CRM using criteria",
            inputSchema={
                "type": "object",
                "properties": {
                    "module": {
                        "type": "string",
                        "description": "CRM module name"
                    },
                    "criteria": {
                        "type": "string",
                        "description": "Search criteria (e.g., 'Email:equals:john@example.com')"
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number",
                        "default": 1
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "Records per page",
                        "default": 20
                    }
                },
                "required": ["module", "criteria"]
            }
        ),
        Tool(
            name="search_crm_by_email",
            description="Search CRM records by email address",
            inputSchema={
                "type": "object",
                "properties": {
                    "module": {
                        "type": "string",
                        "description": "CRM module name (usually Contacts or Leads)"
                    },
                    "email": {
                        "type": "string",
                        "description": "Email address to search for"
                    }
                },
                "required": ["module", "email"]
            }
        ),
        Tool(
            name="search_crm_by_phone",
            description="Search CRM records by phone number",
            inputSchema={
                "type": "object",
                "properties": {
                    "module": {
                        "type": "string",
                        "description": "CRM module name (usually Contacts or Leads)"
                    },
                    "phone": {
                        "type": "string",
                        "description": "Phone number to search for"
                    }
                },
                "required": ["module", "phone"]
            }
        ),
        Tool(
            name="create_crm_lead",
            description="Create a new lead in Zoho CRM with common fields",
            inputSchema={
                "type": "object",
                "properties": {
                    "first_name": {
                        "type": "string",
                        "description": "Lead's first name"
                    },
                    "last_name": {
                        "type": "string",
                        "description": "Lead's last name"
                    },
                    "email": {
                        "type": "string",
                        "description": "Lead's email address"
                    },
                    "company": {
                        "type": "string",
                        "description": "Lead's company"
                    },
                    "phone": {
                        "type": "string",
                        "description": "Lead's phone number"
                    },
                    "lead_source": {
                        "type": "string",
                        "description": "Source of the lead"
                    },
                    "additional_fields": {
                        "type": "object",
                        "description": "Additional custom fields",
                        "additionalProperties": True
                    }
                },
                "required": ["first_name", "last_name"]
            }
        ),
        Tool(
            name="create_crm_contact",
            description="Create a new contact in Zoho CRM with common fields",
            inputSchema={
                "type": "object",
                "properties": {
                    "first_name": {
                        "type": "string",
                        "description": "Contact's first name"
                    },
                    "last_name": {
                        "type": "string",
                        "description": "Contact's last name"
                    },
                    "email": {
                        "type": "string",
                        "description": "Contact's email address"
                    },
                    "account_name": {
                        "type": "string",
                        "description": "Associated account name"
                    },
                    "phone": {
                        "type": "string",
                        "description": "Contact's phone number"
                    },
                    "additional_fields": {
                        "type": "object",
                        "description": "Additional custom fields",
                        "additionalProperties": True
                    }
                },
                "required": ["first_name", "last_name"]
            }
        ),
        Tool(
            name="create_crm_account",
            description="Create a new account in Zoho CRM",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_name": {
                        "type": "string",
                        "description": "Account name"
                    },
                    "website": {
                        "type": "string",
                        "description": "Account website"
                    },
                    "phone": {
                        "type": "string",
                        "description": "Account phone number"
                    },
                    "industry": {
                        "type": "string",
                        "description": "Account industry"
                    },
                    "additional_fields": {
                        "type": "object",
                        "description": "Additional custom fields",
                        "additionalProperties": True
                    }
                },
                "required": ["account_name"]
            }
        ),
        Tool(
            name="get_crm_modules",
            description="Get list of available CRM modules",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_crm_fields",
            description="Get field metadata for a CRM module",
            inputSchema={
                "type": "object",
                "properties": {
                    "module": {
                        "type": "string",
                        "description": "CRM module name"
                    }
                },
                "required": ["module"]
            }
        ),
        Tool(
            name="get_crm_users",
            description="Get list of CRM users",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_crm_org",
            description="Get organization information",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    
    if not crm_client:
        return [TextContent(
            type="text",
            text="Error: Zoho CRM client not initialized. Check your Nango configuration."
        )]
    
    try:
        if name == "get_crm_records":
            result = crm_client.get_records(**arguments)
            
        elif name == "get_crm_record":
            result = crm_client.get_record(arguments["module"], arguments["record_id"])
            
        elif name == "create_crm_record":
            result = crm_client.create_record(arguments["module"], arguments["data"])
            
        elif name == "update_crm_record":
            result = crm_client.update_record(
                arguments["module"], 
                arguments["record_id"], 
                arguments["data"]
            )
            
        elif name == "delete_crm_record":
            result = crm_client.delete_record(arguments["module"], arguments["record_id"])
            
        elif name == "search_crm_records":
            result = crm_client.search_records(**arguments)
            
        elif name == "search_crm_by_email":
            criteria = f"Email:equals:{arguments['email']}"
            result = crm_client.search_records(arguments["module"], criteria)
            
        elif name == "search_crm_by_phone":
            criteria = f"Phone:equals:{arguments['phone']}"
            result = crm_client.search_records(arguments["module"], criteria)
            
        elif name == "create_crm_lead":
            data = {
                "First_Name": arguments["first_name"],
                "Last_Name": arguments["last_name"]
            }
            
            # Add optional fields
            if "email" in arguments:
                data["Email"] = arguments["email"]
            if "company" in arguments:
                data["Company"] = arguments["company"]
            if "phone" in arguments:
                data["Phone"] = arguments["phone"]
            if "lead_source" in arguments:
                data["Lead_Source"] = arguments["lead_source"]
            if "additional_fields" in arguments:
                data.update(arguments["additional_fields"])
                
            result = crm_client.create_record("Leads", data)
            
        elif name == "create_crm_contact":
            data = {
                "First_Name": arguments["first_name"],
                "Last_Name": arguments["last_name"]
            }
            
            # Add optional fields
            if "email" in arguments:
                data["Email"] = arguments["email"]
            if "account_name" in arguments:
                data["Account_Name"] = arguments["account_name"]
            if "phone" in arguments:
                data["Phone"] = arguments["phone"]
            if "additional_fields" in arguments:
                data.update(arguments["additional_fields"])
                
            result = crm_client.create_record("Contacts", data)
            
        elif name == "create_crm_account":
            data = {
                "Account_Name": arguments["account_name"]
            }
            
            # Add optional fields
            if "website" in arguments:
                data["Website"] = arguments["website"]
            if "phone" in arguments:
                data["Phone"] = arguments["phone"]
            if "industry" in arguments:
                data["Industry"] = arguments["industry"]
            if "additional_fields" in arguments:
                data.update(arguments["additional_fields"])
                
            result = crm_client.create_record("Accounts", data)
            
        elif name == "get_crm_modules":
            result = crm_client.get_modules()
            
        elif name == "get_crm_fields":
            result = crm_client.get_fields(arguments["module"])
            
        elif name == "get_crm_users":
            result = crm_client.get_users()
            
        elif name == "get_crm_org":
            result = crm_client.get_org()
            
        else:
            return [TextContent(
                type="text",
                text=f"Error: Unknown tool '{name}'"
            )]
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2, default=str)
        )]
        
    except ZohoCRMError as e:
        return [TextContent(
            type="text",
            text=f"Zoho CRM Error: {str(e)}"
        )]
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        return [TextContent(
            type="text",
            text=f"Error executing tool: {str(e)}"
        )]


async def main():
    """Main entry point for the MCP server"""
    
    # Get transport from environment or use stdio
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="zoho-crm",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


def run():
    asyncio.run(main())