FreeCAD ve Model Context Protocol (MCP) Entegrasyonu: Büyük Dil Modelleri İçin Optimize Edilmiş Otonom CAD Mimarisinin Teknik Analizi
Bilgisayar destekli tasarım (CAD) disiplini, üretken yapay zeka ve büyük dil modellerinin (LLM) yükselişiyle birlikte köklü bir transformasyon sürecine girmiştir. Geleneksel olarak manuel etkileşime, karmaşık arayüz hiyerarşilerine ve derin teknik uzmanlığa dayanan tasarım süreçleri, Model Context Protocol (MCP) gibi açık standartlar aracılığıyla otonom sistemler tarafından yönetilebilir hale gelmektedir. FreeCAD, açık kaynaklı yapısı ve Python temelli genişletilebilir mimarisi sayesinde, bu yeni nesil yapay zeka odaklı tasarım ekosistemleri için birincil aday konumundadır. Bu rapor, FreeCAD platformu için bir MCP sunucusu tasarlarken izlenmesi gereken en iyi mimari uygulamaları, veri serileştirme stratejilerini ve LLM akıl yürütme döngülerini optimize eden çok katmanlı yapıları teknik bir derinlikle incelemektedir.   

Model Context Protocol (MCP) Temelleri ve Mimari Bileşenler
Model Context Protocol, LLM uygulamaları ile harici veri kaynakları ve araçlar arasında standartlaştırılmış, güvenli ve ölçeklenebilir bir köprü kurmayı amaçlayan bir protokoldür. MCP, yapay zeka modellerinin "kapalı kutu" doğasını kırarak, onların gerçek dünya sistemleriyle (bu senaryoda bir CAD çekirdeğiyle) etkileşime girmesine olanak tanır. Protokolün temel felsefesi, dil modeline sadece metin üretme yetisi değil, aynı zamanda fiziksel dünyadaki nesneleri manipüle edebilecek araçları (tools) ve bu araçların çalıştığı ortamın bağlamını (resources) sağlama prensibine dayanır.   

MCP Ekosisteminin Katılımcıları

MCP mimarisi üç temel aktör üzerinden işler: Host, Client ve Server. FreeCAD entegrasyonu özelinde bu aktörlerin rolleri şu şekilde tanımlanabilir:   

Tablo 1: MCP Mimarisi ve FreeCAD Entegrasyon Rolleri

Aktör	Tanım	FreeCAD Uygulama Rolü
MCP Host	
Bağlantıyı başlatan ve koordine eden ana yapay zeka uygulaması.

Claude Desktop, ChatGPT, VS Code veya Cursor gibi IDE'ler.

MCP Client	
Sunucuyla bağlantıyı sürdüren ve bağlamı Host'a ileten bileşen.

Host uygulama içindeki yerleşik konnektörler veya SDK tabanlı istemciler.

MCP Server	
Yetenekleri ve verileri (Tools, Resources) sunan servis.

FreeCAD API'sine erişen ve yetenekleri JSON-RPC üzerinden açan program.

  
Bu katılımcılar arasındaki iletişim, JSON-RPC 2.0 mesajlaşma formatı kullanılarak gerçekleştirilir. Bu durum, ağ gecikmelerini minimize eden ve tip güvenliğini artıran bir yapı sunar. Sunucu, istemciye hangi araçların (tools) kullanılabileceğini bildirdiğinde, bu araçlar bir inputSchema ile birlikte gelir. Bu şema, modelin geçersiz veri (örneğin milimetre cinsinden bir ölçü beklenen yere metin yazılması) göndermesini engelleyen bir doğrulama katmanı sağlar.   

FreeCAD Python API ve Programlanabilir Erişim Katmanı
FreeCAD'in en belirgin özelliği, çekirdek fonksiyonlarının neredeyse %100'ünün Python API'si aracılığıyla erişilebilir olmasıdır. Bu, bir MCP sunucusu için mükemmel bir zemin hazırlar, çünkü sunucu katmanı dil modelinden gelen doğal dil isteklerini doğrudan çalıştırılabilir Python betiklerine dönüştürebilir.   

