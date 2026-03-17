"""
FreeCAD İçi XML-RPC Sunucusu (Thread-Safe Sürüm)
==============================================
Bu dosyayı FreeCAD içinde bir Makro olarak çalıştırın.

Sunucu, gelen istekleri ana iş parçacığına yönlendirir ve çökme koruması sağlar.
"""

import sys
import json
import traceback
import base64
import threading
import tempfile
import os
import queue
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler

# FreeCAD modülleri
import FreeCAD
import Part
import Draft

try:
    import PartDesign
    import Sketcher
    HAS_PART_DESIGN = True
except ImportError:
    HAS_PART_DESIGN = False

try:
    import FreeCADGui
    HAS_GUI = FreeCAD.GuiUp
except Exception:
    HAS_GUI = False

# PySide2 veya PySide6 import denemesi
QtCore = None
try:
    from PySide2 import QtCore
    FreeCAD.Console.PrintMessage("✅ PySide2 bulundu.\\n")
except Exception as e2:
    try:
        from PySide6 import QtCore
        FreeCAD.Console.PrintMessage("✅ PySide6 bulundu.\\n")
    except Exception as e6:
        try:
            from PySide import QtCore
            FreeCAD.Console.PrintMessage("✅ PySide bulundu.\\n")
        except Exception as e1:
            FreeCAD.Console.PrintError(f"❌ Tüm Qt bağlamaları (PySide2/6/1) başarısız oldu!\\n")
            FreeCAD.Console.PrintError(f"   (PySide2 hatası: {str(e2)})\\n")
            FreeCAD.Console.PrintMessage(f"   sys.path: {sys.path[:3]}\\n")
            QtCore = None

HOST = "127.0.0.1"
PORT = 36875 # Claude konfigürasyonundaki port

# ──────────────────────────────────────────────────────────────────────────────
# Thread-Safe İstek İşleyici
# ──────────────────────────────────────────────────────────────────────────────

class RPCRequest:
    def __init__(self, method_name, args, kwargs):
        self.method_name = method_name
        self.args = args
        self.kwargs = kwargs
        self.result = None
        self.error = None
        self.completed = threading.Event()

# Global nesneleri koru (Garbage Collection'ı önle)
global _request_queue, _timer, _server, _service_instance
_request_queue = queue.Queue()

def _process_queue():
    """Ana iş parçacığında (Main Thread) çalışan poller."""
    try:
        while not _request_queue.empty():
            req = _request_queue.get_nowait()
            FreeCAD.Console.PrintMessage(f"RPC İşleniyor: {req.method_name}\\n")
            try:
                method = getattr(_service_instance, req.method_name)
                req.result = method(*req.args, **req.kwargs)
                FreeCAD.Console.PrintMessage(f"RPC Tamamlandı: {req.method_name}\\n")
            except Exception as e:
                req.error = str(e)
                FreeCAD.Console.PrintError(f"RPC Hata [{req.method_name}]: {traceback.format_exc()}\\n")
            finally:
                req.completed.set()
    except queue.Empty:
        pass
    except Exception as e:
        FreeCAD.Console.PrintError(f"Timer Hata: {str(e)}\\n")

# Tanı: GUI durumu
FreeCAD.Console.PrintMessage(f"Tanı: HAS_GUI={HAS_GUI}, QtCore={'Mevcut' if QtCore else 'Yok'}\\n")

# QTimer ile kuyruğu dinle
if QtCore:
    try:
        from PySide2 import QtWidgets
        app = QtWidgets.QApplication.instance()
    except:
        app = None

    if '_timer' in globals() and _timer:
        _timer.stop()
        
    _timer = QtCore.QTimer()
    _timer.timeout.connect(_process_queue)
    _timer.setTimerType(QtCore.Qt.PreciseTimer)
    _timer.start(50) 
    FreeCAD.Console.PrintMessage("✅ QTimer poller (Thread-Safe) başlatıldı.\\n")
else:
    FreeCAD.Console.PrintError("❌ QtCore bulunamadı, poller başlatılamıyor!\\n")

# ──────────────────────────────────────────────────────────────────────────────
# Yardımcı fonksiyonlar
# ──────────────────────────────────────────────────────────────────────────────

