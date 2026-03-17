"""
FreeCAD Bridge — XML-RPC aracılığıyla FreeCAD süreciyle konuşur.

FreeCAD tarafında freecad_rpc_server.py çalışıyor olmalı.
Varsayılan adres: 127.0.0.1:9875
"""

import xmlrpc.client
import base64
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

FREECAD_RPC_URL = "http://127.0.0.1:36875"


class FreeCADBridge:
    """FreeCAD XML-RPC köprüsü."""

    def __init__(self, url: str = FREECAD_RPC_URL):
        self.url = url
        self._proxy: xmlrpc.client.ServerProxy | None = None

    def _get_proxy(self) -> xmlrpc.client.ServerProxy:
        if self._proxy is None:
            self._proxy = xmlrpc.client.ServerProxy(self.url, allow_none=True)
        return self._proxy

    def _call(self, method: str, *args) -> Any:
        proxy = self._get_proxy()
        try:
            fn = getattr(proxy, method)
            result = fn(*args)
            return result
        except xmlrpc.client.Fault as exc:
            raise RuntimeError(f"FreeCAD RPC hatası [{exc.faultCode}]: {exc.faultString}") from exc
        except ConnectionRefusedError:
            raise RuntimeError(
                "FreeCAD RPC sunucusuna bağlanılamadı. "
                "FreeCAD içinde 'freecad_rpc_server.py' çalıştırıldığından emin olun."
            )

    # ------------------------------------------------------------------ #
    # Belge işlemleri
    # ------------------------------------------------------------------ #

    def create_document(self, name: str = "Unnamed") -> dict:
        return json.loads(self._call("create_document", name))

    def open_document(self, filepath: str) -> dict:
        return json.loads(self._call("open_document", filepath))

    def save_document(self, name: str, path: str) -> dict:
        return json.loads(self._call("save_document", name, path))

    def close_document(self, name: str) -> dict:
        return json.loads(self._call("close_document", name))

    def list_documents(self) -> dict:
        return json.loads(self._call("list_documents"))

    # ------------------------------------------------------------------ #
    # Katı geometri
    # ------------------------------------------------------------------ #

    def create_box(self, doc: str, name: str, length: float, width: float, height: float) -> dict:
        return json.loads(self._call("create_box", doc, name, length, width, height))

    def create_cylinder(self, doc: str, name: str, radius: float, height: float) -> dict:
        return json.loads(self._call("create_cylinder", doc, name, radius, height))

    def create_sphere(self, doc: str, name: str, radius: float) -> dict:
        return json.loads(self._call("create_sphere", doc, name, radius))

    def create_cone(self, doc: str, name: str, radius1: float, radius2: float, height: float) -> dict:
        return json.loads(self._call("create_cone", doc, name, radius1, radius2, height))

    # ------------------------------------------------------------------ #
    # Boolean operasyonlar
    # ------------------------------------------------------------------ #

    def boolean_union(self, doc: str, name: str, base: str, tool: str) -> dict:
        return json.loads(self._call("boolean_union", doc, name, base, tool))

    def boolean_cut(self, doc: str, name: str, base: str, tool: str) -> dict:
        return json.loads(self._call("boolean_cut", doc, name, base, tool))

    def boolean_common(self, doc: str, name: str, base: str, tool: str) -> dict:
        return json.loads(self._call("boolean_common", doc, name, base, tool))

    # ------------------------------------------------------------------ #
    # Part Design (Body / Sketch / Pad / Pocket / Fillet / Chamfer)
    # ------------------------------------------------------------------ #

    def create_body(self, doc: str, name: str) -> dict:
        return json.loads(self._call("create_body", doc, name))

    def create_sketch(self, doc: str, body: str, name: str, plane: str = "XY") -> dict:
        return json.loads(self._call("create_sketch", doc, body, name, plane))

    def add_rectangle_to_sketch(
        self, doc: str, sketch: str, x: float, y: float, w: float, h: float
    ) -> dict:
        return json.loads(self._call("add_rectangle_to_sketch", doc, sketch, x, y, w, h))

    def add_circle_to_sketch(self, doc: str, sketch: str, cx: float, cy: float, r: float) -> dict:
        return json.loads(self._call("add_circle_to_sketch", doc, sketch, cx, cy, r))

    def pad(self, doc: str, body: str, sketch: str, length: float, name: str = "") -> dict:
        return json.loads(self._call("pad", doc, body, sketch, length, name))

    def pocket(self, doc: str, body: str, sketch: str, depth: float, name: str = "") -> dict:
        return json.loads(self._call("pocket", doc, body, sketch, depth, name))

    def fillet(self, doc: str, body: str, feature: str, edges: list[int], radius: float) -> dict:
        return json.loads(self._call("fillet", doc, body, feature, edges, radius))

    def chamfer(self, doc: str, body: str, feature: str, edges: list[int], size: float) -> dict:
        return json.loads(self._call("chamfer", doc, body, feature, edges, size))

    # ------------------------------------------------------------------ #
    # Nesne manipülasyonu
    # ------------------------------------------------------------------ #

    def move_object(self, doc: str, obj: str, x: float, y: float, z: float) -> dict:
        return json.loads(self._call("move_object", doc, obj, x, y, z))

    def rotate_object(self, doc: str, obj: str, ax: float, ay: float, az: float, angle: float) -> dict:
        return json.loads(self._call("rotate_object", doc, obj, ax, ay, az, angle))

    def set_property(self, doc: str, obj: str, prop: str, value: Any) -> dict:
        return json.loads(self._call("set_property", doc, obj, prop, json.dumps(value)))

    # ------------------------------------------------------------------ #
    # Bilgi / kaynak sorgulama
    # ------------------------------------------------------------------ #

    def get_object_tree(self, doc: str) -> dict:
        return json.loads(self._call("get_object_tree", doc))

    def get_object_info(self, doc: str, obj: str) -> dict:
        return json.loads(self._call("get_object_info", doc, obj))

    def get_system_info(self) -> dict:
        return json.loads(self._call("get_system_info"))

    def get_view_screenshot(self, doc: str) -> str:
        """Base64 PNG döner."""
        res = json.loads(self._call("get_view_screenshot", doc))
        if not res.get("ok"):
            raise RuntimeError(res.get("error", "Unknown screenshot error"))
        return res["image_base64"]

    # ------------------------------------------------------------------ #
    # Yeni Özellikler (Dışa Aktarma, Kamera)
    # ------------------------------------------------------------------ #

    def export_document(self, doc: str, filename: str) -> dict:
        return json.loads(self._call("export_document", doc, filename))

    def set_camera_view(self, doc: str, view_type: str) -> dict:
        return json.loads(self._call("set_camera_view", doc, view_type))

    # ------------------------------------------------------------------ #
    # Serbest kod yürütme
    # ------------------------------------------------------------------ #

    def execute_code(self, code: str) -> dict:
        return json.loads(self._call("execute_code", code))

    # ------------------------------------------------------------------ #
    # Yeni Profesyonel Araçlar (Topoloji, Kısıtlamalar, TechDraw vb.)
    # ------------------------------------------------------------------ #

    def get_topology_info(self, doc: str, obj: str) -> dict:
        return json.loads(self._call("get_topology_info", doc, obj))

    def add_sketch_constraint(self, doc: str, sketch: str, constraint_type: str, geo1: int, pos1: int, geo2: int=-1, pos2: int=-1, value: float=0.0) -> dict:
        return json.loads(self._call("add_sketch_constraint", doc, sketch, constraint_type, geo1, pos1, geo2, pos2, value))

    def undo(self, doc: str) -> dict:
        return json.loads(self._call("undo", doc))

    def redo(self, doc: str) -> dict:
        return json.loads(self._call("redo", doc))

    def get_physical_properties(self, doc: str, obj: str) -> dict:
        return json.loads(self._call("get_physical_properties", doc, obj))

    def export_techdraw(self, doc: str, obj: str, filepath: str) -> dict:
        return json.loads(self._call("export_techdraw", doc, obj, filepath))

    # ------------------------------------------------------------------ #
    # Yardımcılar
    # ------------------------------------------------------------------ #

    def ping(self) -> bool:
        try:
            result = self._call("ping")
            return result == "pong"
        except Exception:
            return False
