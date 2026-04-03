# EverBridge

**Author:** Jordan Moss  

Blender add-on that patches **Hard Ops** so **Ever Scroll** treats **Normal Magic** geometry-nodes boolean modifiers like native **BOOLEAN** modifiers:

- Boolean Pro, Boolean Extrude, Boolean Trim, Cut Groove  

EverBridge does **not** modify Hard Ops or Normal Magic on disk. It only installs runtime hooks after those add-ons are available.

**Dependencies:** Both **Hard Ops** and **Normal Magic** must be **enabled** in Preferences. The add-on shows OK / missing status in its preferences panel; patches stay inactive until both are detected.

## Requirements

- Blender 4.5+ (including 5.x)
- [Hard Ops](https://masterxeon1001.gumroad.com/)
- [Normal Magic](https://spaghetmenot.github.io/normalmagic/latest/) (stock build without a duplicate Ever Scroll shim, or disable the duplicate)

## Install

1. Copy or zip the `everbridge` folder and install in **Edit → Preferences → Add-ons**.
2. Enable **Normal Magic** and **Hard Ops**, then enable **EverBridge**.
3. Order does not matter; EverBridge retries on file load and after a short delay.

## Preferences

- **Enable Ever Scroll bridge** — when on and both dependencies are met, Hard Ops is patched.

## License

GPL-3.0-or-later (see `blender_manifest.toml`).
