import os
import hashlib
from pathlib import Path
from typing import List, Dict, Any

class GRScraper:
    """
    Scans the incoming Government Resolution (GR) repository and gazette feeds.
    Computes cryptographic SHA-256 hashes to prevent duplicate ingestion.
    """
    def __init__(self, watch_dir: str = None):
        if watch_dir:
            self.watch_dir = Path(watch_dir)
        else:
            self.watch_dir = Path(__file__).resolve().parent.parent.parent / "incoming_gr_pdfs"
        self.watch_dir.mkdir(parents=True, exist_ok=True)
        self.processed_hashes = set()

    def compute_file_hash(self, file_path: Path) -> str:
        """Calculates SHA-256 hash of a file."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    def scan_incoming_pdfs(self) -> List[Dict[str, Any]]:
        """
        Scans watch_dir for new PDFs.
        Returns list of newly discovered PDF metadata.
        """
        new_files = []
        for pdf_file in self.watch_dir.glob("*.pdf"):
            f_hash = self.compute_file_hash(pdf_file)
            if f_hash not in self.processed_hashes:
                self.processed_hashes.add(f_hash)
                new_files.append({
                    "filename": pdf_file.name,
                    "filepath": str(pdf_file),
                    "file_hash": f_hash,
                    "size_bytes": pdf_file.stat().st_size
                })
        return new_files

gr_scraper = GRScraper()
