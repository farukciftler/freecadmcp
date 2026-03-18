"""
FreeCAD MCP Server — main entry point.

Usage:
    python -m server.main          # stdio (For Claude Desktop / Cursor)

'freecad_rpc_server.py' must be running on the FreeCAD side.
"""

import logging
import json
from typing import Any

from mcp.server.fastmcp import FastMCP
from .freecad_bridge import FreeCADBridge
from .error_enricher import enrich_error

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)

mcp = FastMCP(
    name="freecad-mcp",
    instructions=(
        "You are a FreeCAD CAD assistant. "
        "You help the user create, manipulate, and save 3D geometry. "
        "Verify the result after each operation using 'get_object_tree'. "
        "If you encounter an error, use a self-correction loop to fix it. "
        "IMPORTANT RULE: When the user asks for a 'preview', 'screenshot', or 'image', "
        "ABSOLUTELY DO NOT write custom plotting code using external Python libraries "
        "like matplotlib, trimesh, or pyvista. "
        "Instead, ALWAYS use the 'set_camera_view' tool (e.g., isometric) first, "
        "and then call the 'get_view_screenshot' tool to provide the user with "
        "FreeCAD's own high-quality screenshot."
    ),
)

bridge = FreeCADBridge()


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _safe_call(fn, *args, **kwargs) -> dict[str, Any]:
    """Wraps bridge calls with error handling."""
    try:
        return fn(*args, **kwargs)
    except Exception as exc:
        friendly = enrich_error(str(exc))
        logger.error("Bridge error: %s", exc)
        return {"ok": False, "error": friendly}


# ──────────────────────────────────────────────────────────────────────────────
# TOOLS — Document Management
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool(description="Creates a new empty FreeCAD document.")
def create_document(name: str = "Unnamed") -> dict:
    """
    Parameters:
        name: Document name (default: 'Unnamed').
    Returns:
        ok, doc_name
    """
    return _safe_call(bridge.create_document, name)


@mcp.tool(description="Opens an existing FreeCAD (.FCStd) file or a supported format from disk.")
def open_document(file_path: str) -> dict:
    """
    Parameters:
        file_path: Full path to the file to open.
    """
    return _safe_call(bridge.open_document, file_path)


@mcp.tool(description="Saves the document to disk.")
def save_document(doc_name: str, file_path: str) -> dict:
    """
    Parameters:
        doc_name : Name of the document to save.
        file_path: Full file path (with .FCStd extension).
    """
    return _safe_call(bridge.save_document, doc_name, file_path)


@mcp.tool(description="Closes the document.")
def close_document(doc_name: str) -> dict:
    return _safe_call(bridge.close_document, doc_name)


@mcp.tool(description="Lists all open FreeCAD documents.")
def list_documents() -> dict:
    return _safe_call(bridge.list_documents)


# ──────────────────────────────────────────────────────────────────────────────
# TOOLS — Solid Geometry (Part Workbench)
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool(description="Creates a box (rectangular prism) with specified dimensions.")
def create_box(
    doc_name: str,
    object_name: str,
    length: float,
    width: float,
    height: float,
) -> dict:
    """
    Parameters:
        doc_name   : Document name.
        object_name: Name given to the object.
        length     : Length along the X axis (mm).
        width      : Width along the Y axis (mm).
        height     : Height along the Z axis (mm).
    """
    return _safe_call(bridge.create_box, doc_name, object_name, length, width, height)


@mcp.tool(description="Creates a cylinder.")
def create_cylinder(
    doc_name: str,
    object_name: str,
    radius: float,
    height: float,
) -> dict:
    """
    Parameters:
        doc_name   : Document name.
        object_name: Object name.
        radius     : Radius (mm).
        height     : Height (mm).
    """
    return _safe_call(bridge.create_cylinder, doc_name, object_name, radius, height)


@mcp.tool(description="Creates a sphere.")
def create_sphere(
    doc_name: str,
    object_name: str,
    radius: float,
) -> dict:
    return _safe_call(bridge.create_sphere, doc_name, object_name, radius)


@mcp.tool(description="Creates a cone.")
def create_cone(
    doc_name: str,
    object_name: str,
    radius1: float,
    radius2: float,
    height: float,
) -> dict:
    """
    Parameters:
        radius1: Bottom base radius (mm).
        radius2: Top base radius (mm; 0 -> sharp point).
        height : Height (mm).
    """
    return _safe_call(bridge.create_cone, doc_name, object_name, radius1, radius2, height)


