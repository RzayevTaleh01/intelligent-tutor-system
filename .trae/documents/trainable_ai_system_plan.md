# Təlimləndirilə Bilən AI Sistemi Planı (Trainable AI Backbone)

Bu plan, mövcud "onurğa" (backbone) sistemini istənilən fənn (məs. Python, Universitet kursları) üzrə materiallar yükləməklə "öyrədilə bilən" tam funksional platformaya çevirmək üçündür.

## Hədəf
Sistemi elə bir hala gətirmək ki, kod yazmadan, sadəcə PDF/Material yükləməklə yeni bir "Learning Plugin" (Tədris Modulu) yaradılsın və tələbələrə adaptiv şəkildə tədris edilsin.

---

## Mərhələ 1: Memarlıq və Verilənlər Bazası (Core & DB)
Sistemin dinamik olması üçün "Kurs" anlayışını bazaya əlavə etməliyik.

- [ ] **DB Modelinin Genişləndirilməsi:**
    - `courses` cədvəli: `id`, `title`, `description`, `settings` (JSON - pedaqoji qaydalar).
    - `knowledge_sources` cədvəlinə `course_id` əlaqəsi əlavə etmək.
    - `sessions` cədvəlinə `course_id` əlavə etmək (Tələbə hansı kursu oxuyur).
- [ ] **Universal Plugin (`GenericPlugin`) Yaradılması:**
    - Hazırkı `DefaultPlugin`-i təkmilləşdirərək, statik kod əvəzinə DB-dən oxuyan `ConfigurablePlugin` yaratmaq.
    - Bu plugin, verilən `course_id`-ə əsasən RAG (Knowledge Base) və Pedaqoji Qaydaları dinamik yükləyəcək.

## Mərhələ 2: "Müəllim" Modulu (AI Curriculum Builder)
Sistemin "öyrənməsi" üçün materialları analiz edib struktur qurması lazımdır.

- [ ] **Material Yükləmə API-si (`/admin/courses/{id}/upload`):**
    - Faylların (PDF, TXT) qəbulu və `KnowledgeEngine` vasitəsilə indekslənməsi.
- [ ] **Kurikulum Generatoru (AI Agent):**
    - Yüklənmiş materialları analiz edən arxa fon prosesi.
    - **Çıxış:** Mövzular Ağacı (Topic Graph) və Hər mövzu üçün Açar Konseptlər.
    - Bu struktur avtomatik olaraq bazaya (`learner_skills` və ya yeni `course_topics` cədvəlinə) yazılacaq.

## Mərhələ 3: Dinamik Tədris Prosesi (Runtime)
Sistemin işləmə vaxtı (runtime) kursları tanıması.

- [ ] **Dinamik Registry:**
    - `PluginRegistry` sistem işə düşəndə (`startup`) bazadakı bütün aktiv kursları `GenericPlugin` instansiyası kimi qeydiyyata almalıdır.
- [ ] **Sessiya İdarəetməsi:**
    - Tələbə yeni sessiya yaradanda (`POST /sessions`) mütləq `course_id` seçməlidir.
    - Chat və Sual-Cavab zamanı AI yalnız həmin kursun materiallarına (RAG) istinad etməlidir.

## Mərhələ 4: Frontend (Next.js)
İstifadəçi interfeysinin bu yeni funksionallığa uyğunlaşdırılması.

- [ ] **Admin/Müəllim Paneli:**
    - "Create New Course" səhifəsi.
    - Fayl Yükləmə (Drag & Drop).
    - "Generate Curriculum" düyməsi və status barı.
- [ ] **Tələbə Paneli:**
    - Kurs Seçimi Dashboard-u.
    - Seçilmiş kursa uyğun adaptiv dərs ekranı.

---

## İcra Ardıcıllığı (İlk Addımlar)
1.  `src/db/models_course.py` yaradılması və `Course` modelinin əlavə edilməsi.
2.  `src/core/plugin/generic_plugin.py` yaradılması (Universal məntiq).
3.  `src/api/routers/course.py` əlavə edilməsi (CRUD əməliyyatları).
4.  Mövcud `main.py` və `PluginRegistry`-nin DB-dən oxuyacaq şəkildə yenilənməsi.
