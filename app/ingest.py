import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def ingest_documents(
    docs_dir: Optional[str] = None,
    chroma_path: Optional[str] = None,
    collection_name: str = "lembah_asri_docs",
) -> int:
    """
    Membaca dokumen PDF resmi dari folder docs/ dan melakukan embedding ke ChromaDB.
    
    Args:
        docs_dir: Path folder sumber dokumen PDF (default dari env DOCS_DIR atau 'docs').
        chroma_path: Path direktori penyimpanan vektor ChromaDB (default dari env CHROMA_PATH atau 'chroma_data').
        collection_name: Nama collection pada ChromaDB.
        
    Returns:
        Jumlah dokumen atau chunk yang berhasil diindeks.
    """
    target_docs_dir = docs_dir or os.getenv("DOCS_DIR", "docs")
    target_chroma_path = chroma_path or os.getenv("CHROMA_PATH", "chroma_data")

    logger.info(f"Memulai proses ingestion dari '{target_docs_dir}' ke ChromaDB '{target_chroma_path}'...")

    # TODO: Diimplementasikan oleh anggota tim RAG:
    # 1. Baca semua file .pdf di folder target_docs_dir menggunakan PyPDFLoader / DirectoryLoader
    # 2. Lakukan text splitting (RecursiveCharacterTextSplitter)
    # 3. Buat vectorstore ChromaDB persisten dan tambahkan embeddings dokumen
    
    if not os.path.exists(target_docs_dir):
        logger.warning(f"Direktori {target_docs_dir} tidak ditemukan.")
        return 0

    files = [f for f in os.listdir(target_docs_dir) if f.endswith(".pdf")]
    logger.info(f"Ditemukan {len(files)} file PDF untuk di-ingest: {files}")

    return len(files)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ingest_documents()
