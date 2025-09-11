# schema-naming
Single source of truth for **RDB schema naming** (dictionary + lint + tools).
識別子の命名規約と語彙、検証ツール群を横断プロジェクトで共有します。

## What this repo is
- **Canonical dictionary**: `dictionary/naming_dictionary.yaml`（正本）
- **Validation schema**: `dictionary/schema.json`
- **Lint & tooling**: `tools/`（alias-map生成／一覧CSV出力／Excel→YAML 変換 ほか）
- Designed for **submodule pinning** (later packageable)

## Quick start (as submodule)
```bash
git submodule add <REPO-URL> schema-naming
cd schema-naming && git fetch && git checkout v0.1.0
cd .. && git add schema-naming && git commit -m "Use schema-naming v0.1.0"
```

## Repository layout
```
dictionary/      # naming_dictionary.yaml（正本）, schema.json（検証用）
lint/            # lint_config.yaml（正規表現/接尾辞などの共通設定）
tools/           # build_alias_map.py / dictionary_flat.py / lint_names.py / xlsx_to_yaml.py
ci/              # pre_commit_hook.yaml（各プロジェクト側に取り込み）
docs/            # 規約本文（rule_of_database_design.md）など
examples/        # サンプル入力/出力（必要に応じて追加）
schema/          # 辞書やツール -> 詳細は `schema/README.md` を参照
VERSION          # 例: 0.1.0
CHANGELOG.md
```

## Versioning
- **SemVer**: `MAJOR.MINOR.PATCH`
  - MAJOR: 破壊的変更（canonical名変更・禁止語追加 など）
  - MINOR: 語彙追加・説明追記（後方互換）
  - PATCH: 誤字や微修正

## Contribution
1) 辞書の変更は PR 必須（`dictionary/naming_dictionary.yaml` のみ編集）
2) CI で `dictionary/schema.json` による検証を通す
3) `CHANGELOG.md` と `VERSION` を更新、タグを付与

## FAQ
- **辞書とMarkdownはどちらを編集？** → **辞書（YAML）だけ**。Docsは生成 or 反映。
- **略語は使える？** → 識別子では原則禁止。説明/UI文言でのみ（例 “ME”）。
- **例外は？** → 各プロジェクト側の allowlist（期限付き）で管理。
