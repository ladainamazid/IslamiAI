# ============================================================
# islamic_data.py
# IslamiAI — Master Database v3.0 (Consolidated)
# ============================================================
# Versi      : 3.0
# Tanggal    : 2026-06-05
# Status     : Single-file consolidation dari Phase 0 + Block 1–9
# Entri      : 60 ayat Quran  |  38 hadis  |  64 rules Syafi'i
# ─────────────────────────────────────────────────────────────
# CHANGELOG
# ─────────────────────────────────────────────────────────────
# v1.0  Phase 0 base (23 ayat, 14 hadis, 29 rules)
# v2.0  Blok 1–9 terpisah: islamic_data_block*.py / blok*.py
# v3.0  KONSOLIDASI PENUH — satu file saja:
#         • quran_block1     → digabung ke quran_verses
#         • blok3–blok4      → digabung ke quran_verses
#         • blok5–blok6      → digabung ke hadis_collection
#         • blok7–blok9      → digabung ke shafii_rules
#       Perbaikan:
#         • Ref "quran_4_43_tayammum" → "quran_4_43" (fixed)
#         • Theme "akhirah"  → "akhirat" (normalized)
#         • 14 hadis base tanpa theme → diberi theme
#         • 2 ayat baru ditambahkan (quran_2_278, quran_24_30)
#         • 5 hadis stub pending (lihat tabel di bawah)
# ─────────────────────────────────────────────────────────────
# SCHEMA
# ─────────────────────────────────────────────────────────────
# quran_verses[key] = {
#   reference        : "S:A"   surah_ayah  : "S:A"
#   surah : int      ayah : int
#   arabic_text      : str  — teks Usmani, Mushaf Madinah
#   transliteration  : str  — transliterasi akademik
#   translation      : str  — Kemenag RI 2019 / ringkas
#   theme            : str  — tema utama
#   sub_theme        : str  — tema turunan (block1+ only)
#   confidence       : "high|medium|pending"
#   source_check     : str
# }
# hadis_collection[key] = {
#   reference   source   narrator (block5+)
#   arabic_text  transliteration  translation
#   theme        authenticity     grading
#   confidence   fiqh_relevance (block5+)
#   status="stub"  (pending entries only)
# }
# shafii_rules[key] = {
#   ruling   madhab
#   basis_quran : list[str]  ─ cross-ref ke quran_verses
#   basis_hadis : list[str]  ─ cross-ref ke hadis_collection
#   keywords    : list[str]  ─ retrieval keywords
#   reasoning   : str
#   confidence  : "high|medium|pending"
# }
# ─────────────────────────────────────────────────────────────
# PENDING HADIS STUBS (confidence="pending", status="stub")
# Lengkapi teks Arab dari: https://dorar.net / Kutub 9
# ─────────────────────────────────────────────────────────────
# KEY                          REF              TOPIK
# hadis_bukhari_876_jumat      BK 876           Kewajiban Jumat
# hadis_tirmidzi_415_rawatib   Tirmidzi 415     Rawatib 12 rakaat
# hadis_muslim_1337_haji       Muslim 1337      Istitha'ah haji
# hadis_bukhari_1404_zakat     BK 1404          Nishab emas/perak
# hadis_bukhari_2079_khiyar    BK 2079          Khiyar jual beli
# ─────────────────────────────────────────────────────────────
# INTEGRITY STATUS: ✅ 0 broken cross-references
# Verifikasi: python islamic_data.py
# ============================================================