Grafik Arayüzü ve Headless Mod Ayırımı

Bir MCP mimarisi tasarlanırken verilecek en kritik karar, FreeCAD'in nasıl çalıştırılacağıdır. Geleneksel kullanıcı deneyimi grafik arayüz (GUI) odaklı olsa da, otonom sistemler için "Headless" (arayüzsüz) çalışma modları kritik öneme sahiptir.   

Tablo 2: FreeCAD Çalışma Modlarının Karşılaştırmalı Teknik Özellikleri

Mod	Başlatma Komutu	Bellek Tüketimi	Görsel Destek	Tipik Kullanım
GUI Mode	FreeCAD	Yüksek	Tam (3D Görünüm)	
Geliştirme ve görsel doğrulama.

Console Mode	FreeCAD -c	Orta	Yok	
Hızlı prototipleme ve test.

Headless Mode	FreeCADCmd	Düşük	Yok	
Otomasyon, CI/CD ve uzak sunucular.

Lib/Embedded	import FreeCAD	Çok Düşük	Yok	
Python süreçleri içine gömülü sistemler.

  
Mevcut araştırma verileri, otonom CAD ajanları için hibrit bir yaklaşımın en iyisi olduğunu göstermektedir. Geliştirme aşamasında GUI modu, modelin ne ürettiğini kullanıcının görmesini sağlarken; üretim ortamında FreeCADCmd kullanılarak sunucu kaynaklarından tasarruf edilir.   

Tasarım Primitifleri: Tools, Resources ve Prompts
Bir FreeCAD MCP sunucusu, yeteneklerini üç ana başlık altında toplamalıdır. Bu yapı, LLM'nin FreeCAD'i tıpkı bir insan tasarımcı gibi kullanabilmesini sağlar.   

Araçlar (Tools): Geometrik Operasyonlar

Araçlar, modelin gerçekleştirebileceği eylemlerdir. Etkili bir mimari, dil modeline hem atomik (düşük seviyeli) hem de makro (yüksek seviyeli) araçlar sunmalıdır.   

Belge Yönetimi: create_document, save_document, close_document gibi temel dosya sistemi operasyonları.   

Geometrik Primitifler: create_box, create_cylinder, create_sphere gibi doğrudan katı oluşturma komutları.   

Taslak ve Kısıtlamalar: create_sketch, add_geometry, add_constraint gibi Sketcher Workbench tabanlı operasyonlar.   

Modifikasyonlar: pad, pocket, fillet, chamfer gibi mevcut katıları dönüştüren işlemler.   

Serbest Kod Yürütme: execute_code aracı, modelin standart kütüphanelerde olmayan karmaşık Python betiklerini doğrudan FreeCAD içinde çalıştırmasına olanak tanır.   

Kaynaklar (Resources): Bağlamsal Veriler

Kaynaklar, modelin tasarımın mevcut durumunu anlaması için ihtiyaç duyduğu salt okunur bilgilerdir.   

Nesne Ağacı: Belgedeki tüm nesnelerin hiyerarşik yapısı ve özellikleri.   

Geometrik Veri (B-Rep): Nesnelerin yüzey, kenar ve köşe bilgileri.   

Sistem Bilgisi: Desteklenen modüller, yüklü eklentiler ve çalışma birimleri (mm, inç vb.).   

İstemi (Prompts): İş Akışı Şablonları

Prompts, karmaşık görevleri basitleştiren önceden tanımlanmış şablonlardır. Örneğin, "Standart bir M5 cıvatası oluştur" veya "Mevcut parçayı 3D baskı için optimize et" gibi istemler, modelin karmaşık parametreleri doğru set etmesine yardımcı olur.   

