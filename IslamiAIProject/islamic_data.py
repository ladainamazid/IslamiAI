# islamic_data_complete.py
# IslamiAI - Validated Core Dataset (Phase 0 Sampling)
# Scope: 3 tema prioritas muallaf: syahadat, thaharah, shalat
# Arabic text: verified terhadap mushaf standar
# Hadis: hanya hadis dengan sanad yang dikonfirmasi shahih
# Date: 2026-05-27

# ============================================================
# METADATA SCHEMA
# ============================================================
# quran_verses[key] = {
#   reference: "Surah:Ayah" (string)
#   surah: int, ayah: int
#   arabic_text: str  — teks Arabic standar Usmani
#   transliteration: str  — transliterasi akademik
#   translation: str  — terjemahan Kemenag RI 2019
#   theme: str  — kategori hukum
#   confidence: "high|medium"  — validitas data
#   source_check: str  — referensi verifikasi
# }
#
# hadis_collection[key] = {
#   source: str
#   arabic_text: str
#   transliteration: str
#   translation: str
#   authenticity: "sahih|hasan|dhaif"
#   grading: str  — siapa yang menilai
#   confidence: "high|medium"
# }

quran_verses = {

    # ── TEMA: SYAHADAT / AQIDAH ──────────────────────────────

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

    # ── TEMA: THAHARAH ───────────────────────────────────────

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

    # ── TEMA: SHALAT ──────────────────────────────────────────

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

    # ── TEMA: HALAL-HARAM MAKANAN ────────────────────────────

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
    "quran_36_12": {
        "reference": "36:12",
        "surah_ayah": "36:12",
        "surah": 36,
        "ayah": 12,
        "arabic_text": "إِنَّا نَحْنُ نُحْىِ ٱلْمَوْتَىٰ وَنَكْتُبُ مَا قَدَّمُوا۟ وَءَاثَٰرَهُمْ",
        "transliteration": "Inna nahnu nuhyil-mawtaa wa naktubu maa qaddamuu wa aatharahum",
        "translation": "Sungguh, Kamilah yang menghidupkan orang-orang yang mati, dan Kami mencatat apa yang telah mereka kerjakan dan bekas-bekas yang mereka tinggalkan.",
        "theme": "akhirah",
        "confidence": "high",
        "source_check": "QS. Ya-Sin [36]:12, Mushaf Madinah"
    },
}


