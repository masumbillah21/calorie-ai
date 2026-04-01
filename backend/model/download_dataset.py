"""
Download the Food-101 dataset with kagglehub and place it in backend/model/dataset.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

DATASET_REF = "dansbecker/food-101"
DATASET_OWNER, DATASET_SLUG = DATASET_REF.split("/", maxsplit=1)
MODEL_DIR = Path(__file__).resolve().parent
DATASET_PARENT = MODEL_DIR / "dataset"
TARGET_DIR = DATASET_PARENT / "food-101"
TARGET_IMAGES_DIR = TARGET_DIR / "images"
KAGGLE_CACHE_VERSIONS_DIR = (
    Path.home() / ".cache" / "kagglehub" / "datasets" / DATASET_OWNER / DATASET_SLUG / "versions"
)


def load_kagglehub():
    try:
        import kagglehub
    except ImportError as exc:  # pragma: no cover - user environment dependent
        raise SystemExit(
            "kagglehub is not installed. Run `make install-train-deps` first."
        ) from exc
    return kagglehub


def resolve_dataset_root(download_path: Path) -> Path:
    candidates: list[Path] = []
    seen: set[Path] = set()

    direct_candidates = [download_path, download_path / "food-101"]
    direct_candidates.extend(path for path in download_path.iterdir() if path.is_dir())

    for candidate in direct_candidates:
        if candidate in seen or "__MACOSX" in candidate.parts:
            continue
        seen.add(candidate)
        if (candidate / "images").is_dir():
            candidates.append(candidate)

    for images_dir in download_path.rglob("images"):
        if not images_dir.is_dir():
            continue
        candidate = images_dir.parent
        if candidate in seen or "__MACOSX" in candidate.parts:
            continue
        seen.add(candidate)
        candidates.append(candidate)

    if candidates:
        candidates.sort(
            key=lambda path: (
                not (path / "meta").is_dir(),
                len(path.relative_to(download_path).parts),
            )
        )
        return candidates[0]

    raise FileNotFoundError(
        "Downloaded dataset does not contain the expected `images` directory. "
        f"Checked under: {download_path}"
    )


def find_cached_download_path() -> Path | None:
    if not KAGGLE_CACHE_VERSIONS_DIR.is_dir():
        return None

    version_dirs = [path for path in KAGGLE_CACHE_VERSIONS_DIR.iterdir() if path.is_dir()]
    version_dirs.sort(
        key=lambda path: (not path.name.isdigit(), int(path.name) if path.name.isdigit() else path.name),
        reverse=True,
    )

    for version_dir in version_dirs:
        try:
            resolve_dataset_root(version_dir)
        except FileNotFoundError:
            continue
        return version_dir

    return None


def count_classes(images_dir: Path) -> int:
    return sum(1 for item in images_dir.iterdir() if item.is_dir())


def stage_dataset(source_root: Path, force: bool = False) -> Path:
    DATASET_PARENT.mkdir(parents=True, exist_ok=True)

    if TARGET_IMAGES_DIR.is_dir() and not force:
        print(f"Dataset already available at: {TARGET_DIR}")
        print(f"Detected {count_classes(TARGET_IMAGES_DIR)} classes.")
        return TARGET_DIR

    if TARGET_DIR.exists():
        print(f"Removing existing dataset directory: {TARGET_DIR}")
        shutil.rmtree(TARGET_DIR)

    print(f"Copying dataset to: {TARGET_DIR}")
    shutil.copytree(source_root, TARGET_DIR)
    return TARGET_DIR


def main(argv: list[str]) -> None:
    force = "--force" in argv
    refresh = "--refresh" in argv
    kagglehub = load_kagglehub()

    cached_path = None if refresh else find_cached_download_path()

    if cached_path is not None:
        print(f"Using cached {DATASET_REF} dataset from: {cached_path}")
    else:
        print(f"Downloading {DATASET_REF} via kagglehub...")
        cached_path = Path(kagglehub.dataset_download(DATASET_REF))
        print(f"Kaggle cache path: {cached_path}")

    source_root = resolve_dataset_root(cached_path)
    dataset_root = stage_dataset(source_root, force=force)
    images_dir = dataset_root / "images"

    if not images_dir.is_dir():
        raise FileNotFoundError(
            f"Dataset copy completed but `{images_dir}` was not found."
        )

    print("")
    print("Dataset ready.")
    print(f"  Root: {dataset_root}")
    print(f"  Images: {images_dir}")
    print(f"  Classes: {count_classes(images_dir)}")
    print("Run `make train` to start model training.")


if __name__ == "__main__":
    main(sys.argv[1:])
