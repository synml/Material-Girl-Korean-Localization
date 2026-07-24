# Material Girl 한글패치 (Korean Localization)

Steam판 **Material Girl** (RPG Maker MV)의 비공식 한글패치입니다.  
게임의 영어(En) 언어 슬롯을 한국어로 교체하는 방식으로 동작합니다.  
옵션의 언어 항목에는 English 대신 **한국어**로 표시됩니다.

## ⚙️ 요구 사항

- 정품 게임 (Steam판 Material Girl)
- [uv](https://docs.astral.sh/uv/) — 패치 적용/빌드 스크립트 실행용 (Python 자동 관리)

## 📦 설치

게임 설치 경로가 기본값(`D:\SteamLibrary\steamapps\common\Material Girl`)이 아니면 명령 끝에 경로를 추가하세요.

```bash
uv run python tools/apply_patch.py
```

- 게임 옵션에서 언어가 **한국어**(기존 English 슬롯)로 선택되어 있는지 확인하세요.
- 여러 번 실행해도 안전합니다 (패치 파일을 다시 덮어쓸 뿐).
- 게임 업데이트로 파일이 갱신된 경우에도 다시 실행하면 됩니다.

## ♻️ 복원

Steam → 게임 속성 → 설치된 파일 → **게임 파일 무결성 검사**를 실행하면 원본으로 되돌아갑니다.  
패치가 새로 추가한 폰트 파일(`Pretendard-Regular.otf` 등)은 무결성 검사가 지우지 않고 남겨둡니다.  
다만 원본 `gamefont.css`가 복원되어 참조되지 않으므로 무해합니다.

## 🗂️ 리포지토리 구조

```plain
analysis/         캐릭터·문체 분석 자료
patch/            완성된 패치 파일 (게임 폴더에 그대로 덮어쓰는 트리)
  scenario/En/    한국어 시나리오 (XOR 인코딩된 .sl)
  www/data/       한국어화된 데이터 JSON (선택지·DB·맵 텍스트·시스템 용어)
  www/fonts/      Pretendard 폰트 + gamefont.css
  www/js/         한국어화된 플러그인 (TS_Localize, RTK 용어, 언어명, 줄바꿈 폭)
patch_data/       선택지·DB·맵 텍스트·시스템 용어 번역 매핑
source_ch/        디코딩된 중국어 원문 (교차검증 소스)
source_data/      패치 대상 데이터 JSON 원본 사본 (빌드 입력)
source_en/        디코딩된 영어 원문 (번역 소스)
tools/            디코딩/인코딩/추출/주입/검증/조립/적용 스크립트
translated_ko/    한국어 시나리오 평문 (검수·수정용 정본)
CLAUDE.md         작업 가이드라인 (번역·기술 품질 규칙)
GLOSSARY.md       용어집 (구속력 있는 번역 기준)
STYLE_GUIDE.md    캐릭터별 문체 가이드
```

## ✏️ 번역 수정 방법

1. `translated_ko/파일명.txt`에서 해당 줄 수정 (엔진 명령 `@…`, 보이스 ID, 제어 코드는 유지)
2. 재조립:

   ```bash
   uv run python tools/build_patch.py
   ```

3. 표시 폭 검사 (창 밖으로 넘치는 줄이 없는지):

   ```bash
   uv run tools/check_line_width.py
   ```

4. 미번역 잔존 검사 (`translated_ko/` 밖의 표시 경로까지):

   ```bash
   uv run python tools/check_untranslated.py
   ```

5. 게임에 적용:

   ```bash
   uv run python tools/apply_patch.py
   ```

선택지·DB·맵 텍스트·시스템 용어를 수정할 때는 `patch_data/*.json`을 고친 뒤 같은 순서로 재조립·적용하면 됩니다.  
세이브 화면 지역명과 스테이터스 화면의 상대 이름은 데이터가 아니라 플러그인 표에 있습니다  
(`patch/www/js/plugins/TS_Localize.js`의 `ChangeList`) — 이쪽은 재조립 없이 적용만 하면 됩니다.

## 🔧 기술 메모

- `.sl` 파일은 UTF-8 텍스트의 각 문자(UTF-16 코드 유닛)를 255와 XOR한 형식입니다 (`www/js/plugins/TS_Decode.js` 참조).  
  인코딩/디코딩은 대칭이며 `tools/sl_codec.py`로 처리합니다.  
  단, `scenario/cglist.sl`·`rplist.sl`은 인코딩되지 않은 ID 테이블이라 건드리지 않습니다.
- 대사 태그 `[이름/보이스ID]`에서 이름은 표시용(번역), 보이스 ID는 파일 참조(유지)입니다.
- DB 다국어는 노트 태그 `<en:이름,설명>` 방식입니다 (RTK1_Option_EnJa).  
  파서가 쉼표로 무조건 분리하므로 한국어 설명문에는 쉼표를 쓰지 않습니다.
- 선택지 다국어는 `일본어 ||| 영어 ||| 중국어` 구분자 방식으로, 가운데 슬롯을 한국어로 교체합니다.  
  다만 일부 선택지는 이 방식이 아니라 **언어 변수(11) 조건분기**로 언어별 목록이 따로 있어서,
  그쪽은 영어 분기만 골라 교체합니다 (`patch_data/event_ui_ko.json`).
- `System.json`의 용어 배열은 `일본어||한국어` 한 문자열로 만듭니다 — RTK가 이를 분리해 슬롯별로 넣기 때문에  
  배열을 통째로 바꾸지 않고도 한국어 슬롯만 바꿀 수 있습니다 (장비 화면 슬롯명 `소지품`·`옷차림`).
- 자동 줄바꿈은 `TS_ADVsystem.viewMesAdjust()`가 **글자 수**로 처리합니다 (반각·전각 모두 1자).  
  원본은 영어 슬롯에 한해 한 줄 허용치를 27→54자로 2배 늘리는데, 전각 폭인 한글에는 너무 넓어  
  메시지 창(988px)을 넘어 오른쪽이 잘립니다. 그래서 패치는 이 값을 **43자**로 고정하고,  
  같은 함수가 붙이는 왼쪽 들여쓰기도 전각 5-7칸에서 **1-3칸**으로 줄입니다.  
  선택지·DB 설명은 자동 줄바꿈이 없으므로 문장 길이로 직접 맞춰야 하며,  
  `tools/check_line_width.py`가 실제 폰트 메트릭으로 전 경로를 검사합니다.
- 폰트는 **Pretendard Regular(OTF)를 번들**하고 `gamefont.css`의 `@font-face`가 이를 최우선 참조합니다.  
  로드 실패 시 원본 M+ 폰트로 폴백합니다.  
  Pretendard에 없는 글리프(잔존 가나 등)는 크로미움이 시스템 폰트에서 글자 단위로 대체합니다.