# ──────────────────────────────────────────────────────────────────────────────
# TOOLS — Boolean Operations
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool(description="Joins two solids (Union / Fuse).")
def boolean_union(doc_name: str, result_name: str, base_object: str, tool_object: str) -> dict:
    return _safe_call(bridge.boolean_union, doc_name, result_name, base_object, tool_object)


@mcp.tool(description="Subtracts the tool object from the base object (Cut / Subtract).")
def boolean_cut(doc_name: str, result_name: str, base_object: str, tool_object: str) -> dict:
    return _safe_call(bridge.boolean_cut, doc_name, result_name, base_object, tool_object)


@mcp.tool(description="Gets the intersection of two solids (Common / Intersect).")
def boolean_common(doc_name: str, result_name: str, base_object: str, tool_object: str) -> dict:
    return _safe_call(bridge.boolean_common, doc_name, result_name, base_object, tool_object)


# ──────────────────────────────────────────────────────────────────────────────
# TOOLS — Part Design (Body / Sketch / Pad / Pocket / Fillet / Chamfer)
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool(description="Creates a Part Design Body. Sketches and features are attached here.")
def create_body(doc_name: str, body_name: str) -> dict:
    return _safe_call(bridge.create_body, doc_name, body_name)


@mcp.tool(description="Creates a new Sketch attached to a Body.")
def create_sketch(
    doc_name: str,
    body_name: str,
    sketch_name: str,
    plane: str = "XY",
) -> dict:
    """
    Parameters:
        plane: 'XY', 'XZ', or 'YZ'.
    """
    return _safe_call(bridge.create_sketch, doc_name, body_name, sketch_name, plane)


@mcp.tool(description="Adds a rectangle to a Sketch.")
def add_rectangle_to_sketch(
    doc_name: str,
    sketch_name: str,
    x: float,
    y: float,
    width: float,
    height: float,
) -> dict:
    """
    Parameters:
        x, y   : Bottom-left corner of the rectangle.
        width  : Width.
        height : Height.
    """
    return _safe_call(bridge.add_rectangle_to_sketch, doc_name, sketch_name, x, y, width, height)


@mcp.tool(description="Adds a circle to a Sketch.")
def add_circle_to_sketch(
    doc_name: str,
    sketch_name: str,
    center_x: float,
    center_y: float,
    radius: float,
) -> dict:
    return _safe_call(bridge.add_circle_to_sketch, doc_name, sketch_name, center_x, center_y, radius)


@mcp.tool(description="Extrudes the Sketch to a specified length (Pad).")
def pad(
    doc_name: str,
    body_name: str,
    sketch_name: str,
    length: float,
    feature_name: str = "",
) -> dict:
    return _safe_call(bridge.pad, doc_name, body_name, sketch_name, length, feature_name)


@mcp.tool(description="Creates a cavity shaped by the Sketch to a specified depth (Pocket).")
def pocket(
    doc_name: str,
    body_name: str,
    sketch_name: str,
    depth: float,
    feature_name: str = "",
) -> dict:
    return _safe_call(bridge.pocket, doc_name, body_name, sketch_name, depth, feature_name)


@mcp.tool(description="Applies a Fillet to specified edges.")
def fillet(
    doc_name: str,
    body_name: str,
    feature_name: str,
    edge_indices: list[int],
    radius: float,
) -> dict:
    """
    Parameters:
        edge_indices: Indices of the edges to fillet (0-based).
        radius      : Fillet radius (mm).
    """
    return _safe_call(bridge.fillet, doc_name, body_name, feature_name, edge_indices, radius)


@mcp.tool(description="Applies a Chamfer to specified edges.")
def chamfer(
    doc_name: str,
    body_name: str,
    feature_name: str,
    edge_indices: list[int],
    size: float,
) -> dict:
    return _safe_call(bridge.chamfer, doc_name, body_name, feature_name, edge_indices, size)


# ──────────────────────────────────────────────────────────────────────────────
# TOOLS — Object Manipulation
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool(description="Moves the object to the specified coordinate.")
def move_object(
    doc_name: str,
    object_name: str,
    x: float,
    y: float,
    z: float,
) -> dict:
    return _safe_call(bridge.move_object, doc_name, object_name, x, y, z)