quran_verses = {

    # ──────────────────────────────────────────────────────────
    # AQIDAH — TAUHID, RUKUN IMAN & ASMAUL HUSNA
    # ──────────────────────────────────────────────────────────

    "quran_2_255": {
        "reference": "2:255",
        "surah_ayah": "2:255",
        "surah": 2,
        "ayah": 255,
        "arabic_text": "ٱللَّهُ لَآ إِلَٰهَ إِلَّا هُوَ ٱلْحَىُّ ٱلْقَيُّومُ ۚ لَا تَأْخُذُهُۥ سِنَةٌ وَلَا نَوْمٌ",
        "transliteration": "Allāhu lā ilāha illā huwal-ḥayyul-qayyūm. Lā ta'khudhuhu sinatuw-wa lā nawm",
        "translation": "Allah, tidak ada tuhan selain Dia, Yang Mahahidup, terus-menerus mengurus makhluk-Nya. Tidak dilanda kantuk dan tidak tidur.",
        "theme": "aqidah",
        "sub_theme": "ayat_kursi",
        "confidence": "high",
        "source_check": "QS. Al-Baqarah [2]:255, penggalan pembuka, Mushaf Madinah"
    },
    "quran_3_18": {
        "reference": "3:18",
        "surah_ayah": "3:18",
        "surah": 3,
        "ayah": 18,
        "arabic_text": "شَهِدَ ٱللَّهُ أَنَّهُۥ لَآ إِلَٰهَ إِلَّا هُوَ وَٱلْمَلَٰٓئِكَةُ وَأُو۟لُوا۟ ٱلْعِلْمِ قَآئِمًۢا بِٱلْقِسْطِ ۚ لَآ إِلَٰهَ إِلَّا هُوَ ٱلْعَزِيزُ ٱلْحَكِيمُ",
        "transliteration": "Shahida Allāhu annahu lā ilāha illā huwa wal-malā'ikatu wa ulul-'ilmi qā'iman bil-qisṭ. Lā ilāha illā huwal-'azīzul-ḥakīm",
        "translation": "Allah menyatakan bahwasanya tidak ada Tuhan (yang berhak disembah) melainkan Dia, Yang menegakkan keadilan. Para malaikat dan orang-orang yang berilmu (juga menyatakan yang demikian itu). Tak ada Tuhan (yang berhak disembah) melainkan Dia, Yang Mahaperkasa, Mahabijaksana.",
        "theme": "aqidah",
        "confidence": "high",
        "source_check": "QS. Ali Imran [3]:18, Mushaf Madinah"
    },
    "quran_4_136": {
        "reference": "4:136",
        "surah_ayah": "4:136",
        "surah": 4,
        "ayah": 136,
        "arabic_text": "يَٰٓأَيُّهَا ٱلَّذِينَ ءَامَنُوٓا۟ ءَامِنُوا۟ بِٱللَّهِ وَرَسُولِهِۦ وَٱلْكِتَٰبِ ٱلَّذِى نَزَّلَ عَلَىٰ رَسُولِهِۦ وَٱلْكِتَٰبِ ٱلَّذِىٓ أَنزَلَ مِن قَبْلُ",
        "transliteration": "Yā ayyuhal-ladhīna āmanū āminū billāhi wa rasūlihī wal-kitābil-ladhī nazzala 'alā rasūlihī wal-kitābil-ladhī anzala min qabl",
        "translation": "Wahai orang-orang yang beriman! Tetaplah beriman kepada Allah, Rasul-Nya, Kitab yang diturunkan kepada Rasul-Nya, serta kitab yang diturunkan sebelumnya.",
        "theme": "aqidah",
        "sub_theme": "rukun_iman",
        "confidence": "high",
        "source_check": "QS. An-Nisa [4]:136, penggalan awal ayat, Mushaf Madinah"
    },
    "quran_47_19": {
        "reference": "47:19",
        "surah_ayah": "47:19",
        "surah": 47,
        "ayah": 19,
        "arabic_text": "فَٱعْلَمْ أَنَّهُۥ لَآ إِلَٰهَ إِلَّا ٱللَّهُ وَٱسْتَغْفِرْ لِذَنۢبِكَ وَلِلْمُؤْمِنِينَ وَٱلْمُؤْمِنَٰتِ",
        "transliteration": "Fa'lam annahu lā ilāha illallāhu was-taghfir lidhanbika wa lil-mu'minīna wal-mu'mināt",
        "translation": "Maka ketahuilah, bahwa sesungguhnya tidak ada Tuhan (yang berhak disembah) melainkan Allah dan mohonlah ampunan bagi dosamu dan bagi (dosa) orang-orang mukmin laki-laki dan perempuan.",
        "theme": "aqidah",
        "confidence": "high",
        "source_check": "QS. Muhammad [47]:19, Mushaf Madinah"
    },
    "quran_57_3": {
        "reference": "57:3",
        "surah_ayah": "57:3",
        "surah": 57,
        "ayah": 3,
        "arabic_text": "هُوَ ٱلْأَوَّلُ وَٱلْأَخِرُ وَٱلظَّٰهِرُ وَٱلْبَاطِنُ ۖ وَهُوَ بِكُلِّ شَىْءٍ عَلِيمٌ",
        "transliteration": "Huwal-awwalu wal-ākhiru waẓ-ẓāhiru wal-bāṭin. Wa huwa bi-kulli shay'in 'alīm",
        "translation": "Dialah Yang Awal, Yang Akhir, Yang Zahir, dan Yang Batin. Dia Maha Mengetahui segala sesuatu.",
        "theme": "aqidah",
        "sub_theme": "asmaul_husna",
        "confidence": "high",
        "source_check": "QS. Al-Hadid [57]:3, Mushaf Madinah"
    },
    "quran_59_22": {
        "reference": "59:22",
        "surah_ayah": "59:22",
        "surah": 59,
        "ayah": 22,
        "arabic_text": "هُوَ ٱللَّهُ ٱلَّذِى لَآ إِلَٰهَ إِلَّا هُوَ ۖ عَٰلِمُ ٱلْغَيْبِ وَٱلشَّهَٰدَةِ ۖ هُوَ ٱلرَّحْمَٰنُ ٱلرَّحِيمُ",
        "transliteration": "Huwallāhul-ladhī lā ilāha illā hū, 'ālimu al-ghaybi wash-shahādah, huwar-raḥmānur-raḥīm",
        "translation": "Dialah Allah, tidak ada tuhan selain Dia, Yang Mengetahui yang gaib dan yang nyata. Dialah Yang Maha Pengasih, Maha Penyayang.",
        "theme": "aqidah",
        "sub_theme": "asmaul_husna",
        "confidence": "high",
        "source_check": "QS. Al-Hasyr [59]:22, Mushaf Madinah"
    },
    "quran_112_1": {
        "reference": "112:1",
        "surah_ayah": "112:1",
        "surah": 112,
        "ayah": 1,
        "arabic_text": "قُلْ هُوَ ٱللَّهُ أَحَدٌ",
        "transliteration": "Qul huwallāhu aḥad",
        "translation": "Katakanlah, Dialah Allah Yang Maha Esa.",
        "theme": "aqidah",
        "sub_theme": "tauhid",
        "confidence": "high",
        "source_check": "QS. Al-Ikhlas [112]:1, Mushaf Madinah"
    },
    "quran_112_2": {
        "reference": "112:2",
        "surah_ayah": "112:2",
        "surah": 112,
        "ayah": 2,
        "arabic_text": "ٱللَّهُ ٱلصَّمَدُ",
        "transliteration": "Allāhuṣ-ṣamad",
        "translation": "Allah adalah Tuhan yang bergantung kepada-Nya segala sesuatu.",
        "theme": "aqidah",
        "sub_theme": "sifat_allah",
        "confidence": "high",
        "source_check": "QS. Al-Ikhlas [112]:2, Mushaf Madinah"
    },
    "quran_112_3": {
        "reference": "112:3",
        "surah_ayah": "112:3",
        "surah": 112,
        "ayah": 3,
        "arabic_text": "لَمْ يَلِدْ وَلَمْ يُولَدْ",
        "transliteration": "Lam yalid wa lam yūlad",
        "translation": "Dia tidak beranak dan tidak pula diperanakkan.",
        "theme": "aqidah",
        "sub_theme": "sifat_allah",
        "confidence": "high",
        "source_check": "QS. Al-Ikhlas [112]:3, Mushaf Madinah"
    },
    "quran_112_4": {
        "reference": "112:4",
        "surah_ayah": "112:4",
        "surah": 112,
        "ayah": 4,
        "arabic_text": "وَلَمْ يَكُن لَّهُۥ كُفُوًا أَحَدٌ",
        "transliteration": "Wa lam yakul-lahū kufuwan aḥad",
        "translation": "Dan tidak ada sesuatu yang setara dengan Dia.",
        "theme": "aqidah",
        "sub_theme": "sifat_allah",
        "confidence": "high",
        "source_check": "QS. Al-Ikhlas [112]:4, Mushaf Madinah"
    },

    # ──────────────────────────────────────────────────────────
    # THAHARAH — BERSUCI
    # ──────────────────────────────────────────────────────────

    "quran_2_222": {
        "reference": "2:222",
        "surah_ayah": "2:222",
        "surah": 2,
        "ayah": 222,
        "arabic_text": "إِنَّ ٱللَّهَ يُحِبُّ ٱلتَّوَّٰبِينَ وَيُحِبُّ ٱلْمُتَطَهِّرِينَ",
        "transliteration": "Innallāha yuḥibbut-tawwābīna wa yuḥibbul-mutaṭahhirīn",
        "translation": "Sesungguhnya Allah menyukai orang-orang yang bertobat dan orang-orang yang menyucikan diri.",
        "theme": "thaharah",
        "confidence": "high",
        "source_check": "QS. Al-Baqarah [2]:222, penggalan akhir ayat, Mushaf Madinah"
    },
    "quran_4_43": {
        "reference": "4:43",
        "surah_ayah": "4:43",
        "surah": 4,
        "ayah": 43,
        "arabic_text": "فَلَمْ تَجِدُوا۟ مَآءً فَتَيَمَّمُوا۟ صَعِيدًا طَيِّبًا فَٱمْسَحُوا۟ بِوُجُوهِكُمْ وَأَيْدِيكُمْ",
        "transliteration": "Fa-lam tajidū mā'an fa-tayammamū ṣa'īdan ṭayyiban famsaḥū bi-wujūhikum wa aydīkum",
        "translation": "Jika tidak memperoleh air, maka bertayamumlah dengan debu yang bersih; usaplah wajah dan tanganmu dengan debu itu.",
        "theme": "thaharah",
        "sub_theme": "tayammum",
        "confidence": "high",
        "source_check": "QS. An-Nisa [4]:43, penggalan penutup ayat, Mushaf Madinah"
    },
    "quran_5_6": {
        "reference": "5:6",
        "surah_ayah": "5:6",
        "surah": 5,
        "ayah": 6,
        "arabic_text": "يَٰٓأَيُّهَا ٱلَّذِينَ ءَامَنُوٓا۟ إِذَا قُمْتُمْ إِلَى ٱلصَّلَوٰةِ فَٱغْسِلُوا۟ وُجُوهَكُمْ وَأَيْدِيَكُمْ إِلَى ٱلْمَرَافِقِ وَٱمْسَحُوا۟ بِرُءُوسِكُمْ وَأَرْجُلَكُمْ إِلَى ٱلْكَعْبَيْنِ",
        "transliteration": "Yā ayyuhal-ladhīna āmanū idhā qumtum ilaṣ-ṣalāti faghsilū wujūhakum wa aydiyakum ilal-marāfiqi wamsaḥū biru'ūsikum wa arjulakum ilal-ka'bayn",
        "translation": "Wahai orang-orang yang beriman! Apabila kamu hendak melaksanakan shalat, maka basuhlah wajahmu dan tanganmu sampai ke siku, dan sapulah kepalamu dan (basuh) kedua kakimu sampai ke kedua mata kaki.",
        "theme": "thaharah",
        "confidence": "high",
        "source_check": "QS. Al-Ma'idah [5]:6, Mushaf Madinah"
    },

    # ──────────────────────────────────────────────────────────
    # SHALAT
    # ──────────────────────────────────────────────────────────

    "quran_2_43": {
        "reference": "2:43",
        "surah_ayah": "2:43",
        "surah": 2,
        "ayah": 43,
        "arabic_text": "وَأَقِيمُوا۟ ٱلصَّلَوٰةَ وَءَاتُوا۟ ٱلزَّكَوٰةَ وَٱرْكَعُوا۟ مَعَ ٱلرَّٰكِعِينَ",
        "transliteration": "Wa aqīmuṣ-ṣalāta wa ātuz-zakāta warka'ū ma'ar-rāki'īn",
        "translation": "Dan laksanakanlah shalat, tunaikanlah zakat, dan rukuklah beserta orang-orang yang rukuk.",
        "theme": "shalat",
        "confidence": "high",
        "source_check": "QS. Al-Baqarah [2]:43, Mushaf Madinah"
    },
    "quran_2_153": {
        "reference": "2:153",
        "surah_ayah": "2:153",
        "surah": 2,
        "ayah": 153,
        "arabic_text": "يَٰٓأَيُّهَا ٱلَّذِينَ ءَامَنُوا۟ ٱسْتَعِينُوا۟ بِٱلصَّبْرِ وَٱلصَّلَوٰةِ ۚ إِنَّ ٱللَّهَ مَعَ ٱلصَّٰبِرِينَ",
        "transliteration": "Yā ayyuhal-ladhīna āmanūsta'īnū biṣ-ṣabri waṣ-ṣalāh. Innallāha ma'aṣ-ṣābirīn",
        "translation": "Wahai orang-orang beriman! Mohonlah pertolongan dengan sabar dan shalat. Sungguh, Allah beserta orang-orang yang sabar.",
        "theme": "shalat",
        "sub_theme": "shalat_dan_sabar",
        "confidence": "high",
        "source_check": "QS. Al-Baqarah [2]:153"
    },
    "quran_2_238": {
        "reference": "2:238",
        "surah_ayah": "2:238",
        "surah": 2,
        "ayah": 238,
        "arabic_text": "حَٰفِظُوا۟ عَلَى ٱلصَّلَوَٰتِ وَٱلصَّلَوٰةِ ٱلْوُسْطَىٰ وَقُومُوا۟ لِلَّهِ قَٰنِتِينَ",
        "transliteration": "Ḥāfizū 'alaṣ-ṣalawāti waṣ-ṣalātil-wusṭā wa qūmū lillāhi qānitīn",
        "translation": "Peliharalah semua shalat dan shalat Wustha (shalat Ashar). Dan laksanakanlah (shalat) karena Allah dengan khusyuk.",
        "theme": "shalat",
        "confidence": "high",
        "source_check": "QS. Al-Baqarah [2]:238, Mushaf Madinah"
    },
    "quran_4_103": {
        "reference": "4:103",
        "surah_ayah": "4:103",
        "surah": 4,
        "ayah": 103,
        "arabic_text": "إِنَّ ٱلصَّلَوٰةَ كَانَتْ عَلَى ٱلْمُؤْمِنِينَ كِتَٰبًا مَّوْقُوتًا",
        "transliteration": "Innash-ṣalāta kānat 'alal-mu'minīna kitābam mawqūtā",
        "translation": "Sesungguhnya shalat itu adalah kewajiban yang ditentukan waktunya atas orang-orang yang beriman.",
        "theme": "shalat",
        "confidence": "high",
        "source_check": "QS. An-Nisa [4]:103, penggalan akhir ayat, Mushaf Madinah"
    },
    "quran_17_78": {
        "reference": "17:78",
        "surah_ayah": "17:78",
        "surah": 17,
        "ayah": 78,
        "arabic_text": "أَقِمِ ٱلصَّلَوٰةَ لِدُلُوكِ ٱلشَّمْسِ إِلَىٰ غَسَقِ ٱلَّيْلِ وَقُرْءَانَ ٱلْفَجْرِ ۖ إِنَّ قُرْءَانَ ٱلْفَجْرِ كَانَ مَشْهُودًا",
        "transliteration": "Aqimiṣ-ṣalāta liduluukish-shamsi ilā ghasaqil-layli wa qur'ānal-fajr. Inna qur'ānal-fajri kāna mashhūdā",
        "translation": "Laksanakanlah shalat sejak matahari tergelincir sampai gelapnya malam dan (laksanakan pula shalat) Subuh. Sungguh, shalat Subuh itu disaksikan (oleh malaikat).",
        "theme": "shalat",
        "confidence": "high",
        "source_check": "QS. Al-Isra [17]:78, Mushaf Madinah"
    },
    "quran_29_45": {
        "reference": "29:45",
        "surah_ayah": "29:45",
        "surah": 29,
        "ayah": 45,
        "arabic_text": "أَقِمِ ٱلصَّلَوٰةَ ۖ إِنَّ ٱلصَّلَوٰةَ تَنْهَىٰ عَنِ ٱلْفَحْشَآءِ وَٱلْمُنكَرِ",
        "transliteration": "Aqimiṣ-ṣalāh. Innaṣ-ṣalāta tanhā 'anil-faḥshā'i wal-munkar",
        "translation": "Laksanakanlah shalat. Sesungguhnya shalat itu mencegah dari perbuatan keji dan mungkar.",
        "theme": "shalat",
        "sub_theme": "hikmah_shalat",
        "confidence": "high",
        "source_check": "QS. Al-'Ankabut [29]:45 (penggalan)"
    },
    "quran_62_9": {
        "reference": "62:9",
        "surah_ayah": "62:9",
        "surah": 62,
        "ayah": 9,
        "arabic_text": "يَٰٓأَيُّهَا ٱلَّذِينَ ءَامَنُوٓا۟ إِذَا نُودِىَ لِلصَّلَوٰةِ مِن يَوْمِ ٱلْجُمُعَةِ فَٱسْعَوْا۟ إِلَىٰ ذِكْرِ ٱللَّهِ وَذَرُوا۟ ٱلْبَيْعَ",
        "transliteration": "Yā ayyuhal-ladhīna āmanū idhā nūdiya liṣ-ṣalāti min yawmil-jumu'ati fas'aw ilā dhikrillāhi wa dharul-bay'",
        "translation": "Wahai orang-orang beriman! Apabila diseru shalat pada hari Jumat, segeralah mengingat Allah dan tinggalkanlah jual beli.",
        "theme": "shalat",
        "sub_theme": "shalat_jumat",
        "confidence": "high",
        "source_check": "QS. Al-Jumu'ah [62]:9"
    },

    # ──────────────────────────────────────────────────────────
    # PUASA & RAMADHAN
    # ──────────────────────────────────────────────────────────

    "quran_2_183": {
        "reference": "2:183",
        "surah_ayah": "2:183",
        "surah": 2,
        "ayah": 183,
        "arabic_text": "يَٰٓأَيُّهَا ٱلَّذِينَ ءَامَنُوا۟ كُتِبَ عَلَيْكُمُ ٱلصِّيَامُ كَمَا كُتِبَ عَلَى ٱلَّذِينَ مِن قَبْلِكُمْ لَعَلَّكُمْ تَتَّقُونَ",
        "transliteration": "Ya ayyuhal-ladhiina aamanuu kutiba alaykumus-siyamu kama kutiba alal-ladhiina min qablikum laallakum tattaquun",
        "translation": "Wahai orang-orang yang beriman! Diwajibkan atas kamu berpuasa sebagaimana diwajibkan atas orang-orang sebelum kamu, agar kamu bertakwa.",
        "theme": "puasa",
        "confidence": "high",
        "source_check": "QS. Al-Baqarah [2]:183, Mushaf Madinah"
    },
    "quran_2_184": {
        "reference": "2:184",
        "surah_ayah": "2:184",
        "surah": 2,
        "ayah": 184,
        "arabic_text": "فَمَن كَانَ مِنكُم مَّرِيضًا أَوْ عَلَىٰ سَفَرٍ فَعِدَّةٌ مِّنْ أَيَّامٍ أُخَرَ ۚ وَعَلَى ٱلَّذِينَ يُطِيقُونَهُۥ فِدْيَةٌ طَعَامُ مِسْكِينٍ",
        "transliteration": "Fa-man kāna minkum marīḍan aw 'alā safarin fa-'iddatum min ayyāmin ukhar. Wa 'alal-ladhīna yuṭīqūnahū fidyatun ṭa'āmu miskīn",
        "translation": "Barangsiapa sakit atau dalam perjalanan, wajib mengganti di hari lain. Bagi yang berat menjalankannya, wajib membayar fidyah memberi makan orang miskin.",
        "theme": "puasa",
        "sub_theme": "rukhshah_fidyah",
        "confidence": "high",
        "source_check": "QS. Al-Baqarah [2]:184 (penggalan)"
    },
    "quran_2_185": {
        "reference": "2:185",
        "surah_ayah": "2:185",
        "surah": 2,
        "ayah": 185,
        "arabic_text": "شَهْرُ رَمَضَانَ ٱلَّذِىٓ أُنزِلَ فِيهِ ٱلْقُرْءَانُ هُدًى لِّلنَّاسِ وَبَيِّنَٰتٍ مِّنَ ٱلْهُدَىٰ وَٱلْفُرْقَانِ",
        "transliteration": "Shahru Ramadanal-ladhi unzila fiihil-Qurani hudan lin-naasi wa bayyinatin minal-huda wal-furqan",
        "translation": "Bulan Ramadan adalah (bulan) yang di dalamnya diturunkan Al-Quran, sebagai petunjuk bagi manusia dan penjelasan-penjelasan mengenai petunjuk itu dan pembeda (antara yang benar dan yang batil).",
        "theme": "puasa",
        "confidence": "high",
        "source_check": "QS. Al-Baqarah [2]:185, Mushaf Madinah"
    },
    "quran_2_187": {
        "reference": "2:187",
        "surah_ayah": "2:187",
        "surah": 2,
        "ayah": 187,
        "arabic_text": "وَكُلُوا۟ وَٱشْرَبُوا۟ حَتَّىٰ يَتَبَيَّنَ لَكُمُ ٱلْخَيْطُ ٱلْأَبْيَضُ مِنَ ٱلْخَيْطِ ٱلْأَسْوَدِ مِنَ ٱلْفَجْرِ",
        "transliteration": "Wa kulū wāshrabū ḥattā yatabayyana lakumul-khayṭul-abyadhu minal-khayṭil-aswadi minal-fajr",
        "translation": "Makan dan minumlah hingga jelas benang putih dari benang hitam, yaitu fajar.",
        "theme": "puasa",
        "sub_theme": "batas_sahur",
        "confidence": "high",
        "source_check": "QS. Al-Baqarah [2]:187 (penggalan)"
    },

    # ──────────────────────────────────────────────────────────
    # ZAKAT
    # ──────────────────────────────────────────────────────────

    "quran_9_60": {
        "reference": "9:60",
        "surah_ayah": "9:60",
        "surah": 9,
        "ayah": 60,
        "arabic_text": "إِنَّمَا ٱلصَّدَقَٰتُ لِلْفُقَرَآءِ وَٱلْمَسَٰكِينِ وَٱلْعَٰمِلِينَ عَلَيْهَا وَٱلْمُؤَلَّفَةِ قُلُوبُهُمْ",
        "transliteration": "Innamas-sadaqaatu lil-fuqaraa'i wal-masaakiini wal-amiliiina alayha wal-muallafati quluubuhum",
        "translation": "Sesungguhnya zakat itu hanyalah untuk orang-orang fakir, orang miskin, amil zakat, yang dilunakkan hatinya (mualaf).",
        "theme": "zakat",
        "confidence": "high",
        "source_check": "QS. At-Tawbah [9]:60, Mushaf Madinah"
    },
    "quran_9_60_full": {
        "reference": "9:60",
        "surah_ayah": "9:60",
        "surah": 9,
        "ayah": 60,
        "arabic_text": "إِنَّمَا ٱلصَّدَقَٰتُ لِلْفُقَرَآءِ وَٱلْمَسَٰكِينِ وَٱلْعَٰمِلِينَ عَلَيْهَا وَٱلْمُؤَلَّفَةِ قُلُوبُهُمْ وَفِى ٱلرِّقَابِ وَٱلْغَٰرِمِينَ وَفِى سَبِيلِ ٱللَّهِ وَٱبْنِ ٱلسَّبِيلِ",
        "transliteration": "Innamaṣ-ṣadaqātu lil-fuqarā'i wal-masākīni wal-'āmilīna 'alayhā wal-mu'allafati qulūbuhum wa fir-riqābi wal-ghārimīna wa fī sabīlillāhi wabnis-sabīl",
        "translation": "Sesungguhnya zakat hanya untuk orang fakir, miskin, amil zakat, muallaf, memerdekakan hamba, orang berutang, jalan Allah, dan musafir.",
        "theme": "zakat",
        "sub_theme": "delapan_asnaf",
        "confidence": "high",
        "source_check": "QS. At-Tawbah [9]:60"
    },
    "quran_9_103": {
        "reference": "9:103",
        "surah_ayah": "9:103",
        "surah": 9,
        "ayah": 103,
        "arabic_text": "خُذْ مِنْ أَمْوَٰلِهِمْ صَدَقَةً تُطَهِّرُهُمْ وَتُزَكِّيهِم بِهَا",
        "transliteration": "Khudh min amwaalihim sadaqatan tutahhiruhum wa tuzakkiihim biha",
        "translation": "Ambillah zakat dari harta mereka, guna membersihkan dan menyucikan mereka.",
        "theme": "zakat",
        "confidence": "high",
        "source_check": "QS. At-Tawbah [9]:103, Mushaf Madinah"
    },
    "quran_63_10": {
        "reference": "63:10",
        "surah_ayah": "63:10",
        "surah": 63,
        "ayah": 10,
        "arabic_text": "وَأَنفِقُوا۟ مِن مَّا رَزَقْنَٰكُم مِّن قَبْلِ أَن يَأْتِىَ أَحَدَكُمُ ٱلْمَوْتُ",
        "transliteration": "Wa anfiqū mimmā razaqnākum min qabli ay ya'tiya aḥadakumul-mawt",
        "translation": "Infakkanlah sebagian rezeki yang Kami anugerahkan sebelum kematian datang kepada salah seorang di antaramu.",
        "theme": "zakat",
        "sub_theme": "urgensi_infaq",
        "confidence": "high",
        "source_check": "QS. Al-Munafiqun [63]:10 (penggalan)"
    },

    # ──────────────────────────────────────────────────────────
    # HAJI & UMRAH
    # ──────────────────────────────────────────────────────────

    "quran_2_196": {
        "reference": "2:196",
        "surah_ayah": "2:196",
        "surah": 2,
        "ayah": 196,
        "arabic_text": "وَأَتِمُّوا۟ ٱلْحَجَّ وَٱلْعُمْرَةَ لِلَّهِ",
        "transliteration": "Wa atimmul-ḥajja wal-'umrata lillāh",
        "translation": "Sempurnakanlah ibadah haji dan umrah karena Allah.",
        "theme": "haji",
        "sub_theme": "haji_dan_umrah",
        "confidence": "high",
        "source_check": "QS. Al-Baqarah [2]:196 (penggalan)"
    },
    "quran_2_197": {
        "reference": "2:197",
        "surah_ayah": "2:197",
        "surah": 2,
        "ayah": 197,
        "arabic_text": "ٱلْحَجُّ أَشْهُرٌ مَّعْلُومَٰتٌ ۚ فَمَن فَرَضَ فِيهِنَّ ٱلْحَجَّ فَلَا رَفَثَ وَلَا فُسُوقَ وَلَا جِدَالَ فِى ٱلْحَجِّ",
        "transliteration": "Al-ḥajju ashhura ma'lūmāt. Fa-man faraḍa fīhinna al-ḥajja fa-lā rafatha wa lā fusūqa wa lā jidāla fil-ḥajj",
        "translation": "Musim haji pada bulan-bulan yang dimaklumi. Barangsiapa mengerjakan haji, tidak boleh rafats, berbuat fasik, dan berbantah-bantahan.",
        "theme": "haji",
        "sub_theme": "larangan_ihram",
        "confidence": "high",
        "source_check": "QS. Al-Baqarah [2]:197 (penggalan)"
    },
    "quran_3_97": {
        "reference": "3:97",
        "surah_ayah": "3:97",
        "surah": 3,
        "ayah": 97,
        "arabic_text": "وَلِلَّهِ عَلَى ٱلنَّاسِ حِجُّ ٱلْبَيْتِ مَنِ ٱسْتَطَاعَ إِلَيْهِ سَبِيلًا",
        "transliteration": "Wa lillāhi 'alan-nāsi ḥijjul-bayti manistaṭā'a ilayhi sabīlā",
        "translation": "Kewajiban manusia terhadap Allah adalah melaksanakan haji ke Baitullah bagi yang mampu.",
        "theme": "haji",
        "sub_theme": "kewajiban_haji",
        "confidence": "high",
        "source_check": "QS. Ali Imran [3]:97 (penggalan)"
    },
    "quran_22_27": {
        "reference": "22:27",
        "surah_ayah": "22:27",
        "surah": 22,
        "ayah": 27,
        "arabic_text": "وَأَذِّن فِى ٱلنَّاسِ بِٱلْحَجِّ يَأْتُوكَ رِجَالًا وَعَلَىٰ كُلِّ ضَامِرٍ يَأْتِينَ مِن كُلِّ فَجٍّ عَمِيقٍ",
        "transliteration": "Wa adhdhin fin-nāsi bil-ḥajji ya'tūka rijālan wa 'alā kulli ḍāmirin ya'tīna min kulli fajjin 'amīq",
        "translation": "Serulah manusia untuk berhaji, niscaya mereka datang berjalan kaki atau mengendarai unta kurus dari setiap penjuru yang jauh.",
        "theme": "haji",
        "sub_theme": "seruan_haji",
        "confidence": "high",
        "source_check": "QS. Al-Hajj [22]:27"
    },

    # ──────────────────────────────────────────────────────────
    # NIKAH & KELUARGA
    # ──────────────────────────────────────────────────────────

    "quran_2_221": {
        "reference": "2:221",
        "surah_ayah": "2:221",
        "surah": 2,
        "ayah": 221,
        "arabic_text": "وَلَا تَنكِحُوا۟ ٱلْمُشْرِكَٰتِ حَتَّىٰ يُؤْمِنَّ",
        "transliteration": "Wa la tankihul-mushrikaati hattaa yu'minn",
        "translation": "Dan janganlah kamu nikahi perempuan musyrik sebelum mereka beriman.",
        "theme": "nikah",
        "confidence": "high",
        "source_check": "QS. Al-Baqarah [2]:221, Mushaf Madinah"
    },
    "quran_4_19": {
        "reference": "4:19",
        "surah_ayah": "4:19",
        "surah": 4,
        "ayah": 19,
        "arabic_text": "وَعَاشِرُوهُنَّ بِٱلْمَعْرُوفِ",
        "transliteration": "Wa 'āshirūhunna bil-ma'rūf",
        "translation": "Dan bergaullah dengan mereka (para istri) secara patut.",
        "theme": "nikah",
        "sub_theme": "muasyarah_bil_maruf",
        "confidence": "high",
        "source_check": "QS. An-Nisa [4]:19 (penggalan)"
    },
    "quran_30_21": {
        "reference": "30:21",
        "surah_ayah": "30:21",
        "surah": 30,
        "ayah": 21,
        "arabic_text": "وَمِنْ ءَايَٰتِهِۦٓ أَنْ خَلَقَ لَكُم مِّنْ أَنفُسِكُمْ أَزْوَٰجًا لِّتَسْكُنُوٓا۟ إِلَيْهَا وَجَعَلَ بَيْنَكُم مَّوَدَّةً وَرَحْمَةً",
        "transliteration": "Wa min āyātihī an khalaqa lakum min anfusikum azwājal-litaskunū ilayhā wa ja'ala baynakum mawaddataw-wa raḥmah",
        "translation": "Di antara tanda kebesaran-Nya, Dia menciptakan pasangan-pasangan untukmu agar kamu tenteram, dan Dia menjadikan di antaramu kasih dan sayang.",
        "theme": "nikah",
        "sub_theme": "tujuan_pernikahan",
        "confidence": "high",
        "source_check": "QS. Ar-Rum [30]:21 (penggalan)"
    },
    "quran_60_10": {
        "reference": "60:10",
        "surah_ayah": "60:10",
        "surah": 60,
        "ayah": 10,
        "arabic_text": "وَلَا تُمْسِكُوا۟ بِعِصَمِ ٱلْكَوَافِرِ",
        "transliteration": "Wa la tumsiku bi-isamilkawaafir",
        "translation": "Dan janganlah kamu berpegang pada tali (pernikahan) dengan perempuan-perempuan kafir.",
        "theme": "nikah",
        "confidence": "high",
        "source_check": "QS. Al-Mumtahanah [60]:10, Mushaf Madinah"
    },
    "quran_65_6": {
        "reference": "65:6",
        "surah_ayah": "65:6",
        "surah": 65,
        "ayah": 6,
        "arabic_text": "أَسْكِنُوهُنَّ مِنْ حَيْثُ سَكَنتُم مِّن وُجْدِكُمْ",
        "transliteration": "Askinūhunna min ḥaythu sakantum min wujdikum",
        "translation": "Tempatkanlah para istri di mana kamu bertempat tinggal menurut kemampuanmu.",
        "theme": "nikah",
        "sub_theme": "nafkah_tempat_tinggal",
        "confidence": "high",
        "source_check": "QS. At-Talaq [65]:6 (penggalan)"
    },

    # ──────────────────────────────────────────────────────────
    # WARIS (FARAID)
    # ──────────────────────────────────────────────────────────

    "quran_4_11": {
        "reference": "4:11",
        "surah_ayah": "4:11",
        "surah": 4,
        "ayah": 11,
        "arabic_text": "يُوصِيكُمُ ٱللَّهُ فِىٓ أَوْلَٰدِكُمْ ۖ لِلذَّكَرِ مِثْلُ حَظِّ ٱلْأُنثَيَيْنِ",
        "transliteration": "Yusiikumullahu fii awlaadikum, lidh-dhakari mithlu hazz-il-unthayayn",
        "translation": "Allah mensyariatkan kepadamu tentang (pembagian warisan untuk) anak-anakmu, (yaitu) bagian seorang anak laki-laki sama dengan bagian dua orang anak perempuan.",
        "theme": "waris",
        "confidence": "high",
        "source_check": "QS. An-Nisa [4]:11, Mushaf Madinah"
    },
    "quran_4_12": {
        "reference": "4:12",
        "surah_ayah": "4:12",
        "surah": 4,
        "ayah": 12,
        "arabic_text": "وَلَكُمْ نِصْفُ مَا تَرَكَ أَزْوَٰجُكُمْ إِن لَّمْ يَكُن لَّهُنَّ وَلَدٌ ۚ فَإِن كَانَ لَهُنَّ وَلَدٌ فَلَكُمُ ٱلرُّبُعُ",
        "transliteration": "Wa lakum niṣfu mā taraka azwājukum in-lam yakul-lahunna walad. Fa-in kāna lahunna waladun fa-lakumur-rub'",
        "translation": "Bagianmu (suami) seperdua dari harta istri jika tidak punya anak. Jika punya anak, kamu mendapat seperempat.",
        "theme": "waris",
        "sub_theme": "bagian_suami",
        "confidence": "high",
        "source_check": "QS. An-Nisa [4]:12 (penggalan)"
    },

    # ──────────────────────────────────────────────────────────
    # MUAMALAH & EKONOMI ISLAM
    # ──────────────────────────────────────────────────────────

    "quran_2_275": {
        "reference": "2:275",
        "surah": 2,
        "ayah": 275,
        "arabic_text": "وَأَحَلَّ ٱللَّهُ ٱلْبَيْعَ وَحَرَّمَ ٱلرِّبَوٰا۟",
        "transliteration": "Wa aḥallallāhul-bay'a wa ḥarramar-ribā",
        "translation": "Allah telah menghalalkan jual beli dan mengharamkan riba.",
        "theme": "muamalah",
        "sub_theme": "riba_vs_jual_beli",
        "confidence": "high",
        "source_check": "QS. Al-Baqarah [2]:275 (penggalan)"
    },
    "quran_2_278": {
        "reference": "2:278",
        "surah_ayah": "2:278",
        "surah": 2,
        "ayah": 278,
        "arabic_text": "يَٰٓأَيُّهَا ٱلَّذِينَ ءَامَنُوا۟ ٱتَّقُوا۟ ٱللَّهَ وَذَرُوا۟ مَا بَقِىَ مِنَ ٱلرِّبَوٰٓا۟ إِن كُنتُم مُّؤْمِنِينَ",
        "transliteration": "Yā ayyuhal-ladhīna āmanūttaqullāha wa dharū mā baqiya minar-ribā in kuntum mu'minīn",
        "translation": "Wahai orang-orang yang beriman! Bertakwalah kepada Allah dan tinggalkan sisa riba jika kamu orang beriman.",
        "theme": "muamalah",
        "sub_theme": "larangan_riba",
        "confidence": "high",
        "source_check": "QS. Al-Baqarah [2]:278, Mushaf Madinah"
    },
    "quran_2_282": {
        "reference": "2:282",
        "surah": 2,
        "ayah": 282,
        "arabic_text": "يَٰٓأَيُّهَا ٱلَّذِينَ ءَامَنُوٓا۟ إِذَا تَدَايَنتُم بِدَيْنٍ إِلَىٰٓ أَجَلٍ مُّسَمًّى فَٱكْتُبُوهُ",
        "transliteration": "Yā ayyuhal-ladhīna āmanū idhā tadāyantum bidaynin ilā ajalim-musamman faktubūh",
        "translation": "Apabila kamu melakukan utang piutang untuk waktu yang ditentukan, hendaklah kamu menuliskannya.",
        "theme": "muamalah",
        "sub_theme": "pencatatan_hutang",
        "confidence": "high",
        "source_check": "QS. Al-Baqarah [2]:282 (penggalan)"
    },
    "quran_4_29": {
        "reference": "4:29",
        "surah": 4,
        "ayah": 29,
        "arabic_text": "يَٰٓأَيُّهَا ٱلَّذِينَ ءَامَنُوا۟ لَا تَأْكُلُوٓا۟ أَمْوَٰلَكُم بَيْنَكُم بِٱلْبَٰطِلِ إِلَّآ أَن تَكُونَ تِجَٰرَةً عَن تَرَاضٍ مِّنكُمْ",
        "transliteration": "Yā ayyuhal-ladhīna āmanū lā ta'kulū amwālakum baynakum bil-bāṭili illā an takūna tijāratan 'an tarāḍim-minkum",
        "translation": "Janganlah memakan harta sesama dengan cara batil, kecuali melalui perdagangan atas dasar suka sama suka.",
        "theme": "muamalah",
        "sub_theme": "jual_beli_sah",
        "confidence": "high",
        "source_check": "QS. An-Nisa [4]:29 (penggalan)"
    },

    # ──────────────────────────────────────────────────────────
    # AKHLAK & SOSIAL
    # ──────────────────────────────────────────────────────────

    "quran_17_32": {
        "reference": "17:32",
        "surah": 17,
        "ayah": 32,
        "arabic_text": "وَلَا تَقْرَبُوا۟ ٱلزِّنَىٰٓ ۖ إِنَّهُۥ كَانَ فَٰحِشَةً وَسَآءَ سَبِيلًا",
        "transliteration": "Wa lā taqrabuz-zinā. Innahū kāna fāḥishatan wa sā'a sabīlā",
        "translation": "Janganlah mendekati zina. Sesungguhnya zina itu perbuatan keji dan jalan yang buruk.",
        "theme": "akhlak",
        "sub_theme": "larangan_zina",
        "confidence": "high",
        "source_check": "QS. Al-Isra [17]:32"
    },
    "quran_24_30": {
        "reference": "24:30",
        "surah_ayah": "24:30",
        "surah": 24,
        "ayah": 30,
        "arabic_text": "قُل لِّلْمُؤْمِنِينَ يَغُضُّوا۟ مِنْ أَبْصَٰرِهِمْ وَيَحْفَظُوا۟ فُرُوجَهُمْ ۚ ذَٰلِكَ أَزْكَىٰ لَهُمْ ۗ إِنَّ ٱللَّهَ خَبِيرٌۢ بِمَا يَصْنَعُونَ",
        "transliteration": "Qul lil-mu'minīna yaghuḍḍū min abṣārihim wa yaḥfaẓū furūjahum. Dhālika azkā lahum. Innallāha khabīrun bimā yaṣna'ūn",
        "translation": "Katakanlah kepada laki-laki yang beriman agar menjaga pandangannya dan memelihara kemaluannya. Yang demikian lebih suci bagi mereka.",
        "theme": "akhlak",
        "sub_theme": "ghadhdhul_bashar",
        "confidence": "high",
        "source_check": "QS. An-Nur [24]:30, Mushaf Madinah"
    },
    "quran_31_15": {
        "reference": "31:15",
        "surah_ayah": "31:15",
        "surah": 31,
        "ayah": 15,
        "arabic_text": "وَإِن جَٰهَدَاكَ عَلَىٰٓ أَن تُشْرِكَ بِى مَا لَيْسَ لَكَ بِهِۦ عِلْمٌ فَلَا تُطِعْهُمَا وَصَاحِبْهُمَا فِى ٱلدُّنْيَا مَعْرُوفًا",
        "transliteration": "Wa in jahadaka ala an tushrika bi ma laysa laka bihi ilmun fa la tutihuma wa sahhibhuma fid-dunya marufa",
        "translation": "Dan jika keduanya memaksamu untuk mempersekutukan Aku dengan sesuatu yang engkau tidak mempunyai ilmu tentang itu, maka janganlah engkau menaati keduanya, dan pergaulilah keduanya di dunia dengan baik.",
        "theme": "akhlak",
        "confidence": "high",
        "source_check": "QS. Luqman [31]:15, Mushaf Madinah"
    },
    "quran_49_6": {
        "reference": "49:6",
        "surah": 49,
        "ayah": 6,
        "arabic_text": "يَٰٓأَيُّهَا ٱلَّذِينَ ءَامَنُوٓا۟ إِن جَآءَكُمْ فَاسِقٌۢ بِنَبَإٍ فَتَبَيَّنُوٓا۟",
        "transliteration": "Yā ayyuhal-ladhīna āmanū in jā'akum fāsiqum bi-naba'in fa-tabayyanū",
        "translation": "Wahai orang-orang beriman! Jika seseorang yang fasik datang membawa berita, telitilah kebenarannya.",
        "theme": "akhlak",
        "sub_theme": "tabayyun",
        "confidence": "high",
        "source_check": "QS. Al-Hujurat [49]:6 (penggalan)",
        "fiqh_note": "Dasar hukum tabayyun — sangat relevan untuk isu hoaks dan media sosial"
    },
    "quran_49_12": {
        "reference": "49:12",
        "surah": 49,
        "ayah": 12,
        "arabic_text": "يَٰٓأَيُّهَا ٱلَّذِينَ ءَامَنُوا۟ ٱجْتَنِبُوا۟ كَثِيرًا مِّنَ ٱلظَّنِّ إِنَّ بَعْضَ ٱلظَّنِّ إِثْمٌ ۖ وَلَا تَجَسَّسُوا۟ وَلَا يَغْتَب بَّعْضُكُم بَعْضًا",
        "transliteration": "Yā ayyuhal-ladhīna āmanūjtanibū kathīram-minaẓ-ẓann. Inna ba'ḍaẓ-ẓanni ithm. Wa lā tajassasū wa lā yaghtab ba'ḍukum ba'ḍā",
        "translation": "Jauhilah banyak prasangka karena sebagian prasangka adalah dosa. Jangan mencari-cari kesalahan orang, dan jangan menggunjing.",
        "theme": "akhlak",
        "sub_theme": "ghibah_tajassus",
        "confidence": "high",
        "source_check": "QS. Al-Hujurat [49]:12"
    },
    "quran_60_8": {
        "reference": "60:8",
        "surah_ayah": "60:8",
        "surah": 60,
        "ayah": 8,
        "arabic_text": "لَّا يَنْهَىٰكُمُ ٱللَّهُ عَنِ ٱلَّذِينَ لَمْ يُقَٰتِلُوكُمْ فِى ٱلدِّينِ وَلَمْ يُخْرِجُوكُم مِّن دِيَٰرِكُمْ أَن تَبَرُّوهُمْ وَتُقْسِطُوٓا۟ إِلَيْهِمْ",
        "transliteration": "La yanhakumullahu anil-ladhiina lam yuqatilukum fid-diini wa lam yukhrijukum min diyarikum an tabarruhum wa tuqsitu ilayhim",
        "translation": "Allah tidak melarang kamu berbuat baik dan berlaku adil terhadap orang-orang yang tidak memerangimu dalam urusan agama dan tidak mengusir kamu dari kampung halamanmu.",
        "theme": "akhlak",
        "confidence": "high",
        "source_check": "QS. Al-Mumtahanah [60]:8, Mushaf Madinah"
    },

    # ──────────────────────────────────────────────────────────
    # SOSIAL — KEBEBASAN BERAGAMA
    # ──────────────────────────────────────────────────────────

    "quran_2_256": {
        "reference": "2:256",
        "surah": 2,
        "ayah": 256,
        "arabic_text": "لَآ إِكْرَاهَ فِى ٱلدِّينِ ۖ قَد تَّبَيَّنَ ٱلرُّشْدُ مِنَ ٱلْغَىِّ",
        "transliteration": "Lā ikrāha fid-dīn. Qad tabayyanar-rushdu minal-ghayy",
        "translation": "Tidak ada paksaan dalam agama. Jalan yang benar telah jelas dari jalan yang sesat.",
        "theme": "sosial",
        "sub_theme": "kebebasan_beragama",
        "confidence": "high",
        "source_check": "QS. Al-Baqarah [2]:256 (penggalan)"
    },

    # ──────────────────────────────────────────────────────────
    # HALAL / HARAM
    # ──────────────────────────────────────────────────────────

    "quran_2_173": {
        "reference": "2:173",
        "surah_ayah": "2:173",
        "surah": 2,
        "ayah": 173,
        "arabic_text": "إِنَّمَا حَرَّمَ عَلَيْكُمُ ٱلْمَيْتَةَ وَٱلدَّمَ وَلَحْمَ ٱلْخِنزِيرِ وَمَآ أُهِلَّ بِهِۦ لِغَيْرِ ٱللَّهِ",
        "transliteration": "Innama harrama alaikumul-maitata wad-dama wa lahmal-khinziri wa ma uhilla bihi lighairillah",
        "translation": "Sesungguhnya Dia hanya mengharamkan atas kamu bangkai, darah, daging babi, dan (daging) hewan yang disembelih dengan (menyebut nama) selain Allah.",
        "theme": "halal_haram",
        "confidence": "high",
        "source_check": "QS. Al-Baqarah [2]:173, Mushaf Madinah"
    },
    "quran_5_3": {
        "reference": "5:3",
        "surah_ayah": "5:3",
        "surah": 5,
        "ayah": 3,
        "arabic_text": "حُرِّمَتْ عَلَيْكُمُ ٱلْمَيْتَةُ وَٱلدَّمُ وَلَحْمُ ٱلْخِنزِيرِ وَمَآ أُهِلَّ لِغَيْرِ ٱللَّهِ بِهِۦ",
        "transliteration": "Hurrimat alaikumul-maitatu wad-damu wa lahmul-khinziri wa ma uhilla lighairillahi bih",
        "translation": "Diharamkan bagimu (memakan) bangkai, darah, daging babi, dan (daging) hewan yang disembelih bukan atas nama Allah.",
        "theme": "halal_haram",
        "confidence": "high",
        "source_check": "QS. Al-Maidah [5]:3, Mushaf Madinah"
    },
    "quran_5_90": {
        "reference": "5:90",
        "surah_ayah": "5:90",
        "surah": 5,
        "ayah": 90,
        "arabic_text": "يَٰٓأَيُّهَا ٱلَّذِينَ ءَامَنُوٓا۟ إِنَّمَا ٱلْخَمْرُ وَٱلْمَيْسِرُ وَٱلْأَنصَابُ وَٱلْأَزْلَٰمُ رِجْسٌ مِّنْ عَمَلِ ٱلشَّيْطَٰنِ فَٱجْتَنِبُوهُ",
        "transliteration": "Ya ayyuhal-ladhina amanu innamal-khamru wal-maisiru wal-ansabu wal-azlamu rijsun min amalish-shaytani fajtanibuh",
        "translation": "Wahai orang-orang yang beriman! Sesungguhnya minuman keras, berjudi, (berkurban untuk) berhala, dan mengundi nasib adalah perbuatan keji dan termasuk perbuatan setan. Maka jauhilah.",
        "theme": "halal_haram",
        "confidence": "high",
        "source_check": "QS. Al-Maidah [5]:90, Mushaf Madinah"
    },

    # ──────────────────────────────────────────────────────────
    # AURAT
    # ──────────────────────────────────────────────────────────

    "quran_24_31": {
        "reference": "24:31",
        "surah_ayah": "24:31",
        "surah": 24,
        "ayah": 31,
        "arabic_text": "وَقُل لِّلْمُؤْمِنَٰتِ يَغْضُضْنَ مِنْ أَبْصَٰرِهِنَّ وَيَحْفَظْنَ فُرُوجَهُنَّ وَلَا يُبْدِينَ زِينَتَهُنَّ إِلَّا مَا ظَهَرَ مِنْهَا",
        "transliteration": "Wa qul lil-mumiinati yaghdudna min absarihinna wa yahfazna furujahunna wa la yubdina zinatahunna illa ma zahara minha",
        "translation": "Dan katakanlah kepada para perempuan yang beriman agar mereka menjaga pandangannya, memelihara kemaluannya, dan janganlah menampakkan perhiasannya (auratnya), kecuali yang (biasa) terlihat.",
        "theme": "aurat",
        "confidence": "high",
        "source_check": "QS. An-Nur [24]:31, Mushaf Madinah"
    },
    "quran_33_59": {
        "reference": "33:59",
        "surah_ayah": "33:59",
        "surah": 33,
        "ayah": 59,
        "arabic_text": "يَٰٓأَيُّهَا ٱلنَّبِىُّ قُل لِّأَزْوَٰجِكَ وَبَنَاتِكَ وَنِسَآءِ ٱلْمُؤْمِنِينَ يُدْنِينَ عَلَيْهِنَّ مِن جَلَٰبِيبِهِنَّ",
        "transliteration": "Ya ayyuhan-nabiyyu qul li-azwajika wa banatika wa nisail-muminiina yudniina alayhinna min jalaabibihinn",
        "translation": "Wahai Nabi! Katakanlah kepada istri-istrimu, anak-anak perempuanmu, dan istri-istri orang mukmin, hendaklah mereka menutupkan jilbabnya ke seluruh tubuh mereka.",
        "theme": "aurat",
        "confidence": "high",
        "source_check": "QS. Al-Ahzab [33]:59, Mushaf Madinah"
    },

    # ──────────────────────────────────────────────────────────
    # AKHIRAT & BALASAN AMAL
    # ──────────────────────────────────────────────────────────

    "quran_36_12": {
        "reference": "36:12",
        "surah_ayah": "36:12",
        "surah": 36,
        "ayah": 12,
        "arabic_text": "إِنَّا نَحْنُ نُحْىِ ٱلْمَوْتَىٰ وَنَكْتُبُ مَا قَدَّمُوا۟ وَءَاثَٰرَهُمْ",
        "transliteration": "Inna nahnu nuhyil-mawtaa wa naktubu maa qaddamuu wa aatharahum",
        "translation": "Sungguh, Kamilah yang menghidupkan orang-orang yang mati, dan Kami mencatat apa yang telah mereka kerjakan dan bekas-bekas yang mereka tinggalkan.",
        "theme": "akhirat",
        "confidence": "high",
        "source_check": "QS. Ya-Sin [36]:12, Mushaf Madinah"
    },
    "quran_39_53": {
        "reference": "39:53",
        "surah": 39,
        "ayah": 53,
        "arabic_text": "قُلْ يَٰعِبَادِىَ ٱلَّذِينَ أَسْرَفُوا۟ عَلَىٰٓ أَنفُسِهِمْ لَا تَقْنَطُوا۟ مِن رَّحْمَةِ ٱللَّهِ ۚ إِنَّ ٱللَّهَ يَغْفِرُ ٱلذُّنُوبَ جَمِيعًا",
        "transliteration": "Qul yā 'ibādiyalladhīna asrafū 'alā anfusihim lā taqnaṭū mir-raḥmatillāh. Innallāha yaghfirudhdhunūba jamī'ā",
        "translation": "Wahai hamba-Ku yang melampaui batas, jangan berputus asa dari rahmat Allah. Sesungguhnya Allah mengampuni semua dosa.",
        "theme": "akhirat",
        "sub_theme": "ampunan_allah",
        "confidence": "high",
        "source_check": "QS. Az-Zumar [39]:53 (penggalan)"
    },
    "quran_99_7_8": {
        "reference": "99:7-8",
        "surah": 99,
        "ayah": 7,
        "arabic_text": "فَمَن يَعْمَلْ مِثْقَالَ ذَرَّةٍ خَيْرًا يَرَهُۥ ۝ وَمَن يَعْمَلْ مِثْقَالَ ذَرَّةٍ شَرًّا يَرَهُۥ",
        "transliteration": "Fa-man ya'mal mithqāla dharratin khayray-yarah. Wa man ya'mal mithqāla dharratin sharray-yarah",
        "translation": "Barangsiapa mengerjakan kebaikan seberat zarrah akan melihat balasannya. Barangsiapa mengerjakan kejahatan seberat zarrah akan melihat balasannya.",
        "theme": "akhirat",
        "sub_theme": "balasan_amal",
        "confidence": "high",
        "source_check": "QS. Az-Zalzalah [99]:7-8"
    },

    # ──────────────────────────────────────────────────────────
    # DOA MA'TSUR DARI AL-QURAN
    # ──────────────────────────────────────────────────────────

    "quran_2_201": {
        "reference": "2:201",
        "surah": 2,
        "ayah": 201,
        "arabic_text": "رَبَّنَآ ءَاتِنَا فِى ٱلدُّنْيَا حَسَنَةً وَفِى ٱلْأَخِرَةِ حَسَنَةً وَقِنَا عَذَابَ ٱلنَّارِ",
        "transliteration": "Rabbanā ātinā fid-dunyā ḥasanatan wa fil-ākhirati ḥasanatan wa qinā 'adhāban-nār",
        "translation": "Ya Tuhan kami, berilah kebaikan di dunia dan akhirat, dan lindungi kami dari azab neraka.",
        "theme": "doa",
        "sub_theme": "doa_qurani",
        "confidence": "high",
        "source_check": "QS. Al-Baqarah [2]:201"
    },
    "quran_2_286": {
        "reference": "2:286",
        "surah": 2,
        "ayah": 286,
        "arabic_text": "رَبَّنَا لَا تُؤَاخِذْنَآ إِن نَّسِينَآ أَوْ أَخْطَأْنَا",
        "transliteration": "Rabbanā lā tu'ākhidhnā in-nasīnā aw akhṭa'nā",
        "translation": "Ya Tuhan kami, janganlah Engkau hukum kami jika kami lupa atau melakukan kesalahan.",
        "theme": "doa",
        "sub_theme": "doa_qurani",
        "confidence": "high",
        "source_check": "QS. Al-Baqarah [2]:286 (penggalan)"
    },
}


