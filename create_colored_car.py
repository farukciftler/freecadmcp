import os
import sys
sys.path.insert(0, os.path.abspath("."))
from server.freecad_bridge import FreeCADBridge

def build_colored_car():
    bridge = FreeCADBridge()
    doc = "ColoredCar"
    
    print("1. Yeni doküman oluşturuluyor...")
    bridge.create_document(doc)

    print("2. Gövde ve Kabin oluşturuluyor (Ayrı parçalar olarak)...")
    bridge.create_box(doc, "Chassis", 100, 40, 20)
    bridge.move_object(doc, "Chassis", 0, 0, 10)

    bridge.create_box(doc, "Cabin", 50, 36, 15)
    bridge.move_object(doc, "Cabin", 25, 2, 30)

    print("3. Tekerlekler oluşturuluyor...")
    bridge.create_cylinder(doc, "W1", 12, 5)
    bridge.rotate_object(doc, "W1", 1, 0, 0, 90)
    bridge.move_object(doc, "W1", 20, 0, 12)

    bridge.create_cylinder(doc, "W2", 12, 5)
    bridge.rotate_object(doc, "W2", 1, 0, 0, 90)
    bridge.move_object(doc, "W2", 20, 45, 12)

    bridge.create_cylinder(doc, "W3", 12, 5)
    bridge.rotate_object(doc, "W3", 1, 0, 0, 90)
    bridge.move_object(doc, "W3", 80, 0, 12)

    bridge.create_cylinder(doc, "W4", 12, 5)
    bridge.rotate_object(doc, "W4", 1, 0, 0, 90)
    bridge.move_object(doc, "W4", 80, 45, 12)

    print("4. Parçalara Renk Ataması Yapılıyor...")
    # FreeCAD Python API'sini kullanarak ViewObject (Görsel Motor) üzerinden renk ayarı yapıyoruz.
    # RGB değerleri (0.0 - 1.0) aralığında verilir.
    color_code = """
import FreeCAD
try:
    import FreeCADGui
    has_gui = FreeCAD.GuiUp
except ImportError:
    has_gui = False

if has_gui:
    doc = FreeCAD.getDocument('ColoredCar')
    if doc:
        # Şasi: Kırmızı
        chassis = doc.getObject('Chassis')
        if chassis and hasattr(chassis, 'ViewObject') and chassis.ViewObject:
            chassis.ViewObject.ShapeColor = (0.9, 0.1, 0.1)
        
        # Kabin: Mavi
        cabin = doc.getObject('Cabin')
        if cabin and hasattr(cabin, 'ViewObject') and cabin.ViewObject:
            cabin.ViewObject.ShapeColor = (0.1, 0.4, 0.9)
            
        # Tekerlekler: Koyu Gri / Siyah
        for w_name in ['W1', 'W2', 'W3', 'W4']:
            w = doc.getObject(w_name)
            if w and hasattr(w, 'ViewObject') and w.ViewObject:
                w.ViewObject.ShapeColor = (0.15, 0.15, 0.15)
    
    FreeCADGui.updateGui()
"""
    res = bridge.execute_code(color_code)
    if res.get("stderr"):
        print(f"Renk atama uyarısı: {res['stderr']}")

    print("5. FCStd (FreeCAD Projesi) ve STEP (Renkli 3D Formatı) olarak kaydediliyor...")
    fcstd_path = os.path.abspath("colored_toy_car.FCStd")
    step_path = os.path.abspath("colored_toy_car.step")
    
    # 1. FCStd Kaydı
    bridge.save_document(doc, fcstd_path)
    
    # 2. STEP Kaydı
    bridge.export_document(doc, step_path)
    
    print(f"Başarıyla Kaydedildi:\n -> FreeCAD Dosyası: {fcstd_path}\n -> STEP Dosyası: {step_path}")
    
    bridge.close_document(doc)

if __name__ == "__main__":
    try:
        build_colored_car()
    except Exception as e:
        print(f"Hata: {e}")
