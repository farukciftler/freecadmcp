"""
FreeCAD MCP Sunucusu — ana giriş noktası.

Kullanım:
    python -m server.main          # stdio (Claude Desktop / Cursor için)

FreeCAD tarafında freecad_rpc_server.py çalışıyor olmalı.
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
        "Sen bir FreeCAD CAD asistanısın. "
        "Kullanıcının 3D geometri oluşturmasına, manipüle etmesine ve kaydetmesine yardımcı olursun. "
        "Her işlemden sonra 'get_object_tree' ile sonucu doğrula. "
        "Hata alırsan 'self-correction' döngüsüyle düzelt. "
        "ÖNEMLİ KURAL: Kullanıcı 'önizleme', 'ekran görüntüsü' veya 'görsel' istediğinde KESİNLİKLE "
        "matplotlib, trimesh, pyvista gibi harici Python kütüphanelerini kullanarak özel çizim (plot) kodu YAZMA. "
        "Bunun yerine DAİMA önce 'set_camera_view' (örn: isometric) aracını kullan, ardından 'get_view_screenshot' "
        "aracını çağırarak FreeCAD'in kendi yüksek kaliteli ekran görüntüsünü kullanıcıya sun."
        "modellerde ve önizlemede mm kullan. türkçe karakter kullanmaktan çekinme."
    ),
)

bridge = FreeCADBridge()


# ──────────────────────────────────────────────────────────────────────────────
# Yardımcı
# ──────────────────────────────────────────────────────────────────────────────

def _safe_call(fn, *args, **kwargs) -> dict[str, Any]:
    """Bridge çağrısını hata yönetimiyle sarar."""
    try:
        return fn(*args, **kwargs)
    except Exception as exc:
        friendly = enrich_error(str(exc))
        logger.error("Bridge hatası: %s", exc)
        return {"ok": False, "error": friendly}


# ──────────────────────────────────────────────────────────────────────────────
# ARAÇLAR — Belge Yönetimi
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool(description="Yeni bir boş FreeCAD belgesi oluşturur.")
def create_document(name: str = "Unnamed") -> dict:
    """
    Parametre:
        name: Belge adı (varsayılan: 'Unnamed').
    Döner:
        ok, doc_name
    """
    return _safe_call(bridge.create_document, name)


@mcp.tool(description="Diskteki mevcut bir FreeCAD (.FCStd) dosyasını veya desteklenen formattaki bir objeyi açar.")
def open_document(file_path: str) -> dict:
    """
    Parametreler:
        file_path: Açılacak dosyanın tam yolu.
    """
    return _safe_call(bridge.open_document, file_path)


@mcp.tool(description="Belgeyi diske kaydeder.")
def save_document(doc_name: str, file_path: str) -> dict:
    """
    Parametreler:
        doc_name : Kayıt edilecek belge adı.
        file_path: Tam dosya yolu (.FCStd uzantısıyla).
    """
    return _safe_call(bridge.save_document, doc_name, file_path)


@mcp.tool(description="Belgeyi kapatır.")
def close_document(doc_name: str) -> dict:
    return _safe_call(bridge.close_document, doc_name)


@mcp.tool(description="Açık tüm FreeCAD belgelerini listeler.")
def list_documents() -> dict:
    return _safe_call(bridge.list_documents)


# ──────────────────────────────────────────────────────────────────────────────
# ARAÇLAR — Katı Geometri (Part Workbench)
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool(description="Belirtilen boyutlarda bir kutu (dikdörtgen prizma) oluşturur.")
def create_box(
    doc_name: str,
    object_name: str,
    length: float,
    width: float,
    height: float,
) -> dict:
    """
    Parametreler:
        doc_name   : Belge adı.
        object_name: Nesneyei verilecek ad.
        length     : X eksenindeki uzunluk (mm).
        width      : Y eksenindeki genişlik (mm).
        height     : Z eksenindeki yükseklik (mm).
    """
    return _safe_call(bridge.create_box, doc_name, object_name, length, width, height)


@mcp.tool(description="Silindir oluşturur.")
def create_cylinder(
    doc_name: str,
    object_name: str,
    radius: float,
    height: float,
) -> dict:
    """
    Parametreler:
        doc_name   : Belge adı.
        object_name: Nesne adı.
        radius     : Yarıçap (mm).
        height     : Yükseklik (mm).
    """
    return _safe_call(bridge.create_cylinder, doc_name, object_name, radius, height)


@mcp.tool(description="Küre oluşturur.")
def create_sphere(
    doc_name: str,
    object_name: str,
    radius: float,
) -> dict:
    return _safe_call(bridge.create_sphere, doc_name, object_name, radius)


@mcp.tool(description="Koni oluşturur.")
def create_cone(
    doc_name: str,
    object_name: str,
    radius1: float,
    radius2: float,
    height: float,
) -> dict:
    """
    Parametreler:
        radius1: Alt taban yarıçapı (mm).
        radius2: Üst taban yarıçapı (mm; 0 → sivri uç).
        height : Yükseklik (mm).
    """
    return _safe_call(bridge.create_cone, doc_name, object_name, radius1, radius2, height)


# ──────────────────────────────────────────────────────────────────────────────
# ARAÇLAR — Boolean Operasyonlar
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool(description="İki katıyı birleştirir (Union / Fuse).")
def boolean_union(doc_name: str, result_name: str, base_object: str, tool_object: str) -> dict:
    return _safe_call(bridge.boolean_union, doc_name, result_name, base_object, tool_object)


@mcp.tool(description="Temel nesneden araç nesnesini çıkarır (Cut / Subtract).")
def boolean_cut(doc_name: str, result_name: str, base_object: str, tool_object: str) -> dict:
    return _safe_call(bridge.boolean_cut, doc_name, result_name, base_object, tool_object)


@mcp.tool(description="İki katının kesişimini alır (Common / Intersect).")
def boolean_common(doc_name: str, result_name: str, base_object: str, tool_object: str) -> dict:
    return _safe_call(bridge.boolean_common, doc_name, result_name, base_object, tool_object)


# ──────────────────────────────────────────────────────────────────────────────
# ARAÇLAR — Part Design (Body / Sketch / Pad / Pocket / Fillet / Chamfer)
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool(description="Part Design Body oluşturur. Sketch ve feature'lar buraya bağlanır.")
def create_body(doc_name: str, body_name: str) -> dict:
    return _safe_call(bridge.create_body, doc_name, body_name)


@mcp.tool(description="Body'ye bağlı yeni bir Sketch oluşturur.")
def create_sketch(
    doc_name: str,
    body_name: str,
    sketch_name: str,
    plane: str = "XY",
) -> dict:
    """
    Parametreler:
        plane: 'XY', 'XZ' veya 'YZ'.
    """
    return _safe_call(bridge.create_sketch, doc_name, body_name, sketch_name, plane)


@mcp.tool(description="Sketch'e dikdörtgen ekler.")
def add_rectangle_to_sketch(
    doc_name: str,
    sketch_name: str,
    x: float,
    y: float,
    width: float,
    height: float,
) -> dict:
    """
    Parametreler:
        x, y   : Dikdörtgenin sol alt köşesi.
        width  : Genişlik.
        height : Yükseklik.
    """
    return _safe_call(bridge.add_rectangle_to_sketch, doc_name, sketch_name, x, y, width, height)


@mcp.tool(description="Sketch'e daire ekler.")
def add_circle_to_sketch(
    doc_name: str,
    sketch_name: str,
    center_x: float,
    center_y: float,
    radius: float,
) -> dict:
    return _safe_call(bridge.add_circle_to_sketch, doc_name, sketch_name, center_x, center_y, radius)


@mcp.tool(description="Sketch'i belirtilen uzunlukta ekstrüde eder (Pad).")
def pad(
    doc_name: str,
    body_name: str,
    sketch_name: str,
    length: float,
    feature_name: str = "",
) -> dict:
    return _safe_call(bridge.pad, doc_name, body_name, sketch_name, length, feature_name)


@mcp.tool(description="Sketch şeklinde belirlenen derinlikte boşluk açar (Pocket).")
def pocket(
    doc_name: str,
    body_name: str,
    sketch_name: str,
    depth: float,
    feature_name: str = "",
) -> dict:
    return _safe_call(bridge.pocket, doc_name, body_name, sketch_name, depth, feature_name)


@mcp.tool(description="Belirtilen kenarlara yuvarlatma (Fillet) uygular.")
def fillet(
    doc_name: str,
    body_name: str,
    feature_name: str,
    edge_indices: list[int],
    radius: float,
) -> dict:
    """
    Parametreler:
        edge_indices: Yuvarlatılacak kenar indeksleri (0 tabanlı).
        radius      : Yuvarlatma yarıçapı (mm).
    """
    return _safe_call(bridge.fillet, doc_name, body_name, feature_name, edge_indices, radius)


@mcp.tool(description="Belirtilen kenarlara pah (Chamfer) uygular.")
def chamfer(
    doc_name: str,
    body_name: str,
    feature_name: str,
    edge_indices: list[int],
    size: float,
) -> dict:
    return _safe_call(bridge.chamfer, doc_name, body_name, feature_name, edge_indices, size)


# ──────────────────────────────────────────────────────────────────────────────
# ARAÇLAR — Nesne Manipülasyonu
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool(description="Nesneyi belirtilen koordinata taşır.")
def move_object(
    doc_name: str,
    object_name: str,
    x: float,
    y: float,
    z: float,
) -> dict:
    return _safe_call(bridge.move_object, doc_name, object_name, x, y, z)


@mcp.tool(description="Nesneyi belirtilen eksen etrafında döndürür.")
def rotate_object(
    doc_name: str,
    object_name: str,
    axis_x: float,
    axis_y: float,
    axis_z: float,
    angle_deg: float,
) -> dict:
    """
    Parametreler:
        axis_x/y/z: Dönüş ekseni (birim vektör).
        angle_deg  : Dönüş açısı (derece).
    """
    return _safe_call(bridge.rotate_object, doc_name, object_name, axis_x, axis_y, axis_z, angle_deg)


@mcp.tool(description="Nesnenin belirli bir özelliğini (property) değiştirir.")
def set_property(
    doc_name: str,
    object_name: str,
    property_name: str,
    value: Any,
) -> dict:
    return _safe_call(bridge.set_property, doc_name, object_name, property_name, value)


# ──────────────────────────────────────────────────────────────────────────────
# ARAÇLAR — Serbest Kod Yürütme
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool(
    description=(
        "Doğrudan FreeCAD Python ortamında kod çalıştırır. "
        "Standart araçların yetersiz kaldığı karmaşık senaryolar için kullanın. "
        "⚠️  Güvenlik: Zararlı sistem komutları çalıştırmayın."
    )
)
def execute_code(python_code: str) -> dict:
    """
    Parametreler:
        python_code: FreeCAD Python ortamında çalıştırılacak kod.

    Döner:
        ok, stdout, stderr, result
    """
    return _safe_call(bridge.execute_code, python_code)


# ──────────────────────────────────────────────────────────────────────────────
# ARAÇLAR — Görsel Doğrulama
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool(
    description=(
        "Aktif FreeCAD görünümünün ekran görüntüsünü Base64 PNG olarak döner. "
        "Mekansal hataları (yanlış konum, kesişim problemi vb.) düzeltmek için kullanın."
    )
)
def get_view_screenshot(doc_name: str) -> dict:
    """
    Döner:
        ok, image_base64 (PNG, base64 kodlu)
    """
    try:
        b64 = bridge.get_view_screenshot(doc_name)
        return {"ok": True, "image_base64": b64, "format": "png"}
    except Exception as exc:
        return {"ok": False, "error": enrich_error(str(exc))}

@mcp.tool(description="Kamera açısını ayarlar (isometric, top, front, fit). Ekran görüntüsü öncesi faydalıdır.")
def set_camera_view(doc_name: str, view_type: str = "isometric") -> dict:
    return _safe_call(bridge.set_camera_view, doc_name, view_type)

@mcp.tool(description="Belgeyi veya nesneleri STL, STEP formatında dışa aktarır.")
def export_document(doc_name: str, file_path: str) -> dict:
    return _safe_call(bridge.export_document, doc_name, file_path)


# ──────────────────────────────────────────────────────────────────────────────
# YENİ EKLENEN PROFESYONEL ARAÇLAR
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool(description="Pah (Fillet/Chamfer) kırmak veya analiz için nesnenin tüm kenar ve yüzey topolojisini (Uzunluk, Alan ve Merkez Koordinatları) getirir.")
def get_topology_info(doc_name: str, object_name: str) -> dict:
    return _safe_call(bridge.get_topology_info, doc_name, object_name)

@mcp.tool(description="Sketch'e geometrik kısıtlama ekler ('Distance', 'Radius', 'Coincident', 'Parallel', 'Horizontal', vb). pos1/pos2 parametreleri 1=Start, 2=End, 3=Center, 0=Edge'i ifade eder.")
def add_sketch_constraint(
    doc_name: str, sketch_name: str, constraint_type: str, geo1: int, pos1: int, geo2: int = -1, pos2: int = -1, value: float = 0.0
) -> dict:
    return _safe_call(bridge.add_sketch_constraint, doc_name, sketch_name, constraint_type, geo1, pos1, geo2, pos2, value)

@mcp.tool(description="Dokümandaki son işlemi geri alır (Undo). Hata yaptığınızda dokümanı baştan çizmek yerine bunu kullanın.")
def undo(doc_name: str) -> dict:
    return _safe_call(bridge.undo, doc_name)

@mcp.tool(description="Dokümandaki geri alınan işlemi yineler (Redo).")
def redo(doc_name: str) -> dict:
    return _safe_call(bridge.redo, doc_name)

@mcp.tool(description="Nesnenin hacim, ağırlık merkezi (Center of Mass) ve atalet momenti (Matrix of Inertia) gibi fiziksel özelliklerini döner.")
def get_physical_properties(doc_name: str, object_name: str) -> dict:
    return _safe_call(bridge.get_physical_properties, doc_name, object_name)

@mcp.tool(description="Nesnenin teknik çizimini (TechDraw) oluşturup PDF veya SVG olarak dışa aktarır.")
def export_techdraw(doc_name: str, object_name: str, file_path: str) -> dict:
    return _safe_call(bridge.export_techdraw, doc_name, object_name, file_path)


# ──────────────────────────────────────────────────────────────────────────────
# ARAÇLAR — Bağlantı Testi
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool(description="FreeCAD RPC sunucusuna bağlantıyı test eder.")
def ping_freecad() -> dict:
    """FreeCAD bağlantısının canlı olup olmadığını kontrol eder."""
    alive = bridge.ping()
    if alive:
        return {"ok": True, "message": "FreeCAD RPC sunucusu çalışıyor."}
    return {
        "ok": False,
        "message": (
            "FreeCAD'e bağlanılamadı. "
            "FreeCAD'i açın ve 'Macro > Macros' menüsünden "
            "'freecad_rpc_server.py' makrosunu çalıştırın."
        ),
    }


# ──────────────────────────────────────────────────────────────────────────────
# KAYNAKLAR (Resources)
# ──────────────────────────────────────────────────────────────────────────────

@mcp.resource("freecad://documents/{doc_name}/tree")
def resource_object_tree(doc_name: str) -> str:
    """Belgedeki tüm nesnelerin hiyerarşik ağacını döner."""
    result = _safe_call(bridge.get_object_tree, doc_name)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.resource("freecad://documents/{doc_name}/objects/{object_name}")
def resource_object_info(doc_name: str, object_name: str) -> str:
    """Belirli bir nesnenin tüm özelliklerini ve B-Rep özetini döner."""
    result = _safe_call(bridge.get_object_info, doc_name, object_name)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.resource("freecad://system/info")
def resource_system_info() -> str:
    """FreeCAD versiyon, yüklü modüller ve birim sistemi bilgisini döner."""
    result = _safe_call(bridge.get_system_info)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.resource("freecad://documents/list")
def resource_document_list() -> str:
    """Açık tüm belgeleri listeler."""
    result = _safe_call(bridge.list_documents)
    return json.dumps(result, ensure_ascii=False, indent=2)


# ──────────────────────────────────────────────────────────────────────────────
# İSTEMLER (Prompts)
# ──────────────────────────────────────────────────────────────────────────────

@mcp.prompt(description="Standart bir M-serisi metrik cıvata oluşturma iş akışı.")
def prompt_create_bolt(m_size: int = 5, length_mm: float = 20.0) -> str:
    return f"""
