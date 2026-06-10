#!/usr/bin/env zsh
# Setup symlinks corpus/epub: nama pendek (ingest_corpus.py) -> nama panjang (di disk)
# Jalankan sekali setelah clone atau setelah corpus di-download ulang

CORPUS="$(dirname $0)/../corpus/epub"
cd "$CORPUS" || exit 1

declare -A MAP=(
    [al_kiya_harrasi.epub]=al_kiya_harrasi_ahkam_quran.epub
    [al_baihaqi_ahkam.epub]=al_baihaqi_ahkam_quran_syafii.epub
    [al_qurtubi.epub]=al_qurtubi_jami_ahkam_quran.epub
    [al_jassas.epub]=al_jassas_ahkam_quran.epub
    [al_baghawi.epub]=al_baghawi_maalim_tanzil.epub
    [ibn_kathir_tafsir.epub]=ibn_kathir_tafsir_quran_azhim.epub
    [irshad_al_faqih.epub]=ibn_kathir_irsyad_faqih.epub
    [al_mawardi_nukat.epub]=al_mawardi_nukat_uyun.epub
    [ibn_ashur.epub]=ibn_ashur_tahrir_tanwir.epub
    [al_umm.epub]=al_umm_syafii.epub
    [al_risalah.epub]=al_risalah_syafii.epub
    [mukhtasar_muzani.epub]=mukhtasar_al_muzani.epub
    [nihayat_matlab.epub]=nihayat_al_matlab_juwaini.epub
    [minhaj_talibin.epub]=minhaj_al_talibin_nawawi.epub
    [rawdhat_talibin.epub]=rawdhat_al_talibin_nawawi.epub
    [al_majmu.epub]=al_majmu_syarh_muhadhdhab_nawawi.epub
    [al_hawi_kabir.epub]=al_hawi_al_kabir_mawardi.epub
    [tuhfat_muhtaj.epub]=tuhfat_al_muhtaj_ibn_hajar.epub
    [nihayat_muhtaj.epub]=nihayat_al_muhtaj_al_ramli.epub
    [mughni_muhtaj.epub]=mughni_al_muhtaj_syarbini.epub
    [asna_matalib.epub]=asna_al_matalib_zakariyya.epub
    [fath_qarib.epub]=fath_al_qarib_ibn_qasim.epub
    [fath_muin.epub]=fath_al_muin_malibari.epub
    [ianat_talibin.epub]=ianat_al_talibin_bakri.epub
    [al_asybah_suyuthi.epub]=al_asybah_wa_nazair_suyuthi.epub
    [al_mantsur_zarkasyi.epub]=al_mantsur_qawaid_zarkasyi.epub
    [qawaid_ahkam.epub]=qawaid_al_ahkam_izz_abd_salam.epub
)

ok=0; skip=0
for symlink target in ${(kv)MAP}; do
    if [[ -e "$symlink" || -L "$symlink" ]]; then
        ((skip++))
    else
        ln -s "$target" "$symlink" && echo "  ✓ $symlink" && ((ok++))
    fi
done
echo "\nSelesai: $ok dibuat, $skip sudah ada"
