# ------------------------------------------------------------------------
#
# Register the Gramplet ChatWithTreeMCP
#
# ------------------------------------------------------------------------
register(
    GRAMPLET,
    id="ChatWithTreeMCP",  # Unique ID for your addon
    name=_("Chat With Tree Interactive Addon (MCP)"),  # Display name in Gramps, translatable
    description=_("Chat With Tree using an in-process MCP-style tool service and a Large Language Model. Uses only the Python standard library (no extra modules required)."),
    version = '0.1.4',
    gramps_target_version="6.1",  # Specify the Gramps version you are targeting
    status=STABLE,
    audience=EVERYONE,
    fname="ChatWithTreeMCP.py",  # Main file (class ChatWithTreeMCPClass)
    # The 'gramplet' argument points to the class name in your main file
    gramplet="ChatWithTreeMCPClass",
    gramplet_title=_("Chat With Tree"),
    authors = ["Melle Koning"],
    authors_email = ["mellekoning@gmail.com"],
    height=500,
     # No requires_mod: this addon depends only on the Python standard library
    navtypes=["Dashboard"],
    help_url="Addon:ChatWithTree",
)