hadis_collection = {

    # ──────────────────────────────────────────────────────────
    # AQIDAH / RUKUN ISLAM
    # ──────────────────────────────────────────────────────────

    "hadis_bukhari_8": {
        "reference": "bukhari_8",
        "source": "Sahih Bukhari no. 8",
        "arabic_text": "بُنِيَ الْإِسْلَامُ عَلَى خَمْسٍ شَهَادَةِ أَنْ لَا إِلَهَ إِلَّا اللَّهُ وَأَنَّ مُحَمَّدًا رَسُولُ اللَّهِ وَإِقَامِ الصَّلَاةِ وَإِيتَاءِ الزَّكَاةِ وَالْحَجِّ وَصَوْمِ رَمَضَانَ",
        "transliteration": "Buniyal-islāmu 'alā khams: shahādati an lā ilāha illallāhu wa anna Muḥammadan rasūlullāh, wa iqāmiṣ-ṣalāh, wa ītā'iz-zakāh, wal-ḥajj, wa ṣawmi Ramaḍān",
        "translation": "Islam dibangun di atas lima perkara: bersaksi bahwa tidak ada tuhan yang berhak disembah selain Allah dan bahwa Muhammad adalah utusan Allah, mendirikan shalat, menunaikan zakat, haji, dan puasa Ramadhan.",
        "authenticity": "sahih",
        "grading": "Muttafaq 'alaih (Bukhari & Muslim)",
        "confidence": "high",
        "theme": "aqidah"
    },
    "hadis_muslim_16": {
        "reference": "muslim_16",
        "source": "Sahih Muslim no. 16",
        "arabic_text": "أُمِرْتُ أَنْ أُقَاتِلَ النَّاسَ حَتَّى يَشْهَدُوا أَنْ لَا إِلَهَ إِلَّا اللَّهُ وَأَنَّ مُحَمَّدًا رَسُولُ اللَّهِ",
        "transliteration": "Umirtu an uqātilan-nāsa ḥattā yashhadu an lā ilāha illallāhu wa anna Muḥammadan rasūlullāh",
        "translation": "Aku diperintahkan untuk memerangi manusia hingga mereka bersaksi bahwa tidak ada tuhan yang berhak disembah selain Allah dan bahwa Muhammad adalah utusan Allah.",
        "authenticity": "sahih",
        "grading": "Sahih Muslim",
        "confidence": "high",
        "theme": "aqidah"
    },

    # ──────────────────────────────────────────────────────────
    # IBADAH UMUM — NIAT
    # ──────────────────────────────────────────────────────────

    "hadis_bukhari_1_niat": {
        "reference": "Sahih Bukhari No. 1",
        "source": "Bukhari, Kitab Bad'il-Wahy",
        "narrator": "Umar bin Khattab ra.",
        "arabic_text": "إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى",
        "transliteration": "Innamal-a'mālu bin-niyyāti wa innamā li-kulli imri'in mā nawā",
        "translation": "Setiap amal tergantung niatnya. Setiap orang mendapat apa yang ia niatkan.",
        "theme": "ibadah_umum",
        "authenticity": "sahih",
        "grading": "Muttafaqun 'alaih",
        "confidence": "high",
        "fiqh_relevance": ["niat", "semua_ibadah"]
    },

    # ──────────────────────────────────────────────────────────
    # THAHARAH
    # ──────────────────────────────────────────────────────────

    "hadis_muslim_224": {
        "reference": "muslim_224",
        "source": "Sahih Muslim no. 224",
        "arabic_text": "لَا تُقْبَلُ صَلَاةٌ بِغَيْرِ طُهُورٍ",
        "transliteration": "Lā tuqbalu ṣalātun bighayri ṭuhūr",
        "translation": "Tidak diterima shalat tanpa bersuci.",
        "authenticity": "sahih",
        "grading": "Sahih Muslim, dari Abu Hurairah r.a.",
        "confidence": "high",
        "theme": "thaharah"
    },
    "hadis_muslim_223": {
        "reference": "muslim_223",
        "source": "Sahih Muslim no. 223",
        "arabic_text": "الطُّهُورُ شَطْرُ الْإِيمَانِ",
        "transliteration": "Aṭ-ṭuhūru shaṭrul-īmān",
        "translation": "Bersuci adalah separuh iman.",
        "authenticity": "sahih",
        "grading": "Sahih Muslim, dari Abu Malik Al-Asy'ari r.a.",
        "confidence": "high",
        "theme": "thaharah"
    },
    "hadis_muslim_279": {
        "reference": "muslim_279",
        "source": "Sahih Muslim no. 279",
        "arabic_text": "طَهُورُ إِنَاءِ أَحَدِكُمْ إِذَا وَلَغَ فِيهِ الْكَلْبُ أَنْ يَغْسِلَهُ سَبْعَ مَرَّاتٍ أُولَاهُنَّ بِالتُّرَابِ",
        "transliteration": "Ṭahūru inā'i aḥadikum idhā walagha fīhil-kalbu an yagsilahu sab'a marrātin ūlāhunna bit-turāb",
        "translation": "Cara menyucikan bejana salah seorang dari kalian yang dijilat anjing adalah mencucinya tujuh kali, yang pertama dengan tanah.",
        "authenticity": "sahih",
        "grading": "Sahih Muslim, dari Abu Hurairah r.a.",
        "confidence": "high",
        "theme": "thaharah"
    },
    "hadis_muslim_thaharah_iman": {
        "reference": "Sahih Muslim No. 223",
        "source": "Muslim, Kitab At-Thaharah",
        "narrator": "Abu Malik Al-Asy'ari ra.",
        "arabic_text": "الطُّهُورُ شَطْرُ الْإِيمَانِ",
        "transliteration": "Aṭ-ṭuhūru shaṭrul-īmān",
        "translation": "Bersuci adalah setengah dari iman.",
        "theme": "thaharah",
        "authenticity": "sahih",
        "grading": "Sahih Muslim",
        "confidence": "high",
        "fiqh_relevance": ["thaharah", "wudhu"]
    },
    "hadis_muslim_279_anjing": {
        "reference": "Sahih Muslim No. 279",
        "source": "Muslim, Kitab At-Thaharah",
        "narrator": "Abu Hurairah ra.",
        "arabic_text": "إِذَا وَلَغَ الْكَلْبُ فِي إِنَاءِ أَحَدِكُمْ فَلْيَغْسِلْهُ سَبْعَ مَرَّاتٍ أُولَاهُنَّ بِالتُّرَابِ",
        "transliteration": "Idhā walaga al-kalbu fī inā'i aḥadikum fal-yaghsilhu sab'a marrātin ūlāhunna bit-turāb",
        "translation": "Jika anjing menjilat bejana salah seorang dari kamu, cucilah tujuh kali, yang pertama dengan tanah.",
        "theme": "thaharah",
        "authenticity": "sahih",
        "grading": "Sahih Muslim",
        "confidence": "high",
        "fiqh_relevance": ["najis_mughallazah"]
    },

    # ──────────────────────────────────────────────────────────
    # SHALAT
    # ──────────────────────────────────────────────────────────

    "hadis_muslim_233": {
        "reference": "muslim_233",
        "source": "Sahih Muslim no. 233",
        "arabic_text": "الصَّلَوَاتُ الْخَمْسُ وَالْجُمُعَةُ إِلَى الْجُمُعَةِ كَفَّارَةٌ لِمَا بَيْنَهُنَّ مَا لَمْ تُغْشَ الْكَبَائِرُ",
        "transliteration": "Aṣ-ṣalawātul-khamsu wal-jumu'atu ilal-jumu'ati kaffāratun limā baynahunna mā lam tughashal-kabā'ir",
        "translation": "Shalat lima waktu, dan Jum'at ke Jum'at berikutnya adalah penghapus dosa di antara keduanya selama dosa-dosa besar tidak dilakukan.",
        "authenticity": "sahih",
        "grading": "Sahih Muslim, dari Abu Hurairah r.a.",
        "confidence": "high",
        "theme": "shalat"
    },
    "hadis_bukhari_527": {
        "reference": "bukhari_527",
        "source": "Sahih Bukhari no. 527",
        "arabic_text": "مَنْ أَدْرَكَ رَكْعَةً مِنَ الصَّلَاةِ فَقَدْ أَدْرَكَ الصَّلَاةَ",
        "transliteration": "Man adraka rak'atan minaṣ-ṣalāti faqad adraka ṣ-ṣalāh",
        "translation": "Barang siapa mendapati satu rakaat dari shalat, maka sesungguhnya ia telah mendapatkan shalat tersebut.",
        "authenticity": "sahih",
        "grading": "Muttafaq 'alaih, dari Abu Hurairah r.a.",
        "confidence": "high",
        "theme": "shalat"
    },
    "hadis_muslim_233_shalat": {
        "reference": "Sahih Muslim No. 233",
        "source": "Muslim, Kitab Al-Iman",
        "narrator": "Jabir bin Abdillah ra.",
        "arabic_text": "بَيْنَ الرَّجُلِ وَبَيْنَ الشِّرْكِ وَالْكُفْرِ تَرْكُ الصَّلَاةِ",
        "transliteration": "Baynar-rajuli wa baynashshirki wal-kufri tarku-ṣ-ṣalāh",
        "translation": "Pemisah antara seseorang dengan syirik dan kufur adalah meninggalkan shalat.",
        "theme": "shalat",
        "authenticity": "sahih",
        "grading": "Sahih Muslim",
        "confidence": "high",
        "fiqh_relevance": ["kewajiban_shalat", "meninggalkan_shalat"]
    },
    "hadis_bukhari_527_shalat_tepat": {
        "reference": "Sahih Bukhari No. 527",
        "source": "Bukhari, Kitab Mawaqit As-Shalah",
        "narrator": "Ibn Mas'ud ra.",
        "arabic_text": "الصَّلَاةُ عَلَى وَقْتِهَا",
        "transliteration": "Aṣ-ṣalātu 'alā waqtihā",
        "translation": "Shalat tepat waktu (adalah amal yang paling dicintai Allah).",
        "theme": "shalat",
        "authenticity": "sahih",
        "grading": "Muttafaqun 'alaih",
        "confidence": "high",
        "fiqh_relevance": ["waktu_shalat", "awal_waktu"]
    },
    "hadis_abu_dawud_1211_jama_qashar": {
        "reference": "Sunan Abu Dawud No. 1211",
        "source": "Abu Dawud, Kitab As-Shalah",
        "narrator": "Ibn Umar ra.",
        "arabic_text": "كَانَ النَّبِيُّ ﷺ إِذَا سَافَرَ يَقْصُرُ الصَّلَاةَ وَيُجْمَعُ بَيْنَهُمَا",
        "transliteration": "Kāna an-nabiyyu ṣallallāhu 'alayhi wa sallama idhā sāfara yaqṣuru ṣ-ṣalāta wa yajma'u baynahumā",
        "translation": "Nabi ﷺ bila safar mengqashar dan menjama' shalat.",
        "theme": "shalat",
        "authenticity": "sahih",
        "grading": "Abu Dawud — dihasankan Al-Albani",
        "confidence": "high",
        "fiqh_relevance": ["qashar", "jama_shalat", "musafir"]
    },
    "hadis_bukhari_876_jumat": {
        "reference": "Sahih Bukhari No. 876",
        "source": "Bukhari, Kitab Al-Jumuah",
        "narrator": "—",
        "theme": "shalat",
        "arabic_text": "— PENDING VERIFIKASI —",
        "transliteration": "— pending —",
        "translation": "Hadis kewajiban shalat Jumat — teks Arab pending verifikasi.",
        "authenticity": "sahih",
        "grading": "Sahih Bukhari (pending detail citation)",
        "confidence": "pending",
        "status": "stub"
    },
    "hadis_tirmidzi_415_rawatib": {
        "reference": "Sunan Tirmidzi No. 415",
        "source": "Tirmidzi, Kitab As-Shalah",
        "narrator": "—",
        "theme": "shalat",
        "arabic_text": "— PENDING VERIFIKASI —",
        "transliteration": "— pending —",
        "translation": "Hadis keutamaan 12 rakaat rawatib — teks Arab pending verifikasi.",
        "authenticity": "sahih",
        "grading": "Tirmidzi (pending detail citation)",
        "confidence": "pending",
        "status": "stub"
    },

    # ──────────────────────────────────────────────────────────
    # PUASA
    # ──────────────────────────────────────────────────────────

    "hadis_bukhari_1901_puasa": {
        "reference": "Sahih Bukhari No. 1901",
        "source": "Bukhari, Kitab As-Saum",
        "narrator": "Abu Hurairah ra.",
        "arabic_text": "مَنْ صَامَ رَمَضَانَ إِيمَانًا وَاحْتِسَابًا غُفِرَ لَهُ مَا تَقَدَّمَ مِنْ ذَنْبِهِ",
        "transliteration": "Man ṣāma Ramaḍāna īmānan waḥtisāban ghufira lahū mā taqaddama min dhanbih",
        "translation": "Barangsiapa puasa Ramadhan dengan iman dan mengharap pahala, diampuni dosanya yang telah lalu.",
        "theme": "puasa",
        "authenticity": "sahih",
        "grading": "Muttafaqun 'alaih",
        "confidence": "high",
        "fiqh_relevance": ["keutamaan_ramadhan"]
    },
    "hadis_muslim_1164_syawal": {
        "reference": "Sahih Muslim No. 1164",
        "source": "Muslim, Kitab As-Siyam",
        "narrator": "Abu Ayyub Al-Anshari ra.",
        "arabic_text": "مَنْ صَامَ رَمَضَانَ ثُمَّ أَتْبَعَهُ سِتًّا مِنْ شَوَّالٍ كَانَ كَصِيَامِ الدَّهْرِ",
        "transliteration": "Man ṣāma Ramaḍāna thumma atba'ahū sittan min Shawwālin kāna kaṣiyāmid-dahr",
        "translation": "Puasa Ramadhan lalu diikuti enam hari Syawal seperti puasa setahun penuh.",
        "theme": "puasa",
        "authenticity": "sahih",
        "grading": "Sahih Muslim",
        "confidence": "high",
        "fiqh_relevance": ["puasa_sunnah_syawal"]
    },

    # ──────────────────────────────────────────────────────────
    # ZAKAT
    # ──────────────────────────────────────────────────────────

    "hadis_bukhari_1404_zakat": {
        "reference": "Sahih Bukhari No. 1404",
        "source": "Bukhari, Kitab Az-Zakah",
        "narrator": "—",
        "theme": "zakat",
        "arabic_text": "— PENDING VERIFIKASI —",
        "transliteration": "— pending —",
        "translation": "Hadis nishab zakat emas/perak — teks Arab pending verifikasi.",
        "authenticity": "sahih",
        "grading": "Sahih Bukhari (pending detail citation)",
        "confidence": "pending",
        "status": "stub"
    },

    # ──────────────────────────────────────────────────────────
    # HAJI
    # ──────────────────────────────────────────────────────────

    "hadis_bukhari_1773_haji_mabrur": {
        "reference": "Sahih Bukhari No. 1773",
        "source": "Bukhari, Kitab Al-Hajj",
        "narrator": "Abu Hurairah ra.",
        "arabic_text": "الْحَجُّ الْمَبْرُورُ لَيْسَ لَهُ جَزَاءٌ إِلَّا الْجَنَّةُ",
        "transliteration": "Al-ḥajju al-mabrūru laysa lahū jazā'un illal-jannah",
        "translation": "Haji mabrur tidak ada balasannya kecuali surga.",
        "theme": "haji",
        "authenticity": "sahih",
        "grading": "Muttafaqun 'alaih",
        "confidence": "high",
        "fiqh_relevance": ["keutamaan_haji"]
    },
    "hadis_muslim_1337_haji": {
        "reference": "Sahih Muslim No. 1337",
        "source": "Muslim, Kitab Al-Hajj",
        "narrator": "—",
        "theme": "haji",
        "arabic_text": "— PENDING VERIFIKASI —",
        "transliteration": "— pending —",
        "translation": "Hadis syarat wajib haji (istitha'ah) — teks Arab pending verifikasi.",
        "authenticity": "sahih",
        "grading": "Sahih Muslim (pending detail citation)",
        "confidence": "pending",
        "status": "stub"
    },

    # ──────────────────────────────────────────────────────────
    # NIKAH
    # ──────────────────────────────────────────────────────────

    "hadis_bukhari_5066_nikah": {
        "reference": "Sahih Bukhari No. 5066",
        "source": "Bukhari, Kitab An-Nikah",
        "narrator": "Ibn Mas'ud ra.",
        "arabic_text": "يَا مَعْشَرَ الشَّبَابِ مَنِ اسْتَطَاعَ مِنْكُمُ الْبَاءَةَ فَلْيَتَزَوَّجْ",
        "transliteration": "Yā ma'shara ash-shabābi manistaṭā'a minkumul-bā'ata fal-yatazawwaj",
        "translation": "Wahai para pemuda, barangsiapa mampu menikah, maka menikahlah.",
        "theme": "nikah",
        "authenticity": "sahih",
        "grading": "Muttafaqun 'alaih",
        "confidence": "high",
        "fiqh_relevance": ["anjuran_nikah"]
    },
    "hadis_abu_dawud_2085_wali": {
        "reference": "Sunan Abu Dawud No. 2085",
        "source": "Abu Dawud, Kitab An-Nikah",
        "narrator": "Abu Musa ra.",
        "arabic_text": "لَا نِكَاحَ إِلَّا بِوَلِيٍّ",
        "transliteration": "Lā nikāḥa illā bi-waliyy",
        "translation": "Tidak sah nikah kecuali dengan wali.",
        "theme": "nikah",
        "authenticity": "sahih",
        "grading": "Sahih — Ahmad, Abu Dawud, Tirmidzi, Ibn Majah",
        "confidence": "high",
        "fiqh_relevance": ["wali_nikah", "syarat_nikah"]
    },
    "hadis_muslim_1408_kriteria": {
        "reference": "Sahih Muslim No. 1408",
        "source": "Muslim, Kitab An-Nikah",
        "narrator": "Abu Hurairah ra.",
        "arabic_text": "تُنْكَحُ الْمَرْأَةُ لِأَرْبَعٍ: لِمَالِهَا وَلِحَسَبِهَا وَلِجَمَالِهَا وَلِدِينِهَا، فَاظْفَرْ بِذَاتِ الدِّينِ تَرِبَتْ يَدَاكَ",
        "transliteration": "Tunkahu al-mar'atu li-arba': limālihā wa liḥasabihā wa lijamālihā wa lidīnihā. Faẓfar bidhātid-dīni tarbat yadāk",
        "translation": "Perempuan dinikahi karena empat hal: harta, keturunan, kecantikan, dan agamanya. Pilihlah yang beragama, niscaya kamu beruntung.",
        "theme": "nikah",
        "authenticity": "sahih",
        "grading": "Muttafaqun 'alaih",
        "confidence": "high",
        "fiqh_relevance": ["kriteria_pasangan"]
    },

    # ──────────────────────────────────────────────────────────
    # WARIS
    # ──────────────────────────────────────────────────────────

    "hadis_bukhari_6764": {
        "reference": "bukhari_6764",
        "source": "Sahih Bukhari no. 6764",
        "arabic_text": "لَا يَرِثُ الْمُسْلِمُ الْكَافِرَ وَلَا الْكَافِرُ الْمُسْلِمَ",
        "transliteration": "La yarithu al-muslimu al-kafira wa la al-kafiru al-muslim",
        "translation": "Seorang Muslim tidak mewarisi orang kafir, dan orang kafir tidak mewarisi seorang Muslim.",
        "authenticity": "sahih",
        "grading": "Muttafaq alaih, dari Usamah bin Zaid r.a.",
        "confidence": "high",
        "theme": "waris"
    },
    "hadis_muslim_1614": {
        "reference": "muslim_1614",
        "source": "Sahih Muslim no. 1614",
        "arabic_text": "لَا يَتَوَارَثُ أَهْلُ مِلَّتَيْنِ شَتَّى",
        "transliteration": "La yatawarathu ahlu millatayni shatta",
        "translation": "Pemeluk dua agama yang berbeda tidak saling mewarisi.",
        "authenticity": "sahih",
        "grading": "Sahih Muslim, dari Jabir r.a.",
        "confidence": "high",
        "theme": "waris"
    },
    "hadis_bukhari_6764_waris": {
        "reference": "Sahih Bukhari No. 6764",
        "source": "Bukhari, Kitab Al-Faraid",
        "narrator": "Usamah bin Zaid ra.",
        "arabic_text": "لَا يَرِثُ الْمُسْلِمُ الْكَافِرَ وَلَا الْكَافِرُ الْمُسْلِمَ",
        "transliteration": "Lā yarithu al-muslimu al-kāfira wa lā al-kāfiru al-muslima",
        "translation": "Muslim tidak mewarisi kafir dan kafir tidak mewarisi Muslim.",
        "theme": "waris",
        "authenticity": "sahih",
        "grading": "Muttafaqun 'alaih",
        "confidence": "high",
        "fiqh_relevance": ["penghalang_waris", "perbedaan_agama"]
    },
    "hadis_bukhari_6732_faraid": {
        "reference": "Sahih Bukhari No. 6732",
        "source": "Bukhari, Kitab Al-Faraid",
        "narrator": "Ibn Abbas ra.",
        "arabic_text": "أَلْحِقُوا الْفَرَائِضَ بِأَهْلِهَا فَمَا بَقِيَ فَهُوَ لِأَوْلَى رَجُلٍ ذَكَرٍ",
        "transliteration": "Alḥiqū al-farā'iḍa bi-ahlihā fa-mā baqiya fa-huwa li-awlā rajulin dhakar",
        "translation": "Bagikan harta waris kepada yang berhak, sisanya untuk laki-laki yang paling dekat.",
        "theme": "waris",
        "authenticity": "sahih",
        "grading": "Muttafaqun 'alaih",
        "confidence": "high",
        "fiqh_relevance": ["ashabah", "pembagian_waris"]
    },

    # ──────────────────────────────────────────────────────────
    # MUAMALAH & EKONOMI
    # ──────────────────────────────────────────────────────────

    "hadis_muslim_1598_riba": {
        "reference": "Sahih Muslim No. 1598",
        "source": "Muslim, Kitab Al-Musaqah",
        "narrator": "Jabir ra.",
        "arabic_text": "لَعَنَ رَسُولُ اللهِ ﷺ آكِلَ الرِّبَا وَمُوكِلَهُ وَكَاتِبَهُ وَشَاهِدَيْهِ وَقَالَ هُمْ سَوَاءٌ",
        "transliteration": "La'ana rasūlullāhi ṣallallāhu 'alayhi wa sallama ākila ar-ribā wa mūkilahu wa kātibahu wa shāhidayhi wa qāla hum sawā'",
        "translation": "Rasulullah ﷺ melaknat pemakan riba, pemberinya, penulisnya, dan dua saksinya. Mereka semua sama.",
        "theme": "muamalah",
        "authenticity": "sahih",
        "grading": "Sahih Muslim",
        "confidence": "high",
        "fiqh_relevance": ["riba_haram", "bank_konvensional", "pinjol"]
    },
    "hadis_bukhari_2079_khiyar": {
        "reference": "Sahih Bukhari No. 2079",
        "source": "Bukhari, Kitab Al-Buyu'",
        "narrator": "—",
        "theme": "muamalah",
        "arabic_text": "— PENDING VERIFIKASI —",
        "transliteration": "— pending —",
        "translation": "Hadis hak khiyar dalam jual beli — teks Arab pending verifikasi.",
        "authenticity": "sahih",
        "grading": "Sahih Bukhari (pending detail citation)",
        "confidence": "pending",
        "status": "stub"
    },

    # ──────────────────────────────────────────────────────────
    # HALAL / HARAM
    # ──────────────────────────────────────────────────────────

    "hadis_bukhari_5585": {
        "reference": "bukhari_5585",
        "source": "Sahih Bukhari no. 5585",
        "arabic_text": "كُلُّ مُسْكِرٍ حَرَامٌ",
        "transliteration": "Kullu muskirin haraam",
        "translation": "Setiap yang memabukkan adalah haram.",
        "authenticity": "sahih",
        "grading": "Muttafaq alaih, dari Ibnu Umar r.a.",
        "confidence": "high",
        "theme": "halal_haram"
    },
    "hadis_abu_dawud": {
        "reference": "abu_dawud_3674",
        "source": "Sunan Abu Dawud no. 3674",
        "arabic_text": "إِنَّ اللَّهَ حَرَّمَ الْخَمْرَ وَثَمَنَهَا",
        "transliteration": "Innallaha harramal-khamra wa thamanaha",
        "translation": "Sesungguhnya Allah mengharamkan khamar dan harga penjualannya.",
        "authenticity": "sahih",
        "grading": "Dishahihkan Al-Albani, dari Ibnu Abbas r.a.",
        "confidence": "high",
        "theme": "halal_haram"
    },
    "hadis_bukhari_52_syubhat": {
        "reference": "Sahih Bukhari No. 52",
        "source": "Bukhari, Kitab Al-Iman",
        "narrator": "Nu'man bin Basyir ra.",
        "arabic_text": "الْحَلَالُ بَيِّنٌ وَالْحَرَامُ بَيِّنٌ وَبَيْنَهُمَا مُشَبَّهَاتٌ لَا يَعْلَمُهَا كَثِيرٌ مِنَ النَّاسِ، فَمَنِ اتَّقَى الشُّبُهَاتِ اسْتَبْرَأَ لِدِينِهِ وَعِرْضِهِ",
        "transliteration": "Al-ḥalālu bayyinun wal-ḥarāmu bayyinun wa baynahumā mushabbahāt. Fa-manittaqā ash-shubuhāti istabra'a li-dīnihī wa 'irḍih",
        "translation": "Halal itu jelas, haram itu jelas, di antaranya ada syubhat. Siapa menjaga diri dari syubhat, ia membersihkan agama dan kehormatannya.",
        "theme": "halal_haram",
        "authenticity": "sahih",
        "grading": "Muttafaqun 'alaih",
        "confidence": "high",
        "fiqh_relevance": ["syubhat", "fintech", "crypto", "asuransi"]
    },

    # ──────────────────────────────────────────────────────────
    # AKHLAK SOSIAL
    # ──────────────────────────────────────────────────────────

    "hadis_bukhari_2620": {
        "reference": "bukhari_2620",
        "source": "Sahih Bukhari no. 2620",
        "arabic_text": "قَدِمَتْ عَلَيَّ أُمِّي وَهِيَ مُشْرِكَةٌ فَاسْتَفْتَيْتُ رَسُولَ اللَّهِ قُلْتُ إِنَّ أُمِّي قَدِمَتْ وَهِيَ رَاغِبَةٌ أَفَأَصِلُ أُمِّي قَالَ نَعَمْ صِلِي أُمَّكِ",
        "transliteration": "Qadimat alayya ummi wa hiya mushrikatun fastaftaytu rasulullah qultu inna ummi qadimat wa hiya raghibah afa-asilu ummi qala naam sili ummak",
        "translation": "Ibuku datang kepadaku dalam keadaan musyrik. Aku meminta fatwa kepada Rasulullah dan berkata: Ibuku datang, apakah aku boleh menyambung hubungan dengannya? Beliau menjawab: Ya, sambunglah hubungan dengan ibumu.",
        "authenticity": "sahih",
        "grading": "Muttafaq alaih, dari Asma binti Abu Bakr r.a.",
        "confidence": "high",
        "theme": "akhlak"
    },
    "hadis_muslim_1003": {
        "reference": "muslim_1003",
        "source": "Sahih Muslim no. 1003",
        "arabic_text": "لَا يَحِلُّ لِمُسْلِمٍ أَنْ يَهْجُرَ أَخَاهُ فَوْقَ ثَلَاثَةِ أَيَّامٍ",
        "transliteration": "La yahillu li-muslimin an yahjura akhahu fawqa thalathat ayyam",
        "translation": "Tidak halal bagi seorang Muslim untuk memutuskan hubungan dengan saudaranya lebih dari tiga hari.",
        "authenticity": "sahih",
        "grading": "Sahih Muslim, dari Abu Hurairah r.a.",
        "confidence": "high",
        "theme": "akhlak"
    },
    "hadis_muslim_2162": {
        "reference": "muslim_2162",
        "source": "Sahih Muslim no. 2162",
        "arabic_text": "حَقُّ الْمُسْلِمِ عَلَى الْمُسْلِمِ سِتٌّ إِذَا لَقِيتَهُ فَسَلِّمْ عَلَيْهِ وَإِذَا دَعَاكَ فَأَجِبْهُ وَإِذَا اسْتَنْصَحَكَ فَانْصَحْهُ وَإِذَا عَطَسَ فَحَمِدَ اللَّهَ فَسَمِّتْهُ وَإِذَا مَرِضَ فَعُدْهُ وَإِذَا مَاتَ فَاتَّبِعْهُ",
        "transliteration": "Haqqul-muslimi alal-muslimi sittu: idha laqiitahu fa-sallim alayh, wa idha daaka fa-ajibh, wa idha istansahaka fan-sah, wa idha atasa fa-hamidallaha fa-sammithu, wa idha marida fa-udh, wa idha mata fattabih",
        "translation": "Hak seorang Muslim atas Muslim lainnya ada enam: bila bertemu ucapkan salam, bila mengundang penuhilah, bila meminta nasihat nasihati, bila bersin lalu memuji Allah doakanlah, bila sakit jenguklah, dan bila meninggal iringilah jenazahnya.",
        "authenticity": "sahih",
        "grading": "Sahih Muslim, dari Abu Hurairah r.a.",
        "confidence": "high",
        "theme": "akhlak"
    },
    "hadis_muslim_2589_ghibah": {
        "reference": "Sahih Muslim No. 2589",
        "source": "Muslim, Kitab Al-Birr",
        "narrator": "Abu Hurairah ra.",
        "arabic_text": "ذِكْرُكَ أَخَاكَ بِمَا يَكْرَهُ",
        "transliteration": "Dhikruka akhāka bimā yakrah",
        "translation": "Ghibah adalah kamu menyebut saudaramu dengan sesuatu yang ia benci.",
        "theme": "akhlak",
        "authenticity": "sahih",
        "grading": "Sahih Muslim",
        "confidence": "high",
        "fiqh_relevance": ["ghibah", "media_sosial", "konten_negatif"]
    },
    "hadis_bukhari_2620_non_muslim": {
        "reference": "Sahih Bukhari No. 2620",
        "source": "Bukhari, Kitab Al-Hibah",
        "narrator": "Asma' binti Abu Bakr ra.",
        "arabic_text": "قَدِمَتْ عَلَيَّ أُمِّي وَهِيَ مُشْرِكَةٌ... أَفَأَصِلُ أُمِّي؟ قَالَ: نَعَمْ صِلِي أُمَّكِ",
        "transliteration": "Qadimat 'alayya ummī wa hiya mushrikata... afaṣilu ummī? Qāla: na'am ṣilī ummak",
        "translation": "Ibuku datang dan masih musyrik... Bolehkah aku menyambung hubungan dengannya? Rasulullah menjawab: Ya, sambunglah.",
        "theme": "akhlak",
        "authenticity": "sahih",
        "grading": "Muttafaqun 'alaih",
        "confidence": "high",
        "fiqh_relevance": ["hubungan_keluarga_non_muslim", "silaturahmi_muallaf"]
    },

    # ──────────────────────────────────────────────────────────
    # ILMU / TAFAQQUH FID-DIN
    # ──────────────────────────────────────────────────────────

    "hadis_bukhari_ilmu_71": {
        "reference": "Sahih Bukhari No. 71",
        "source": "Bukhari, Kitab Al-Ilm",
        "narrator": "Muawiyah ra.",
        "arabic_text": "مَنْ يُرِدِ اللهُ بِهِ خَيْرًا يُفَقِّهْهُ فِي الدِّينِ",
        "transliteration": "Man yuridillāhu bihī khayran yufaqqihhū fid-dīn",
        "translation": "Siapa yang Allah kehendaki kebaikan padanya, Allah jadikan ia faqih dalam agama.",
        "theme": "ilmu",
        "authenticity": "sahih",
        "grading": "Muttafaqun 'alaih",
        "confidence": "high",
        "fiqh_relevance": ["menuntut_ilmu", "tafaqquh_fid_din"]
    },
}


