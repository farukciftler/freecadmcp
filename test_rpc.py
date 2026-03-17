import sys
import os

# freecad_bridge.py'nin bulunduğu dizini sys.path'e ekle
sys.path.append(os.path.join(os.getcwd(), "server"))

from freecad_bridge import FreeCADBridge

def run_test():
    # Sunucu adresi: 127.0.0.1:36875
    bridge = FreeCADBridge("http://127.0.0.1:36875")
    
    print("--- FreeCAD RPC Testi Başlatılıyor ---")
    
    # 1. Ping testi
    print("1. Ping testi...")
    if bridge.ping():
        print("✅ Sunucuya erişildi (Pong!)")
    else:
        print("❌ Sunucuya erişilemedi.")
        return

    # 2. Sistem Bilgisi
    print("\n2. Sistem Bilgisi alınıyor...")
    sys_info = bridge.get_system_info()
    if sys_info.get("ok"):
        print(f"✅ FreeCAD Versiyonu: {sys_info.get('freecad_version')}")
    else:
        print(f"❌ Hata: {sys_info.get('error')}")

    # 3. Belge Oluşturma
    doc_name = "TestDoc"
    print(f"\n3. '{doc_name}' belgesi oluşturuluyor...")
    res = bridge.create_document(doc_name)
    if res.get("ok"):
        print(f"✅ Belge oluşturuldu: {res.get('doc_name')}")
    else:
        print(f"❌ Hata: {res.get('error')}")

    # 4. Kutu (Box) Oluşturma
    print("\n4. Kutu (Box) oluşturuluyor...")
    res = bridge.create_box(doc_name, "MyBox", 10.0, 20.0, 30.0)
    if res.get("ok"):
        print(f"✅ Kutu oluşturuldu: {res.get('object')}")
        shape = res.get("shape", {})
        print(f"   Hacim: {shape.get('volume')}, Alan: {shape.get('area')}")
    else:
        print(f"❌ Hata: {res.get('error')}")

    # 5. Belge Listeleme
    print("\n5. Belgeler listeleniyor...")
    res = bridge.list_documents()
    if res.get("ok"):
        docs = res.get("documents", [])
        print(f"✅ Mevcut belgeler: {', '.join(docs)}")
    else:
        print(f"❌ Hata: {res.get('error')}")

    print("\n--- Test Tamamlandı ---")

if __name__ == "__main__":
    run_test()