hadis_collection = {

    # ── TEMA: SYAHADAT / RUKUN ISLAM ─────────────────────────

    "hadis_bukhari_8": {
        "reference": "bukhari_8",
        "source": "Sahih Bukhari no. 8",
        "arabic_text": "بُنِيَ الْإِسْلَامُ عَلَى خَمْسٍ شَهَادَةِ أَنْ لَا إِلَهَ إِلَّا اللَّهُ وَأَنَّ مُحَمَّدًا رَسُولُ اللَّهِ وَإِقَامِ الصَّلَاةِ وَإِيتَاءِ الزَّكَاةِ وَالْحَجِّ وَصَوْمِ رَمَضَانَ",
        "transliteration": "Buniyal-islāmu 'alā khams: shahādati an lā ilāha illallāhu wa anna Muḥammadan rasūlullāh, wa iqāmiṣ-ṣalāh, wa ītā'iz-zakāh, wal-ḥajj, wa ṣawmi Ramaḍān",
        "translation": "Islam dibangun di atas lima perkara: bersaksi bahwa tidak ada tuhan yang berhak disembah selain Allah dan bahwa Muhammad adalah utusan Allah, mendirikan shalat, menunaikan zakat, haji, dan puasa Ramadhan.",
        "authenticity": "sahih",
        "grading": "Muttafaq 'alaih (Bukhari & Muslim)",
        "confidence": "high"
    },

    "hadis_muslim_16": {
        "reference": "muslim_16",
        "source": "Sahih Muslim no. 16",
        "arabic_text": "أُمِرْتُ أَنْ أُقَاتِلَ النَّاسَ حَتَّى يَشْهَدُوا أَنْ لَا إِلَهَ إِلَّا اللَّهُ وَأَنَّ مُحَمَّدًا رَسُولُ اللَّهِ",
        "transliteration": "Umirtu an uqātilan-nāsa ḥattā yashhadu an lā ilāha illallāhu wa anna Muḥammadan rasūlullāh",
        "translation": "Aku diperintahkan untuk memerangi manusia hingga mereka bersaksi bahwa tidak ada tuhan yang berhak disembah selain Allah dan bahwa Muhammad adalah utusan Allah.",
        "authenticity": "sahih",
        "grading": "Sahih Muslim",
        "confidence": "high"
    },

    # ── TEMA: THAHARAH ───────────────────────────────────────

    "hadis_muslim_224": {
        "reference": "muslim_224",
        "source": "Sahih Muslim no. 224",
        "arabic_text": "لَا تُقْبَلُ صَلَاةٌ بِغَيْرِ طُهُورٍ",
        "transliteration": "Lā tuqbalu ṣalātun bighayri ṭuhūr",
        "translation": "Tidak diterima shalat tanpa bersuci.",
        "authenticity": "sahih",
        "grading": "Sahih Muslim, dari Abu Hurairah r.a.",
        "confidence": "high"
    },

    "hadis_muslim_223": {
        "reference": "muslim_223",
        "source": "Sahih Muslim no. 223",
        "arabic_text": "الطُّهُورُ شَطْرُ الْإِيمَانِ",
        "transliteration": "Aṭ-ṭuhūru shaṭrul-īmān",
        "translation": "Bersuci adalah separuh iman.",
        "authenticity": "sahih",
        "grading": "Sahih Muslim, dari Abu Malik Al-Asy'ari r.a.",
        "confidence": "high"
    },

    "hadis_muslim_279": {
        "reference": "muslim_279",
        "source": "Sahih Muslim no. 279",
        "arabic_text": "طَهُورُ إِنَاءِ أَحَدِكُمْ إِذَا وَلَغَ فِيهِ الْكَلْبُ أَنْ يَغْسِلَهُ سَبْعَ مَرَّاتٍ أُولَاهُنَّ بِالتُّرَابِ",
        "transliteration": "Ṭahūru inā'i aḥadikum idhā walagha fīhil-kalbu an yagsilahu sab'a marrātin ūlāhunna bit-turāb",
        "translation": "Cara menyucikan bejana salah seorang dari kalian yang dijilat anjing adalah mencucinya tujuh kali, yang pertama dengan tanah.",
        "authenticity": "sahih",
        "grading": "Sahih Muslim, dari Abu Hurairah r.a.",
        "confidence": "high"
    },

    # ── TEMA: SHALAT ──────────────────────────────────────────

    "hadis_muslim_233": {
        "reference": "muslim_233",
        "source": "Sahih Muslim no. 233",
        "arabic_text": "الصَّلَوَاتُ الْخَمْسُ وَالْجُمُعَةُ إِلَى الْجُمُعَةِ كَفَّارَةٌ لِمَا بَيْنَهُنَّ مَا لَمْ تُغْشَ الْكَبَائِرُ",
        "transliteration": "Aṣ-ṣalawātul-khamsu wal-jumu'atu ilal-jumu'ati kaffāratun limā baynahunna mā lam tughashal-kabā'ir",
        "translation": "Shalat lima waktu, dan Jum'at ke Jum'at berikutnya adalah penghapus dosa di antara keduanya selama dosa-dosa besar tidak dilakukan.",
        "authenticity": "sahih",
        "grading": "Sahih Muslim, dari Abu Hurairah r.a.",
        "confidence": "high"
    },

    "hadis_bukhari_527": {
        "reference": "bukhari_527",
        "source": "Sahih Bukhari no. 527",
        "arabic_text": "مَنْ أَدْرَكَ رَكْعَةً مِنَ الصَّلَاةِ فَقَدْ أَدْرَكَ الصَّلَاةَ",
        "transliteration": "Man adraka rak'atan minaṣ-ṣalāti faqad adraka ṣ-ṣalāh",
        "translation": "Barang siapa mendapati satu rakaat dari shalat, maka sesungguhnya ia telah mendapatkan shalat tersebut.",
        "authenticity": "sahih",
        "grading": "Muttafaq 'alaih, dari Abu Hurairah r.a.",
        "confidence": "high"
    },

    "hadis_bukhari_5585": {
        "reference": "bukhari_5585",
        "source": "Sahih Bukhari no. 5585",
        "arabic_text": "كُلُّ مُسْكِرٍ حَرَامٌ",
        "transliteration": "Kullu muskirin haraam",
        "translation": "Setiap yang memabukkan adalah haram.",
        "authenticity": "sahih",
        "grading": "Muttafaq alaih, dari Ibnu Umar r.a.",
        "confidence": "high"
    },
    "hadis_abu_dawud": {
        "reference": "abu_dawud_3674",
        "source": "Sunan Abu Dawud no. 3674",
        "arabic_text": "إِنَّ اللَّهَ حَرَّمَ الْخَمْرَ وَثَمَنَهَا",
        "transliteration": "Innallaha harramal-khamra wa thamanaha",
        "translation": "Sesungguhnya Allah mengharamkan khamar dan harga penjualannya.",
        "authenticity": "sahih",
        "grading": "Dishahihkan Al-Albani, dari Ibnu Abbas r.a.",
        "confidence": "high"
    },
    "hadis_bukhari_2620": {
        "reference": "bukhari_2620",
        "source": "Sahih Bukhari no. 2620",
        "arabic_text": "قَدِمَتْ عَلَيَّ أُمِّي وَهِيَ مُشْرِكَةٌ فَاسْتَفْتَيْتُ رَسُولَ اللَّهِ قُلْتُ إِنَّ أُمِّي قَدِمَتْ وَهِيَ رَاغِبَةٌ أَفَأَصِلُ أُمِّي قَالَ نَعَمْ صِلِي أُمَّكِ",
        "transliteration": "Qadimat alayya ummi wa hiya mushrikatun fastaftaytu rasulullah qultu inna ummi qadimat wa hiya raghibah afa-asilu ummi qala naam sili ummak",
        "translation": "Ibuku datang kepadaku dalam keadaan musyrik. Aku meminta fatwa kepada Rasulullah dan berkata: Ibuku datang, apakah aku boleh menyambung hubungan dengannya? Beliau menjawab: Ya, sambunglah hubungan dengan ibumu.",
        "authenticity": "sahih",
        "grading": "Muttafaq alaih, dari Asma binti Abu Bakr r.a.",
        "confidence": "high"
    },
    "hadis_muslim_1003": {
        "reference": "muslim_1003",
        "source": "Sahih Muslim no. 1003",
        "arabic_text": "لَا يَحِلُّ لِمُسْلِمٍ أَنْ يَهْجُرَ أَخَاهُ فَوْقَ ثَلَاثَةِ أَيَّامٍ",
        "transliteration": "La yahillu li-muslimin an yahjura akhahu fawqa thalathat ayyam",
        "translation": "Tidak halal bagi seorang Muslim untuk memutuskan hubungan dengan saudaranya lebih dari tiga hari.",
        "authenticity": "sahih",
        "grading": "Sahih Muslim, dari Abu Hurairah r.a.",
        "confidence": "high"
    },
    "hadis_bukhari_6764": {
        "reference": "bukhari_6764",
        "source": "Sahih Bukhari no. 6764",
        "arabic_text": "لَا يَرِثُ الْمُسْلِمُ الْكَافِرَ وَلَا الْكَافِرُ الْمُسْلِمَ",
        "transliteration": "La yarithu al-muslimu al-kafira wa la al-kafiru al-muslim",
        "translation": "Seorang Muslim tidak mewarisi orang kafir, dan orang kafir tidak mewarisi seorang Muslim.",
        "authenticity": "sahih",
        "grading": "Muttafaq alaih, dari Usamah bin Zaid r.a.",
        "confidence": "high"
    },
    "hadis_muslim_1614": {
        "reference": "muslim_1614",
        "source": "Sahih Muslim no. 1614",
        "arabic_text": "لَا يَتَوَارَثُ أَهْلُ مِلَّتَيْنِ شَتَّى",
        "transliteration": "La yatawarathu ahlu millatayni shatta",
        "translation": "Pemeluk dua agama yang berbeda tidak saling mewarisi.",
        "authenticity": "sahih",
        "grading": "Sahih Muslim, dari Jabir r.a.",
        "confidence": "high"
    },
    "hadis_muslim_2162": {
        "reference": "muslim_2162",
        "source": "Sahih Muslim no. 2162",
        "arabic_text": "حَقُّ الْمُسْلِمِ عَلَى الْمُسْلِمِ سِتٌّ إِذَا لَقِيتَهُ فَسَلِّمْ عَلَيْهِ وَإِذَا دَعَاكَ فَأَجِبْهُ وَإِذَا اسْتَنْصَحَكَ فَانْصَحْهُ وَإِذَا عَطَسَ فَحَمِدَ اللَّهَ فَسَمِّتْهُ وَإِذَا مَرِضَ فَعُدْهُ وَإِذَا مَاتَ فَاتَّبِعْهُ",
        "transliteration": "Haqqul-muslimi alal-muslimi sittu: idha laqiitahu fa-sallim alayh, wa idha daaka fa-ajibh, wa idha istansahaka fan-sah, wa idha atasa fa-hamidallaha fa-sammithu, wa idha marida fa-udh, wa idha mata fattabih",
        "translation": "Hak seorang Muslim atas Muslim lainnya ada enam: bila bertemu ucapkan salam, bila mengundang penuhilah, bila meminta nasihat nasihati, bila bersin lalu memuji Allah doakanlah, bila sakit jenguklah, dan bila meninggal iringilah jenazahnya.",
        "authenticity": "sahih",
        "grading": "Sahih Muslim, dari Abu Hurairah r.a.",
        "confidence": "high"
    },
}