def _ok(**kwargs) -> str:
    return json.dumps({"ok": True, **kwargs})

def _err(msg: str) -> str:
    return json.dumps({"ok": False, "error": msg})

def _get_doc(name: str) -> FreeCAD.Document:
    doc = FreeCAD.getDocument(name)
    if doc is None:
        raise ValueError(f"No document named '{name}'")
    return doc

def _shape_info(shape) -> dict:
    try:
        bb = shape.BoundBox
        return {
            "type": shape.ShapeType,
            "faces": len(shape.Faces),
            "edges": len(shape.Edges),
            "vertices": len(shape.Vertexes),
            "volume": round(shape.Volume, 6),
            "area": round(shape.Area, 6),
            "bounding_box": {
                "x_min": round(bb.XMin, 4), "x_max": round(bb.XMax, 4),
                "y_min": round(bb.YMin, 4), "y_max": round(bb.YMax, 4),
                "z_min": round(bb.ZMin, 4), "z_max": round(bb.ZMax, 4),
                "x_length": round(bb.XLength, 4),
                "y_length": round(bb.YLength, 4),
                "z_length": round(bb.ZLength, 4),
            }
        }
    except Exception:
        return {}

# ──────────────────────────────────────────────────────────────────────────────
# RPC Metotları (Gerçek Mantık)
# ──────────────────────────────────────────────────────────────────────────────

