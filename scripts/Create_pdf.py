import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def create_dummy_pdf(filename="pt_freshveggies.pdf"):
    # Pastikan folder 'data' ada
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Folder '{data_dir}' dibuat.")

    # Gabungkan path: data/nama_file.pdf
    filepath = os.path.join(data_dir, filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    content = """
🏛️ Laporan Komprehensif: Standar Operasional Prosedur Akademik & Kepegawaian UIN Salatiga
I. PENYUSUNAN KALENDER AKADEMIK

Nomor Dokumen: B-01/In.21/IR.1/HO.00.7/05/2015
Tanggal Pembuatan: Agustus 2015
Revisi Terakhir: 28 Agustus 2023
Disahkan oleh: Prof. Dr. Muh. Saerozi, M.Ag.

Dasar Hukum

Undang-Undang Nomor 12 Tahun 2012 tentang Pendidikan Tinggi.

Peraturan Pemerintah Nomor 4 Tahun 2014 tentang Penyelenggaraan Pendidikan Tinggi.

Peraturan Pemerintah Nomor 66 Tahun 2010 jo. Nomor 17 Tahun 2010 tentang Pengelolaan Pendidikan.

Kualifikasi Pelaksana

Mampu melaksanakan tugas keadministrasian, mengoperasikan komputer dan SIAKAD, serta menyusun dokumen kegiatan akademik.

Peralatan

Komputer & internet, printer, konsep kalender akademik, serta kalender tahun sebelumnya.

Prosedur Utama

Menyusun konsep kalender akademik berdasar kalender sebelumnya.

Memberikan masukan terhadap konsep tersebut (3 hari).

Revisi konsep sesuai hasil rapat senat.

Pengesahan konsep final dan penandatanganan oleh pejabat berwenang.

Distribusi kalender akademik ke fakultas, pascasarjana, dan lembaga.

⚠️ Jika SOP ini tidak dijalankan, maka keabsahan kalender akademik tertunda dan kegiatan akademik dapat terhambat.

II. REGISTRASI MAHASISWA LAMA

Tanggal Revisi: 28 Agustus 2023
Disahkan oleh: Dr. Muh. Saerozi, M.Ag.

Dasar Hukum

UU No. 12 Tahun 2012.

PP No. 4 Tahun 2014.

PP No. 66 Tahun 2010 jo. 17 Tahun 2010.

Kualifikasi Pelaksana

Kompetensi administrasi, komputer, dan SIAKAD.

Peralatan

Komputer, internet, printer, dan dokumen tagihan UKT.

Alur Proses

Input Tagihan UKT ke SIAKAD – 5 menit.

Mahasiswa melihat tagihan – 5 menit.

Pembayaran UKT ke bank tujuan – 15 menit.

Pengisian dan pencetakan KRS – 30 menit.

Persetujuan KRS oleh Dosen PA – 1 hari.

Revisi KRS (jika perlu) – 30 menit.

Pengumpulan KRS final ke fakultas – 5 menit.

⚠️ Keterlambatan registrasi menghambat akses perkuliahan dan validasi akademik.

III. PENGISIAN KRS MAHASISWA BARU (USER EDUCATION)

Revisi: 28 Agustus 2023
Disahkan oleh: Rektor melalui Bidang Akademik.

Dasar Hukum

Sama dengan SOP Registrasi Mahasiswa Lama, ditambah Pedoman Pendidikan Tahun Berjalan.

Kualifikasi Pelaksana

Mahasiswa baru yang mampu mengoperasikan komputer dan SIAKAD.

Langkah-langkah

Pengumuman jadwal pelaksanaan User Education – 20 menit.

Mahasiswa memperoleh informasi jadwal pelatihan – 5 menit.

Mengikuti User Education dan melakukan pengisian KRS di SIAKAD – 2 minggu.

Output akhir: KRS mahasiswa baru yang sudah terekam di sistem akademik.

IV. PENERBITAN IJAZAH

Disahkan oleh: Rektor dan Dekan UIN Salatiga.

Dasar Hukum

UU No. 12 Tahun 2012

PP No. 4 Tahun 2014

PP No. 66 Tahun 2010 jo. 17 Tahun 2010

Kualifikasi & Peralatan

Kemampuan administratif, komunikasi online, komputer, printer, ATK, dan blangko ijazah kosong.

Tahapan

Pengumpulan data calon wisudawan – 3 hari.

Validasi penulisan data ijazah – 3 hari.

Penyusunan konsep ijazah + nomor ijazah nasional (PIN) – 1 hari.

Distribusi konsep ijazah untuk validasi – 1 minggu.

Validasi dan pencetakan ijazah final – 3 hari.

Penandatanganan oleh Dekan dan Rektor – 1 hari.

Penyerahan ijazah ke mahasiswa – 5 menit per penerima.

⚠️ Keterlambatan pelaksanaan akan menunda legalitas akademik mahasiswa yang telah lulus.

V. REKAPITULASI KEHADIRAN PEGAWAI

Nomor: B-/In.21/B/HO.00.7/11/2019
Efektif: 1 Oktober 2023
Disahkan oleh: Drs. H. Suhersi.

Dasar Hukum

UU No. 5 Tahun 2014 tentang ASN.

PP No. 11 Tahun 2017 jo. PP No. 17 Tahun 2020.

Peraturan Badan Kepegawaian No. 24 Tahun 2017 jo. No. 7 Tahun 2021.

Kualifikasi Pelaksana

Menguasai aplikasi PUSAKA dan presensi instansi.

Memahami regulasi cuti dan renstra instansi.

Peralatan

Database kepegawaian, aplikasi PUSAKA & presensi, ATK, komputer, internet.

Langkah-langkah

Pegawai melakukan absensi harian (Senin–Kamis: 07.30–16.00; Jumat: 07.30–16.30).

Validasi surat tugas, izin, dan cuti.

Rekapitulasi hasil rekonsiliasi data absen bulanan.

Verifikasi akhir oleh tim kepegawaian.

⚠️ Rekap tidak tepat waktu dapat menghambat pembayaran tunjangan kinerja dan pelaporan ke pimpinan.

🔍 Kesimpulan Umum

Kelima SOP ini memperlihatkan pola manajemen akademik dan kepegawaian UIN Salatiga yang sangat sistematis, dengan tahapan waktu yang jelas dan tanggung jawab spesifik di setiap level birokrasi. Seluruh proses — mulai dari penyusunan kalender akademik hingga pencetakan ijazah — menekankan keabsahan administratif, efisiensi waktu, serta integritas sistem digital (SIAKAD dan PUSAKA).
    """

    for line in content.split("\n\n"):
        story.append(Paragraph(line.strip(), styles["Normal"]))
        story.append(Spacer(1, 12))

    doc.build(story)
    print(f"PDF berhasil disimpan di: {filepath}")

if __name__ == "__main__":
    create_dummy_pdf("sop_uin_salatiga.pdf")