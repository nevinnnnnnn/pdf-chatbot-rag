import os
import sys
import types

# Keep this file plain ASCII/UTF-8 without null bytes
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Minimal fake pypdf so test does not require external package install
class _DummyPdfReader:
    def __init__(self, path):
        self.pages = []

fake_pypdf = types.ModuleType("pypdf")
fake_pypdf.PdfReader = _DummyPdfReader
sys.modules["pypdf"] = fake_pypdf

from core.pdf_processor import RecursiveCharacterTextSplitter, _clean_text


def test_clean_and_split_basic():
    raw = "This is a test.\n\nSecond paragraph with some content.\n\nThird paragraph."
    cleaned = _clean_text(raw)
    assert "\x00" not in cleaned
    assert "  " not in cleaned

    splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=10)
    chunks = splitter.split_text(cleaned)

    assert isinstance(chunks, list)
    assert len(chunks) >= 1
    for c in chunks:
        assert isinstance(c, str) and c.strip()
