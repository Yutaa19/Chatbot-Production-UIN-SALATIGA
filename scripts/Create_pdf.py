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
Pendidikan Profesi Guru (PPG) di UIN Salatiga dikenal sebagai entitas pendidikan tinggi yang memiliki peran sentral dalam membentuk dan melatih calon-calon guru profesional berintegritas. Misi utamanya adalah memberikan pembekalan yang holistik kepada para calon guru, meliputi aspek moral dan spiritualitas Islam. Dengan visi yang teguh untuk meningkatkan kualitas pendidikan di Indonesia, PPG UIN Salatiga diharapkan menjadi pusat pembentukan bagi generasi guru yang mampu memberikan dampak positif dan signifikan dalam meningkatkan mutu pendidikan nasional.

PPG UIN Salatiga menawarkan beragam program studi yang dirancang dengan cermat, memungkinkan eksplorasi konsep-konsep pedagogis terkini seiring dengan kemajuan ilmu pengetahuan dan teknologi. Kurikulum yang disusun mencakup empat pilar kompetensi utama: pedagogik, sosial, kepribadian, dan ilmu keislaman, yang diberikan secara holistik untuk memastikan para lulusan tidak hanya memiliki keterampilan teknis, tetapi juga fondasi moral dan keislaman yang kokoh.

PPG UIN Salatiga, Menyemai Ilmu,Membangun Profesionalisme Guru

Prof. Dr. Mansur, M.Ag (Ketua LPTK UIN Salatiga)
Sejak berdirinya, PPG UIN Salatiga telah menjadi tempat berkembangnya pendidik berkualitas yang mampu beradaptasi dengan dinamika era pos-humanisme, terutama dalam konteks teknologi kecerdasan buatan. Prestasi dan kontribusi lulusan PPG UIN Salatiga telah diakui luas, menegaskan peran lembaga ini sebagai episentrum pendidikan dan motor penggerak perubahan dalam dunia pendidikan.

Tidak hanya sebagai tempat inkubasi pendidik, PPG UIN Salatiga juga aktif dalam kegiatan riset dan inovasi, khususnya dalam bidang pedagogik. Dengan menyatukan teori dan praktik, lembaga ini berupaya memberikan kontribusi pada pengembangan ilmu pengetahuan pedagogik keislaman serta memperkuat landasan ilmiah dalam proses pembelajaran.

Dengan komitmen yang teguh terhadap profesionalisme dan nilai-nilai Islam, PPG UIN Salatiga telah menjadi pusat keunggulan dalam pendidikan profesi guru di Indonesia. Melalui pendekatan ilmiah dan holistik, lembaga ini tidak hanya mencetak generasi guru berkualitas, tetapi juga membuka ruang untuk eksplorasi dan pengembangan pengetahuan yang mendukung perubahan positif dalam dunia pendidikan.

Sejarah Program Studi Pendidikan Profesi Guru (PPG) di Universitas Islam Negeri (UIN) Salatiga merupakan cerminan dari perubahan dan evolusi dalam sistem pendidikan Indonesia, yang senantiasa beradaptasi dengan dinamika zaman dan tuntutan masyarakat. Dalam menghadapi tantangan baru yang muncul dengan cepat dan tidak terduga, terutama dalam dunia pendidikan, penting bagi lembaga pendidikan untuk terus memperbarui diri guna menjawab kebutuhan masyarakat akan tenaga pendidik yang berkualitas.

Pada tanggal 6 Januari 2021, Menteri Agama Republik Indonesia mengeluarkan Surat Keputusan Nomor 72 tahun 2021, yang memberikan izin kepada UIN Salatiga untuk menyelenggarakan Program Studi Pendidikan Profesi Guru (PPG). Keputusan ini merupakan langkah strategis dalam menjawab kompleksitas tantangan pendidikan yang dihadapi bangsa, termasuk di antaranya meningkatkan kualitas pendidikan serta kesejahteraan guru.

Visi: program Studi Pendidikan Profesi Guru di UIN Salatiga adalah:

Menjadi pusat unggulan Program Studi Pendidikan Profesi Guru di bidang sains, teknologi, dan seni untuk keluhuran martabat kemanusiaan berbasis wasatiyah Islam pada tahun 2045.

Misi: program Studi Pendidikan Profesi Guru di UIN Salatiga melaksanakan misi sebagai berikut:

a. Menyelenggarakan program pendidikan profesi guru keagamaan yang berkualitas, akuntabel, dan amanah, dengan memastikan penyelenggaraan pembelajaran yang inovatif dan berbasis kebutuhan zaman.

b. Melaksanakan penelitian dan pengabdian dalam upaya meningkatkan profesionalitas guru dan pembinaannya secara berkelanjutan dan kredibel, dengan fokus pada pengembangan metode pengajaran yang efektif serta implementasi praktik terbaik dalam bidang pendidikan keagamaan.

c. Menyediakan media publikasi ilmiah dan fasilitasnya untuk meningkatkan keterampilan guru keagamaan yang profesional, dengan tujuan memfasilitasi pertukaran pengetahuan dan pengalaman antar para praktisi pendidikan keagamaan serta mendorong terciptanya lingkungan akademik yang inspiratif dan kolaboratif.

Dengan visi dan misi ini, Program Studi Pendidikan Profesi Guru di UIN Salatiga bertekad untuk menjadi garda terdepan dalam mencetak guru-guru yang tidak hanya berkualitas dalam bidang sains, teknologi, dan seni, tetapi juga memiliki komitmen tinggi terhadap nilai-nilai wasatiyah Islam dan mengabdi pada kemajuan pendidikan serta kemartabatan kemanusiaan.

    """

    for line in content.split("\n\n"):
        story.append(Paragraph(line.strip(), styles["Normal"]))
        story.append(Spacer(1, 12))

    doc.build(story)
    print(f"PDF berhasil disimpan di: {filepath}")

if __name__ == "__main__":
    create_dummy_pdf("prodi_ppg.pdf")