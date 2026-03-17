"""
Hata zenginleştirme modülü.

FreeCAD'in ham Python traceback veya RPC hata mesajlarını
LLM'nin anlayabileceği açıklayıcı mesajlara dönüştürür.
"""

import re

# Bilinen hata kalıpları → insan dostu açıklama
_ERROR_PATTERNS: list[tuple[re.Pattern, str]] = [
    (
        re.compile(r"Sketcher::ConstraintError.*edge\s+(\d+)", re.IGNORECASE),
        lambda m: (
            f"Kenar #{m.group(1)} üzerinde çelişen kısıtlamalar var. "
            "Mevcut kısıtlamaları 'get_object_info' ile kontrol edin "
            "veya çakışan kısıtlamayı kaldırın."
        ),
    ),
    (
        re.compile(r"No document named '(.+)'", re.IGNORECASE),
        lambda m: (
            f"'{m.group(1)}' adında bir belge bulunamadı. "
            "'list_documents' aracıyla mevcut belgeleri listeleyin."
        ),
    ),
    (
        re.compile(r"Object '(.+)' not found", re.IGNORECASE),
        lambda m: (
            f"'{m.group(1)}' adında bir nesne bulunamadı. "
            "'get_object_tree' ile belgenizdeki nesnelere bakın."
        ),
    ),
    (
        re.compile(r"Boolean operation failed", re.IGNORECASE),
        lambda _: (
            "Boolean operasyonu başarısız oldu. "
            "İki nesnenin gerçekten kesişip kesişmediğini kontrol edin; "
            "nesneleri biraz örtüştürmek sorunu çözebilir."
        ),
    ),
    (
        re.compile(r"FreeCAD RPC sunucusuna bağlanılamadı", re.IGNORECASE),
        lambda _: (
            "FreeCAD'e bağlanılamadı. FreeCAD açık ve "
            "'freecad_rpc_server.py' çalışır durumda olmalı. "
            "Makro menüsünden sunucuyu başlatın."
        ),
    ),
    (
        re.compile(r"ConnectionRefusedError", re.IGNORECASE),
        lambda _: (
            "FreeCAD RPC bağlantısı reddedildi. "
            "FreeCAD'in açık ve RPC sunucusunun port 9875'te dinlediğinden emin olun."
        ),
    ),
    (
        re.compile(r"Part::NullShapeException", re.IGNORECASE),
        lambda _: (
            "Geçersiz (boş) geometri oluştu. "
            "Boyutların sıfırdan büyük olduğunu ve sketch'in doğru kapandığını kontrol edin."
        ),
    ),
    (
        re.compile(r"Pad.*failed|Pocket.*failed", re.IGNORECASE),
        lambda _: (
            "Pad/Pocket işlemi başarısız. "
            "Sketch'in tüm geometrileri kapalı profil oluşturduğundan ve "
            "ekstrüzyon yönünün doğru olduğundan emin olun."
        ),
    ),
]


def enrich_error(raw_message: str) -> str:
    """Ham hata mesajını LLM dostu bir mesaja çevirir."""
    for pattern, builder in _ERROR_PATTERNS:
        m = pattern.search(raw_message)
        if m:
            return builder(m) if callable(builder) else builder
    # Hiçbir kalıp eşleşmezse orijinal mesajı döndür ama biraz formatla
    return f"FreeCAD hatası: {raw_message.strip()}"
