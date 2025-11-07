import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def create_dummy_pdf(filename="ukt.pdf"):
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
# Informasi Pimpinan dan Struktur Organisasi Universitas Islam Negeri (UIN) Salatiga

## Pimpinan Universitas (Rektorat)

Struktur pimpinan utama UIN Salatiga dipimpin oleh Rektor.
Rektor UIN Salatiga adalah Prof. Dr. Zakiyyudin, M.Ag.

Rektor dibantu oleh tiga Wakil Rektor dan Kepala Biro:
1.  Wakil Rektor Bidang Administrasi Umum: Prof. Dr. Muh. Saerozi, M.Ag. (Beliau juga mengesahkan SOP Akademik).
2.  Wakil Rektor Bidang Akademik dan Kelembagaan: Prof. Dr. Miftahuddin, M.Ag.
3.  Wakil Rektor Bidang Kemahasiswaan, Alumni dan Kerjasama: Dr. Suwandi, S.Pd, M.Pd.

Kepala Biro Umum, Akademik, Perencanaan, dan Keuangan (Biro UAPK) adalah Dr. H. Agus Suryo Suripto, S.Ag., M.H.
Kepala Bagian Umum dan Akademik adalah M. Hidayatur Rohman, S.Pd., M.Sc.

## Pimpinan Lembaga

-   Ketua Lembaga Penjaminan Mutu (LPM) adalah Prof. Dr. Budiyono Saputro, M.Pd.
-   Sekretaris Lembaga Penjaminan Mutu (LPM) adalah Dr. Nafis Irkami, M.Ag., M.A.
-   Ketua Lembaga Penelitian dan Pengabdian Kepada Masyarakat (LP2M) adalah Hammam, M.Pd., Ph.D.
-   Sekretaris LP2M adalah Ari Setiawan, S.Pd., M.M.

## Pimpinan Pascasarjana

-   Direktur Pascasarjana adalah Prof. Dr. Phil Widianto, M.Ag., M.A.

## Pimpinan Fakultas Tarbiyah dan Ilmu Keguruan (FTIK)

-   Dekan FTIK adalah Prof. Dr. Rasimin, M.Ag.
-   Wakil Dekan Bidang Akademik dan Kelembagaan FTIK adalah Dr. Fatchurrohman, S.Ag., M.Pd.
-   Wakil Dekan Bidang Administrasi Umum, Perencanaan dan Keuangan FTIK adalah Norwanto, S.Pd., M.Hum., Ph.D.
-   Wakil Dekan Bidang Kemahasiswaan, Alumni, dan Kerja Sama FTIK adalah Dr. Maslikhah, M.Si.
-   Kepala Bagian Tata Usaha FTIK adalah Nidaul Hasanah, S.T., M.E.
-   Ketua Program Studi (Kaprodi) Pendidikan Agama Islam (PAI) adalah Purnomo, M.Pd.I.
-   Ketua Program Studi (Kaprodi) Pendidikan Bahasa Arab (PBA) adalah Wakhidati Nurrohmah Putri, M.Pd.I.
-   Ketua Program Studi (Kaprodi) Tadris Bahasa Inggris (TBI) adalah Rr. Dewi Wahyu Mustikasari, S.S., M.Pd., Ph.D.
-   Ketua Program Studi (Kaprodi) Pendidikan Guru Madrasah Ibtidaiyah (PGMI) adalah Wulan Izzatul Himmah, S.Pd., M.Pd.
-   Ketua Program Studi (Kaprodi) Pendidikan Islam Anak Usia Dini (PIAUD) adalah M. Agung Hidayatulloh, S.S., M.Pd.I.
-   Ketua Program Studi (Kaprodi) Tadris Matematika adalah Prof. Dr. Winarno, S.Si., M.Pd.
-   Ketua Program Studi (Kaprodi) Tadris IPA adalah Dr. Peni Susapti, S.Si., M.Si.
-   Ketua Program Studi (Kaprodi) Bimbingan dan Konseling Pendidikan Islam (BKPI) adalah Dr. Wahidin, M.Pd.
-   Ketua Program Studi (Kaprodi) Pendidikan Profesi Guru (PPG) adalah Imam Subqi, M.S.I.
-   Ketua Program Studi (Kaprodi) Sains Data adalah Enika Wulandari, M.Pd.

## Pimpinan Fakultas Syariah

-   Dekan Fakultas Syariah adalah Prof. Dr. Ilyya Muhsin, M.Si.
-   Wakil Dekan Bidang Akademik dan Kelembagaan Fakultas Syariah adalah Dr. Farkhani, S.H., S.H.I, M.H.
-   Wakil Dekan Bidang Administrasi Umum, Perencanaan dan Keuangan Fakultas Syariah adalah Dr. Siti Zumrotun, M.Ag.
-   Wakil Dekan Bidang Kemahasiswaan, Alumni, dan Kerja Sama Fakultas Syariah adalah Sukron Ma'mun, Ph.D.
-   Kepala Bagian Tata Usaha Fakultas Syariah adalah Dra. Astuti Sakdiyah, M.Pd.
-   Ketua Program Studi (Kaprodi) Hukum Keluarga Islam (HKI) adalah Ahmadi Hasanudin Dardiri, M.H.
-   Ketua Program Studi (Kaprodi) Hukum Ekonomi Syari'ah (HES) adalah Endang Sriani, M.H.
-   Ketua Program Studi (Kaprodi) Hukum Tata Negara (HTN) adalah Cholida Hanum, M.H.

