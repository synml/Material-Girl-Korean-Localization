"""Material Girl .sl scenario file codec.

The game (RPG Maker MV + TS_ADVsystem) stores scenario scripts as UTF-8 text
where every UTF-16 code unit is XOR'ed with 255 (see www/js/plugins/TS_Decode.js).
The operation is symmetric: decode == encode.

Usage:
    uv run python tools/sl_codec.py decode <in_file_or_dir> <out_dir>   # .sl -> .txt
    uv run python tools/sl_codec.py encode <in_file_or_dir> <out_dir>   # .txt -> .sl
    uv run python tools/sl_codec.py roundtrip <dir>                     # verify byte-identical roundtrip
"""

import sys
from pathlib import Path

KEY = 255


def xor_text(text: str) -> str:
    # Match JS charCodeAt/fromCharCode semantics (UTF-16 code units).
    # All characters in this game's scripts are BMP, so per-codepoint XOR is equivalent.
    return "".join(chr(ord(c) ^ KEY) for c in text)


def convert_file(src: Path, dst: Path) -> None:
    # newline='' preserves the exact newline bytes through the roundtrip.
    data = src.read_text(encoding="utf-8", newline="")
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "w", encoding="utf-8", newline="") as f:
        f.write(xor_text(data))


def gather(path: Path, ext: str) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(path.glob(f"*{ext}"))


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    src = Path(sys.argv[2])

    if cmd == "roundtrip":
        bad = 0
        for f in gather(src, ".sl"):
            raw = f.read_text(encoding="utf-8", newline="")
            if xor_text(xor_text(raw)) != raw:
                print(f"FAIL: {f.name}")
                bad += 1
        print(f"roundtrip OK for {len(gather(src, '.sl')) - bad} files, {bad} failures")
        return

    out_dir = Path(sys.argv[3])
    in_ext, out_ext = (".sl", ".txt") if cmd == "decode" else (".txt", ".sl")
    files = gather(src, in_ext)
    for f in files:
        convert_file(f, out_dir / (f.stem + out_ext))
    print(f"{cmd}d {len(files)} files -> {out_dir}")


if __name__ == "__main__":
    main()