M{m_size}x{length_mm} metrik cıvata oluştur. Adımlar:

1. '{m_size}m_bolt' adında yeni bir belge aç.
2. 'Body' oluştur.
3. XY düzleminde 'HeadSketch' adlı bir sketch ekle; merkezi (0,0) olan
   yarıçapı {m_size * 0.9:.1f} mm olan bir altıgen çiz (6 çizgi ile kapalı profil).
4. HeadSketch'i {m_size * 0.7:.1f} mm pad et → 'BoltHead'.
5. Yeni bir 'ShankSketch' ekle; merkezi (0,0) yarıçapı {m_size / 2:.2f} mm daire.
6. ShankSketch'i {length_mm} mm pad et → 'BoltShank'.
7. BoltHead ve BoltShank'i birleştir.
8. Üstteki 2 kenara {m_size * 0.05:.2f} mm chamfer uygula.
9. Sonucu '/tmp/{m_size}m_bolt.FCStd' olarak kaydet.
10. Ekran görüntüsü al ve doğrula.
"""


@mcp.prompt(description="Mevcut parçayı FDM 3D baskı için optimize eder.")
def prompt_optimize_for_3d_print(doc_name: str, object_name: str) -> str:
    return f"""
'{doc_name}' belgesindeki '{object_name}' nesnesini FDM 3D baskı için optimize et:

1. Önce 'get_object_info' ile nesneyi incele.
2. 90°'den fazla sarkma (overhang) olan yüzleri tespit et.
3. Gerekli destek yapılarını en aza indirecek şekilde nesneyi yeniden yönlendir
   (rotate_object kullan).
4. Wall thickness'in minimum 1.2 mm (2 perimeter) olduğunu doğrula.
5. Keskin iç köşelere en az 0.4 mm fillet uygula (printer nozzle çapı).
6. Görsel doğrulama için ekran görüntüsü al.
7. Optimize edilmiş versiyonu '/tmp/{doc_name}_3dprint.FCStd' olarak kaydet.
"""


@mcp.prompt(description="Boş bir belgeyle başlayıp adım adım geometri oluşturmak için genel iş akışı.")
def prompt_new_part_workflow(part_description: str) -> str:
    return f"""
Şu parçayı oluştur: {part_description}

Genel iş akışı:
1. ping_freecad ile bağlantıyı doğrula.
2. Anlamlı bir isimle yeni belge oluştur.
3. Tasarımı küçük adımlara böl: ana gövde → delikler → detaylar.
4. Her adımdan sonra get_object_tree ile ağacı kontrol et.
5. Karmaşık geometri için önce Part Workbench (create_box/cylinder),
   detaylar için Part Design (Body/Sketch/Pad/Pocket) kullan.
6. Tamamlandığında görsel doğrulama yap (get_view_screenshot).
7. Belgeyi kaydet.
"""


# ──────────────────────────────────────────────────────────────────────────────
# Giriş noktası
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")