## Pimpinan Fakultas Dakwah

-   Dekan Fakultas Dakwah adalah Prof. Dr. Adang Kuswaya, M.Ag.
-   Wakil Dekan Bidang Akademik dan Kelembagaan Fakultas Dakwah adalah Dr. Abdul Aziz, N.P, M.M.
-   Wakil Dekan Bidang Administrasi Umum, Perencanaan dan Keuangan Fakultas Dakwah adalah Dr. Muna Erawati, M.Si.
-   Wakil Dekan Bidang Kemahasiswaan dan Kerjasama Fakultas Dakwah adalah Rovi'in, M.Ag.
-   Kepala Bagian Tata Usaha Fakultas Dakwah adalah Muh. Amin, M.M.
-   Ketua Program Studi (Kaprodi) Komunikasi & Penyiaran Islam (KPI) adalah Rr. Wuri Arenggoasih, M.I.Kom.
-   Ketua Program Studi (Kaprodi) Manajemen Dakwah (MD) adalah Sutrisno, M.Pd.I.
-   Ketua Program Studi (Kaprodi) Psikologi Islam (PI) adalah Sya'ban Maghfur, M.Pd.I.
-   Ketua Program Studi (Kaprodi) Pengembangan Masyarakat Islam (PMI) adalah Dra. Sri Suparwi, M.A.
-   Ketua Program Studi (Kaprodi) Teknologi Informasi (TI) adalah Juwita Artanti K, M.Cs.

## Pimpinan Fakultas Ushuluddin, Adab, dan Humaniora (FUADAH)

-   Dekan FUADAH adalah Prof. Dr. Supardi, M.A.
-   Wakil Dekan I FUADAH adalah Prof. Dr. Benny Ridwan, M.Hum.
-   Wakil Dekan II FUADAH adalah Dr. M. Guron, M.Ag.
-   Wakil Dekan III FUADAH adalah Drs. Abdul Syukur, M.Si.
-   Kepala Bagian Tata Usaha FUADAH adalah Heru Heriyanto, S.E.
-   Ketua Program Studi (Kaprodi) Sejarah Peradaban Islam (SPI) adalah A. Faidi, M.Hum.
-   Ketua Program Studi (Kaprodi) Ilmu Al-Qur'an dan Tafsir (IAT) adalah Farid Hasan, M.Hum.
-   Ketua Program Studi (Kaprodi) Bahasa dan Sastra Arab (BSA) adalah Dr. Sri Guno Najib Chaqoqo, M.A.
-   Ketua Program Studi (Kaprodi) Ilmu Hadis (IH) adalah Ulfi Putra Sany, M.Hum.
-   Ketua Program Studi (Kaprodi) Aqidah dan Filsafat Islam (AFI) adalah Erkham Maskuri, Lc., M.S.I.
-   Ketua Program Studi (Kaprodi) Perpustakaan dan Sains Informasi (PSI) adalah Suryanto, M.A.

## Pimpinan Fakultas Ekonomi dan Bisnis Islam (FEBI)

-   Dekan FEBI adalah Prof. Dr. Agus Waluyo, M.Ag.
-   Wakil Dekan Bidang Akademik dan Kelembagaan FEBI adalah Dr. Fetria Eka Yudiana, M.Si.
-   Wakil Dekan Bidang Administrasi Umum, Perencanaan dan Keuangan FEBI adalah Dr. Qi Mangku Bahjatulloh, Lc., M.SI.
-   Wakil Dekan Bidang Kemahasiswaan, Alumni, dan Kerja Sama FEBI adalah Dr. Faqih Nabhan, S.E., M.M.
-   Kepala Bagian Tata Usaha FEBI adalah Umi Sahil, S.E., M.M.
-   Ketua Program Studi (Kaprodi) Ekonomi Syariah adalah Emy Widyastuti, M.E.
-   Ketua Program Studi (Kaprodi) Perbankan Syariah adalah Nur Huri Mustofa, S.Ag., M.SI.
-   Ketua Program Studi (Kaprodi) Akuntansi Syariah adalah Yusvita Nena Arinta, M.Si.
-   Ketua Program Studi (Kaprodi) Manajemen Bisnis Syariah adalah Diyah Ariyani, M.A.
-   Ketua Program Studi (Kaprodi) Bisnis Digital adalah Saifudin, M.E.
    """

    for line in content.split("\n\n"):
        story.append(Paragraph(line.strip(), styles["Normal"]))
        story.append(Spacer(1, 12))

    doc.build(story)
    print(f"PDF berhasil disimpan di: {filepath}")

if __name__ == "__main__":
    create_dummy_pdf("pimpinan all fakultas.pdf")