shafii_rules = {

    # ──────────────────────────────────────────────────────────
    # AQIDAH / SYAHADAT
    # ──────────────────────────────────────────────────────────

    "syahadat": {
        "ruling": "wajib",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_3_18", "quran_47_19"],
        "basis_hadis": ["hadis_bukhari_8", "hadis_muslim_16"],
        "keywords": ["syahadat", "tauhid", "masuk islam", "ikrar", "dua kalimat tayyibah", "kalimat syahadat"],
        "reasoning": "Syahadat adalah rukun pertama Islam dan fondasi akidah. Dalam mazhab Shafi'i, pengucapan syahadat dengan lisan disertai keyakinan hati adalah syarat sah keislaman seseorang.",
        "confidence": "high"
    },

    # ──────────────────────────────────────────────────────────
    # THAHARAH
    # ──────────────────────────────────────────────────────────

    "thaharah_wudhu": {
        "ruling": "wajib",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_5_6", "quran_2_222"],
        "basis_hadis": ["hadis_muslim_224", "hadis_muslim_223"],
        "keywords": ["wudhu", "bersuci", "thaharah", "hadas kecil", "basuh muka", "cuci tangan", "cara wudhu"],
        "reasoning": "Wudhu adalah syarat sah shalat. Mazhab Shafi'i mewajibkan empat fardu wudhu: membasuh wajah, kedua tangan hingga siku, mengusap sebagian kepala, membasuh kedua kaki hingga mata kaki.",
        "confidence": "high"
    },
    "thaharah_mandi_wajib": {
        "ruling": "wajib",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_5_6"],
        "basis_hadis": ["hadis_muslim_279"],
        "keywords": ["mandi", "junub", "ghusl", "bersuci besar", "thaharah besar", "setelah berhubungan", "baru masuk islam"],
        "reasoning": "Mandi wajib (ghusl) diwajibkan oleh tiga sebab: janabah (setelah jimak atau keluar mani), haid, dan nifas. Muallaf yang baru masuk Islam juga dianjurkan mandi sebagai bentuk penyucian.",
        "confidence": "high"
    },
    "thaharah_tayammum": {
        "ruling": "boleh_pengganti_wudhu",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_4_43"],
        "basis_hadis": [],
        "keywords": ["tayammum", "debu", "tidak ada air", "sakit", "safar", "darurat bersuci"],
        "reasoning": "Tayammum dibolehkan sebagai pengganti wudhu atau ghusl saat tidak ada air atau tidak mampu menggunakannya karena sakit. Caranya: niat, mengusap wajah dan kedua tangan hingga pergelangan dengan debu suci.",
        "confidence": "high"
    },

    # ──────────────────────────────────────────────────────────
    # THAHARAH — NAJIS
    # ──────────────────────────────────────────────────────────

    "najis_ringkan": {
        "ruling": "wajib_dibersihkan",
        "madhab": "Shafi'i",
        "basis_quran": [],
        "basis_hadis": [],
        "keywords": ["najis", "air seni bayi laki-laki", "hadas", "najis ringan", "najis mukhaffafah"],
        "reasoning": "Najis mukhaffafah (ringan) seperti air seni bayi laki-laki yang belum makan selain ASI cukup disucikan dengan memercikkan air ke seluruh area yang terkena.",
        "confidence": "high"
    },
    "najis_sedang": {
        "ruling": "wajib_dibersihkan",
        "madhab": "Shafi'i",
        "basis_quran": [],
        "basis_hadis": [],
        "keywords": ["najis", "darah", "feses", "kotoran", "air seni", "najis sedang", "najis mutawassithah"],
        "reasoning": "Najis mutawassithah (sedang) seperti darah, feses, dan air seni harus dihilangkan 'ain (zatnya) lalu dicuci dengan air hingga hilang warna, bau, dan rasanya.",
        "confidence": "high"
    },
    "najis_berat": {
        "ruling": "wajib_dibersihkan",
        "madhab": "Shafi'i",
        "basis_quran": [],
        "basis_hadis": ["hadis_muslim_279"],
        "keywords": ["najis", "anjing", "babi", "jilatan anjing", "najis berat", "najis mughallazah", "tujuh kali"],
        "reasoning": "Najis mughallazah (berat) dari jilatan anjing atau babi wajib dibasuh tujuh kali, salah satunya dicampur tanah. Ini berdasarkan hadis shahih Muslim no. 279.",
        "confidence": "high"
    },

    # ──────────────────────────────────────────────────────────
    # SHALAT
    # ──────────────────────────────────────────────────────────

    "shalat_lima_waktu": {
        "ruling": "wajib",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_2_43", "quran_4_103", "quran_17_78", "quran_2_238"],
        "basis_hadis": ["hadis_muslim_233", "hadis_bukhari_8"],
        "keywords": ["shalat", "salah", "rukuk", "sujud", "takbir", "imam", "shalat lima waktu", "subuh", "dzuhur", "ashar", "maghrib", "isya"],
        "reasoning": "Shalat lima waktu adalah rukun Islam kedua dan kewajiban individual (fardhu 'ain) setiap Muslim yang baligh dan berakal. Mazhab Shafi'i menetapkan syarat dan rukun shalat yang ketat.",
        "confidence": "high"
    },
    "shalat_jama_qashar_safar": {
        "ruling": "boleh",
        "madhab": "Shafi'i",
        "basis_quran": [],
        "basis_hadis": ["hadis_abu_dawud_1211_jama_qashar"],
        "keywords": ["jama", "qashar", "safar", "perjalanan", "musafir", "shalat di jalan", "shalat perjalanan"],
        "reasoning": "Musafir yang bepergian minimal 2 marhalah (~80 km) boleh mengqashar shalat 4 rakaat menjadi 2, dan menjama' Zhuhur-Ashar atau Maghrib-Isya. Syarat: niat sebelum shalat pertama, tidak bermakmum pada imam yang mukim.",
        "confidence": "high"
    },
    "shalat_jumat_kewajiban": {
        "ruling": "fardhu_ain",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_62_9"],
        "basis_hadis": ["hadis_bukhari_876_jumat"],
        "keywords": ["jumat", "shalat jumat", "wajib jumat", "khutbah jumat", "meninggalkan jumat"],
        "reasoning": "Shalat Jumat fardhu ain bagi laki-laki Muslim, baligh, berakal, sehat, dan mukim. Syarat sah: dilaksanakan berjamaah minimal 40 orang (qaul azhar Syafi'i), didahului dua khutbah, di waktu Zhuhur.",
        "confidence": "high"
    },
    "shalat_sunnah_rawatib": {
        "ruling": "sunnah_muakkadah",
        "madhab": "Shafi'i",
        "basis_quran": [],
        "basis_hadis": ["hadis_tirmidzi_415_rawatib"],
        "keywords": ["shalat sunnah", "rawatib", "sebelum subuh", "setelah zhuhur", "shalat 12 rakaat", "sunnah muakkadah"],
        "reasoning": "Sunnah rawatib muakkadah: 2 rakaat sebelum Subuh, 4 sebelum Zhuhur, 2 setelah Zhuhur, 2 setelah Maghrib, 2 setelah Isya — total 12 rakaat. Hadis menyebutkan balasan rumah di surga.",
        "confidence": "high"
    },

    # ──────────────────────────────────────────────────────────
    # PUASA
    # ──────────────────────────────────────────────────────────

    "puasa_ramadhan": {
        "ruling": "wajib",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_2_183", "quran_2_185"],
        "basis_hadis": ["hadis_bukhari_8"],
        "keywords": ["puasa", "ramadhan", "bulan puasa", "sahur", "berbuka", "berpuasa", "wajib puasa"],
        "reasoning": "Puasa Ramadhan adalah rukun Islam keempat, wajib bagi setiap Muslim yang mukallaf, sehat, dan mukim. Syarat sah: niat sebelum subuh, menahan diri dari pembatal puasa.",
        "confidence": "high"
    },
    "puasa_muallaf_tengah_ramadhan": {
        "ruling": "wajib_sejak_islam",
        "madhab": "Shafi'i",
        "basis_quran": [],
        "basis_hadis": [],
        "keywords": ["puasa", "baru muslim", "muallaf", "ramadhan tengah", "masuk islam bulan puasa"],
        "reasoning": "Muallaf yang masuk Islam di tengah bulan Ramadhan wajib berpuasa mulai hari ia masuk Islam. Hari-hari sebelum masuk Islam tidak diwajibkan qadha karena ia belum mukallaf.",
        "confidence": "high"
    },
    "puasa_qadha": {
        "ruling": "wajib",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_2_184"],
        "basis_hadis": [],
        "keywords": ["qadha puasa", "ganti puasa", "bayar puasa", "batal puasa", "puasa sakit", "puasa haid"],
        "reasoning": "Wajib mengqadha puasa Ramadhan yang ditinggalkan karena udzur (sakit, safar, haid, nifas). Dilaksanakan di hari lain sebelum Ramadhan berikutnya. Jika ditunda hingga Ramadhan berikutnya tanpa udzur, wajib qadha + fidyah.",
        "confidence": "high"
    },
    "puasa_fidyah": {
        "ruling": "wajib",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_2_184"],
        "basis_hadis": [],
        "keywords": ["fidyah", "lansia puasa", "tidak mampu puasa", "sakit permanen", "hamil menyusui fidyah"],
        "reasoning": "Fidyah wajib bagi yang tidak mampu puasa secara permanen (lansia, sakit menahun). Juga bagi ibu hamil/menyusui yang tidak berpuasa khawatir anaknya — wajib qadha + fidyah menurut Syafi'i. Besarnya: 1 mud (~750 gr) makanan pokok per hari.",
        "confidence": "high"
    },
    "puasa_digital_konteks_ibadah": {
        "ruling": "tidak_ada_dalil_khusus",
        "madhab": "kontemporer_maslahat",
        "basis_quran": ["quran_2_183"],
        "basis_hadis": [],
        "keywords": ["puasa medsos", "detox digital", "puasa HP", "istirahat medsos", "digital fasting"],
        "reasoning": "Tidak ada dalil khusus 'puasa media sosial' dalam fiqh. Namun konsep menjaga diri dari hal yang sia-sia (laghw) didukung nash. Praktik 'digital detox' di bulan Ramadhan atau untuk meningkatkan ibadah: boleh dan bahkan dianjurkan sebagai sarana mendekatkan diri kepada Allah.",
        "confidence": "medium"
    },

    # ──────────────────────────────────────────────────────────
    # ZAKAT
    # ──────────────────────────────────────────────────────────

    "zakat_fitrah": {
        "ruling": "wajib",
        "madhab": "Shafi'i",
        "basis_quran": [],
        "basis_hadis": [],
        "keywords": ["zakat fitrah", "akhir ramadhan", "zakat puasa", "makanan pokok", "beras zakat"],
        "reasoning": "Zakat fitrah wajib bagi setiap Muslim yang memiliki lebih dari kebutuhan pokok pada hari raya. Besarnya 1 sha' (sekitar 2,5 kg) makanan pokok, dibayar sebelum shalat Id.",
        "confidence": "high"
    },
    "zakat_harta": {
        "ruling": "wajib",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_9_103", "quran_2_43"],
        "basis_hadis": [],
        "keywords": ["zakat", "harta", "emas", "perak", "perdagangan", "nishab", "haul", "zakat maal"],
        "reasoning": "Zakat harta 2,5% pada emas, perak, dan barang perdagangan setelah mencapai nishab (85 gram emas) dan haul (satu tahun hijriyah). Wajib bagi muallaf setelah satu tahun penuh.",
        "confidence": "high"
    },
    "zakat_muallaf": {
        "ruling": "mungkin_asnaf",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_9_60"],
        "basis_hadis": [],
        "keywords": ["zakat", "muallaf", "penerima zakat", "asnaf", "berhak zakat", "muallaf zakat"],
        "reasoning": "Muallaf (yang dilunakkan hatinya) termasuk delapan asnaf penerima zakat. Syafi'i membaginya menjadi muallaf Muslim (yang keislamannya lemah) dan muallaf non-Muslim. Penetapannya oleh amil/pemerintah.",
        "confidence": "medium"
    },
    "zakat_nishab_emas_perak": {
        "ruling": "wajib",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_9_103"],
        "basis_hadis": ["hadis_bukhari_1404_zakat"],
        "keywords": ["nishab emas", "nishab perak", "85 gram", "zakat 2.5 persen", "haul", "zakat perhiasan"],
        "reasoning": "Nishab emas: 20 mitsqal = 85 gram. Nishab perak: 200 dirham = 595 gram. Kadar: 2,5%. Syarat haul: dimiliki selama 12 bulan hijriyah. Perhiasan emas yang dipakai: ulama beda pendapat, Syafi'i mayoritas mewajibkan zakat.",
        "confidence": "high"
    },
    "zakat_profesi_kontemporer": {
        "ruling": "wajib_menurut_sebagian_ulama",
        "madhab": "kontemporer",
        "basis_quran": ["quran_9_103"],
        "basis_hadis": [],
        "keywords": ["zakat profesi", "gaji", "penghasilan", "zakat penghasilan", "zakat gaji bulanan"],
        "reasoning": "Zakat profesi/penghasilan tidak dikenal dalam fiqh klasik. Ulama kontemporer (Qaradhawi, MUI) membolehkan dengan qiyas pada zakat hasil pertanian: 2,5% dari penghasilan bersih jika mencapai nishab 85 gram emas. Tidak semua ulama mewajibkan.",
        "confidence": "medium"
    },
    "zakat_delapan_asnaf": {
        "ruling": "wajib_pada_ashnaf",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_9_60_full"],
        "basis_hadis": [],
        "keywords": ["8 asnaf", "penerima zakat", "fakir miskin", "amil", "muallaf", "riqab", "gharim", "fisabilillah", "ibnu sabil"],
        "reasoning": "Delapan asnaf penerima zakat: (1) Fakir, (2) Miskin, (3) Amil, (4) Muallaf, (5) Riqab (pembebasan budak — kini dianalogikan pada program pemberdayaan), (6) Gharim (orang berutang), (7) Fi sabilillah, (8) Ibnu sabil. Syafi'i mensyaratkan distribusi rata ke 8 asnaf.",
        "confidence": "high"
    },

    # ──────────────────────────────────────────────────────────
    # HAJI & UMRAH
    # ──────────────────────────────────────────────────────────

    "haji_syarat_wajib": {
        "ruling": "fardhu_ain",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_3_97"],
        "basis_hadis": ["hadis_muslim_1337_haji"],
        "keywords": ["haji wajib", "syarat haji", "mampu haji", "istitha'ah", "haji seumur hidup"],
        "reasoning": "Syarat wajib haji: Islam, baligh, berakal, merdeka, istitha'ah (mampu secara fisik dan finansial). Wajib seumur hidup sekali. Perempuan wajib disertai mahram atau rombongan wanita terpercaya.",
        "confidence": "high"
    },
    "haji_rukun": {
        "ruling": "wajib_dilaksanakan",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_2_196"],
        "basis_hadis": [],
        "keywords": ["rukun haji", "ihram", "wukuf arafah", "thawaf ifadhah", "sa'i", "tahallul", "tertib"],
        "reasoning": "Rukun haji (tidak bisa diganti dam): Ihram dengan niat, Wukuf di Arafah, Thawaf Ifadhah (7 putaran), Sa'i (7 kali Shafa-Marwah), Tahallul, Tertib. Meninggalkan satu rukun membatalkan haji.",
        "confidence": "high"
    },
    "haji_wajib": {
        "ruling": "wajib_kena_dam_jika_ditinggal",
        "madhab": "Shafi'i",
        "basis_quran": [],
        "basis_hadis": [],
        "keywords": ["wajib haji", "mabit muzdalifah", "mabit mina", "lempar jumrah", "thawaf wada", "dam"],
        "reasoning": "Wajib haji (dapat diganti dam jika ditinggal): Ihram dari miqat, Mabit di Muzdalifah, Mabit di Mina, Melempar 3 jumrah, Thawaf Wada'. Meninggalkan wajib haji mengharuskan membayar dam (denda).",
        "confidence": "high"
    },
    "umrah_hukum": {
        "ruling": "wajib",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_2_196"],
        "basis_hadis": [],
        "keywords": ["umrah", "hukum umrah", "wajib umrah", "umrah sekali"],
        "reasoning": "Umrah wajib sekali seumur hidup menurut pendapat azhar Syafi'i. Rukun umrah: Ihram, Thawaf (7 putaran), Sa'i (Shafa-Marwah 7 kali), Tahallul (cukur/potong rambut).",
        "confidence": "high"
    },

    # ──────────────────────────────────────────────────────────
    # NIKAH
    # ──────────────────────────────────────────────────────────

    "nikah_syarat_rukun": {
        "ruling": "wajib_terpenuhi",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_2_221"],
        "basis_hadis": ["hadis_abu_dawud_2085_wali"],
        "keywords": ["syarat nikah", "rukun nikah", "akad nikah", "sah nikah"],
        "reasoning": "Rukun nikah Syafi'i: (1) Calon suami, (2) Calon istri, (3) Wali, (4) Dua saksi, (5) Ijab-Qabul. Syarat wali: Muslim, laki-laki, baligh, berakal, tidak ihram. Nikah tanpa wali tidak sah.",
        "confidence": "high"
    },
    "nikah_mahar": {
        "ruling": "wajib",
        "madhab": "Shafi'i",
        "basis_quran": [],
        "basis_hadis": [],
        "keywords": ["mahar", "mas kawin", "mahr", "maskawin", "mahr misil"],
        "reasoning": "Mahar wajib diberikan suami kepada istri. Tidak ada batas minimum yang baku dalam Syafi'i, tetapi tidak boleh nol. Jika tidak disebut saat akad, istri berhak mahr mitsl (standar mahar perempuan setara). Boleh kontan atau hutang.",
        "confidence": "high"
    },

    # ──────────────────────────────────────────────────────────
    # NIKAH — KASUS MUALLAF
    # ──────────────────────────────────────────────────────────

    "pernikahan_suami_islam_istri_kafir": {
        "ruling": "ditangguhkan",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_2_221", "quran_60_10"],
        "basis_hadis": [],
        "keywords": ["nikah", "pernikahan", "suami islam", "istri kafir", "suami masuk islam", "faskh"],
        "reasoning": "Jika suami masuk Islam sementara istri belum, pernikahan tidak langsung batal. Ditunggu hingga iddah tiga kali quru'. Jika istri masuk Islam sebelum iddah habis, pernikahan lanjut. Jika tidak, fasakh.",
        "confidence": "high"
    },
    "pernikahan_istri_islam_suami_kafir": {
        "ruling": "batal",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_2_221", "quran_60_10"],
        "basis_hadis": [],
        "keywords": ["nikah", "istri islam", "suami kafir", "istri masuk islam", "pernikahan batal", "faskh"],
        "reasoning": "Jika istri masuk Islam sementara suami tetap kafir, pernikahan fasakh (batal) setelah masa iddah. Alasan: laki-laki kafir tidak boleh menguasai perempuan Muslimah (QS. 4:141).",
        "confidence": "high"
    },
    "pernikahan_keduanya_islam": {
        "ruling": "sah",
        "madhab": "Shafi'i",
        "basis_quran": [],
        "basis_hadis": [],
        "keywords": ["nikah", "keduanya islam", "akad ulang", "suami istri masuk islam bersama"],
        "reasoning": "Jika keduanya masuk Islam bersamaan sebelum berhubungan, pernikahan tetap sah tanpa akad ulang. Ini adalah pendapat azhar Shafi'i berdasarkan kasus sahabat.",
        "confidence": "high"
    },

    # ──────────────────────────────────────────────────────────
    # NIKAH — TALAK & KHULUK
    # ──────────────────────────────────────────────────────────

    "talak_jenis": {
        "ruling": "dibolehkan_dengan_syarat",
        "madhab": "Shafi'i",
        "basis_quran": [],
        "basis_hadis": [],
        "keywords": ["talak", "cerai", "talak satu", "talak raj'i", "talak bain", "ruju"],
        "reasoning": "Talak raj'i (talak 1-2): suami boleh ruju' selama masa iddah tanpa akad baru. Talak bain sughra (3 talak): hanya bisa rujuk setelah menikah dengan orang lain dan bercerai. Talak wajib diucapkan dengan niat. Talak dalam kondisi marah tetap sah menurut jumhur.",
        "confidence": "high"
    },
    "khuluk": {
        "ruling": "boleh",
        "madhab": "Shafi'i",
        "basis_quran": [],
        "basis_hadis": [],
        "keywords": ["khuluk", "gugat cerai", "cerai dari istri", "istri minta cerai", "tebus talak"],
        "reasoning": "Khuluk adalah istri meminta cerai dengan mengembalikan mahar atau memberi ganti kepada suami. Sah apabila ada alasan yang dibenarkan syariat. Akibatnya: talak bain sughra — suami tidak bisa ruju' kecuali akad nikah baru.",
        "confidence": "high"
    },

    # ──────────────────────────────────────────────────────────
    # WARIS
    # ──────────────────────────────────────────────────────────

    "waris_perbedaan_agama": {
        "ruling": "haram_waris",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_4_11"],
        "basis_hadis": ["hadis_bukhari_6764", "hadis_muslim_1614"],
        "keywords": ["waris", "warisan", "perbedaan agama", "muslim kafir", "tidak mewarisi", "penghalang waris"],
        "reasoning": "Ikhtilaf al-diin (perbedaan agama) adalah salah satu tiga penghalang pewarisan dalam fiqh Shafi'i, bersama perbudakan dan pembunuhan. Muslim tidak mewarisi kafir dan sebaliknya.",
        "confidence": "high"
    },
    "waris_muallaf_keluarga_non_muslim": {
        "ruling": "tidak_dapat_warisan",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_4_11"],
        "basis_hadis": ["hadis_bukhari_6764", "hadis_muslim_1614"],
        "keywords": ["waris", "muallaf", "keluarga kafir", "warisan non muslim", "surat wasiat"],
        "reasoning": "Muallaf tidak berhak mewarisi harta keluarga non-Muslim yang meninggal. Solusi legal: keluarga dapat membuat surat wasiat (hingga 1/3 harta) sebelum wafat sebagai jalan keluar.",
        "confidence": "high"
    },
    "waris_hijab": {
        "ruling": "terhalang",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_4_11"],
        "basis_hadis": ["hadis_bukhari_6732_faraid"],
        "keywords": ["hijab waris", "terhalang waris", "cucu laki", "saudara", "kakek waris"],
        "reasoning": "Hijab (penghalangan) waris: Anak laki-laki menghijab cucu laki-laki dari anak laki-laki. Ayah menghijab kakek. Suami/istri tidak terhijab. Saudara sekandung menghijab saudara seayah. Penting dipahami muallaf dalam konteks pembagian waris keluarga.",
        "confidence": "high"
    },

    # ──────────────────────────────────────────────────────────
    # JENAZAH
    # ──────────────────────────────────────────────────────────

    "jenazah_ghusl": {
        "ruling": "fardhu_kifayah",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_36_12"],
        "basis_hadis": ["hadis_muslim_2162"],
        "keywords": ["jenazah", "mandikan", "ghusl jenazah", "memandikan mayat", "mayat muslim"],
        "reasoning": "Memandikan jenazah Muslim adalah fardhu kifayah. Mazhab Shafi'i mensyaratkan air suci, niat, dan membasuh seluruh tubuh. Dilakukan oleh mahram atau sesama jenis kelamin.",
        "confidence": "high"
    },
    "jenazah_takfin": {
        "ruling": "fardhu_kifayah",
        "madhab": "Shafi'i",
        "basis_quran": [],
        "basis_hadis": ["hadis_muslim_2162"],
        "keywords": ["jenazah", "kafan", "kain putih", "mengkafani", "kafan jenazah"],
        "reasoning": "Mengkafani jenazah adalah fardhu kifayah. Minimal satu lapis kain yang menutup seluruh tubuh. Sunnah tiga lapis untuk laki-laki dan lima lapis untuk perempuan dalam mazhab Shafi'i.",
        "confidence": "high"
    },
    "jenazah_shalat": {
        "ruling": "fardhu_kifayah",
        "madhab": "Shafi'i",
        "basis_quran": [],
        "basis_hadis": ["hadis_muslim_2162"],
        "keywords": ["jenazah", "shalat jenazah", "takbir empat", "shalat mayat", "shalat ghaib"],
        "reasoning": "Menshalatkan jenazah Muslim adalah fardhu kifayah dengan empat takbir. Syarat: menghadap kiblat, menutup aurat, suci dari hadas dan najis.",
        "confidence": "high"
    },
    "jenazah_dafan": {
        "ruling": "fardhu_kifayah",
        "madhab": "Shafi'i",
        "basis_quran": [],
        "basis_hadis": ["hadis_muslim_2162"],
        "keywords": ["jenazah", "kuburan", "dafan", "mengubur jenazah", "kubur"],
        "reasoning": "Menguburkan jenazah adalah fardhu kifayah. Mazhab Shafi'i mensyaratkan kedalaman lubang yang mencegah bau dan binatang buas, dengan posisi miring ke kanan menghadap kiblat.",
        "confidence": "high"
    },
    "jenazah_keluarga_non_muslim": {
        "ruling": "tidak_wajib",
        "madhab": "Shafi'i",
        "basis_quran": [],
        "basis_hadis": [],
        "keywords": ["jenazah", "keluarga kafir", "tidak shalat", "hadir pemakaman", "ta'ziyah non muslim"],
        "reasoning": "Muslim tidak wajib dan tidak boleh menshalatkan jenazah non-Muslim. Namun boleh hadir di pemakaman untuk ta'ziyah (belasungkawa) kepada keluarga yang masih hidup.",
        "confidence": "high"
    },

    # ──────────────────────────────────────────────────────────
    # MUAMALAH — JUAL BELI
    # ──────────────────────────────────────────────────────────

    "jual_beli_syarat": {
        "ruling": "halal_dengan_syarat",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_4_29"],
        "basis_hadis": ["hadis_bukhari_2079_khiyar"],
        "keywords": ["jual beli", "beli online", "transaksi", "syarat jual beli", "e-commerce"],
        "reasoning": "Syarat sah jual beli Syafi'i: (1) Penjual/pembeli baligh dan berakal, (2) Objek jelas dan halal, (3) Ada serah terima, (4) Saling ridha. Jual beli online sah selama objek jelas, tidak gharar (ketidakjelasan), dan ada mekanisme retur yang jelas.",
        "confidence": "high"
    },

    # ──────────────────────────────────────────────────────────
    # MUAMALAH — RIBA & PERBANKAN
    # ──────────────────────────────────────────────────────────

    "riba_jenis": {
        "ruling": "haram",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_2_275", "quran_2_278"],
        "basis_hadis": ["hadis_muslim_1598_riba"],
        "keywords": ["riba", "bunga bank", "kredit berbunga", "pinjaman berbunga", "riba fadhl", "riba nasi'ah"],
        "reasoning": "Dua jenis riba utama: (1) Riba nasi'ah: kelebihan dalam hutang-piutang karena penundaan waktu — inilah yang umum dalam sistem bunga bank. (2) Riba fadhl: pertukaran barang sejenis dengan takaran berbeda. Keduanya haram qath'i.",
        "confidence": "high"
    },
    "bank_konvensional_hukum": {
        "ruling": "haram",
        "madhab": "kontemporer_jumhur",
        "basis_quran": ["quran_2_275"],
        "basis_hadis": ["hadis_muslim_1598_riba"],
        "keywords": ["bank konvensional", "bunga bank", "tabungan berbunga", "deposito", "hukum bunga"],
        "reasoning": "Bunga bank konvensional adalah riba nasi'ah yang diharamkan. Fatwa MUI No. 1/2004 mengharamkan bunga bank. Solusi: gunakan bank syariah berbasis akad mudharabah, murabahah, atau wadiah. Dalam kondisi darurat (tidak ada bank syariah), sebagian ulama membolehkan dengan tidak menikmati bunga.",
        "confidence": "high"
    },

    # ──────────────────────────────────────────────────────────
    # MUAMALAH — HUTANG PIUTANG
    # ──────────────────────────────────────────────────────────

    "hutang_piutang": {
        "ruling": "boleh_dengan_syarat",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_2_282"],
        "basis_hadis": [],
        "keywords": ["hutang", "pinjam", "qardh", "utang", "bayar hutang", "wajib bayar hutang"],
        "reasoning": "Hutang piutang (qardh) boleh, bahkan dianjurkan sebagai tolong-menolong. Wajib dicatat dan ada saksi jika jumlah besar. Wajib dibayar tepat waktu. Menunda pembayaran hutang padahal mampu adalah kezhaliman. Hutang tidak gugur karena kematian, menjadi prioritas dari harta warisan.",
        "confidence": "high"
    },

    # ──────────────────────────────────────────────────────────
    # MUAMALAH — FINTECH & KONTRAK MODERN
    # ──────────────────────────────────────────────────────────

    "asuransi_konvensional": {
        "ruling": "khilaf_cenderung_haram",
        "madhab": "kontemporer",
        "basis_quran": ["quran_5_90"],
        "basis_hadis": ["hadis_bukhari_52_syubhat"],
        "keywords": ["asuransi", "asuransi jiwa", "asuransi kesehatan", "premi asuransi", "hukum asuransi"],
        "reasoning": "Asuransi konvensional mengandung unsur gharar (ketidakjelasan), maysir (spekulasi), dan riba — dilarang oleh mayoritas ulama kontemporer. Alternatif: Asuransi Syariah (Takaful) berbasis akad tabarru' (hibah untuk tolong-menolong), difatwakan halal MUI No. 21/2001.",
        "confidence": "medium"
    },
    "pinjol_fintech": {
        "ruling": "haram_jika_berbunga",
        "madhab": "kontemporer",
        "basis_quran": ["quran_2_278"],
        "basis_hadis": ["hadis_muslim_1598_riba"],
        "keywords": ["pinjol", "pinjaman online", "fintech lending", "kredit online", "cicilan berbunga", "pay later"],
        "reasoning": "Pinjaman online (pinjol) konvensional dengan bunga/biaya tetap adalah riba nasi'ah — haram. Platform fintech syariah dengan akad murabahah atau ijarah dibolehkan jika benar-benar bebas bunga. Hati-hati dengan 'biaya admin' yang sejatinya merupakan bunga terselubung.",
        "confidence": "high"
    },
    "kripto_investasi": {
        "ruling": "khilaf_syubhat",
        "madhab": "kontemporer",
        "basis_quran": ["quran_4_29"],
        "basis_hadis": ["hadis_bukhari_52_syubhat"],
        "keywords": ["kripto", "bitcoin", "ethereum", "cryptocurrency", "nft", "investasi kripto", "trading kripto"],
        "reasoning": "Cryptocurrency masih diperdebatkan ulama. Argumen halal: aset digital yang diperdagangkan atas dasar ridha. Argumen haram/syubhat: mengandung gharar tinggi, tidak ada nilai intrinsik, berpotensi maysir. OJK-MUI belum mengeluarkan fatwa final. Pendapat hati-hati: hindari hingga ada kepastian hukum.",
        "confidence": "medium"
    },

    # ──────────────────────────────────────────────────────────
    # AKHLAK SOSIAL
    # ──────────────────────────────────────────────────────────

    "keluarga_non_muslim_hubungan": {
        "ruling": "halal_dengan_adab",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_31_15", "quran_60_8"],
        "basis_hadis": ["hadis_bukhari_2620", "hadis_muslim_1003"],
        "keywords": ["keluarga", "orang tua", "non-muslim", "berbuat baik", "silaturahmi", "hubungan keluarga non muslim"],
        "reasoning": "Berbuat baik (birr) kepada keluarga non-Muslim yang tidak memerangi agama adalah halal bahkan dianjurkan. Larangan hanya pada wala' (loyalitas agama) bukan pada hubungan kemanusiaan.",
        "confidence": "high"
    },

    # ──────────────────────────────────────────────────────────
    # AURAT
    # ──────────────────────────────────────────────────────────

    "aurat_laki_laki": {
        "ruling": "wajib_tutup",
        "madhab": "Shafi'i",
        "basis_quran": [],
        "basis_hadis": [],
        "keywords": ["aurat", "pakaian", "laki-laki", "pusar", "lutut", "aurat pria", "batas aurat"],
        "reasoning": "Aurat laki-laki adalah antara pusar dan lutut (pusar dan lutut bukan aurat dalam pendapat azhar Shafi'i). Wajib ditutup saat shalat dan di hadapan orang lain.",
        "confidence": "high"
    },
    "aurat_perempuan_shalat": {
        "ruling": "wajib_tutup",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_24_31", "quran_33_59"],
        "basis_hadis": [],
        "keywords": ["aurat", "jilbab", "perempuan", "aurat wanita shalat", "shalat wanita", "pakaian shalat"],
        "reasoning": "Aurat perempuan dalam shalat adalah seluruh tubuh kecuali wajah dan telapak tangan (bagian dalam dan luar). Rambut yang keluar membatalkan shalat menurut mazhab Shafi'i.",
        "confidence": "high"
    },
    "aurat_perempuan_di_luar_shalat": {
        "ruling": "wajib_tutup",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_24_31", "quran_33_59"],
        "basis_hadis": [],
        "keywords": ["jilbab", "aurat di luar", "aurat perempuan", "pria ajnabi", "mahram", "hijab"],
        "reasoning": "Di hadapan pria ajnabi (bukan mahram), seluruh tubuh perempuan adalah aurat kecuali wajah dan telapak tangan — namun menutup wajah (niqab) lebih utama dalam mazhab Shafi'i.",
        "confidence": "high"
    },

    # ──────────────────────────────────────────────────────────
    # HALAL / HARAM
    # ──────────────────────────────────────────────────────────

    "makanan_haram_umum": {
        "ruling": "haram",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_5_3", "quran_2_173"],
        "basis_hadis": [],
        "keywords": ["haram", "makanan", "bangkai", "babi", "darah", "hukum makanan", "makan apa"],
        "reasoning": "Diharamkan memakan bangkai, darah yang mengalir, daging babi, dan hewan yang disembelih tidak atas nama Allah. Ini adalah hukum qath'i (pasti) berdasarkan nash Al-Qur'an.",
        "confidence": "high"
    },
    "makanan_haram_minuman": {
        "ruling": "haram",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_5_90"],
        "basis_hadis": ["hadis_bukhari_5585", "hadis_abu_dawud"],
        "keywords": ["khamar", "minuman", "alkohol", "mabuk", "bir", "wine", "haram minuman"],
        "reasoning": "Setiap minuman yang memabukkan (khamar) adalah haram, sedikit maupun banyak. Kaedah Shafi'i: mā askarā kathīruhu fa qalīluhu ḥarām.",
        "confidence": "high"
    },
    "makanan_halal_penyembelihan": {
        "ruling": "halal",
        "madhab": "Shafi'i",
        "basis_quran": [],
        "basis_hadis": [],
        "keywords": ["sembelih", "daging halal", "sapi", "kambing", "ayam", "halal daging", "cara sembelih"],
        "reasoning": "Daging hewan halal jika disembelih oleh Muslim atau Ahli Kitab (Yahudi/Kristen) dengan menyebut nama Allah, memotong saluran nafas dan makan, serta darah mengalir keluar.",
        "confidence": "high"
    },

    # ──────────────────────────────────────────────────────────
    # KONTEMPORER
    # ──────────────────────────────────────────────────────────

    "medsos_ghibah_online": {
        "ruling": "haram",
        "madhab": "kontemporer_qiyas",
        "basis_quran": ["quran_49_12"],
        "basis_hadis": ["hadis_muslim_2589_ghibah"],
        "keywords": ["medsos", "gosip online", "share aib", "screenshot privat", "ghibah online", "subtweet", "fitnah digital"],
        "reasoning": "Ghibah di media sosial lebih berat dari ghibah lisan karena: (1) disaksikan ribuan orang, (2) permanen, (3) bisa di-screenshot dan disebarkan. Hukumnya haram qiyas pada ghibah konvensional. Termasuk: share aib orang tanpa izin, 'subtweet' yang menyindir identitas tertentu, dan komentar merendahkan.",
        "confidence": "high"
    },
    "medsos_hoaks_tabayyun": {
        "ruling": "wajib_tabayyun",
        "madhab": "kontemporer_qiyas",
        "basis_quran": ["quran_49_6"],
        "basis_hadis": [],
        "keywords": ["hoaks", "berita palsu", "share tanpa cek", "sebar informasi", "tabayyun digital", "forward pesan"],
        "reasoning": "Menyebarkan informasi tanpa verifikasi (tabayyun) adalah pelanggaran QS. 49:6. Di era digital, ini mencakup: forward pesan WhatsApp tanpa cek fakta, share berita tanpa baca konten, dan menyebarkan screenshot tanpa konfirmasi. Hukum: minimal makruh, bisa haram jika menimbulkan fitnah.",
        "confidence": "high"
    },
    "musik_hukum": {
        "ruling": "khilaf",
        "madhab": "khilaf_ulama",
        "basis_quran": [],
        "basis_hadis": [],
        "keywords": ["musik", "lagu", "nyanyi", "hukum musik", "alat musik", "streaming musik", "konser"],
        "reasoning": "Ulama berkhilaf dalam 3 posisi: (1) Haram mutlak — alat musik dan nyanyian haram (Ibn Mas'ud, sebagian Syafi'i); (2) Halal dengan syarat — tidak mengandung lirik bermasalah, tidak membangkitkan syahwat, tidak berlebihan (jumhur kontemporer); (3) Halal kecuali yang jelas mengarah pada kemaksiatan. Pendapat pertengahan yang kuat: musik sebagai hiburan boleh selama tidak melalaikan kewajiban dan tidak berkonten haram.",
        "confidence": "medium"
    },
    "gambar_foto_video": {
        "ruling": "boleh_dengan_batasan",
        "madhab": "kontemporer_jumhur",
        "basis_quran": [],
        "basis_hadis": [],
        "keywords": ["foto", "video", "gambar makhluk hidup", "selfie", "konten visual", "hukum foto"],
        "reasoning": "Fotografi dan videografi digital: mayoritas ulama kontemporer membolehkan foto/video makhluk hidup untuk tujuan yang mubah (dokumentasi, pendidikan, dakwah, berita). Yang dilarang: konten yang mengandung aurat, pornografi, merendahkan, atau menipu. Hadis larangan gambar konteksnya pada patung/lukisan tangan.",
        "confidence": "medium"
    },
    "kerja_perusahaan_non_halal": {
        "ruling": "haram_terlibat_langsung",
        "madhab": "kontemporer_qiyas",
        "basis_quran": ["quran_5_90"],
        "basis_hadis": ["hadis_muslim_1598_riba"],
        "keywords": ["kerja di bank", "kerja pabrik rokok", "kerja restoran babi", "penghasilan haram", "profesi haram"],
        "reasoning": "Terlibat langsung dalam transaksi/produksi haram adalah haram (kasir di restoran babi, dealer alkohol, akuntansi riba). Terlibat jauh/tidak langsung: diperbolehkan menurut sebagian ulama dengan alasan darurat atau manfaat tidak langsung. Panduan: jika bisa pindah ke halal, wajib berusaha. Jika terjebak, berikhtiar keluar sambil tetap menghindari yang langsung haram.",
        "confidence": "medium"
    },
    "pacaran_sebelum_nikah": {
        "ruling": "haram",
        "madhab": "Shafi'i_dan_jumhur",
        "basis_quran": ["quran_17_32", "quran_24_30"],
        "basis_hadis": [],
        "keywords": ["pacaran", "dating", "hubungan pranikah", "kekasih sebelum nikah", "pdkt", "ta'aruf vs pacaran"],
        "reasoning": "Pacaran dalam pengertian hubungan romantis dengan bukan mahram (berduaan, bersentuhan, komunikasi intim) haram karena mendekatkan pada zina (QS. 17:32). Alternatif syar'i: ta'aruf melalui wali, nazhar (melihat calon) dengan izin wali, tanpa khalwat. Komunikasi digital yang berlebihan dan intim juga termasuk yang dilarang.",
        "confidence": "high"
    },
    "operasi_plastik_kecantikan": {
        "ruling": "haram_jika_mengubah_ciptaan",
        "madhab": "jumhur",
        "basis_quran": [],
        "basis_hadis": [],
        "keywords": ["operasi plastik", "filler", "botox", "suntik putih", "rhinoplasty", "kecantikan medis"],
        "reasoning": "Operasi kosmetik dibedakan: (1) Tujuan medis/perbaikan cacat: boleh (rekonstruksi, koreksi kelainan). (2) Tujuan mengubah ciptaan Allah semata: haram — termasuk augmentasi payudara, rhinoplasty untuk kecantikan, whitening injeksi. (3) Perawatan non-permanen (skincare, perawatan kulit): boleh. Prinsip: مَنْ لَعَنَهُ اللهُ (dilaknat Allah orang yang mengubah ciptaan-Nya — HR. Bukhari 5931).",
        "confidence": "medium"
    },
    "lingkungan_hidup_islami": {
        "ruling": "wajib_menjaga",
        "madhab": "kontemporer_maqashid",
        "basis_quran": [],
        "basis_hadis": [],
        "keywords": ["lingkungan", "sampah", "polusi", "kebersihan", "khalifah fil ardh", "ekologi islam"],
        "reasoning": "Menjaga lingkungan hidup adalah kewajiban dalam Islam berdasarkan: (1) Peran manusia sebagai khalifah fil ardh (QS. 2:30), (2) Larangan fasad (kerusakan) di bumi (QS. 2:11), (3) Hadis tentang kebersihan sebagian dari iman. Membuang sampah sembarangan, merusak hutan, dan pencemaran adalah fasad yang dilarang.",
        "confidence": "medium"
    },
    "kesehatan_mental_islam": {
        "ruling": "wajib_dijaga",
        "madhab": "kontemporer_maqashid",
        "basis_quran": ["quran_2_286", "quran_39_53"],
        "basis_hadis": [],
        "keywords": ["kesehatan mental", "depresi", "cemas", "stress", "psikolog", "terapi", "kesehatan jiwa"],
        "reasoning": "Menjaga jiwa (hifz an-nafs) adalah salah satu dari 5 maqashid syariah. Mencari bantuan psikologis/terapi dibolehkan bahkan dianjurkan jika diperlukan. Allah tidak membebani di luar kemampuan (QS. 2:286). Putus asa dari rahmat Allah dilarang (QS. 39:53). Mengabaikan kondisi mental parah hingga merugikan diri: makruh atau haram.",
        "confidence": "medium"
    },
}


