# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 日本語でのやり取り

- Claudeとのやり取りは日本語で行い、ドキュメントも原則日本語でお願いします

## プロジェクト概要

このリポジトリは、RDBスキーマの命名規約とツール群の単一情報源 (Single Source of Truth) です。国際対応の命名ルール化、辞書管理、およびPoCからProduct版への自動変換ツールを提供します。

- **メイン辞書**: `dictionary/naming_dictionary.yaml`（正本）
- **検証スキーマ**: `dictionary/schema.json`
- **ツール群**: `tools/`ディレクトリ
- **Lint設定**: `lint/lint_config.yaml`
- **CI設定**: `ci/pre_commit_hook.yaml`

## アーキテクチャ

### 核となるコンポーネント

1. **命名辞書** (`dictionary/naming_dictionary.yaml`)
   - 医療機関・医療機器等のエンティティ定義
   - 正規名・同義語・禁止語の管理
   - n:n中間テーブルパターン定義
   - 主キー・タイムスタンプの命名ルール

2. **変換ツール群** (`tools/`)
   - `xlsx_to_yaml.py`: Excel → YAML変換
   - `build_alias_map.py`: 旧名→新名の対応表生成
   - `dictionary_flat.py`: 辞書の一覧CSV出力
   - `lint_names.py`: 命名規約チェック

3. **設定ファイル**
   - `tools/config/header_map.yaml`: Excel見出しマッピング
   - `tools/config/smds_poc/`: PoC版のDB仕様書
   - `tools/config/optiserve/`: ルールを意識したサブプロジェクトのテーブル仕様書（YAML管理）
   - `lint/lint_config.yaml`: 正規表現・接尾辞ルール
   - `ci/pre_commit_hook.yaml`: プリコミットフック設定

4. **作業領域** (`schema/`)
   - `schema/tables/`: 最終成果（新命名のテーブル定義YAML）
   - `schema/derived/`: 生成物・レポート（基本的にコミット対象外）

## 開発コマンド

### ツール実行
```bash
# 辞書から対応表を生成
python tools/build_alias_map.py

# 辞書を一覧CSV形式で出力
python tools/dictionary_flat.py

# 命名規約チェック
python tools/lint_names.py

# Excel → YAML変換
python tools/xlsx_to_yaml.py
```

### Lint/CI
```bash
# プリコミットフック設定（各プロジェクト側で実行）
cp ci/pre_commit_hook.yaml .pre-commit-config.yaml
```

## バージョニング

- **SemVer**: `MAJOR.MINOR.PATCH`
- MAJOR: 破壊的変更（正規名変更・禁止語追加）
- MINOR: 語彙追加・説明追記（後方互換）
- PATCH: 誤字や微修正

## 開発ワークフロー

### 辞書・ルール管理
1. **段取り確認**: `Checklist.md`の順序で作業進行
2. **辞書編集**: `dictionary/naming_dictionary.yaml`のみ編集（Docsは生成物）
3. **PR必須**: 辞書変更は必ずPRレビューを通す
4. **CI検証**: `dictionary/schema.json`による検証を通す
5. **バージョン更新**: `CHANGELOG.md`と`VERSION`を更新してタグ付与

### スキーマ変換作業（Product前段）
1. **置換候補の抽出**: ツールで `schema/derived/alias_map/YYYY-MM-DD/alias_map.csv` を作成
2. **レビュー＆確定**: FK語幹・n:n形式・施設の接頭辞などの方針を最終確認
3. **YAML生成**: 新命名で `schema/tables/` にテーブル定義を追加
4. **Lint**: 命名規約（PK/FK/禁止語/接尾辞）のチェックを通す
5. **PR**: レビュー対象は主に `schema/tables/*.yaml`、必要に応じて当日の `derived/` を添付

### 当日フォルダの作成
```bash
export TODAY=$(date +%F)
mkdir -p schema/derived/alias_map/$TODAY schema/derived/scans/$TODAY
```

## 重要なファイル

- **作業計画**: `Checklist.md` - 詳細なフェーズ別作業リスト
- **命名規約**: `docs/rule_of_database_design.md` - 包括的な命名ルール
- **作業領域ガイド**: `schema/README.md` - スキーマ変換作業の詳細手順
- **元データ**: 
  - `tools/config/smds_poc/` - PoCのDB設計書
  - `tools/config/optiserve/` - サブプロジェクトのテーブル仕様書（YAML）
- **バージョン情報**: `VERSION`, `CHANGELOG.md`

## gitignore推奨設定

```gitignore
schema/derived/**
!schema/derived/**/README.md
```

## 次フェーズの参照方法

```bash
# サブモジュールとして固定バージョンで参照
git submodule add <REPO-URL> schema-naming
cd schema-naming && git checkout v0.1.0
```

