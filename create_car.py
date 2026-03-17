import os
import sys
sys.path.insert(0, os.path.abspath("."))
from server.freecad_bridge import FreeCADBridge

def build_car():
    bridge = FreeCADBridge()
    doc = "CarProject"
    
    print("1. Yeni doküman oluşturuluyor...")
    bridge.create_document(doc)

    print("2. Gövde ve Kabin oluşturuluyor...")
    # Şasi: 100mm uzunluk, 40mm genişlik, 20mm yükseklik. Z=10 seviyesine koyalım ki altı boş olsun (tekerlekler için)
    bridge.create_box(doc, "Chassis", 100, 40, 20)
    bridge.move_object(doc, "Chassis", 0, 0, 10)

    # Kabin: 50mm uzunluk, 36mm genişlik, 15mm yükseklik.
    bridge.create_box(doc, "Cabin", 50, 36, 15)
    bridge.move_object(doc, "Cabin", 25, 2, 30) # Şasinin ortasına ve üstüne oturttuk (Y'de 2mm içeride)

    # Şasi ve Kabini birleştir
    bridge.boolean_union(doc, "CarBody", "Chassis", "Cabin")

    print("3. Tekerlekler oluşturuluyor ve hizalanıyor...")
    # Tekerlek boyutları: Yarıçap=12, Kalınlık=5
    # Silindirler normalde Z ekseninde uzar. Tekerlek olması için X veya Y eksenine yatırmalıyız. (X etrafında 90 derece döndüreceğiz)
    
    wheel_radius = 12
    wheel_width = 5
    
    # Tekerlek 1 (Ön Sol)
    bridge.create_cylinder(doc, "W1", wheel_radius, wheel_width)
    bridge.rotate_object(doc, "W1", 1, 0, 0, 90) # X ekseninde 90 derece yatır
    bridge.move_object(doc, "W1", 20, 0, 12) # Y=0 (Sol), Z=12 (Yere değecek şekil)

    # Tekerlek 2 (Ön Sağ)
    bridge.create_cylinder(doc, "W2", wheel_radius, wheel_width)
    bridge.rotate_object(doc, "W2", 1, 0, 0, 90)
    bridge.move_object(doc, "W2", 20, 45, 12) # Y=45 (Sağ)

    # Tekerlek 3 (Arka Sol)
    bridge.create_cylinder(doc, "W3", wheel_radius, wheel_width)
    bridge.rotate_object(doc, "W3", 1, 0, 0, 90)
    bridge.move_object(doc, "W3", 80, 0, 12)

    # Tekerlek 4 (Arka Sağ)
    bridge.create_cylinder(doc, "W4", wheel_radius, wheel_width)
    bridge.rotate_object(doc, "W4", 1, 0, 0, 90)
    bridge.move_object(doc, "W4", 80, 45, 12)

    print("4. Tüm parçalar tek bir modelde birleştiriliyor...")
    # Iteratif birleştirme (FreeCAD MultiFuse desteklese de köprümüz 2'li birleştirme alıyor)
    bridge.boolean_union(doc, "U1", "CarBody", "W1")
    bridge.boolean_union(doc, "U2", "U1", "W2")
    bridge.boolean_union(doc, "U3", "U2", "W3")
    bridge.boolean_union(doc, "FinalCar", "U3", "W4")

    print("5. 3D Baskı için STL formatında dışa aktarılıyor...")
    stl_path = os.path.abspath("toy_car_3d_print.stl")
    bridge.export_document(doc, stl_path)
    print(f"Başarıyla Kaydedildi: {stl_path}")
    
    # İşimiz bitti, dokümanı hafızadan silebiliriz
    bridge.close_document(doc)

if __name__ == "__main__":
    try:
        build_car()
    except Exception as e:
        print(f"Hata oluştu: {e}")