# ============================================================
# INTEGRITY CHECK — python islamic_data.py
# ============================================================
if __name__ == "__main__":
    from collections import Counter

    print("=" * 66)
    print("  IslamiAI v3.0 — DATABASE INTEGRITY REPORT")
    print("=" * 66)

    arabic_ok = [k for k, v in quran_verses.items()
                 if "PENDING" not in v.get("arabic_text", "")]
    hadis_stubs_ = [k for k, v in hadis_collection.items()
                    if v.get("status") == "stub"]
    print(f"\n  Quran verses (total)  : {len(quran_verses)}")
    print(f"  Quran verified        : {len(arabic_ok)}")
    print(f"  Hadis entries (total) : {len(hadis_collection)}")
    print(f"  Hadis stubs (pending) : {len(hadis_stubs_)}")
    for s in hadis_stubs_:
        print(f"    → {s}")
    print(f"  Shafi\'i rules         : {len(shafii_rules)}")

    print("\n  Theme distribution (Quran):")
    for t, c in sorted(Counter(v["theme"] for v in quran_verses.values()).items()):
        print(f"    {t:<25}: {c}")

    print("\n  Theme distribution (Hadis):")
    for t, c in sorted(Counter(v.get("theme","?") for v in hadis_collection.values()).items()):
        print(f"    {t:<25}: {c}")

    print("\n  Madhab distribution (Rules):")
    for m, c in sorted(Counter(v.get("madhab","?") for v in shafii_rules.values()).items()):
        print(f"    {m:<30}: {c}")

    broken_q, broken_h = [], []
    for rk, rule in shafii_rules.items():
        for ref in rule.get("basis_quran", []):
            if ref not in quran_verses:
                broken_q.append((rk, ref))
        for ref in rule.get("basis_hadis", []):
            if ref not in hadis_collection:
                broken_h.append((rk, ref))

    print()
    if broken_q:
        print(f"  ⚠  BROKEN QURAN REFS ({len(broken_q)}):")
        for r, ref in broken_q: print(f"     [{r}] \'{ref}\'")
    else:
        print("  ✅ Quran cross-refs   : all valid")
    if broken_h:
        print(f"  ⚠  BROKEN HADIS REFS ({len(broken_h)}):")
        for r, ref in broken_h: print(f"     [{r}] \'{ref}\'")
    else:
        print("  ✅ Hadis cross-refs   : all valid")

    status = "OK" if not (broken_q or broken_h) else "WARNINGS"
    print(f"\n  OVERALL STATUS: {status}")
    print("=" * 66)
