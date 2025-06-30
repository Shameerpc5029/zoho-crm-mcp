# Zoho CRM MCP Server

A powerful Model Context Protocol (MCP) server that seamlessly integrates Zoho CRM with Claude AI. This server provides comprehensive CRM operations through a simple, intuitive interface.

## 🚀 Features

- **Complete CRM Operations**: Create, read, update, and delete records across all Zoho CRM modules
- **Smart Search**: Advanced search capabilities with multiple criteria
- **Module Flexibility**: Works with Leads, Contacts, Accounts, Deals, and custom modules
- **Secure Authentication**: Uses Nango for secure OAuth-based authentication
- **Claude Integration**: Optimized for use with Claude AI assistant

## 📋 Prerequisites

- Python 3.13 or higher
- Zoho CRM account with API access
- Nango account for authentication management
- Claude Desktop App (for Claude integration)

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/zoho-crm-mcp.git
cd zoho-crm-mcp
```

### 2. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

### 3. Environment Setup

Create a `.env` file in the project root:

```env
# Nango Configuration
NANGO_CONNECTION_ID=your_connection_id
NANGO_INTEGRATION_ID=your_integration_id
NANGO_BASE_URL=https://api.nango.dev
NANGO_SECRET_KEY=your_secret_key

# Zoho Configuration
ZOHO_REGION=in  # Options: in, eu, us, au, jp, ca
```

### 4. Nango Setup

1. Create a [Nango account](https://www.nango.dev/)
2. Set up a Zoho CRM integration
3. Configure your OAuth credentials
4. Get your connection ID and integration ID

## 🔧 Claude Configuration

To use this MCP server with Claude Desktop, add the following to your Claude configuration file:

```json
{
  "zoho-crm": {
      "command": "uvx",
      "args": ["git+https://github.com/Shameerpc5029/zoho-crm-mcp.git"],
      "env": {
        "NANGO_BASE_URL": "enter your nango base url",
        "NANGO_SECRET_KEY": "enter your nango secret key",
        "NANGO_CONNECTION_ID": "enter your nango connection id",
        "NANGO_INTEGRATION_ID": "enter your nango integration id",
        "ZOHO_REGION": ""
      }
    }
}
```

### Configuration File Locations

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

## 🎯 Available Tools

### Record Management
- `get_crm_records` - Get records from any CRM module with pagination
- `get_crm_record` - Get a specific record by ID
- `create_crm_record` - Create new records
- `update_crm_record` - Update existing records
- `delete_crm_record` - Delete records

### Search Operations
- `search_crm_records` - Advanced search with custom criteria
- `search_crm_by_email` - Quick email-based search
- `search_crm_by_phone` - Quick phone number search

### Quick Actions
- `create_crm_lead` - Create leads with common fields
- `create_crm_contact` - Create contacts with common fields
- `create_crm_account` - Create accounts with common fields

### System Information
- `get_crm_modules` - List all available modules
- `get_crm_fields` - Get field metadata for any module
- `get_crm_users` - List CRM users
- `get_crm_org` - Get organization information

## 📖 Usage Examples

### With Claude Desktop

Once configured, you can interact with your Zoho CRM directly through Claude:

**Create a new lead:**
```
"Create a new lead for John Smith from Acme Corp with email john@acme.com"
```

**Search for contacts:**
```
"Find all contacts with email domain @microsoft.com"
```

**Get lead information:**
```
"Show me all leads created this month sorted by creation date"
```

**Update a record:**
```
"Update lead ID 123456 with status 'Qualified' and add note 'Follow up scheduled'"
```

### Direct Python Usage

```python
from main import ZohoCRMClient

# Initialize client
client = ZohoCRMClient(region='in')

# Get all leads
leads = client.get_records('Leads', per_page=50)

# Create a new contact
contact_data = {
    'First_Name': 'Jane',
    'Last_Name': 'Doe',
    'Email': 'jane@example.com',
    'Phone': '+1234567890'
}
result = client.create_record('Contacts', contact_data)

# Search by email
contacts = client.search_records('Contacts', 'Email:equals:jane@example.com')
```

## 🔍 Search Criteria Examples

The search functionality supports various criteria formats:

- **Exact match**: `Email:equals:john@example.com`
- **Contains**: `Company:contains:Tech`
- **Starts with**: `Last_Name:starts_with:Smith`
- **Date range**: `Created_Time:between:2024-01-01,2024-12-31`
- **Multiple criteria**: `(Email:contains:@gmail.com)and(Lead_Status:equals:New)`

## 🔐 Security

- All API communications are encrypted using HTTPS
- OAuth tokens are managed securely through Nango
- No sensitive credentials are stored in the codebase
- Environment variables are used for all configuration

## 🛡️ Error Handling

The server includes comprehensive error handling:

- **Authentication errors**: Clear messages for token issues
- **API rate limits**: Automatic retry logic with backoff
- **Validation errors**: Detailed field validation messages
- **Network errors**: Graceful handling of connectivity issues

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: Report bugs or request features via [GitHub Issues](https://github.com/your-username/zoho-crm-mcp/issues)
- **Documentation**: Check the [Zoho CRM API docs](https://www.zoho.com/crm/developer/docs/)
- **Nango Help**: Visit [Nango Documentation](https://docs.nango.dev/)

## 🎯 Roadmap

- [ ] Bulk operations support
- [ ] Webhook integration
- [ ] Custom field mapping
- [ ] Advanced reporting tools
- [ ] Multi-org support
- [ ] Caching layer for better performance

---

**Made with ❤️ for the Claude AI community**
