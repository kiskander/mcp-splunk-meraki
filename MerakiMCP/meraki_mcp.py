import  meraki
import logging
import os
from mcp.server.fastmcp import FastMCP

# Read Envs
MERAKI_KEY = os.environ.get('MERAKI_KEY')
MERAKI_ORG = os.environ.get('MERAKI_ORG')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("meraki_mcp.log")
    ]
)
logger = logging.getLogger(__name__)


# Environment variables
FASTMCP_PORT = int(os.environ.get("FASTMCP_PORT", "5000"))
os.environ["FASTMCP_PORT"] = str(FASTMCP_PORT)

mcp = FastMCP(
    "meraki",
    description="MCP Server for Meraki",
    version="0.1.0",
    host="0.0.0.0",  # Listen on all interfaces
    port=FASTMCP_PORT
)

dashboard = meraki.DashboardAPI(MERAKI_KEY, output_log=False, suppress_logging=True)


@mcp.tool()
async def get_meraki_orgs() -> dict:
    """
    Retrieves a list of organizations from the Meraki Dashboard.

    Returns:
        dict: A dictionary containing the list of organizations.
    """
    try:
        orgs = dashboard.organizations.getOrganizations()
        org_list = [{"id": org["id"], "name": org["name"]} for org in orgs]
        return {"organizations": org_list}
    except Exception as e:
        logger.error(f"Failed to fetch organizations: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_meraki_networks_by_org(org_id: str) -> dict:
    """
    Retrieves a list of networks for a given organization ID from the Meraki Dashboard.

    Args:
        org_id (str): The ID of the organization.

    Returns:
        dict: A dictionary containing the list of networks.
    """
    try:
        networks = dashboard.organizations.getOrganizationNetworks(org_id)
        network_list = [{"id": net["id"], "name": net["name"]} for net in networks]
        return {"networks": network_list}
    except Exception as e:
        logger.error(f"Failed to fetch networks for org {org_id}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_meraki_devices_by_network(network_id: str) -> dict:
    """
    Retrieves a list of devices for a given network ID from the Meraki Dashboard.

    Args:
        network_id (str): The ID of the network.

    Returns:
        dict: A dictionary containing the list of devices.
    """
    try:
        devices = dashboard.networks.getNetworkDevices(network_id)
        device_list = [{"serial": dev["serial"], "model": dev["model"], "name": dev.get("name", "")} for dev in devices]
        return {"devices": device_list}
    except Exception as e:
        logger.error(f"Failed to fetch devices for network {network_id}: {e}")
        return {"error": str(e)}


@mcp.tool()
async def update_meraki_device_settings(
    serial: str,
    name: str = None,
    ip: str = None,
    subnet: str = None,
    gateway: str = None,
    dns: list = None,
    switch_port: int = None
) -> dict:
    """
    Updates device settings on the Meraki Dashboard.

    Args:
        serial (str): The serial number of the device to update.
        name (str, optional): The new name for the device.
        ip (str, optional): The new IP address for the device's management interface.
        subnet (str, optional): The new subnet mask.
        gateway (str, optional): The new gateway.
        dns (list, optional): DNS servers (comma-separated string or list).
        switch_port (int, optional): The switch port number to modify if device is a switch.

    Returns:
        dict: A dictionary containing the status of the update.
    """
    results = {}

    try:
        # Update device name
        if name:
            dashboard.devices.updateDevice(serial, name=name)
            results["device_update"] = "name updated"

        # Update management interface IP, subnet, gateway, dns
        if ip or subnet or gateway or dns:
            interface_id = "lan"
            update_fields = {}
            update_fields["usingStaticIp"] = True
            if ip:
                update_fields["staticIp"] = ip
            if subnet:
                update_fields["staticSubnetMask"] = subnet
            if gateway:
                update_fields["staticGatewayIp"] = gateway
            if dns:
                # Accept both a comma-separated string or a list for dns
                update_fields["dnsNameservers"] = dns if isinstance(dns, str) else ','.join(dns)
            dashboard.devices.updateDeviceManagementInterface(
                serial=serial, wan1={**update_fields}
            )
            results["management_interface_update"] = "IP/interface updated"

        # Check if device is a switch and update port if requested
        device = dashboard.devices.getDevice(serial)
        if "MS" in device["model"] and switch_port is not None:
            dashboard.switch.switchPorts.updateNetworkSwitchPort(
                networkId=device["networkId"],
                switchPortId=str(switch_port),
                body={"name": name if name else ""}
            )
            results["switch_port_update"] = f"Port {switch_port} updated"

        if not results:
            results["status"] = "No updates provided"

        return results

    except Exception as e:
        logger.error(f"Failed to update device {serial}: {e}")
        return {"error": str(e)}

# ---- MCP Tools for Switch Configuration Endpoints ----

@mcp.tool()
async def get_network_switch_settings(network_id: str) -> dict:
    """Get switch settings for a network."""
    try:
        return dashboard.switch_settings.getNetworkSwitchSettings(network_id)
    except Exception as e:
        logger.error(f"Failed to fetch switch settings for network {network_id}: {e}")
        return {"error": str(e)}

@mcp.tool()
async def update_network_switch_settings(network_id: str, **kwargs) -> dict:
    """Update switch settings for a network (kwargs: vlanId, useCombinedPower, etc)."""
    try:
        return dashboard.switch_settings.updateNetworkSwitchSettings(network_id, **kwargs)
    except Exception as e:
        logger.error(f"Failed to update switch settings for network {network_id}: {e}")
        return {"error": str(e)}

@mcp.tool()
async def get_network_switch_ports(network_id: str, device_serial: str) -> dict:
    """List all switch ports on a device."""
    try:
        return dashboard.switch_ports.getNetworkSwitchPorts(network_id, device_serial)
    except Exception as e:
        logger.error(f"Failed to fetch switch ports for device {device_serial}: {e}")
        return {"error": str(e)}

@mcp.tool()
async def get_network_switch_port(network_id: str, device_serial: str, port_id: str) -> dict:
    """Get a single switch port's configuration."""
    try:
        return dashboard.switch_ports.getNetworkSwitchPort(network_id, device_serial, port_id)
    except Exception as e:
        logger.error(f"Failed to fetch switch port {port_id} for device {device_serial}: {e}")
        return {"error": str(e)}

@mcp.tool()
async def update_network_switch_port(network_id: str, device_serial: str, port_id: str, **kwargs) -> dict:
    """Update a switch port's configuration (kwargs: name, vlan, enabled, etc)."""
    try:
        return dashboard.switch_ports.updateNetworkSwitchPort(network_id, device_serial, port_id, **kwargs)
    except Exception as e:
        logger.error(f"Failed to update switch port {port_id} for device {device_serial}: {e}")
        return {"error": str(e)}

@mcp.tool()
async def get_network_switch_stacks(network_id: str) -> dict:
    """List all switch stacks in a network."""
    try:
        return dashboard.switch_stacks.getNetworkSwitchStacks(network_id)
    except Exception as e:
        logger.error(f"Failed to fetch switch stacks for network {network_id}: {e}")
        return {"error": str(e)}

@mcp.tool()
async def create_network_switch_stack(network_id: str, name: str, serials: list) -> dict:
    """Create a switch stack in a network."""
    try:
        return dashboard.switch_stacks.createNetworkSwitchStack(network_id, name, serials)
    except Exception as e:
        logger.error(f"Failed to create switch stack in network {network_id}: {e}")
        return {"error": str(e)}

@mcp.tool()
async def delete_network_switch_stack(network_id: str, switch_stack_id: str) -> dict:
    """Delete a switch stack."""
    try:
        return dashboard.switch_stacks.deleteNetworkSwitchStack(network_id, switch_stack_id)
    except Exception as e:
        logger.error(f"Failed to delete switch stack {switch_stack_id}: {e}")
        return {"error": str(e)}

@mcp.tool()
async def add_network_switch_stack_member(network_id: str, switch_stack_id: str, serials: list) -> dict:
    """Add member switches to a stack."""
    try:
        return dashboard.switch_stacks.addNetworkSwitchStackMember(network_id, switch_stack_id, serials)
    except Exception as e:
        logger.error(f"Failed to add member(s) to stack {switch_stack_id}: {e}")
        return {"error": str(e)}

@mcp.tool()
async def remove_network_switch_stack_member(network_id: str, switch_stack_id: str, serials: list) -> dict:
    """Remove member switches from a stack."""
    try:
        return dashboard.switch_stacks.removeNetworkSwitchStackMember(network_id, switch_stack_id, serials)
    except Exception as e:
        logger.error(f"Failed to remove member(s) from stack {switch_stack_id}: {e}")
        return {"error": str(e)}


# ---- MCP Tool: Get  Management Interface ----
@mcp.tool()
async def get_switch_management_interface(serial: str) -> dict:
    """Retrieve the management interface info for a switch (by serial)."""
    try:
        return dashboard.devices.getDeviceManagementInterface(serial)
    except Exception as e:
        logger.error(f"Failed to fetch management interface for switch {serial}: {e}")
        return {"error": str(e)}

# Initialize MCP server
if __name__ == "__main__":
    logger.info(f"🚀 Starting Meraki MCP server")
    mcp.run(transport="stdio")