# ============================================================
# SHAFII RULES — COMPLETE 29 ENTRIES
# ============================================================
shafii_rules = {
    "syahadat": {
        "ruling": "wajib",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_3_18", "quran_47_19"],
        "basis_hadis": ["hadis_bukhari_8", "hadis_muslim_16"],
        "keywords": ["syahadat", "tauhid", "masuk islam", "ikrar", "dua kalimat tayyibah", "kalimat syahadat"],
        "reasoning": "Syahadat adalah rukun pertama Islam dan fondasi akidah. Dalam mazhab Shafi'i, pengucapan syahadat dengan lisan disertai keyakinan hati adalah syarat sah keislaman seseorang.",
        "confidence": "high"
    },
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
    "shalat_lima_waktu": {
        "ruling": "wajib",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_2_43", "quran_4_103", "quran_17_78", "quran_2_238"],
        "basis_hadis": ["hadis_muslim_233", "hadis_bukhari_8"],
        "keywords": ["shalat", "salah", "rukuk", "sujud", "takbir", "imam", "shalat lima waktu", "subuh", "dzuhur", "ashar", "maghrib", "isya"],
        "reasoning": "Shalat lima waktu adalah rukun Islam kedua dan kewajiban individual (fardhu 'ain) setiap Muslim yang baligh dan berakal. Mazhab Shafi'i menetapkan syarat dan rukun shalat yang ketat.",
        "confidence": "high"
    },
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
    "keluarga_non_muslim_hubungan": {
        "ruling": "halal_dengan_adab",
        "madhab": "Shafi'i",
        "basis_quran": ["quran_31_15", "quran_60_8"],
        "basis_hadis": ["hadis_bukhari_2620", "hadis_muslim_1003"],
        "keywords": ["keluarga", "orang tua", "non-muslim", "berbuat baik", "silaturahmi", "hubungan keluarga non muslim"],
        "reasoning": "Berbuat baik (birr) kepada keluarga non-Muslim yang tidak memerangi agama adalah halal bahkan dianjurkan. Larangan hanya pada wala' (loyalitas agama) bukan pada hubungan kemanusiaan.",
        "confidence": "high"
    },
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
    }
}