@mcp.tool(description="Rotates the object around the specified axis.")
def rotate_object(
    doc_name: str,
    object_name: str,
    axis_x: float,
    axis_y: float,
    axis_z: float,
    angle_deg: float,
) -> dict:
    """
    Parameters:
        axis_x/y/z: Rotation axis (unit vector).
        angle_deg  : Rotation angle (degrees).
    """
    return _safe_call(bridge.rotate_object, doc_name, object_name, axis_x, axis_y, axis_z, angle_deg)


@mcp.tool(description="Changes a specific property of the object.")
def set_property(
    doc_name: str,
    object_name: str,
    property_name: str,
    value: Any,
) -> dict:
    return _safe_call(bridge.set_property, doc_name, object_name, property_name, value)


# ──────────────────────────────────────────────────────────────────────────────
# TOOLS — Free Code Execution
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool(
    description=(
        "Executes code directly in the FreeCAD Python environment. "
        "Use for complex scenarios where standard tools are insufficient. "
        "⚠️ Safety: Do not run harmful system commands."
    )
)
def execute_code(python_code: str) -> dict:
    """
    Parameters:
        python_code: Code to run in the FreeCAD Python environment.

    Returns:
        ok, stdout, stderr, result
    """
    return _safe_call(bridge.execute_code, python_code)


# ──────────────────────────────────────────────────────────────────────────────
# TOOLS — Visual Verification
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool(
    description=(
        "Returns a screenshot of the active FreeCAD view as a Base64 PNG. "
        "Use to fix spatial errors (wrong position, intersection problems, etc.)."
    )
)
def get_view_screenshot(doc_name: str) -> dict:
    """
    Returns:
        ok, image_base64 (PNG, base64 encoded)
    """
    try:
        b64 = bridge.get_view_screenshot(doc_name)
        return {"ok": True, "image_base64": b64, "format": "png"}
    except Exception as exc:
        return {"ok": False, "error": enrich_error(str(exc))}

@mcp.tool(description="Sets the camera angle (isometric, top, front, fit). Useful before taking a screenshot.")
def set_camera_view(doc_name: str, view_type: str = "isometric") -> dict:
    return _safe_call(bridge.set_camera_view, doc_name, view_type)

@mcp.tool(description="Exports the document or objects in STL, STEP format.")
def export_document(doc_name: str, file_path: str) -> dict:
    return _safe_call(bridge.export_document, doc_name, file_path)


# ──────────────────────────────────────────────────────────────────────────────
# PROFESSIONAL TOOLS
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool(description="Retrieves the full edge and face topology (Length, Area, and Center Coordinates) of an object for Fillet/Chamfer or analysis.")
def get_topology_info(doc_name: str, object_name: str) -> dict:
    return _safe_call(bridge.get_topology_info, doc_name, object_name)

@mcp.tool(description="Adds a geometric constraint to a Sketch ('Distance', 'Radius', 'Coincident', 'Parallel', 'Horizontal', etc.). pos1/pos2 parameters represent 1=Start, 2=End, 3=Center, 0=Edge.")
def add_sketch_constraint(
    doc_name: str, sketch_name: str, constraint_type: str, geo1: int, pos1: int, geo2: int = -1, pos2: int = -1, value: float = 0.0
) -> dict:
    return _safe_call(bridge.add_sketch_constraint, doc_name, sketch_name, constraint_type, geo1, pos1, geo2, pos2, value)

@mcp.tool(description="Undoes the last operation in the document (Undo). Use this instead of redrawing the document from scratch when you make a mistake.")
def undo(doc_name: str) -> dict:
    return _safe_call(bridge.undo, doc_name)

@mcp.tool(description="Redoes the undone operation in the document (Redo).")
def redo(doc_name: str) -> dict:
    return _safe_call(bridge.redo, doc_name)

@mcp.tool(description="Returns physical properties of the object such as volume, Center of Mass, and Matrix of Inertia.")
def get_physical_properties(doc_name: str, object_name: str) -> dict:
    return _safe_call(bridge.get_physical_properties, doc_name, object_name)

@mcp.tool(description="Creates a TechDraw (Blueprint) of the object and exports it as a PDF or SVG.")
def export_techdraw(doc_name: str, object_name: str, file_path: str) -> dict:
    return _safe_call(bridge.export_techdraw, doc_name, object_name, file_path)


