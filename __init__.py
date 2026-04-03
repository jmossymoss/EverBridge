"""
EverBridge — Hard Ops Ever Scroll compatibility for Normal Magic geometry-nodes booleans
(Boolean Pro, Extrude, Trim, Cut Groove).

Author: Jordan Moss
"""

import bpy
from bpy.app.handlers import persistent
from bpy.types import AddonPreferences

from . import hops_patch

bl_info = {
    "name": "EverBridge",
    "author": "Jordan Moss",
    "version": (1, 1, 0),
    "blender": (4, 5, 0),
    "location": "Preferences > Add-ons",
    "description": "Lets Hard Ops Ever Scroll treat Normal Magic geometry-nodes boolean modifiers "
    "like native BOOLEAN modifiers. Requires Hard Ops and Normal Magic enabled.",
    "category": "Object",
}


def _prefs_update(self, context):
    if self.enable_bridge:
        hops_patch.try_install_shim()
    else:
        hops_patch.remove_shim()


class EverBridgeAddonPreferences(AddonPreferences):
    bl_idname = __name__

    enable_bridge: bpy.props.BoolProperty(
        name="Enable Ever Scroll bridge",
        description="Patch Hard Ops so Ever Scroll works with Normal Magic GN booleans",
        default=True,
        update=_prefs_update,
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "enable_bridge")

        nm_ok = hops_patch.is_normal_magic_enabled()
        ho_ok = hops_patch.is_hard_ops_available()
        all_ok = nm_ok and ho_ok

        box = layout.box()
        box.label(text="Dependencies (must be enabled in Add-ons):", icon="INFO")
        row = box.row()
        row.label(
            text="Normal Magic: OK" if nm_ok else "Normal Magic: not detected — enable the add-on",
            icon="CHECKMARK" if nm_ok else "ERROR",
        )
        row = box.row()
        row.label(
            text="Hard Ops: OK" if ho_ok else "Hard Ops: not detected — enable the add-on",
            icon="CHECKMARK" if ho_ok else "ERROR",
        )

        if self.enable_bridge and not all_ok:
            layout.label(
                text="Bridge is on but patches stay inactive until both add-ons are available.",
                icon="INFO",
            )

        layout.separator()
        box2 = layout.box()
        box2.label(
            text="If another Normal Magic build adds its own Hard Ops Ever Scroll shim,",
        )
        box2.label(text="disable one of the two to avoid double patches.")


@persistent
def _load_post_try_install(_dummy=None):
    hops_patch.load_post_try_install()


def register():
    bpy.utils.register_class(EverBridgeAddonPreferences)
    bpy.app.handlers.load_post.append(_load_post_try_install)
    bpy.app.timers.register(hops_patch._deferred_try_install, first_interval=0.2)


def unregister():
    hops_patch.remove_shim()
    if _load_post_try_install in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_load_post_try_install)
    bpy.utils.unregister_class(EverBridgeAddonPreferences)
