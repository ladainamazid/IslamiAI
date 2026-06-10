# File: formatter.py
# Format output dengan 3 text fields: arabic | transliteration | translation
# Phase A.5: tambah seksi _kitab_hits untuk _source='kitab_corpus'

# ── Lookup tables ────────────────────────────────────────────────────────────

_AUTHORITY_LABELS = {
    1: "Qawl Imam (Al-Imam al-Syafi'i)",
    2: "Qawl Ashhab",
    3: "Mu'tamad",
    4: "Syarh Mu'tamad",
    5: "Tafsir Ahkam / Qawa'id Fiqhiyyah",
}

_SLUG_TO_NAME = {
    # Tafsir Ahkam
    "al_kiya_al_harrasi":      "Ahkam al-Qur'an (Al-Kiya al-Harrasi)",
    "al_qurtubi":              "Al-Jami' li Ahkam al-Qur'an (Al-Qurtubi)",
    "al_jassas":               "Ahkam al-Qur'an (Al-Jassas)",
    "ibn_kathir":              "Tafsir Ibn Kathir",
    "ibn_ashur":               "Al-Tahrir wa al-Tanwir (Ibn Ashur)",
    # Fiqh Syafi'i — Qawl Imam (level 1)
    "al_umm":                  "Al-Umm (Al-Imam al-Syafi'i)",
    "al_risalah":              "Al-Risalah (Al-Imam al-Syafi'i)",
    # Qawl Ashhab (level 2)
    "mukhtasar_al_muzani":     "Mukhtasar al-Muzani",
    # Mu'tamad (level 3)
    "minhaj_al_talibin":       "Minhaj al-Talibin (Al-Nawawi)",
    "rawdhat_al_talibin":      "Rawdhat al-Talibin (Al-Nawawi)",
    "al_majmu":                "Al-Majmu' Syarh al-Muhadhdhab (Al-Nawawi)",
    "al_hawi_al_kabir":        "Al-Hawi al-Kabir (Al-Mawardi)",
    # Syarh Mu'tamad (level 4)
    "tuhfat_al_muhtaj":        "Tuhfat al-Muhtaj (Ibn Hajar al-Haytami)",
    "nihayat_al_muhtaj":       "Nihayat al-Muhtaj (Al-Ramli)",
    "mughni_al_muhtaj":        "Mughni al-Muhtaj (Al-Khatib al-Syarbini)",
    "asna_al_matalib":         "Asna al-Matalib (Zakariyya al-Anshari)",
    "fath_al_muin":            "Fath al-Mu'in (Al-Malibari)",
    "fath_al_wahhab":          "Fath al-Wahhab (Zakariyya al-Anshari)",
    "ianat_al_talibin":        "I'anat al-Talibin (Al-Bakri al-Dimyathi)",
    "irshad_al_faqih":         "Irshad al-Faqih (Ibn al-Naqib)",
    "bughyat_al_mustarsyidin": "Bughyat al-Mustarsyidin (Al-Hadrami)",
    "hasyiyah_al_bajuri":      "Hasyiyah al-Bajuri",
    # Qawa'id Fiqhiyyah (level 5)
    "al_ashbah_al_suyuthi":    "Al-Ashbah wa al-Nazha'ir (Al-Suyuthi)",
    "al_ashbah_al_zarkasyi":   "Al-Mantsur fi al-Qawa'id (Al-Zarkasyi)",
    "qawaid_al_izz":           "Qawa'id al-Ahkam (Al-'Izz ibn Abd al-Salam)",
    # Baghawi
    "al_baghawi":              "Syarh al-Sunnah (Al-Baghawi)",
}

_ARABIC_TEXT_MAX_CHARS = 280   # potong teks panjang dari EPUB


def _book_display_name(slug: str) -> str:
    """Kembalikan nama tampilan dari slug; fallback ke title-case slug."""
    return _SLUG_TO_NAME.get(slug, slug.replace("_", " ").title())


def _authority_label(level: int) -> str:
    return _AUTHORITY_LABELS.get(level, f"Level {level}")


def _truncate_arabic(text: str, max_chars: int = _ARABIC_TEXT_MAX_CHARS) -> str:
    """Potong teks Arab panjang dengan indikator."""
    if not text or len(text) <= max_chars:
        return text
    cut = text[:max_chars].rsplit(" ", 1)[0]
    return cut + " ..."


# ── Formatter utama ──────────────────────────────────────────────────────────

def format_answer(retrieval_result):
    """
    Format output jawaban.

    Mendukung dua path:
    1. Layer 1-3 (_source: static_rules / keyword_search / cache_extended)
       -> tampilkan HUKUM, Quran, Hadis, Penjelasan
    2. Layer 4  (_source: kitab_corpus)
       -> tampilkan header ringkas + seksi RUJUKAN KITAB
    """
    if retrieval_result is None:
        return (
            "Maaf, pertanyaan ini belum ada di database kami. "
            "Silakan tanya kepada ulama setempat."
        )

    source = retrieval_result.get("_source", "")

    if source == "kitab_corpus":
        return _format_kitab_answer(retrieval_result)

    return _format_standard_answer(retrieval_result)


# ── Format standard (Layer 1-3) ──────────────────────────────────────────────

