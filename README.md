<div align="center">

# 🚀 FreeCAD MCP (Model Context Protocol) Server

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![FreeCAD](https://img.shields.io/badge/FreeCAD-1.0+-red.svg)](https://www.freecadweb.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

**Perform Direct 3D CAD Engineering with your AI (Claude, Cursor, Cline)!**

</div>

FreeCAD MCP is a robust bridge that empowers your AI assistants (like Claude Desktop or Cursor AI) to **talk directly to the FreeCAD 3D CAD software.** 

Simply tell your AI in natural language: *"Draw a curved smartphone holder for the desk and give me the 3D print file"*, and the AI will use FreeCAD's powerful C++ engine in the background to parametrically design the part, generate its technical blueprints, and export it ready for 3D printing (STL/STEP)!

---

## 🌟 Features & Capabilities

This server is not a toy for drawing basic shapes; it is coded as a complete engineering assistant.

- **🛠 Basic & Complex Geometries:** Draw primitives (Box, Cylinder, Cone, etc.) or create 2D Sketches and perform Pad (Extrude) / Pocket (Cut) operations.
- **🏗 Boolean Operations:** Combine parts (Union), subtract them (Cut), or find their Intersection.
- **📐 Parametric Engineering (Constraints):** Instead of memorizing coordinates, apply Sketcher constraints such as Tangent, Parallel, Coincident, or Distance.
- **👁 Topological Precision:** The AI can query the exact Length, Area, and Center of Mass coordinates of any edge or face. This enables the AI to precisely target "the top face" or "the longest edge" when applying Fillets or Chamfers.
- **⚖️ Physical Analysis:** Calculate the Volume, Center of Mass, and Matrix of Inertia of any designed part instantly.
- **📸 High-Quality Previews (Rendering):** Instead of generating fake Python plots, the AI utilizes FreeCAD's professional 3D viewport to capture and deliver *real screenshots* of your model, complete with shadows and accurate perspectives.
- **📄 2D TechDraw (Blueprints):** Automatically generate A4-sized Technical Drawing templates (Blueprints) showing the Top, Front, Right, and Isometric views of your 3D models.
- **💾 Multi-Format Export:** Export your designs as `.FCStd` (FreeCAD Project), `.STL` (for 3D Printing), and `.STEP` (Universal CAD format).

---

## ⚙️ Installation (2 Simple Steps)

The system consists of two parts: a listening macro inside FreeCAD, and the MCP Server running on your machine.

### Step 1: Prepare FreeCAD (Macro Installation)
1. Clone this project to your machine (`git clone`).
2. Open FreeCAD. From the top menu, go to **Macro > Macros...**
3. In the window that appears, find the **Destination** path. This is the folder where FreeCAD reads its macros (e.g., `~/Library/Application Support/FreeCAD/Macro` on macOS).
4. Copy the **`freecad_rpc_server.py`** file from this project into that destination folder (you can rename it to `newmacro.FCMacro` if you prefer).
5. Select this file in the Macro window and click **Execute**.
*(You will see a message in the FreeCAD console saying "✅ Safe RPC sunucusu başladı → 127.0.0.1:36875". FreeCAD is now listening for commands from your AI!)*

### Step 2: Add the MCP Server to Your AI

#### Option A: For Cursor Editor
We have included a `cursor_mcp_launcher.sh` script to help Cursor seamlessly run the server and generate 3D models.
1. Open Cursor.
2. Go to **Settings > Features > MCP Servers**.
3. Click **+ Add New MCP Server** and enter the following:
   - **Name:** FreeCAD
   - **Type:** command
   - **Command:** `[FULL_PATH_TO_PROJECT]/cursor_mcp_launcher.sh` *(e.g., `/Users/John/freecad-mcp/cursor_mcp_launcher.sh`)*
4. Save and refresh. You can now prompt Cursor in the Chat (Cmd+L) to start 3D designing!

#### Option B: For Claude Desktop
Copy the contents of `claude_desktop_config.example.json` and paste them into your Claude configuration file (on macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "freecad": {
      "command": "python",
      "args": ["-m", "server.main"],
      "env": {
        "PYTHONPATH": "/[FULL_PATH_TO_PROJECT]"
      }
    }
  }
}
```

---

## 💡 How to Use (Prompt Examples)

Once the setup is complete and FreeCAD is running in the background (with the macro executed), you can prompt your AI (Claude / Cursor) with tasks like:

* *"Draw me a cylinder with a 10mm diameter and 20mm height, apply a 2mm fillet to the top edge, and save it as an STL."*
* *"Open the existing 'engine_block.FCStd' file. Calculate the center of mass for the 'MainBody' part and tell me the result."*
* *"Model a curved, modern smartphone stand. Don't just write the code; actually produce it in FreeCAD. Create an A4 TechDraw template containing the Top, Front, and Side views of the part. Then, send me a real screenshot from the Isometric camera."*

---

## 🏗 Architecture (How it Works)

The system uses a two-way, thread-safe architecture:
1. **FreeCAD RPC Server (`freecad_rpc_server.py`):** An XML-RPC bridge that safely exposes FreeCAD's Python API to the outside world, ensuring operations run on FreeCAD's Main Thread to prevent crashes.
2. **MCP Fast API Server (`server/main.py`):** The core logic layer that speaks the language of Claude or Cursor (stdio-based) and provides them with "Tools". It intercepts all natural language AI commands and forwards the exact geometric instructions to FreeCAD via the Bridge.

## 🤝 Contributing
Feel free to submit Pull Requests to add missing FreeCAD features (e.g., Assembly4 constraints, FEM analysis) into the `server/freecad_bridge.py` and `freecad_rpc_server.py` files.

**License:** MIT License
