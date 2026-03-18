<div align="center">

# 🚀 FreeCAD MCP (Model Context Protocol) Server

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![FreeCAD](https://img.shields.io/badge/FreeCAD-1.0+-red.svg)](https://www.freecadweb.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

**Yapay Zeka (Claude, Cursor, Cline) ile Doğrudan 3D CAD Mühendisliği Yapın!**

</div>

FreeCAD MCP, yapay zeka asistanlarınızın (Claude Desktop, Cursor AI vb.) doğrudan **FreeCAD 3D CAD yazılımı ile konuşmasını sağlayan** bir köprüdür. 

Siz sadece doğal dilde *"Masa için kavisli bir akıllı telefon tutucu çiz ve 3D çıktısını ver"* dersiniz; yapay zeka arka planda FreeCAD'in güçlü C++ motorunu kullanarak tasarımı paramerik olarak çizer, teknik resimlerini çıkartır ve 3D yazıcıya (STL/STEP) hazır hale getirir!

---

## 🌟 Neler Yapabilirsiniz? (Yetenekler)

Bu sunucu basit şekiller çizen bir "oyuncak" değildir; eksiksiz bir mühendislik asistanı olarak kodlanmıştır.

- **🛠 Temel ve Karmaşık Geometriler:** Küp, Silindir, Koni vb. primitifler veya Sketch (2D Çizim) üzerinden Pad (Extrude) ve Pocket (Kesme) işlemleri.
- **🏗 Boolean İşlemleri:** Parçaları Birleştirme (Union), Kesme (Cut/Subtract) ve Kesişim (Intersection).
- **📐 Parametrik Mühendislik (Constraints):** Koordinat ezberlemek yerine; Teğet (Tangent), Paralel (Parallel), Eşmerkezli (Coincident) gibi Sketch kısıtlamaları ekleyebilme.
- **👁 Topolojik Hassasiyet:** Yapay zekanın "şu nesnenin en üst yüzeyi" veya "şu kenar" diyebilmesi için tüm modelin Alan, Uzunluk ve Kütle Merkezi koordinatlarını saniyesinde okuma.
- **⚖️ Fiziksel Analizler:** Tasarlanan parçanın Hacmini, Ağırlık Merkezini (Center of Mass) ve Atalet Momentini hesaplama.
- **📸 Yüksek Kaliteli Önizlemeler (Render):** Yapay zeka, sahte grafik çizimleri yerine, FreeCAD'in profesyonel 3D viewport'undan *gerçek ekran görüntülerini* alarak size anında sunar.
- **📄 2D Teknik Çizim (TechDraw):** 3D modelin Üst, Ön, Yan ve İzometrik açılarından otomatik olarak A4 ölçülü Teknik Çizim (Blueprint) kağıtları oluşturma.
- **💾 Çoklu Format (Export):** `.FCStd` (FreeCAD Projesi), `.STL` (3D Baskı) ve `.STEP` (Evrensel CAD) formatlarında dışa aktarma.

---

## ⚙️ Kurulum (2 Adımda Çok Basit)

Sistemin çalışması için iki parça vardır: FreeCAD'in içindeki dinleyici makro ve bilgisayarınızda çalışan MCP Sunucusu.

### Adım 1: FreeCAD'i Hazırlayın (Makro Kurulumu)
1. Bu projeyi bilgisayarınıza indirin (`git clone`).
2. FreeCAD'i açın. Üst menüden **Macro > Macros...** (Makrolar) seçeneğine tıklayın.
3. Çıkan pencerede **Destination (Hedef Dizin)** yazan yeri bulun. Bu, FreeCAD'in makroları okuduğu klasördür (Örn: `~/Library/Application Support/FreeCAD/Macro`).
4. Proje klasöründeki **`freecad_rpc_server.py`** dosyasını (veya adını değiştirip `newmacro.FCMacro` yaparak) bu hedefe kopyalayın.
5. Makro penceresinde bu dosyayı seçip **Execute (Çalıştır)** butonuna basın.
*(FreeCAD konsolunda "✅ Safe RPC sunucusu başladı → 127.0.0.1:36875" yazdığını göreceksiniz. Artık FreeCAD, yapay zekadan gelecek komutları dinliyor!)*

### Adım 2: MCP Sunucusunu Yapay Zekaya (AI) Ekleyin

#### Seçenek A: Cursor Editör İçin
Cursor'ın 3D modelleri kendi kendine çizmesi için projeye bir `cursor_mcp_launcher.sh` dosyası dahil ettik.
1. Cursor'ı açın.
2. **Settings (Ayarlar) > Features > MCP Servers** menüsüne gidin.
3. **+ Add New MCP Server** diyerek şu bilgileri girin:
   - **Name:** FreeCAD
   - **Type:** command
   - **Command:** `[PROJENIN_TAM_YOLU]/cursor_mcp_launcher.sh` *(Örn: `/Users/Ahmet/freecad-mcp/cursor_mcp_launcher.sh`)*
4. Kaydedin ve yenileyin. Artık Cursor'da Cmd+L (Chat) ekranında 3D tasarımlar yaptırabilirsiniz!

#### Seçenek B: Claude Desktop İçin
`claude_desktop_config.example.json` dosyasını kopyalayıp Claude uygulamanızın (Mac'te: `~/Library/Application Support/Claude/claude_desktop_config.json`) ayar dosyasına yapıştırın:
```json
{
  "mcpServers": {
    "freecad": {
      "command": "python",
      "args": ["-m", "server.main"],
      "env": {
        "PYTHONPATH": "/[PROJENIN_TAM_YOLU]"
      }
    }
  }
}
```

---

## 💡 Nasıl Kullanılır? (Örnek İstekler)

Sistem kurulduktan ve FreeCAD arkaplanda (veya açıkken makro çalıştırılmış halde) beklerken yapay zekanıza (Claude / Cursor) şunları yazabilirsiniz:

* *"Bana 10mm çapında ve 20mm yüksekliğinde bir silindir çiz, üst kenarına 2mm pah (fillet) kır ve stl olarak kaydet."*
* *"Mevcut 'motor_blogu.FCStd' dosyasını aç. İçindeki 'AnaGovde' parçasının ağırlık merkezini hesapla ve bana söyle."*
* *"Kavisli, modern bir akıllı telefon standı modelle. Sadece kodu yazma, FreeCAD'de de üret. Parçanın her yönden (Üst, Ön, Yan) teknik çizimlerini içeren A4 şablonunu oluştur. Sonra da bana Isometric kameradan gerçek bir ekran görüntüsünü at."*

---

## 🏗 Mimari (Nasıl Çalışıyor?)

Sistem iki yönlü, çökme korumalı (thread-safe) bir mimari kullanır:
1. **FreeCAD RPC Server (`freecad_rpc_server.py`):** FreeCAD içindeki Python API'sini ana iş parçacığında (Main Thread) güvenli bir şekilde dışa açan bir XML-RPC köprüsüdür.
2. **MCP Fast API Sunucusu (`server/main.py`):** Claude veya Cursor'ın dilinden anlayan (stdio tabanlı) ve onlara "Araçlar (Tools)" sunan ana mantık katmanıdır. Gelen tüm komutları yakalar ve Bridge (Köprü) üzerinden FreeCAD'e iletir.

## 🤝 Katkıda Bulunun (Contributing)
Eksik gördüğünüz FreeCAD özelliklerini (Örn: Assembly4, FEM analizleri vb.) `server/freecad_bridge.py` ve `freecad_rpc_server.py` dosyalarına ekleyerek Pull Request atabilirsiniz. 

**Lisans:** MIT License