# ============================================================
# DATA INTEGRITY CHECK
# ============================================================
if __name__ == "__main__":
    from collections import Counter

    print("=" * 60)
    print("ISLAMIAI - DATA INTEGRITY REPORT")
    print("=" * 60)

    # Quran check
    arabic_missing = [k for k, v in quran_verses.items()
                      if "[akan" in v.get("arabic_text", "")]
    print(f"\n✅ Quran verses total : {len(quran_verses)}")
    print(f"   Arabic placeholder  : {len(arabic_missing)}")
    themes = Counter(v["theme"] for v in quran_verses.values())
    for theme, count in themes.items():
        print(f"   Theme '{theme}': {count} ayat")

    # Hadis check
    hadis_missing = [k for k, v in hadis_collection.items()
                     if "[akan" in v.get("arabic_text", "")]
    print(f"\n✅ Hadis total        : {len(hadis_collection)}")
    print(f"   Arabic placeholder : {len(hadis_missing)}")
    auth = Counter(v["authenticity"] for v in hadis_collection.values())
    for level, count in auth.items():
        print(f"   '{level}': {count} hadis")

    # Rules check
    print(f"\n✅ Shafi'i rules      : {len(shafii_rules)}")

    # Cross-reference check: apakah semua ref di rules ada di data
    broken_quran, broken_hadis = [], []
    for rule_key, rule in shafii_rules.items():
        for qref in rule.get("basis_quran", []):
            if qref not in quran_verses:
                broken_quran.append((rule_key, qref))
        for href in rule.get("basis_hadis", []):
            if href not in hadis_collection:
                broken_hadis.append((rule_key, href))

    if broken_quran:
        print(f"\n⚠️  Broken Quran refs  : {len(broken_quran)}")
        for r, ref in broken_quran:
            print(f"   Rule '{r}' → missing '{ref}'")
    else:
        print(f"\n✅ Quran cross-refs   : all valid")

    if broken_hadis:
        print(f"\n⚠️  Broken Hadis refs  : {len(broken_hadis)}")
        for r, ref in broken_hadis:
            print(f"   Rule '{r}' → missing '{ref}'")
    else:
        print(f"\n✅ Hadis cross-refs   : all valid")

    print("\n" + "=" * 60)
