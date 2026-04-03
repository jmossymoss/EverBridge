"""
Geometry-nodes modifier sockets by display name (Normal Magic compatible).
Self-contained for EverBridge.
"""

import bpy


def socket_name_from_display_name(
    modifier: bpy.types.NodesModifier, socket_name: str, index: int = 0
):
    """Map socket display name to RNA identifier. Index selects duplicate display names."""
    if not modifier.node_group:
        return None
    matching = []
    try:
        items_tree = modifier.node_group.interface.items_tree
    except Exception:
        return None
    for item in items_tree:
        try:
            iname = item.name or ""
        except Exception:
            continue
        if iname.lower() == (socket_name or "").lower():
            matching.append(item.identifier)
    if not matching:
        return None
    if index >= len(matching):
        return matching[0]
    return matching[index]


def set_socket_by_name(
    modifier: bpy.types.NodesModifier, socket_name: str, value, index: int = 0
):
    ident = socket_name_from_display_name(modifier, socket_name, index)
    if ident is None:
        return
    modifier[ident] = value


def get_socket_by_name(
    modifier: bpy.types.NodesModifier, socket_name: str, index: int = 0
):
    ident = socket_name_from_display_name(modifier, socket_name, index)
    if ident is None:
        return None
    return modifier[ident]
