# 🧠 Self-Healing Network with MCP Agents

This repository demonstrates how to build agentic workflows using two MCP servers to detect and reverse configuration drift in a Meraki network. The system utilizes:

- A **Splunk MCP Agent** to detect network changes. *Credit to [William Searle](https://github.com/livehybrid/splunk-mcp) for the Splunk MCP Server.*
- A **Meraki MCP Agent** to reverse unauthorized changes.

Agentic AI handles both detection and remediation based on natural language prompts—no hardcoded orchestration required.

---

## 🚀 How It Works

1. You ask: _“What changed in my Meraki network?”_
2. The **Splunk MCP Agent** queries Splunk using its SDK and returns configuration drift.
3. The **Meraki MCP Agent** compares the change to the source of truth and calls the appropriate Meraki API to reverse it.

---

## 🛠️ Prerequisites

- Python 3.10 or higher
- Access to:
  - A Splunk instance with relevant logs
  - A Meraki Dashboard API key
  - Claude Desktop or any MCP-compatible client
- `claude_desktop_config.json` configured with correct tool registration and MCP server paths

---

## 📦 Installation

**Clone the repository:**

   ```bash
   git clone https://github.com/kiskander/mcp-splunk-meraki.git
   cd mcp-splunk-meraki
   ```

### Splunk MCP Setup (Local Installation)
for more Splunk MCP installation options checkout: https://github.com/livehybrid/splunk-mcp
1. **Access Splunk MCP:**

   ```bash
   cd mcp-splunk-meraki/SplunkMCP
   ```

2. **Install dependencies using Poetry:**

   ```bash
   poetry install
   ```

3. **Configure environment variables:**

   Copy the example environment file and update it with your Splunk credentials:

   ```bash
   cp .env.example .env
   ```

   Update the `.env` file with the following:

   ```ini
   SPLUNK_HOST=your_splunk_host
   SPLUNK_PORT=8089
   SPLUNK_USERNAME=your_username
   SPLUNK_PASSWORD=your_password
   SPLUNK_SCHEME=https
   VERIFY_SSL=true
   FASTMCP_LOG_LEVEL=INFO
   SERVER_MODE=stdio
   ```

4. **Run the Splunk MCP:**

   ```bash
   poetry run python splunk_mcp.py stdio
   ```
---

### Meraki MCP Setup

1. **Install `uv` (if not already installed):**

   For macOS/Linux:

   ```bash
   brew install uv
   ```

2. **Set Up Your Meraki MCP Project:**

   ```bash
   cd mcp-splunk-meraki/MerakiMCP
   ```

3. **Install dependencies using `uv`:**

   ```bash
   uv init

   uv venv
   source .venv/bin/activate # or .venv\Scripts\activate on Windows

   uv add "mcp[cli]"
   uv add "meraki"  
   ```
4. **Run the Meraki MCP Agent:**

   ```bash
   python meraki_mcp.py
   ```
---
