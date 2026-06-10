#!/usr/bin/env python3
"""
cek_status.py — IslamiAI Corpus Status Checker
═══════════════════════════════════════════════
Mengecek status 30 kitab korpus di folder corpus/epub/.
Mendeteksi file dengan nama lama dan menyarankan rename.

Cara pakai:
  cd /home/muhammad/IslamiAI/IslamiAIProject
  python3 tools/cek_status.py
"""

import sys
from pathlib import Path

# ── Path ────────────────────────────────────────────────────────────────────
SCRIPT_DIR  = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
EPUB_DIR    = PROJECT_DIR / "corpus" / "epub"

# ── Registry 30 Kitab ───────────────────────────────────────────────────────
# Format: (key, label_tampilan, shamela_id, [nama_file_lama_jika_ada])
KITAB = [
    # ── Tafsir Ahkam ──────────────────────────────────────────────────────
    ("al_kiya_harrasi_ahkam_quran",   "Ahkam al-Quran — Al-Kiya al-Harrasi",               23582, []),
    ("al_baihaqi_ahkam_quran_syafii", "Ahkam al-Quran al-Syafi'i — Al-Baihaqi",            92,    []),
    ("al_qurtubi_jami_ahkam_quran",   "Al-Jami' li Ahkam al-Quran — Al-Qurtubi",           20855, []),
    ("al_jassas_ahkam_quran",         "Ahkam al-Quran — Al-Jassas",                        7370,  []),
    ("al_baghawi_maalim_tanzil",      "Ma'alim al-Tanzil — Al-Baghawi",                    41,    []),
    ("ibn_kathir_tafsir_quran_azhim", "Tafsir al-Quran al-Azhim — Ibn Kathir",             8473,  []),
    ("ibn_kathir_irsyad_faqih",       "Irshad al-Faqih — Ibn Kathir",                      260,   []),
    ("al_mawardi_nukat_uyun",         "Al-Nukat wa'l-Uyun — Al-Mawardi",                  8346,  []),
    ("ibn_ashur_tahrir_tanwir",       "Al-Tahrir wa'l-Tanwir — Ibn Ashur",                 9776,  []),

    # ── Fiqh Syafi'i — Qawl Imam ──────────────────────────────────────────
    ("al_umm_syafii",                 "Al-Umm — Al-Syafi'i",                               1655,  []),
    ("al_risalah_syafii",             "Al-Risalah — Al-Syafi'i",                           8180,  []),
    ("mukhtasar_al_muzani",           "Mukhtasar al-Muzani",                               914,   []),

    # ── Fiqh Syafi'i — Mu'tamad ───────────────────────────────────────────
    ("minhaj_al_talibin_nawawi",      "Minhaj al-Talibin — Al-Nawawi",                    12096, []),
    ("rawdhat_al_talibin_nawawi",     "Rawdhat al-Talibin — Al-Nawawi",                   499,   []),
    ("al_majmu_syarh_muhadhdhab_nawawi", "Al-Majmu' — Al-Nawawi",                        2186,  []),
    ("nihayat_al_matlab_juwaini",     "Nihayat al-Matlab — Al-Juwayni",                   9851,  []),

    # ── Fiqh Syafi'i — Sharh Mu'tamad ────────────────────────────────────
    ("tuhfat_al_muhtaj_ibn_hajar",    "Tuhfat al-Muhtaj — Ibn Hajar",                     9059,  []),
    ("nihayat_al_muhtaj_al_ramli",    "Nihayat al-Muhtaj — Al-Ramli",                     3565,  []),
    ("mughni_al_muhtaj_syarbini",     "Mughni al-Muhtaj — Al-Syarbini",                  11444, []),
    ("asna_al_matalib_zakariyya",     "Asna al-Matalib — Zakariyya al-Ansari",           11468, []),
    ("al_hawi_al_kabir_mawardi",      "Al-Hawi al-Kabir — Al-Mawardi",                   6157,  []),
    ("fath_al_aziz_rafii",            "Fath al-Aziz (DKI) — Al-Rafi'i",                  13577,
     # alias: nama lama dari download manual sebelum rename
     ["al_rafii_fath_al_aziz_dki", "al_rafii_fath_al_aziz"]),

    # ── Fiqh Syafi'i — Rantai Pesantren ──────────────────────────────────
    ("fath_al_qarib_ibn_qasim",       "Fath al-Qarib — Ibn Qasim al-Ghazzi",             35120, []),
    ("al_iqna_shirbini",              "Al-Iqna' fi Hall Alfadh Abi Shuja' — Al-Shirbini", 6121,
     # alias: nama lama dari download manual yang salah ID/nama
     ["al_shirbini_iqna", "al_iqna_mawardi"]),
    ("fath_al_muin_malibari",         "Fath al-Mu'in — Al-Malibari",                     11327, []),
    ("ianat_al_talibin_bakri",        "I'anat al-Talibin — Al-Bakri",                    963,   []),

    # ── Qawa'id Fiqhiyyah ─────────────────────────────────────────────────
    ("al_asybah_wa_nazair_suyuthi",   "Al-Asybah wa'l-Nazha'ir — Al-Suyuthi",            21719, []),
    ("al_mantsur_qawaid_zarkasyi",    "Al-Mantsur fi al-Qawa'id — Al-Zarkasyi",          21592, []),
    ("qawaid_al_ahkam_izz_abd_salam", "Qawa'id al-Ahkam — Al-'Izz ibn Abd al-Salam",    8608,  []),

    # ── Fiqh Syafi'i — Qawl Ashhab (baru v5) ─────────────────────────────
    ("al_bayan_imrani",               "Al-Bayan fi Madhhab al-Imam al-Shafi'i — Al-Imrani", 21721,
     # alias: nama lama dari download manual
     ["al_imrani_al_bayan"]),
]