Teknik Mimari: Uzaktan Prosedür Çağrısı (RPC) ve Soket Yönetimi
FreeCAD ve MCP sunucusu arasındaki iletişim katmanı, sistemin stabilitesi ve hızı için kritiktir. Mevcut "Robust MCP Server" gibi başarılı projeler, çoklu bağlantı modlarını destekleyerek farklı kullanım senaryolarına uyum sağlar.   

Bağlantı Modları ve Protokol Analizi

Mimari tasarımda tercih edilebilecek üç temel bağlantı modu bulunmaktadır:

Tablo 3: RPC ve Bağlantı Modu Karşılaştırması

Mod	Mekanizma	Platform Desteği	Gecikme	Notlar
XML-RPC	
HTTP tabanlı uzaktan çağrı.

Tüm Platformlar	
Orta.

Kurulumu en basit, en stabil moddur.

Socket (JSON-RPC)	
Ham TCP soketleri.

Tüm Platformlar	
Düşük.

Performans kritik uygulamalar için idealdir.

Embedded	
Doğrudan süreç içi import.

Sadece Linux	Çok Düşük	
macOS/Windows'ta ABI uyumluluk sorunları yaşar.

  
XML-RPC modunda, 127.0.0.1 üzerinden iletişim kurmak, localhost çözümlemesinden kaynaklanan gecikmeleri ortadan kaldırarak performansı saniyede 1 çağrıdan 1000 çağrıya kadar çıkarabilir. Bu, CAD operasyonları gibi yüzlerce küçük komutun ardışık olarak yürütüldüğü senaryolarda hayati önem taşır.   

Geometrik Veri Temsili ve B-Rep Serileştirme Zorlukları
LLM'lerin bir CAD modelini "anlaması" için metin tabanlı bir temsil gereklidir. Ancak FreeCAD'in dahili veri yapıları (OpenCASCADE nesneleri) JSON formatına doğrudan uygun değildir.   

Vektör ve Şekil Serileştirme Problemi

FreeCAD'in Base.Vector nesnesi standart Python json kütüphanesi tarafından doğrudan serileştirilemez. Bu durum, bir MCP sunucusu tasarlanırken verilerin dönüştürülmesini zorunlu kılar. En iyi uygulama, vektörleri (x, y, z) şeklinde demetlere (tuples) veya listelere dönüştürmek ve istemci tarafında tekrar yapılandırmaktır.   

B-Rep (Boundary Representation) ve LLM Bağlamı

Boundary Representation (B-Rep), bir katının yüzeyler, kenarlar ve köşeler aracılığıyla tanımlanmasıdır. LLM'lere bu veriyi aktarırken tüm B-Rep ağacını göndermek token sınırlarını zorlayabilir. Modern araştırmalar, "Pointer-CAD" gibi yaklaşımları önermektedir; bu yaklaşımda geometri bir "Yüz-Komşuluk Grafiği" (Face-Adjacency Graph) olarak temsil edilir.   

LaTeX ile B-Rep Örnekleme Formülasyonu

Geometrik ipuçlarını çıkarmak için yüzeyler genellikle bir (u,v) parametrik alanı üzerinden örneklenir. Bir S(u,v) yüzeyi üzerindeki N×N ızgara örneklemesi şu şekilde ifade edilebilir:

P 
i,j
​	
 =S(u 
min
​	
 + 
N
i
​	
 (u 
max
​	
 −u 
min
​	
 ),v 
min
​	
 + 
N
j
​	
 (v 
max
​	
 −v 
min
​	
 ))
Bu örnekleme noktaları, yüzey normalleri ve Gauss eğriliği ile birleştirilerek LLM'ye zengin bir mekansal bağlam sunulur.   

Çok Modlu (Multimodal) Geri Bildirim Döngüleri
LLM'lerin 3D uzaydaki akıl yürütme yetenekleri, sadece metinle sınırlı kaldığında "mekansal halüsinasyonlara" yol açabilir. Bu sorunu çözmek için mimariye görsel bir doğrulama katmanı eklenmelidir.   

Görsel Doğrulama Mimarisi

