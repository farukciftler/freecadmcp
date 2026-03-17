import xmlrpc.client
import json

proxy = xmlrpc.client.ServerProxy("http://127.0.0.1:36875")
try:
    res = json.loads(proxy.execute_code("""
import FreeCAD
try:
    import FreeCADGui
    has_gui = FreeCADGui.GuiUp
    msg = f"Import OK, GuiUp: {has_gui}"
except Exception as e:
    msg = f"Import Failed: {e}"
_result = msg
"""))
    print("Execute Result:", res['result'])
except Exception as e:
    print("Error:", e)