# ──────────────────────────────────────────────────────────────────────────────
# TOOLS — Connection Test
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool(description="Tests the connection to the FreeCAD RPC server.")
def ping_freecad() -> dict:
    """Checks if the FreeCAD connection is alive."""
    alive = bridge.ping()
    if alive:
        return {"ok": True, "message": "FreeCAD RPC server is running."}
    return {
        "ok": False,
        "message": (
            "Could not connect to FreeCAD. "
            "Open FreeCAD and run the 'freecad_rpc_server.py' macro "
            "from the 'Macro > Macros' menu."
        ),
    }


# ──────────────────────────────────────────────────────────────────────────────
# RESOURCES
# ──────────────────────────────────────────────────────────────────────────────

@mcp.resource("freecad://documents/{doc_name}/tree")
def resource_object_tree(doc_name: str) -> str:
    """Returns the hierarchical tree of all objects in the document."""
    result = _safe_call(bridge.get_object_tree, doc_name)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.resource("freecad://documents/{doc_name}/objects/{object_name}")
def resource_object_info(doc_name: str, object_name: str) -> str:
    """Returns all properties and B-Rep summary of a specific object."""
    result = _safe_call(bridge.get_object_info, doc_name, object_name)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.resource("freecad://system/info")
def resource_system_info() -> str:
    """Returns FreeCAD version, installed modules, and unit system info."""
    result = _safe_call(bridge.get_system_info)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.resource("freecad://documents/list")
def resource_document_list() -> str:
    """Lists all open documents."""
    result = _safe_call(bridge.list_documents)
    return json.dumps(result, ensure_ascii=False, indent=2)


# ──────────────────────────────────────────────────────────────────────────────
# PROMPTS
# ──────────────────────────────────────────────────────────────────────────────

@mcp.prompt(description="Standard M-series metric bolt creation workflow.")
def prompt_create_bolt(m_size: int = 5, length_mm: float = 20.0) -> str:
    return f"""
Create an M{m_size}x{length_mm} metric bolt. Steps:

1. Open a new document named '{m_size}m_bolt'.
2. Create a 'Body'.
3. Add a sketch named 'HeadSketch' on the XY plane; draw a hexagon
   with a radius of {m_size * 0.9:.1f} mm centered at (0,0) (closed profile with 6 lines).
4. Pad HeadSketch by {m_size * 0.7:.1f} mm -> 'BoltHead'.
5. Add a new 'ShankSketch'; circle centered at (0,0) with a radius of {m_size / 2:.2f} mm.
6. Pad ShankSketch by {length_mm} mm -> 'BoltShank'.
7. Union BoltHead and BoltShank.
8. Apply a {m_size * 0.05:.2f} mm chamfer to the top 2 edges.
9. Save the result as '/tmp/{m_size}m_bolt.FCStd'.
10. Take a screenshot and verify.
"""


@mcp.prompt(description="Optimizes the existing part for FDM 3D printing.")
def prompt_optimize_for_3d_print(doc_name: str, object_name: str) -> str:
    return f"""
Optimize the '{object_name}' object in the '{doc_name}' document for FDM 3D printing:

1. First, inspect the object using 'get_object_info'.
2. Identify faces with more than 90° overhang.
3. Reorient the object (using rotate_object) to minimize required support structures.
4. Verify that wall thickness is at least 1.2 mm (2 perimeters).
5. Apply at least a 0.4 mm fillet (printer nozzle diameter) to sharp internal corners.
6. Take a screenshot for visual verification.
7. Save the optimized version as '/tmp/{doc_name}_3dprint.FCStd'.
"""


@mcp.prompt(description="General workflow to build geometry step-by-step starting with an empty document.")
def prompt_new_part_workflow(part_description: str) -> str:
    return f"""
Create the following part: {part_description}

General workflow:
1. Verify connection using ping_freecad.
2. Create a new document with a meaningful name.
3. Break the design into small steps: main body -> holes -> details.
4. Check the tree with get_object_tree after each step.
5. Use Part Workbench (create_box/cylinder) for complex geometry,
   and Part Design (Body/Sketch/Pad/Pocket) for details.
6. Perform visual verification when complete (get_view_screenshot).
7. Save the document.
"""


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")
