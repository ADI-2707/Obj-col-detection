from pathlib import Path
from vision.manual import generate_features_manual_pdf, get_manual_pdf_path


def test_get_manual_pdf_path():
    path = get_manual_pdf_path()
    assert path.name == "Vision_Features_and_Operation_Manual.pdf"


def test_generate_features_manual_pdf_creates_file(tmp_path):
    out_pdf = tmp_path / "manual_output.pdf"
    res = generate_features_manual_pdf(out_pdf)
    assert res == out_pdf
    assert out_pdf.exists()
    assert out_pdf.stat().st_size > 15000
    pdf_bytes = out_pdf.read_bytes()
    assert pdf_bytes.startswith(b"%PDF-")


def test_open_pdf_manual_generates_if_not_present(monkeypatch, tmp_path):
    from vision.manual import open_pdf_manual
    target_pdf = tmp_path / "test_docs" / "manual.pdf"
    opened = []
    monkeypatch.setattr("os.startfile", lambda p: opened.append(p), raising=False)
    monkeypatch.setattr("subprocess.Popen", lambda *args, **kwargs: opened.append(args), raising=False)
    res = open_pdf_manual(target_pdf)
    assert res == target_pdf
    assert target_pdf.exists()
    assert len(opened) > 0


def test_draw_page_watermark_gracefully_handles_missing_logo():
    from vision.manual import draw_page_watermark_and_chrome
    from reportlab.pdfgen import canvas
    import io

    class DummyDoc:
        pagesize = (595.27, 841.89)

    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    draw_page_watermark_and_chrome(c, DummyDoc(), Path("nonexistent_logo_123.png"))
    c.save()
    assert buf.getvalue().startswith(b"%PDF-")
