"""
Normal Magic geometry-nodes modifiers treated as booleans for Hard Ops Ever Scroll.
No dependency on importing the Normal Magic add-on package.
"""

import bpy

from . import nm_sockets

NM_BOOLEAN_NODE_BASES = frozenset(
    {"Boolean Pro", "Boolean Extrude", "Boolean Trim", "Cut Groove"}
)


def nm_boolean_nodes_base_name(modifier: bpy.types.Modifier):
    if modifier.type != "NODES" or not modifier.node_group:
        return None
    return modifier.node_group.name.split(".")[0]


def is_nm_boolean_nodes_modifier(modifier: bpy.types.Modifier) -> bool:
    base = nm_boolean_nodes_base_name(modifier)
    return base is not None and base in NM_BOOLEAN_NODE_BASES


def get_generic_nm_references(modifier: bpy.types.NodesModifier):
    referenced_objects = []
    collection = None

    use_collection = nm_sockets.get_socket_by_name(modifier, "") == 1

    if use_collection:
        collection = nm_sockets.get_socket_by_name(modifier, "Collection")
        return referenced_objects, collection

    object_count = nm_sockets.get_socket_by_name(modifier, "Object Count")
    if object_count is None:
        object_count = 0
    for i in range(int(object_count) + 1):
        object_ref = nm_sockets.get_socket_by_name(modifier, "Object", i)
        if object_ref:
            referenced_objects.append(object_ref)
    return referenced_objects, collection


def _nm_boolean_referenced_objects(modifier: bpy.types.NodesModifier) -> list:
    referenced_objects = []
    collection = None
    base = nm_boolean_nodes_base_name(modifier)
    if base is None:
        return referenced_objects

    if base == "Boolean Pro":
        object_value = nm_sockets.get_socket_by_name(modifier, "Object")
        if object_value is not None:
            referenced_objects.append(object_value)
        collection_value = nm_sockets.get_socket_by_name(modifier, "Collection")
        if collection_value is not None:
            collection = collection_value
    elif base in ("Boolean Extrude", "Boolean Trim", "Cut Groove"):
        referenced_objects, collection = get_generic_nm_references(modifier)
    else:
        return referenced_objects

    if collection is not None:
        for obj in collection.objects:
            referenced_objects.append(obj)
    return referenced_objects


def nm_boolean_scroll_cutter(modifier: bpy.types.Modifier):
    """First referenced mesh object by name, for Ever Scroll when multiple cutters exist."""
    if not is_nm_boolean_nodes_modifier(modifier):
        return None
    objs = _nm_boolean_referenced_objects(modifier)
    meshes = sorted(
        (o for o in objs if o and getattr(o, "type", None) == "MESH"),
        key=lambda o: o.name,
    )
    return meshes[0] if meshes else None
