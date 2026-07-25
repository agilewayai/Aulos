from aulos_mcp.server import create_server


def main() -> None:
    """Run the MCP server over stdio (default MCP transport)."""
    mcp = create_server()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
