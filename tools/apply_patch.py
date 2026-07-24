"""Apply the Korean patch to the installed game.

Copies everything under patch/ into the game directory, overwriting the
originals. To revert to the original game files, use Steam's
"Verify integrity of game files" feature.

Usage:
    uv run python tools/apply_patch.py [game_dir]

Default game_dir: D:\\SteamLibrary\\steamapps\\common\\Material Girl
"""

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATCH = ROOT / "patch"
DEFAULT_GAME = Path(r"D:\SteamLibrary\steamapps\common\Material Girl")


def apply(game: Path) -> None:
    n = 0
    for src in PATCH.rglob("*"):
        if not src.is_file():
            continue
        dst = game / src.relative_to(PATCH)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        n += 1
    print(f"applied {n} files to {game}")
    print("revert: Steam > 속성 > 설치된 파일 > 게임 파일 무결성 검사")


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "apply"]  # tolerate legacy subcommand
    game = Path(args[0]) if args else DEFAULT_GAME
    if not (game / "Game.exe").exists():
        print(f"error: {game} does not look like the game directory (Game.exe not found)")
        sys.exit(1)
    apply(game)


if __name__ == "__main__":
    main()
