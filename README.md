# FreeCAD MCP Sunucusu

FreeCAD'i büyük dil modelleri (Claude, GPT-4o vb.) ile konuşturan bir **Model Context Protocol (MCP)** sunucusu.

## Mimari

```
┌──────────────────────┐        stdio/JSON-RPC       ┌───────────────────┐
│  LLM Host            │ ◄──────────────────────────► │  MCP Sunucusu     │
│  (Claude Desktop /   │                              │  server/main.py   │
│   Cursor / VS Code)  │                              └────────┬──────────┘
└──────────────────────┘                                       │ XML-RPC
                                                               │ 127.0.0.1:9875
                                                      ┌────────▼──────────┐
                                                      │  FreeCAD          │
                                                      │  + RPC Makrosu    │
                                                      │  freecad_rpc_     │
                                                      │  server.py        │
                                                      └───────────────────┘
```

## Kurulum

### 1. Bağımlılıkları yükle

```bash
cd /Users/farukciftler/Documents/projects/freecadmcp
pip install -e .
```

### 2. FreeCAD'de RPC sunucusunu başlat

1. FreeCAD'i aç
2. **Makrolar > Makrolar...** menüsüne git
3. `freecad_rpc_server.py` dosyasını seç ve **Çalıştır**
4. FreeCAD konsolunda `✅ FreeCAD RPC sunucusu başladı → 127.0.0.1:9875` mesajını gör

### 3. MCP sunucusunu yapılandır

**Claude Desktop için:**

`~/Library/Application Support/Claude/claude_desktop_config.json` dosyasını düzenle:

```json
{
  "mcpServers": {
    "freecad": {
      "command": "python",
      "args": ["-m", "server.main"],
      "cwd": "/Users/farukciftler/Documents/projects/freecadmcp"
    }
  }
}
```

**Test için doğrudan çalıştır:**

```bash
python -m server.main
```

## Araçlar (Tools)

| Araç | Açıklama |
|------|----------|
| `ping_freecad` | Bağlantı testi |
| `create_document` | Yeni belge oluştur |
| `save_document` | Belgeyi kaydet |
| `close_document` | Belgeyi kapat |
| `list_documents` | Açık belgeleri listele |
| `create_box` | Kutu (dikdörtgen prizma) oluştur |
| `create_cylinder` | Silindir oluştur |
| `create_sphere` | Küre oluştur |
| `create_cone` | Koni oluştur |
| `boolean_union` | Birleştirme (Fuse) |
| `boolean_cut` | Çıkarma (Cut) |
| `boolean_common` | Kesişim (Common) |
| `create_body` | Part Design Body oluştur |
| `create_sketch` | Sketch oluştur |
| `add_rectangle_to_sketch` | Sketch'e dikdörtgen ekle |
| `add_circle_to_sketch` | Sketch'e daire ekle |
| `pad` | Sketch'i ekstrüde et |
| `pocket` | Sketch ile boşluk aç |
| `fillet` | Kenar yuvarlatma |
| `chamfer` | Pah kırma |
| `move_object` | Nesneyi taşı |
| `rotate_object` | Nesneyi döndür |
| `set_property` | Özellik değiştir |
| `execute_code` | Serbest Python kodu çalıştır |
| `get_view_screenshot` | Ekran görüntüsü al (görsel doğrulama) |

## Kaynaklar (Resources)

| URI | Açıklama |
|-----|----------|
| `freecad://documents/{doc}/tree` | Nesne ağacı |
| `freecad://documents/{doc}/objects/{obj}` | Nesne detayları |
| `freecad://system/info` | FreeCAD sistem bilgisi |
| `freecad://documents/list` | Belge listesi |

## İstemler (Prompts)

| İstem | Açıklama |
|-------|----------|
| `prompt_create_bolt` | M-serisi cıvata oluştur |
| `prompt_optimize_for_3d_print` | 3D baskı optimizasyonu |
| `prompt_new_part_workflow` | Genel parça oluşturma iş akışı |

## Örnek Kullanım

Claude'a söyle:
> "FreeCAD'de 100x50x30mm boyutlarında bir kutu oluştur, üstüne 10mm derinliğinde 20mm çaplı bir delik aç ve kaydet."

Claude sırayla şunları yapacak:
1. `ping_freecad` → bağlantı kontrolü
2. `create_document` → belge aç
3. `create_box` → kutu oluştur
4. `create_body` + `create_sketch` + `add_circle_to_sketch` + `pocket` → delik
5. `get_view_screenshot` → görsel doğrulama
6. `save_document` → kaydet

## Proje Yapısı

```
freecadmcp/
├── server/
│   ├── __init__.py
│   ├── main.py              # MCP sunucusu (araçlar, kaynaklar, istemler)
│   ├── freecad_bridge.py    # XML-RPC köprüsü
│   └── error_enricher.py   # Hata mesajı zenginleştirici
├── freecad_rpc_server.py    # FreeCAD içi makro (RPC sunucusu)
├── pyproject.toml
├── claude_desktop_config.example.json
└── README.md
```

## Güvenlik

- RPC sunucusu yalnızca `127.0.0.1` (localhost) dinler
- `execute_code` aracı güçlüdür; zararlı kod çalıştırmayın
- Üretim ortamında FreeCAD'i Docker içinde izole edin

## Lisans

MIT
