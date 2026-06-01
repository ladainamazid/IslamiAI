# File: formatter.py (RESTRUCTURED)
# Format output dengan 3 text fields: arabic | transliteration | translation

def format_answer(retrieval_result):
    """
    Format dengan struktur:
    HUKUM
    MADHAB
    -----
    📖 DASAR AL-QUR'AN:
      QS. X:Y
      [Arabic]
      Transliterasi: ...
      Terjemahan: ...
    
    📜 DASAR HADIS:
      Source
      [Arabic]
      Transliterasi: ...
      Terjemahan: ...
    
    💭 PENJELASAN: ...
    """
    
    if retrieval_result is None:
        return "Maaf, pertanyaan ini belum ada di database kami. Silakan tanya kepada ulama setempat."
    
    output = []
    output.append("=" * 70)
    output.append(f"🔖 HUKUM: {retrieval_result['ruling'].upper()}")
    output.append(f"🕌 MADHAB: {retrieval_result['madhab']}")
    output.append("=" * 70)
    
    # Ayat Quran
    if retrieval_result['quran']:
        output.append("\n📖 DASAR AL-QUR'AN:\n")
        for idx, q in enumerate(retrieval_result['quran'], 1):
            ayah_ref = q.get('surah_ayah', q.get('reference', ''))
            output.append(f"  [{idx}] QS. {ayah_ref}")
            
            # Arabic text (jika ada)
            if q.get('arabic_text') and q['arabic_text'] != "[akan ditambahkan]":
                output.append(f"      {q['arabic_text']}")
            
            # Transliterasi
            if q.get('transliteration'):
                output.append(f"      Transliterasi: {q['transliteration']}")
            
            # Terjemahan
            if q.get('translation'):
                output.append(f"      Terjemahan: {q['translation']}")
            
            output.append("")  # Empty line between entries
    
    # Hadis
    if retrieval_result['hadis']:
        output.append("\n📜 DASAR HADIS:\n")
        for idx, h in enumerate(retrieval_result['hadis'], 1):
            hadis_source = h.get('source', h.get('reference', ''))
            output.append(f"  [{idx}] {hadis_source}")
            
            # Arabic text (jika ada)
            if h.get('arabic_text') and h['arabic_text'] != "[akan ditambahkan]":
                output.append(f"      {h['arabic_text']}")
            
            # Transliterasi
            if h.get('transliteration'):
                output.append(f"      Transliterasi: {h['transliteration']}")
            
            # Terjemahan
            if h.get('translation'):
                output.append(f"      Terjemahan: {h['translation']}")
            
            output.append("")  # Empty line between entries
    
    # Penjelasan
    output.append("\n💭 PENJELASAN:")
    output.append(f"  {retrieval_result['reasoning']}")
    
    output.append("\n" + "=" * 70)
    
    return "\n".join(output)

if __name__ == "__main__":
    from retrieval import retrieve_ruling
    
    result = retrieve_ruling("syahadat")
    answer = format_answer(result)
    print(answer)