Bir LLM ajanı bir komut yürüttüğünde (örneğin "delik aç"), süreç şu döngüyle devam etmelidir:

Eylem: Model Python kodunu gönderir ve sunucu kodu FreeCAD içinde yürütür.   

Gözlem: Sunucu, aktif görünümün bir ekran görüntüsünü alır (get_view).   

Analiz: Ekran görüntüsü, multimodal bir modele (örneğin GPT-4o veya Claude 3.5 Sonnet) gönderilir.   

Hata Giderme: Model, görseli analiz ederek "Delik yanlış yerde" veya "Parça kendini kesiyor" gibi tespitlerde bulunur ve kodu revize eder.   

Tablo 4: Görsel Geri Bildirim Veri İletim Stratejileri

Yöntem	Mekanizma	Avantaj	Dezavantaj
Base64 Encoding	
Görüntü verisini doğrudan JSON içine gömer.

Tek mesajda iletim, kolay entegrasyon.

Mesaj boyutunu büyütür, performansı düşürür.

Local File URI	
Görüntüyü diske kaydeder ve bir URL döner.

Düşük bellek kullanımı, CDN desteği.

İstemcinin dosya sistemine erişimi gerekir.

  
En iyi uygulama, görüntüyü geçici bir dizine kaydedip modelin bu görüntüye referans vermesini sağlamaktır; ancak doğrudan sohbet arayüzlerinde Base64 kullanımı daha hızlı prototipleme sunar.   

Güvenlik, İzole Çalışma ve Konteynerizasyon
LLM'lerin sistem üzerinde keyfi Python kodu çalıştırmasına izin vermek (arbitrary code execution), ciddi güvenlik riskleri barındırır. Bu riskleri minimize etmek için MCP sunucusu ve FreeCAD'in izole edilmiş bir ortamda çalıştırılması şarttır.   

Dockerized FreeCAD Sunucusu

FreeCAD'i bir Docker konteyneri içinde çalıştırmak, hem bağımlılıkların yönetilmesini sağlar hem de ana sistemi zararlı kodlardan korur. lscr.io/linuxserver/freecad gibi görüntüler, hem GUI desteği (VNC/Kasm üzerinden) hem de headless operasyonlar için optimize edilmiştir.   

Sandboxing Prensipleri

Gelişmiş bir mimaride şu güvenlik önlemleri uygulanmalıdır:

İşlem Sınırlandırma: Konteynerin CPU ve RAM kullanımı docker-compose üzerinden kısıtlanmalıdır.   

Ağ İzolasyonu: MCP sunucusunun dış internete erişimi kapatılmalı, sadece localhost veya belirli IP'ler üzerinden gelen RPC çağrılarını kabul etmelidir.   

Dosya Sistemi Kısıtlaması: FreeCAD'in sadece belirli bir "çalışma dizinine" (workspace) yazma izni olmalıdır.   

GVisor veya Kata Containers: Daha yüksek güvenlik gereksinimleri için kullanıcı alanı çekirdek izolasyonu sağlayan gVisor gibi teknolojiler tercih edilebilir.   

Ajan Tabanlı İş Akışları ve Kendi Kendini Düzeltme (Self-Correction)
LLM CAD entegrasyonu, sadece komut göndermekten ibaret değildir; bu, iteratif bir problem çözme sürecidir. Bir tasarımın başarıyla tamamlanması için ajanın "Düşün-Uygula-Gözlemle-Düzelt" döngüsünü otonom olarak yürütebilmesi gerekir.   

Hata Mesajlarının LLM Dostu Hale Getirilmesi

Standart Python traceback mesajları dil modelleri için kafa karıştırıcı olabilir. Başarılı bir MCP sunucusu, FreeCAD hatalarını yakalayıp onları semantik olarak zenginleştirmelidir.   

Ham Hata: Sketcher::ConstraintError: Multiple constraints on edge 4

Zenginleştirilmiş Hata: "4 numaralı kenara paralellik kısıtlaması eklenemedi çünkü zaten dikey olarak kısıtlanmış durumda. Lütfen mevcut kısıtlamaları kontrol edin veya çelişen kısıtlamayı kaldırın".   

