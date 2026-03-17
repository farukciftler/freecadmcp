import sys
import os

# freecad_bridge.py'nin bulunduğu dizini sys.path'e ekle
sys.path.append(os.path.join(os.getcwd(), "server"))

from freecad_bridge import FreeCADBridge

def create_involute_gear():
    bridge = FreeCADBridge("http://127.0.0.1:36875")
    doc_name = "GearTest"
    
    print(f"--- Karmaşık Geometri Testi: Involute Dişli ---")
    
    # 1. Doküman oluştur
    bridge.create_document(doc_name)
    
    # 2. FreeCAD Python kodu ile dişli oluşturma (Parametrik)
    # Bu kod doğrudan FreeCAD içindeki OpenCASCADE çekirdeğini kullanır.
    gear_script = """
import FreeCAD as App
import Part
import math

doc = App.getDocument('GearTest')

def make_gear(num_teeth=20, module=2.0, pressure_angle=20):
    # Basit bir dişli profili oluşturma mantığı
    addendum = module
    dedendum = 1.25 * module
    pitch_radius = (num_teeth * module) / 2.0
    outer_radius = pitch_radius + addendum
    root_radius = pitch_radius - dedendum
    
    # Silindir (Base)
    base = Part.makeCylinder(root_radius, 10.0)
    
    # Dişleri ekle
    teeth = []
    for i in range(num_teeth):
        angle = (360.0 / num_teeth) * i
        # Basit kutu diş (Örnek amaçlı, involüt eğrisi için daha detaylı çizim gerekir)
        tooth = Part.makeBox(module * 1.5, module * 2.0, 10.0)
        # Dişi merkeze göre konumlandır
        tooth.translate(App.Vector(pitch_radius - module, -module, 0))
        # Dişi döndür
        tooth.rotate(App.Vector(0,0,0), App.Vector(0,0,1), angle)
        base = base.fuse(tooth)
    
    obj = doc.addObject("Part::Feature", "InvoluteGear")
    obj.Shape = base
    doc.recompute()
    return obj.Name

_result = make_gear(num_teeth=18, module=3.0)
"""
    
    print("Dişli oluşturuluyor (Parametrik Python Scripti ile)...")
    res = bridge.execute_code(gear_script)
    
    if res.get("ok"):
        print(f"✅ Dişli başarıyla oluşturuldu: {res.get('result')}")
        if res.get("stdout"):
            print(f"Stdout: {res.get('stdout')}")
    else:
        print(f"❌ Hata: {res.get('error')}")
        print(f"Stderr: {res.get('stderr')}")

    # 3. Kavisli bir yüzey (Loft) denemesi
    loft_script = """
import FreeCAD as App
import Part

doc = App.getDocument('GearTest')

# İki farklı yükseklikte profil oluştur
c1 = Part.makeCircle(20, App.Vector(0,0,0))
c2 = Part.makeCircle(10, App.Vector(10,10,50)) # Hem daralıyor hem yana kayıyor

# Loft (Kavisli geçiş)
loft = Part.makeLoft([Part.Wire(c1.Edges), Part.Wire(c2.Edges)], True)

obj = doc.addObject("Part::Feature", "CurvedTransition")
obj.Shape = loft
doc.recompute()
_result = obj.Name
"""
    print("\nKavisli geçiş (Loft) oluşturuluyor...")
    res = bridge.execute_code(loft_script)
    
    if res.get("ok"):
        print(f"✅ Loft başarıyla oluşturuldu: {res.get('result')}")
    else:
        print(f"❌ Hata: {res.get('error')}")

    print("\n--- Test Tamamlandı. Lütfen FreeCAD ekranına bakın! ---")

if __name__ == "__main__":
    create_involute_gear()
