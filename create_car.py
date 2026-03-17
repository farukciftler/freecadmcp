import sys
import os

# freecad_bridge.py'nin bulunduğu dizini sys.path'e ekle
sys.path.append(os.path.join(os.getcwd(), "server"))

from freecad_bridge import FreeCADBridge

def create_stylized_car():
    bridge = FreeCADBridge("http://127.0.0.1:36875")
    doc_name = "CarDesign"
    
    print(f"--- Araba Modelleme Başlatılıyor ---")
    
    # 1. Doküman oluştur
    bridge.create_document(doc_name)
    
    # 2. Araba Gövdesi ve Tekerleklerini oluşturacak Script
    car_script = """
import FreeCAD as App
import Part
import math

doc = App.getDocument('CarDesign')

def make_car():
    # --- 1. GÖVDE (Loft ile kavisli tasarım) ---
    # Alt taban profili
    p1 = Part.makeBox(120, 60, 2).Shape
    p1.translate(App.Vector(0,0,0))
    
    # Orta gövde profili (biraz daha kavisli/dar)
    p2 = Part.makeBox(110, 55, 2).Shape
    p2.translate(App.Vector(5,2.5,15))
    
    # Üst tavan profili
    p3 = Part.makeBox(60, 45, 2).Shape
    p3.translate(App.Vector(30,7.5,30))
    
    # Loft ile bu profilleri birleştirerek kavisli bir gövde elde et
    try:
        body = Part.makeLoft([Part.Wire(p1.Edges), Part.Wire(p2.Edges), Part.Wire(p3.Edges)], True, False, False)
        body_obj = doc.addObject("Part::Feature", "CarBody")
        body_obj.Shape = body
        body_obj.ViewObject.ShapeColor = (0.8, 0.1, 0.1) # Kırmızı
    except:
        # Loft başarısız olursa basit kutu gövde (Güvenlik için)
        body_obj = doc.addObject("Part::Box", "CarBodySimple")
        body_obj.Length = 120
        body_obj.Width = 60
        body_obj.Height = 25
        body = body_obj.Shape

    # --- 2. TEKERLEK YUVALARI (Kesme işlemi) ---
    wheel_radius = 12
    wheel_width = 15
    
    # Tekerlek koordinatları [x, y]
    wheel_positions = [
        (25, -5),   # Sol ön
        (25, 50),   # Sağ ön
        (95, -5),   # Sol arka
        (95, 50)    # Sağ arka
    ]
    
    final_body = body
    wheels = []
    
    for i, (x, y) in enumerate(wheel_positions):
        # Tekerlek silindiri
        wheel = Part.makeCylinder(wheel_radius, wheel_width, App.Vector(x, y, 0), App.Vector(0, 1, 0))
        
        # Tekerlek objesi olarak ekle
        w_obj = doc.addObject("Part::Feature", f"Wheel_{i}")
        w_obj.Shape = wheel
        w_obj.ViewObject.ShapeColor = (0.1, 0.1, 0.1) # Siyah
        
        # Gövdeden tekerlek yuvasını çıkar (Cut)
        # Biraz daha büyük bir silindirle boşluk açalım
        cutter = Part.makeCylinder(wheel_radius + 2, wheel_width + 10, App.Vector(x, y-5, 0), App.Vector(0, 1, 0))
        final_body = final_body.cut(cutter)
    
    # Güncellenmiş gövdeyi ata
    body_obj.Shape = final_body
    
    # --- 3. CAMLAR / DETAYLAR ---
    # Ön cam alanı (Basit bir eğik kutu)
    windshield = Part.makeBox(30, 40, 15)
    windshield.translate(App.Vector(25, 10, 18))
    # Windshield'ı gövdeye kaynatalım veya ayrı obje yapalım
    ws_obj = doc.addObject("Part::Feature", "Windshield")
    ws_obj.Shape = windshield
    ws_obj.ViewObject.ShapeColor = (0.5, 0.8, 1.0, 0.5) # Şeffaf Mavi
    ws_obj.ViewObject.Transparency = 50

    doc.recompute()
    return "CarComplete"

_result = make_car()
"""
    
    print("Stylized Araba modeli (Loft/Cut/Merge) oluşturuluyor...")
    res = bridge.execute_code(car_script)
    
    if res.get("ok"):
        print(f"✅ Araba başarıyla oluşturuldu: {res.get('result')}")
    else:
        print(f"❌ Hata: {res.get('error')}")
        print(f"Stderr: {res.get('stderr')}")

    print("\n--- Model Tamamlandı. Lütfen FreeCAD ekranını 3D olarak döndürerek inceleyin! ---")

if __name__ == "__main__":
    create_stylized_car()
