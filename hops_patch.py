"""
Monkey-patch Hard Ops so Ever Scroll treats Normal Magic GN booleans like BOOLEAN modifiers.
"""

import importlib
import sys
import bpy

from . import nm_boolean_targets as targets
from . import nm_sockets

_orig_mod_type = None
_orig_bool_object_get = None
_patched = False
_patched_hops_mod = None

_popup_shim_applied = False
_popups_module = None
_orig_popup_enum_ids = None
_orig_get_boolean_operation = None
_orig_set_boolean_operation = None


def is_normal_magic_enabled() -> bool:
    """True if an enabled add-on module id looks like Normal Magic (legacy or extension)."""
    try:
        for key in bpy.context.preferences.addons.keys():
            if "normalmagic" in key.lower():
                return True
    except Exception:
        pass
    return False


def _prefs_allow_shim() -> bool:
    try:
        pkg = __package__
        ad = bpy.context.preferences.addons.get(pkg)
        if not ad or not hasattr(ad, "preferences"):
            return True
        return bool(getattr(ad.preferences, "enable_bridge", True))
    except Exception:
        return True


def dependencies_met() -> bool:
    """Hard Ops must be importable and Normal Magic must be enabled in preferences."""
    if not is_normal_magic_enabled():
        return False
    hops_mod, _ = _import_hops_modifier_module()
    return hops_mod is not None


def _import_hops_modifier_module():
    for modname in ("HOps.utility.modifier", "hops.utility.modifier"):
        try:
            m = importlib.import_module(modname)
            return m, modname
        except ImportError:
            continue

    try:
        import addon_utils

        for item in addon_utils.modules():
            mod = item[0] if isinstance(item, (tuple, list)) and item else item
            info = getattr(mod, "bl_info", None) or {}
            name = info.get("name") or ""
            if not str(name).startswith("Hard Ops"):
                continue
            base = mod.__name__
            target = f"{base}.utility.modifier"
            try:
                return importlib.import_module(target), target
            except ImportError:
                continue
    except Exception:
        pass

    for key, m in sys.modules.items():
        if not key.endswith(".utility.modifier"):
            continue
        if (
            getattr(m, "bool_mod_get", None)
            and getattr(m, "mod_type", None)
            and getattr(m, "bool_object_get", None)
        ):
            return m, key

    return None, None


def is_hard_ops_available() -> bool:
    return _import_hops_modifier_module()[0] is not None


def _wrapped_mod_type(mod):
    t = _orig_mod_type(mod)
    if t == "BOOLEAN":
        return t
    if targets.is_nm_boolean_nodes_modifier(mod):
        return "BOOLEAN"
    return t


def _wrapped_bool_object_get(mod):
    obj = _orig_bool_object_get(mod)
    if obj is not None:
        return obj
    if targets.is_nm_boolean_nodes_modifier(mod):
        return targets.nm_boolean_scroll_cutter(mod)
    return None


def _hops_root_package(hops_modifier_module) -> str:
    parts = hops_modifier_module.__name__.split(".")
    return ".".join(parts[:-2])


def _nm_operation_idx_to_id(idx):
    return {0: "INTERSECT", 1: "UNION", 2: "DIFFERENCE", 4: "SLICE"}.get(
        int(idx) if idx is not None else 2, "DIFFERENCE"
    )


def _nm_operation_id_to_idx(ident: str) -> int:
    return {"INTERSECT": 0, "UNION": 1, "DIFFERENCE": 2, "SLICE": 4}.get(str(ident), 2)


def _nm_boolean_operation_opts(mod):
    opts = ["INTERSECT", "UNION", "DIFFERENCE"]
    if targets.nm_boolean_nodes_base_name(mod) == "Boolean Pro":
        opts = opts + ["SLICE"]
    return opts


def _nm_nodes_needs_operation_popup(mod, propname: str) -> bool:
    if propname != "operation":
        return False
    if targets.is_nm_boolean_nodes_modifier(mod):
        return True
    if mod.type != "NODES" or not getattr(mod, "node_group", None):
        return False
    name = mod.node_group.name
    if not name:
        return False
    bases = ("Boolean Pro", "Boolean Extrude", "Boolean Trim", "Cut Groove")
    for b in bases:
        if name == b or name.startswith(b + "."):
            return True
    return False


def _wrapped_popup_enum_ids(mod, propname):
    if _nm_nodes_needs_operation_popup(mod, propname):
        return _nm_boolean_operation_opts(mod)
    return _orig_popup_enum_ids(mod, propname)


