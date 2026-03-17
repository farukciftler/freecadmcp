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
    HAS_GUI = FreeCADGui.GuiUp
except Exception:
    HAS_GUI = False

# PySide2 veya PySide6 import denemesi
QtCore = None
try:
    from PySide2 import QtCore
    FreeCAD.Console.PrintMessage("✅ PySide2 bulundu.\n")
except Exception as e2:
    try:
        from PySide6 import QtCore
        FreeCAD.Console.PrintMessage("✅ PySide6 bulundu.\n")
    except Exception as e6:
        try:
            from PySide import QtCore
            FreeCAD.Console.PrintMessage("✅ PySide bulundu.\n")
        except Exception as e1:
            FreeCAD.Console.PrintError(f"❌ Tüm Qt bağlamaları (PySide2/6/1) başarısız oldu!\n")
            FreeCAD.Console.PrintError(f"   (PySide2 hatası: {str(e2)})\n")
            FreeCAD.Console.PrintMessage(f"   sys.path: {sys.path[:3]}...\n")
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
        # Debug: Her çağrıldığında konsola nokta bas (Çok sık olursa kaldırırız)
        # FreeCAD.Console.PrintMessage(".") 
        
        while not _request_queue.empty():
            req = _request_queue.get_nowait()
            FreeCAD.Console.PrintMessage(f"RPC İşleniyor: {req.method_name}\n")
            try:
                method = getattr(_service_instance, req.method_name)
                req.result = method(*req.args, **req.kwargs)
                FreeCAD.Console.PrintMessage(f"RPC Tamamlandı: {req.method_name}\n")
            except Exception as e:
                req.error = str(e)
                FreeCAD.Console.PrintError(f"RPC Hata [{req.method_name}]: {traceback.format_exc()}\n")
            finally:
                req.completed.set()
    except queue.Empty:
        pass
    except Exception as e:
        FreeCAD.Console.PrintError(f"Timer Hata: {str(e)}\n")

# Tanı: GUI durumu
FreeCAD.Console.PrintMessage(f"Tanı: HAS_GUI={HAS_GUI}, QtCore={'Mevcut' if QtCore else 'Yok'}\n")

# QTimer ile kuyruğu dinle
if QtCore:
    # QTimer için bir uygulama örneği (Application instance) gerekir.
    # FreeCAD GUI modunda bu zaten vardır.
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
    FreeCAD.Console.PrintMessage("✅ QTimer poller (Thread-Safe) başlatıldı.\n")
else:
    FreeCAD.Console.PrintError("❌ QtCore bulunamadı, poller başlatılamıyor!\n")

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
    """Bu sınıf metotları DOĞRUDAN çağrılmaz, kuyruk üzerinden dispatcher ile çalışır."""

    def ping(self) -> str:
        return "pong"

    def create_document(self, name: str) -> str:
        try:
            doc = FreeCAD.newDocument(name)
            return _ok(doc_name=doc.Name)
        except Exception as e:
            return _err(str(e))

    def save_document(self, name: str, path: str) -> str:
        try:
            doc = _get_doc(name)
            doc.saveAs(path)
            return _ok(path=path)
        except Exception as e:
            return _err(str(e))

    def close_document(self, name: str) -> str:
        try:
            doc = _get_doc(name)
            FreeCAD.closeDocument(doc.Name)
            return _ok(closed=name)
        except Exception as e:
            return _err(str(e))

    def list_documents(self) -> str:
        try:
            docs = [d.Name for d in FreeCAD.listDocuments().values()]
            return _ok(documents=docs)
        except Exception as e:
            return _err(str(e))

    def create_box(self, doc: str, name: str, length: float, width: float, height: float) -> str:
        try:
            d = _get_doc(doc)
            obj = d.addObject("Part::Box", name)
            obj.Length = length
            obj.Width = width
            obj.Height = height
            d.recompute()
            return _ok(object=name, shape=_shape_info(obj.Shape))
        except Exception as e:
            return _err(str(e))

    def create_cylinder(self, doc: str, name: str, radius: float, height: float) -> str:
        try:
            d = _get_doc(doc)
            obj = d.addObject("Part::Cylinder", name)
            obj.Radius = radius
            obj.Height = height
            d.recompute()
            return _ok(object=name, shape=_shape_info(obj.Shape))
        except Exception as e:
            return _err(str(e))

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
        except Exception as e:
            return _err(str(e))

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
        except Exception as e:
            return _err(str(e))
            
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

# Global örnek
_service_instance = FreeCADServiceImpl()

class ThreadSafeFreeCADProxy:
    """XML-RPC sunucusunun doğrudan çağırdığı sınıf. İstekleri kuyruğa yönlendirir."""
    
    def _dispatch(self, method, params):
        """Tüm XML-RPC çağrılarını yakalar ve ana iş parçacığına paslar."""
        req = RPCRequest(method, params, {})
        _request_queue.put(req)
        
        # Ana iş parçacığının bitirmesini bekle (Zaman aşımı eklenebilir)
        finished = req.completed.wait(timeout=10.0)
        
        if not finished:
            return _err("Request timed out (Main thread busy?)")
        if req.error:
            return _err(req.error)
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
        FreeCAD.Console.PrintMessage("RPC sunucusu zaten çalışıyor.\n")
        return

    _server = SimpleXMLRPCServer(
        (HOST, PORT),
        requestHandler=_QuietHandler,
        allow_none=True,
        logRequests=False,
    )
    
    # Tüm metodları Dispatcher üzerinden geçir
    _server.register_instance(ThreadSafeFreeCADProxy())
    _server.register_introspection_functions()

    thread = threading.Thread(target=_server.serve_forever, daemon=True)
    thread.start()
    FreeCAD.Console.PrintMessage(f"✅ Safe RPC sunucusu başladı → {HOST}:{PORT}\n")

def stop_server():
    global _server, _timer
    if _server:
        _server.shutdown()
        _server = None
    if _timer:
        _timer.stop()
        _timer = None
    FreeCAD.Console.PrintMessage("🛑 Safe RPC sunucusu durduruldu.\n")

if __name__ == "__main__":
    start_server()