TOTAL = len(KITAB)  # 30


def find_epub(key: str, aliases: list[str]) -> tuple[Path | None, str | None]:
    """
    Cari epub berdasarkan key utama dulu, lalu alias jika tidak ketemu.
    Returns (path_found, nama_alias_jika_dari_alias) atau (None, None).
    """
    # Cek key utama
    primary = EPUB_DIR / f"{key}.epub"
    if primary.exists() and primary.stat().st_size > 5 * 1024:
        return primary, None

    # Cek alias (nama lama/salah)
    for alias in aliases:
        p = EPUB_DIR / f"{alias}.epub"
        if p.exists() and p.stat().st_size > 5 * 1024:
            return p, alias

    return None, None


def main():
    if not EPUB_DIR.exists():
        print(f"Folder corpus tidak ditemukan: {EPUB_DIR}")
        sys.exit(1)

    sudah     = []   # (label, size_kb)
    perlu_rename = []  # (key, alias_lama, label, size_kb)
    belum     = []   # (label, id)

    for key, label, shamela_id, aliases in KITAB:
        path, alias_used = find_epub(key, aliases)

        if path is None:
            belum.append((label, shamela_id))
        elif alias_used:
            size_kb = path.stat().st_size // 1024
            sudah.append((label, size_kb))
            perlu_rename.append((key, alias_used, label, size_kb, path))
        else:
            size_kb = path.stat().st_size // 1024
            sudah.append((label, size_kb))

    # ── Output ───────────────────────────────────────────────────────────────
    print("=" * 60)
    print(f"  SUDAH ({len(sudah)}/{TOTAL}):")
    for label, size_kb in sudah:
        print(f"    ✅ {label} ({size_kb} KB)")

    if perlu_rename:
        print()
        print(f"  ⚠  PERLU RENAME ({len(perlu_rename)}) — nama file lama, tidak akan terdeteksi script:")
        for key, alias, label, size_kb, path in perlu_rename:
            correct = EPUB_DIR / f"{key}.epub"
            print(f"    • {label}")
            print(f"      Ada    : {path.name} ({size_kb} KB)")
            print(f"      Rename : mv corpus/epub/{alias}.epub corpus/epub/{key}.epub")

    if belum:
        print()
        print(f"  BELUM ({len(belum)}):")
        for label, shamela_id in belum:
            print(f"    • {label}")
            print(f"      python3 -m shamela2epub download "
                  f'"https://shamela.ws/book/{shamela_id}" '
                  f'-o "corpus/epub/{[k for k, l, i, _ in KITAB if i == shamela_id][0]}.epub"')

    # ── Summary ───────────────────────────────────────────────────────────────
    # Cek file bonus (fath_al_aziz Dar al-Fikr jika ada)
    bonus_files = [
        EPUB_DIR / "fath_al_aziz_rafii_1142.epub",
        EPUB_DIR / "al_rafii_fath_al_aziz.epub",
    ]
    bonus_found = [(p.name, p.stat().st_size // 1024) for p in bonus_files if p.exists()]

    print()
    print(f"  Progress: {len(sudah)}/{TOTAL}")
    if bonus_found:
        print(f"\n  Bonus corpus (tidak dihitung dalam total):")
        for name, size in bonus_found:
            print(f"    📦 {name} ({size} KB)")

    epub_total = len(list(EPUB_DIR.glob("*.epub")))
    print(f"\n  Total file .epub di disk: {epub_total}")
    print("=" * 60)

    # Exit code berguna untuk scripting
    sys.exit(0 if not belum else 1)


if __name__ == "__main__":
    main()
