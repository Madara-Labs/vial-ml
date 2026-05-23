import json
from pathlib import Path


class Workspace:
    METADATA_FILENAME = "metadata.json"

    def __init__(self, directory: Path | str = ".vial_workspace"):
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.metadata_path = self.dir / self.METADATA_FILENAME

    def isolated_path(self, target_name: str) -> Path:
        return self.dir / f"{target_name}_isolated.py"

    def save_metadata(self, meta: dict) -> None:
        self.metadata_path.write_text(json.dumps(meta, indent=2))

    def load_metadata(self) -> dict:
        if not self.metadata_path.exists():
            raise FileNotFoundError(
                f"No active session found in {self.dir}. Run `vial extract` first."
            )
        return json.loads(self.metadata_path.read_text())

    def cleanup(self) -> None:
        meta = self.load_metadata()
        isolated = Path(meta["isolated_filepath"])
        if isolated.exists():
            isolated.unlink()
        self.metadata_path.unlink()