Bu tür bir geri bildirim, ajanın halüsinasyona düşmesini engeller ve doğru çözüme çok daha hızlı ulaşmasını sağlar.   

Tablo 5: Ajan Geri Bildirim Döngüsü Bileşenleri

Döngü Aşaması	İşlem	Araç/Teknik
Planlama	
Karmaşık talebi küçük adımlara böler.

stepPlanning Ajanı.

Yürütme	
Python kodunu oluşturur ve çalıştırır.

execute_code Tool.

Doğrulama	
Çıktıyı geometrik ve görsel olarak denetler.

visualInspection Ajanı.

Refleksiyon	
Hatalardan ders çıkarır ve planı günceller.

self-reflection döngüsü.

  
Bellek ve Bağlam Yönetimi (Memory & Context Management)
LLM'lerin sınırlı bir bağlam penceresi (context window) vardır. Çok uzun süren CAD tasarım seanslarında, her adımda tüm geçmişi ve tüm nesne listesini modele göndermek hem maliyeti artırır hem de akıl yürütme kalitesini düşürür.   

Akıllı Bağlam Stratejileri

Özetleme: Geçmiş tasarım adımları belirli aralıklarla özetlenmeli ve modelin belleği tazelenmelidir.   

Vektör Veritabanı Entegrasyonu: Karmaşık projelerde, FreeCAD dokümantasyonu veya geçmiş tasarım desenleri bir vektör veritabanında (RAG) tutularak sadece ihtiyaç duyulan kısımlar modele sunulmalıdır.   

Lazy Loading: Model sadece üzerinde çalıştığı nesnenin (örneğin belirli bir Sketch veya Body) detaylı bilgilerini çekmeli, diğer nesneleri sadece isim bazında görmelidir.   

Sonuç ve Mimari Öneriler
FreeCAD için bir Model Context Protocol (MCP) sunucusu tasarlarken, sistemin sadece bir "kod yürütücü" değil, aynı zamanda bir "geometrik danışman" olması hedeflenmelidir. Analiz edilen veriler ışığında, en iyi mimari şu özelliklere sahip olmalıdır:

Hibrit Bağlantı Katmanı: Hız için ham soketleri (JSON-RPC), geniş uyumluluk için XML-RPC'yi destekleyen çok modlu bir sunucu yapısı kurulmalıdır.   

Konteynerize Güvenlik: Tüm FreeCAD süreçleri Docker içinde izole edilmeli ve kaynak sınırları net bir şekilde tanımlanmalıdır.   

Çok Modlu Doğrulama: Ajanın mekansal hatalarını yakalamak için ekran görüntüleri üzerinden görsel geri bildirim döngüleri (Visual Feedback Loops) mimariye entegre edilmelidir.   

Zenginleştirilmiş Semantik: FreeCAD'in teknik hata mesajları ve B-Rep verileri, LLM'lerin anlayabileceği yapılandırılmış JSON veya doğal dil formatına dönüştürülmelidir.   

Ajanik Akıl Yürütme: Sistemin "Düşün-Uygula-Refleksiyon Yap" döngüsünü destekleyen bir istem (prompt) ve araç (tool) seti ile donatılması sağlanmalıdır.   

Bu mimari yaklaşımlar, FreeCAD'i sadece bir CAD yazılımı olmaktan çıkarıp, otonom yapay zeka ajanlarının karmaşık mühendislik tasarımlarını sıfırdan oluşturabildiği, optimize edebildiği ve doğrulayabildiği akıllı bir üretim motoruna dönüştürecektir. Gelecekte, CAD'e özel eğitilmiş LLM'lerin (Pointer-CAD vb.) bu MCP mimarilerine doğrudan entegrasyonuyla, tasarım süreçlerindeki insan müdahalesi sadece yüksek seviyeli "niyet" belirleme seviyesine indirgenebilecektir.   

