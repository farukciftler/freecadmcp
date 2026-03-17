import os
import sys
import tempfile
sys.path.insert(0, os.path.abspath("."))
from server.freecad_bridge import FreeCADBridge

def run_tests():
    bridge = FreeCADBridge()
    
    print("--- 1. Temel Bağlantı ---")
    try:
        print("Ping:", bridge.ping())
    except Exception as e:
        print("Bağlantı Hatası:", e)
        return

    print("\n--- 2. Sistem Bilgisi ---")
    print(bridge.get_system_info())

    doc_name = "TestDocMCP"
    print("\n--- 3. Doküman Yönetimi ---")
    print("Create Doc:", bridge.create_document(doc_name))
    print("List Docs:", bridge.list_documents())

    print("\n--- 4. İlkel Geometrik Şekiller (Primitives) ---")
    print("Box:", bridge.create_box(doc_name, "MyBox", 10, 10, 10))
    print("Cylinder:", bridge.create_cylinder(doc_name, "MyCyl", 5, 10))
    print("Sphere:", bridge.create_sphere(doc_name, "MySphere", 5))
    print("Cone:", bridge.create_cone(doc_name, "MyCone", 5, 2, 10))

    print("\n--- 5. Boolean İşlemleri ---")
    print("Union:", bridge.boolean_union(doc_name, "MyUnion", "MyBox", "MyCyl"))
    print("Cut:", bridge.boolean_cut(doc_name, "MyCut", "MyUnion", "MySphere"))

    print("\n--- 6. Part Design Araçları ---")
    print("Body:", bridge.create_body(doc_name, "MyBody"))
    print("Sketch:", bridge.create_sketch(doc_name, "MyBody", "MySketch", "XY"))
    print("Rectangle:", bridge.add_rectangle_to_sketch(doc_name, "MySketch", 0, 0, 20, 20))
    print("Pad:", bridge.pad(doc_name, "MyBody", "MySketch", 10, "MyPad"))

    print("\n--- 7. Obje Manipülasyonu ---")
    print("Move:", bridge.move_object(doc_name, "MyPad", 10, 10, 10))
    print("Rotate:", bridge.rotate_object(doc_name, "MyPad", 0, 0, 1, 45))

    print("\n--- 8. Veri & Hiyerarşi Okuma ---")
    tree = bridge.get_object_tree(doc_name)
    print(f"Tree: {tree.get('count', 0)} obje bulundu.")
    
    print("\n--- 9. Dışa Aktarma (Export) ---")
    tmp_stl = os.path.join(tempfile.gettempdir(), "test_export.stl")
    print("Export STL:", bridge.export_document(doc_name, tmp_stl))

    print("\n--- 10. GUI Bağımlı Özellikler (Hata Bekleniyor) ---")
    try:
        print("Set Camera:", bridge.set_camera_view(doc_name, "isometric"))
    except Exception as e:
        print("Set Camera Beklenen Hata:", e)
        
    try:
        res = bridge.get_view_screenshot(doc_name)
        print("Screenshot Başarılı (Beklenmiyordu):", str(res)[:20])
    except Exception as e:
        print("Screenshot Beklenen Hata:", e)

    print("\n--- 11. Temizlik ---")
    print("Close Doc:", bridge.close_document(doc_name))

if __name__ == "__main__":
    run_tests()
