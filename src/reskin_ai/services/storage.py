from __future__ import annotations

import hashlib
import shutil
import uuid
from pathlib import Path


class LocalStorageService:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.uploads_dir = self.root / "uploads"
        self.concepts_dir = self.root / "concepts"
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.concepts_dir.mkdir(parents=True, exist_ok=True)

    def _normalize_suffix(self, filename: str, content_type: str) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
            return suffix
        if content_type == "image/jpeg":
            return ".jpg"
        if content_type == "image/png":
            return ".png"
        if content_type == "image/webp":
            return ".webp"
        return ".bin"

    def save_upload(self, *, filename: str, content_type: str, content: bytes) -> dict[str, str | int]:
        suffix = self._normalize_suffix(filename, content_type)
        file_id = uuid.uuid4().hex[:12]
        stored_name = f"{file_id}{suffix}"
        path = self.uploads_dir / stored_name
        path.write_bytes(content)
        checksum = hashlib.sha256(content).hexdigest()
        return {
            "storage_uri": f"/media/uploads/{stored_name}",
            "local_path": str(path),
            "size_bytes": len(content),
            "checksum": checksum,
        }

    def save_concept_asset(self, *, concept_id: str, content: bytes, extension: str) -> dict[str, str]:
        normalized_ext = extension.lower() if extension.startswith(".") else f".{extension.lower()}"
        if normalized_ext not in {".png", ".jpg", ".jpeg", ".webp", ".svg"}:
            normalized_ext = ".bin"
        file_name = f"{concept_id}{normalized_ext}"
        path = self.concepts_dir / file_name
        path.write_bytes(content)
        return {
            "storage_uri": f"/media/concepts/{file_name}",
            "local_path": str(path),
        }

    def save_concept_svg(self, *, concept_id: str, prompt_text: str, variant_index: int) -> dict[str, str]:
        safe_text = prompt_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        body = f"""<svg xmlns="http://www.w3.org/2000/svg" width="720" height="720">
<rect width="100%" height="100%" fill="#f4f1ea"/>
<text x="50%" y="30%" text-anchor="middle" font-size="26" fill="#2f2a1f">ReSkin Concept {variant_index}</text>
<text x="50%" y="45%" text-anchor="middle" font-size="16" fill="#5b5446">Prototype Preview</text>
<text x="50%" y="58%" text-anchor="middle" font-size="14" fill="#6d6556">{safe_text[:100]}</text>
</svg>"""
        return self.save_concept_asset(concept_id=concept_id, content=body.encode("utf-8"), extension=".svg")

    def delete_file(self, path_value: str | None) -> None:
        if not path_value:
            return
        path = Path(path_value)
        try:
            path.relative_to(self.root)
        except ValueError:
            return
        if path.exists() and path.is_file():
            path.unlink()

    def reset_for_tests(self) -> None:
        if self.uploads_dir.exists():
            shutil.rmtree(self.uploads_dir)
        if self.concepts_dir.exists():
            shutil.rmtree(self.concepts_dir)
        self._ensure_dirs()