class FreeCADServiceImpl:
    def ping(self) -> str:
        return "pong"

    def create_document(self, name: str) -> str:
        try:
            doc = FreeCAD.newDocument(name)
            return _ok(doc_name=doc.Name)
        except Exception as e: return _err(str(e))

    def open_document(self, filepath: str) -> str:
        try:
            doc = FreeCAD.openDocument(filepath)
            return _ok(doc_name=doc.Name)
        except Exception as e: return _err(str(e))

    def save_document(self, name: str, path: str) -> str:
        try:
            doc = _get_doc(name)
            doc.saveAs(path)
            return _ok(path=path)
        except Exception as e: return _err(str(e))

    def close_document(self, name: str) -> str:
        try:
            doc = _get_doc(name)
            FreeCAD.closeDocument(doc.Name)
            return _ok(closed=name)
        except Exception as e: return _err(str(e))

    def list_documents(self) -> str:
        try:
            docs = [d.Name for d in FreeCAD.listDocuments().values()]
            return _ok(documents=docs)
        except Exception as e: return _err(str(e))

    def create_box(self, doc: str, name: str, length: float, width: float, height: float) -> str:
        try:
            d = _get_doc(doc)
            obj = d.addObject("Part::Box", name)
            obj.Length = length
            obj.Width = width
            obj.Height = height
            d.recompute()
            return _ok(object=name, shape=_shape_info(obj.Shape))
        except Exception as e: return _err(str(e))

    def create_cylinder(self, doc: str, name: str, radius: float, height: float) -> str:
        try:
            d = _get_doc(doc)
            obj = d.addObject("Part::Cylinder", name)
            obj.Radius = radius
            obj.Height = height
            d.recompute()
            return _ok(object=name, shape=_shape_info(obj.Shape))
        except Exception as e: return _err(str(e))

    def create_sphere(self, doc: str, name: str, radius: float) -> str:
        try:
            d = _get_doc(doc)
            obj = d.addObject("Part::Sphere", name)
            obj.Radius = radius
            d.recompute()
            return _ok(object=name, shape=_shape_info(obj.Shape))
        except Exception as e: return _err(str(e))

    def create_cone(self, doc: str, name: str, radius1: float, radius2: float, height: float) -> str:
        try:
            d = _get_doc(doc)
            obj = d.addObject("Part::Cone", name)
            obj.Radius1 = radius1
            obj.Radius2 = radius2
            obj.Height = height
            d.recompute()
            return _ok(object=name, shape=_shape_info(obj.Shape))
        except Exception as e: return _err(str(e))

    def boolean_union(self, doc: str, name: str, base: str, tool: str) -> str:
        try:
            d = _get_doc(doc)
            b_obj = d.getObject(base)
            t_obj = d.getObject(tool)
            obj = d.addObject("Part::MultiFuse", name)
            obj.Shapes = [b_obj, t_obj]
            d.recompute()
            return _ok(object=name)
        except Exception as e: return _err(str(e))

    def boolean_cut(self, doc: str, name: str, base: str, tool: str) -> str:
        try:
            d = _get_doc(doc)
            b_obj = d.getObject(base)
            t_obj = d.getObject(tool)
            obj = d.addObject("Part::Cut", name)
            obj.Base = b_obj
            obj.Tool = t_obj
            d.recompute()
            return _ok(object=name)
        except Exception as e: return _err(str(e))

    def boolean_common(self, doc: str, name: str, base: str, tool: str) -> str:
        try:
            d = _get_doc(doc)
            b_obj = d.getObject(base)
            t_obj = d.getObject(tool)
            obj = d.addObject("Part::MultiCommon", name)
            obj.Shapes = [b_obj, t_obj]
            d.recompute()
            return _ok(object=name)
        except Exception as e: return _err(str(e))

    def create_body(self, doc: str, name: str) -> str:
        try:
            if not HAS_PART_DESIGN: return _err("PartDesign module not loaded.")
            d = _get_doc(doc)
            obj = d.addObject('PartDesign::Body', name)
            d.recompute()
            return _ok(object=name)
        except Exception as e: return _err(str(e))

    def create_sketch(self, doc: str, body: str, name: str, plane: str) -> str:
        try:
            d = _get_doc(doc)
            b_obj = d.getObject(body)
            obj = d.addObject('Sketcher::SketchObject', name)
            
            if plane == "XY":
                obj.Placement = FreeCAD.Placement(FreeCAD.Vector(0,0,0), FreeCAD.Rotation(0,0,0,1))
            elif plane == "XZ":
                obj.Placement = FreeCAD.Placement(FreeCAD.Vector(0,0,0), FreeCAD.Rotation(FreeCAD.Vector(1,0,0),90))
            elif plane == "YZ":
                obj.Placement = FreeCAD.Placement(FreeCAD.Vector(0,0,0), FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90))
            
            b_obj.addObject(obj)
            d.recompute()
            return _ok(object=name)
        except Exception as e: return _err(str(e))

    def add_rectangle_to_sketch(self, doc: str, sketch: str, x: float, y: float, w: float, h: float) -> str:
        try:
            d = _get_doc(doc)
            s_obj = d.getObject(sketch)
            p1 = FreeCAD.Vector(x, y, 0)
            p2 = FreeCAD.Vector(x+w, y, 0)
            p3 = FreeCAD.Vector(x+w, y+h, 0)
            p4 = FreeCAD.Vector(x, y+h, 0)
            s_obj.addGeometry(Part.LineSegment(p1, p2), False)
            s_obj.addGeometry(Part.LineSegment(p2, p3), False)
            s_obj.addGeometry(Part.LineSegment(p3, p4), False)
            s_obj.addGeometry(Part.LineSegment(p4, p1), False)
            d.recompute()
            return _ok(object=sketch)
        except Exception as e: return _err(str(e))

    def add_circle_to_sketch(self, doc: str, sketch: str, cx: float, cy: float, r: float) -> str:
        try:
            d = _get_doc(doc)
            s_obj = d.getObject(sketch)
            circle = Part.Circle(FreeCAD.Vector(cx, cy, 0), FreeCAD.Vector(0,0,1), r)
            s_obj.addGeometry(circle, False)
            d.recompute()
            return _ok(object=sketch)
        except Exception as e: return _err(str(e))

    def pad(self, doc: str, body: str, sketch: str, length: float, name: str) -> str:
        try:
            d = _get_doc(doc)
            b_obj = d.getObject(body)
            s_obj = d.getObject(sketch)
            pad_name = name if name else "Pad"
            obj = d.addObject('PartDesign::Pad', pad_name)
            obj.Profile = s_obj
            obj.Length = length
            b_obj.addObject(obj)
            d.recompute()
            return _ok(object=obj.Name)
        except Exception as e: return _err(str(e))

    def pocket(self, doc: str, body: str, sketch: str, depth: float, name: str) -> str:
        try:
            d = _get_doc(doc)
            b_obj = d.getObject(body)
            s_obj = d.getObject(sketch)
            pocket_name = name if name else "Pocket"
            obj = d.addObject('PartDesign::Pocket', pocket_name)
            obj.Profile = s_obj
            obj.Length = depth
            b_obj.addObject(obj)
            d.recompute()
            return _ok(object=obj.Name)
        except Exception as e: return _err(str(e))

    def fillet(self, doc: str, body: str, feature: str, edges: list, radius: float) -> str:
        try:
            d = _get_doc(doc)
            b_obj = d.getObject(body)
            f_obj = d.getObject(feature)
            obj = d.addObject("PartDesign::Fillet", "Fillet")
            obj.Base = (f_obj, [f"Edge{i+1}" for i in edges])
            obj.Radius = radius
            b_obj.addObject(obj)
            d.recompute()
            return _ok(object=obj.Name)
        except Exception as e: return _err(str(e))

    def chamfer(self, doc: str, body: str, feature: str, edges: list, size: float) -> str:
        try:
            d = _get_doc(doc)
            b_obj = d.getObject(body)
            f_obj = d.getObject(feature)
            obj = d.addObject("PartDesign::Chamfer", "Chamfer")
            obj.Base = (f_obj, [f"Edge{i+1}" for i in edges])
            obj.Size = size
            b_obj.addObject(obj)
            d.recompute()
            return _ok(object=obj.Name)
        except Exception as e: return _err(str(e))

    def move_object(self, doc: str, obj: str, x: float, y: float, z: float) -> str:
        try:
            d = _get_doc(doc)
            o = d.getObject(obj)
            o.Placement.Base = FreeCAD.Vector(x, y, z)
            d.recompute()
            return _ok(object=obj)
        except Exception as e: return _err(str(e))

    def rotate_object(self, doc: str, obj: str, ax: float, ay: float, az: float, angle: float) -> str:
        try:
            d = _get_doc(doc)
            o = d.getObject(obj)
            rot = FreeCAD.Rotation(FreeCAD.Vector(ax, ay, az), angle)
            o.Placement.Rotation = rot.multiply(o.Placement.Rotation)
            d.recompute()
            return _ok(object=obj)
        except Exception as e: return _err(str(e))

    def set_property(self, doc: str, obj: str, prop: str, value: str) -> str:
        try:
            d = _get_doc(doc)
            o = d.getObject(obj)
            val = json.loads(value)
            setattr(o, prop, val)
            d.recompute()
            return _ok(object=obj, property=prop)
        except Exception as e: return _err(str(e))

    def get_system_info(self) -> str:
        try:
            v_list = FreeCAD.Version()
            info = {
                "freecad_version": ".".join(v_list[:3]) if isinstance(v_list, (list, tuple)) else str(v_list),
                "python_version": sys.version,
                "has_gui": HAS_GUI,
                "has_part_design": HAS_PART_DESIGN,
            }
            return _ok(**info)
        except Exception as e: return _err(str(e))

    def get_object_tree(self, doc: str) -> str:
        try:
            d = _get_doc(doc)
            tree = []
            for obj in d.Objects:
                entry = {
                    "name": obj.Name,
                    "label": obj.Label,
                    "type": obj.TypeId,
                }
                if hasattr(obj, "Shape") and obj.Shape:
                    entry["shape"] = _shape_info(obj.Shape)
                tree.append(entry)
            return _ok(doc=doc, objects=tree, count=len(tree))
        except Exception as e: return _err(str(e))

    def get_object_info(self, doc: str, obj: str) -> str:
        try:
            d = _get_doc(doc)
            o = d.getObject(obj)
            if not o: return _err("Object not found")
            info = {"name": o.Name, "type": o.TypeId}
            if hasattr(o, "Shape") and o.Shape:
                info["shape"] = _shape_info(o.Shape)
            return _ok(info=info)
        except Exception as e: return _err(str(e))

    def get_view_screenshot(self, doc: str) -> str:
        try:
            if not HAS_GUI: return _err("FreeCAD GUI is not running.")
            import FreeCADGui
            gui_doc = FreeCADGui.getDocument(doc)
            if not gui_doc: return _err("GUI Document not found")
            view = gui_doc.ActiveView
            if not view: return _err("Active view not found")
            
            tmp_path = os.path.join(tempfile.gettempdir(), f"mcp_screenshot_{doc}.png")
            view.saveImage(tmp_path, 800, 600, "Transparent")
            with open(tmp_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')
            os.remove(tmp_path)
            return _ok(image_base64=b64)
        except Exception as e: return _err(str(e))

    def export_document(self, doc: str, filename: str) -> str:
        try:
            d = _get_doc(doc)
            objs = d.Objects
            if not objs: return _err("Document is empty")
            
            ext = filename.lower().split('.')[-1]
            if ext == 'stl':
                import Mesh
                Mesh.export(objs, filename)
            elif ext in ['step', 'stp']:
                import Import
                Import.export(objs, filename)
            else:
                return _err(f"Unsupported export format: {ext}")
            return _ok(path=filename)
        except Exception as e: return _err(str(e))

    def set_camera_view(self, doc: str, view_type: str) -> str:
        try:
            if not HAS_GUI: return _err("FreeCAD GUI is not running.")
            import FreeCADGui
            gui_doc = FreeCADGui.getDocument(doc)
            if not gui_doc: return _err("GUI Document not found")
            view = gui_doc.ActiveView
            if not view: return _err("Active view not found")
            
            vt = view_type.lower()
            if vt == "isometric": view.viewAxometric()
            elif vt == "front": view.viewFront()
            elif vt == "top": view.viewTop()
            elif vt == "fit": view.fitAll()
            else: return _err(f"Unknown view type: {vt}")
                
            view.fitAll()
            return _ok(view=vt)
        except Exception as e: return _err(str(e))

    def execute_code(self, code: str) -> str:
        import io
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        result_val = None
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = stdout_buf, stderr_buf
        try:
            exec_globals = {
                "FreeCAD": FreeCAD,
                "Part": Part,
                "__builtins__": __builtins__,
            }
            exec(code, exec_globals)
            result_val = exec_globals.get("_result", None)
        except Exception:
            stderr_buf.write(traceback.format_exc())
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr

        return json.dumps({
            "ok": True,
            "stdout": stdout_buf.getvalue(),
            "stderr": stderr_buf.getvalue(),
            "result": str(result_val) if result_val is not None else None,
        })

    # --- YENİ EKLENEN PROFESYONEL ÖZELLİKLER ---

    def get_topology_info(self, doc: str, obj: str) -> str:
        try:
            d = _get_doc(doc)
            o = d.getObject(obj)
            if not o or not hasattr(o, "Shape") or not o.Shape: return _err("Object has no shape")
            
            edges = []
            for i, e in enumerate(o.Shape.Edges):
                edges.append({
                    "index": i, "length": round(e.Length, 4),
                    "center_mass": [round(c, 4) for c in [e.CenterOfMass.x, e.CenterOfMass.y, e.CenterOfMass.z]]
                })
            
            faces = []
            for i, f in enumerate(o.Shape.Faces):
                faces.append({
                    "index": i, "area": round(f.Area, 4),
                    "center_mass": [round(c, 4) for c in [f.CenterOfMass.x, f.CenterOfMass.y, f.CenterOfMass.z]]
                })
                
            return _ok(edges=edges, faces=faces)
        except Exception as e: return _err(str(e))

    def add_sketch_constraint(self, doc: str, sketch: str, constraint_type: str, geo1: int, pos1: int, geo2: int=-1, pos2: int=-1, value: float=0.0) -> str:
        try:
            d = _get_doc(doc)
            s = d.getObject(sketch)
            if not s: return _err("Sketch not found")
            
            import Sketcher
            # Constraint Tipleri örn: 'Distance', 'Radius', 'Coincident', 'Parallel', 'Horizontal'
            # Pos Değerleri: 1 (Start), 2 (End), 3 (Center), 0 (Edge)
            if geo2 != -1 and value != 0.0:
                c = Sketcher.Constraint(constraint_type, geo1, pos1, geo2, pos2, value)
            elif geo2 != -1:
                c = Sketcher.Constraint(constraint_type, geo1, pos1, geo2, pos2)
            elif value != 0.0:
                c = Sketcher.Constraint(constraint_type, geo1, pos1, value)
            else:
                c = Sketcher.Constraint(constraint_type, geo1, pos1)
                    
            s.addConstraint(c)
            d.recompute()
            return _ok(constraint_type=constraint_type)
        except Exception as e: return _err(str(e))

    def undo(self, doc: str) -> str:
        try:
            d = _get_doc(doc)
            d.undo()
            return _ok(action="undo")
        except Exception as e: return _err(str(e))
        
    def redo(self, doc: str) -> str:
        try:
            d = _get_doc(doc)
            d.redo()
            return _ok(action="redo")
        except Exception as e: return _err(str(e))

    def get_physical_properties(self, doc: str, obj: str) -> str:
        try:
            d = _get_doc(doc)
            o = d.getObject(obj)
            shape = o.Shape
            return _ok(
                volume=round(shape.Volume, 4),
                center_of_mass=[round(c, 4) for c in [shape.CenterOfMass.x, shape.CenterOfMass.y, shape.CenterOfMass.z]],
                matrix_of_inertia=[round(v, 4) for v in shape.MatrixOfInertia.A]
            )
        except Exception as e: return _err(str(e))

    def export_techdraw(self, doc: str, obj: str, filepath: str) -> str:
        try:
            d = _get_doc(doc)
            o = d.getObject(obj)
            import TechDraw
            
            page = d.addObject('TechDraw::DrawPage', 'Page')
            template = d.addObject('TechDraw::DrawSVGTemplate', 'Template')
            template.Template = FreeCAD.getResourceDir() + "Mod/TechDraw/Templates/A4_LandscapeTD.svg"
            page.Template = template
            
            view = d.addObject('TechDraw::DrawViewPart', 'View')
            view.Source = o
            view.Direction = FreeCAD.Vector(0, 0, 1) # Varsayılan Üst (Top) Görünüş
            page.addView(view)
            
            d.recompute()
            
            # Eğer GUI çalışmıyorsa PDF dışa aktarma sorun yaratabilir, SVG'ye zorluyoruz.
            if HAS_GUI:
                import TechDrawGui
                TechDrawGui.exportPageAsPdf(page, filepath)
            else:
                if not filepath.lower().endswith(".svg"):
                    filepath += ".svg"
                page.exportPage(filepath)
                
            return _ok(path=filepath)
        except Exception as e: return _err(str(e))

_service_instance = FreeCADServiceImpl()

class ThreadSafeFreeCADProxy:
    def _dispatch(self, method, params):
        req = RPCRequest(method, params, {})
        _request_queue.put(req)
        finished = req.completed.wait(timeout=10.0)
        if not finished: return _err("Request timed out (Main thread busy?)")
        if req.error: return _err(req.error)
        return req.result

# ──────────────────────────────────────────────────────────────────────────────
# Sunucuyu başlat
# ──────────────────────────────────────────────────────────────────────────────

class _QuietHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ("/", "/RPC2")
    def log_message(self, fmt, *args): pass

_server: SimpleXMLRPCServer | None = None

def start_server():
    global _server
    if _server is not None:
        FreeCAD.Console.PrintMessage("RPC sunucusu zaten çalışıyor.\\n")
        return

    _server = SimpleXMLRPCServer(
        (HOST, PORT),
        requestHandler=_QuietHandler,
        allow_none=True,
        logRequests=False,
    )
    _server.register_instance(ThreadSafeFreeCADProxy())
    _server.register_introspection_functions()

    thread = threading.Thread(target=_server.serve_forever, daemon=True)
    thread.start()
    FreeCAD.Console.PrintMessage(f"✅ Safe RPC sunucusu başladı → {HOST}:{PORT}\\n")

def stop_server():
    global _server, _timer
    if _server:
        _server.shutdown()
        _server = None
    if _timer:
        _timer.stop()
        _timer = None
    FreeCAD.Console.PrintMessage("🛑 Safe RPC sunucusu durduruldu.\\n")

if __name__ == "__main__":
    start_server()