def _wrapped_get_boolean_operation(mod):
    if _nm_nodes_needs_operation_popup(mod, "operation"):
        try:
            idx = nm_sockets.get_socket_by_name(mod, "Operation")
        except Exception:
            idx = 2
        ident = _nm_operation_idx_to_id(idx)
        opts = _nm_boolean_operation_opts(mod)
        if ident not in opts:
            ident = "DIFFERENCE"
        return ident
    return _orig_get_boolean_operation(mod)


def _wrapped_set_boolean_operation(opt, mod):
    if _nm_nodes_needs_operation_popup(mod, "operation"):
        idx = _nm_operation_id_to_idx(opt)
        try:
            nm_sockets.set_socket_by_name(mod, "Operation", idx)
        except Exception:
            pass
        mod.id_data.update_tag()
        return
    _orig_set_boolean_operation(opt, mod)


_wrapped_popup_enum_ids._everbridge_shim = True


def _ensure_popup_shim(hops_modifier_module):
    global _popup_shim_applied, _popups_module
    global _orig_popup_enum_ids, _orig_get_boolean_operation, _orig_set_boolean_operation

    root = _hops_root_package(hops_modifier_module)
    try:
        popups = importlib.import_module(f"{root}.operators.modals.ever_scroll.popups")
    except ImportError:
        return

    if getattr(popups.enum_ids, "_everbridge_shim", False):
        _popups_module = popups
        _popup_shim_applied = True
        return

    _orig_popup_enum_ids = popups.enum_ids
    _orig_get_boolean_operation = popups.get_boolean_operation
    _orig_set_boolean_operation = popups.set_boolean_operation
    popups.enum_ids = _wrapped_popup_enum_ids
    popups.get_boolean_operation = _wrapped_get_boolean_operation
    popups.set_boolean_operation = _wrapped_set_boolean_operation
    _popups_module = popups
    _popup_shim_applied = True


def _remove_popup_shim():
    global _popup_shim_applied, _popups_module
    global _orig_popup_enum_ids, _orig_get_boolean_operation, _orig_set_boolean_operation

    if not _popup_shim_applied or _popups_module is None:
        _popup_shim_applied = False
        _popups_module = None
        return
    try:
        if _orig_popup_enum_ids is not None:
            _popups_module.enum_ids = _orig_popup_enum_ids
        if _orig_get_boolean_operation is not None:
            _popups_module.get_boolean_operation = _orig_get_boolean_operation
        if _orig_set_boolean_operation is not None:
            _popups_module.set_boolean_operation = _orig_set_boolean_operation
    except Exception:
        pass
    _popup_shim_applied = False
    _popups_module = None
    _orig_popup_enum_ids = None
    _orig_get_boolean_operation = None
    _orig_set_boolean_operation = None


def remove_shim():
    global _patched, _orig_mod_type, _orig_bool_object_get, _patched_hops_mod

    _remove_popup_shim()

    if not _patched:
        return

    hops_mod = _patched_hops_mod
    if hops_mod is None:
        hops_mod, _ = _import_hops_modifier_module()
    if hops_mod is None:
        _patched = False
        _orig_mod_type = None
        _orig_bool_object_get = None
        _patched_hops_mod = None
        return

    if _orig_mod_type is not None:
        hops_mod.mod_type = _orig_mod_type
    if _orig_bool_object_get is not None:
        hops_mod.bool_object_get = _orig_bool_object_get
    _patched = False
    _orig_mod_type = None
    _orig_bool_object_get = None
    _patched_hops_mod = None


def try_install_shim():
    global _patched, _orig_mod_type, _orig_bool_object_get, _patched_hops_mod

    allow = _prefs_allow_shim()
    if not allow:
        remove_shim()
        return

    if not dependencies_met():
        remove_shim()
        return

    if _patched:
        if _patched_hops_mod is not None:
            _ensure_popup_shim(_patched_hops_mod)
        return

    hops_mod, _resolved = _import_hops_modifier_module()
    if hops_mod is None:
        return

    _orig_mod_type = hops_mod.mod_type
    _orig_bool_object_get = hops_mod.bool_object_get
    hops_mod.mod_type = _wrapped_mod_type
    hops_mod.bool_object_get = _wrapped_bool_object_get
    _patched = True
    _patched_hops_mod = hops_mod
    _ensure_popup_shim(hops_mod)


def load_post_try_install(dummy=None):
    try_install_shim()


def _deferred_try_install():
    try_install_shim()
    return None
