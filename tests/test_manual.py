from pathlib import Path
from orbix.manual import generate_features_manual_pdf, get_manual_pdf_path


def test_get_manual_pdf_path():
    path = get_manual_pdf_path()
    assert path.name == "Orbix_Features_and_Operation_Manual.pdf"


def test_generate_features_manual_pdf_creates_file(tmp_path):
    out_pdf = tmp_path / "manual_output.pdf"
    res = generate_features_manual_pdf(out_pdf)
    assert res == out_pdf
    assert out_pdf.exists()
    assert out_pdf.stat().st_size > 10000