def _format_standard_answer(retrieval_result):
    output = []
    output.append("=" * 70)
    output.append(f"HUKUM: {retrieval_result['ruling'].upper()}")
    output.append(f"MADHAB: {retrieval_result['madhab']}")
    output.append("=" * 70)

    # Ayat Quran
    if retrieval_result.get("quran"):
        output.append("\nDASAR AL-QUR'AN:\n")
        for idx, q in enumerate(retrieval_result["quran"], 1):
            ayah_ref = q.get("surah_ayah", q.get("reference", ""))
            output.append(f"  [{idx}] QS. {ayah_ref}")

            if q.get("arabic_text") and q["arabic_text"] != "[akan ditambahkan]":
                output.append(f"      {q['arabic_text']}")

            if q.get("transliteration"):
                output.append(f"      Transliterasi: {q['transliteration']}")

            if q.get("translation"):
                output.append(f"      Terjemahan: {q['translation']}")

            output.append("")

    # Hadis
    if retrieval_result.get("hadis"):
        output.append("\nDASAR HADIS:\n")
        for idx, h in enumerate(retrieval_result["hadis"], 1):
            hadis_source = h.get("source", h.get("reference", ""))
            output.append(f"  [{idx}] {hadis_source}")

            if h.get("arabic_text") and h["arabic_text"] != "[akan ditambahkan]":
                output.append(f"      {h['arabic_text']}")

            if h.get("transliteration"):
                output.append(f"      Transliterasi: {h['transliteration']}")

            if h.get("translation"):
                output.append(f"      Terjemahan: {h['translation']}")

            output.append("")

    # Penjelasan
    output.append("\nPENJELASAN:")
    output.append(f"  {retrieval_result.get('reasoning', '')}")
    output.append("\n" + "=" * 70)

    return "\n".join(output)


# ── Format kitab_corpus (Layer 4) ────────────────────────────────────────────

def _format_kitab_answer(retrieval_result):
    """
    Format khusus hasil FTS5 dari kitab_corpus.
    Tidak ada ruling/quran/hadis terstruktur — hanya teks kutipan kitab.
    """
    kitab_hits = retrieval_result.get("_kitab_hits", [])
    madhab = retrieval_result.get("madhab", "shafii")

    output = []
    output.append("=" * 70)
    output.append("SUMBER: Kitab Korpus Klasik (28 Kitab)")
    output.append(f"MADHAB: {madhab.title()}")
    output.append("=" * 70)

    if not kitab_hits:
        output.append("\n[Tidak ada teks kitab yang relevan ditemukan.]\n")
        output.append("=" * 70)
        return "\n".join(output)

    output.append(f"\nRUJUKAN KITAB: ({len(kitab_hits)} temuan)\n")

    for idx, hit in enumerate(kitab_hits, 1):
        slug    = hit.get("book_slug", "")
        level   = hit.get("authority_level", 5)
        chapter = hit.get("chapter_title", "")
        page    = hit.get("page_ref", "")
        arabic  = _truncate_arabic(hit.get("arabic_text", ""))

        name  = _book_display_name(slug)
        label = _authority_label(level)

        output.append(f"  [{idx}] {name}")
        output.append(f"       {label}  |  Level {level}")

        if chapter:
            output.append(f"       Bab  : {chapter}")
        if page:
            output.append(f"       Hal  : {page}")

        if arabic:
            output.append(f"       {'-' * 50}")
            output.append(f"       {arabic}")
            output.append(f"       {'-' * 50}")

        output.append("")

    output.append("=" * 70)
    return "\n".join(output)


if __name__ == "__main__":
    print("── Test Layer 1-3 (standard) ──")
    mock_standard = {
        "_source": "static_rules",
        "ruling": "wajib",
        "madhab": "shafii",
        "quran": [{"surah_ayah": "2:183", "arabic_text": "يَا أَيُّهَا الَّذِينَ آمَنُوا",
                   "transliteration": "Yaa ayyuhalladzii...",
                   "translation": "Wahai orang-orang yang beriman..."}],
        "hadis": [{"source": "HR. Bukhari no. 8", "arabic_text": "بُنِيَ الْاِسْلَامُ",
                   "transliteration": "Buniya al-Islamu...",
                   "translation": "Islam dibangun..."}],
        "reasoning": "Shalat lima waktu adalah rukun Islam.",
    }
    print(format_answer(mock_standard))

    print("\n── Test Layer 4 (kitab_corpus) ──")
    mock_kitab = {
        "_source": "kitab_corpus",
        "ruling": "",
        "madhab": "shafii",
        "quran": [],
        "hadis": [],
        "_kitab_hits": [
            {"book_slug": "tuhfat_al_muhtaj", "authority_level": 4,
             "chapter_title": "بَابُ الطَّهَارَةِ", "page_ref": "45",
             "arabic_text": "وَيَجِبُ النِّيَّةُ فِي الْوُضُوءِ"},
            {"book_slug": "al_umm", "authority_level": 1,
             "chapter_title": "كِتَابُ الطَّهَارَةِ", "page_ref": "12",
             "arabic_text": "قَالَ الشَّافِعِيُّ وَلَا وُضُوءَ اِلَّا بِنِيَّةٍ"},
        ],
    }
    print(format_answer(mock_kitab))
