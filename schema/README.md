# schema/ — プロジェクト側のスキーマ作業領域

このディレクトリは **各プロジェクトで運用する作業スペース** です。
- 最終成果（新命名のYAML定義）は `tables/` に置いて **コミット対象**。
- 生成物（対照表やレポートなどの一時ファイル）は `derived/` に置いて **基本はコミットしない**（レビューで必要なときのみコミット）。

## ディレクトリ構成
```
schema/
  tables/        # 最終成果（新命名のテーブル定義YAMLをここにコミット）
  derived/       # 生成物（レビュー/一次成果）
    alias_map/
      YYYY-MM-DD/
        alias_map.csv        # 旧→新 置換の確定表（レビュー対象のことがある）
        alias_report.json    # 置換候補の統計/サマリ
    scans/
      YYYY-MM-DD/
        token_counts.csv     # 解析用（辞書拡張の参考資料）
```

## 何をコミットする？ / What to commit
- ✅ `tables/*.yaml`（**新命名のみ**。旧名はコメントでも残さない）
- ⛔ `derived/**`（原則コミットしない）
  - ただし、**レビュー**や**記録**目的で必要な日付フォルダのみコミット可（PRが終われば削除可）

### 推奨 .gitignore（プロジェクトのルートに配置）
```gitignore
schema/derived/**
!schema/derived/**/README.md
```

## 典型的な作業手順（Product 前段）
1. **辞書とルールを固定**（例：サブモジュール `schema-naming` をタグで固定）  
2. **置換候補の抽出**：ツールで `derived/alias_map/YYYY-MM-DD/alias_map.csv` を作成  
3. **レビュー＆確定**：FK語幹・n:n 形式・施設の接頭辞などの方針を最終確認  
4. **YAML生成**：新命名で `tables/` にテーブル定義を追加  
5. **Lint**：命名規約（PK/FK/禁止語/接尾辞）のチェックを通す  
6. **PR**：レビュー対象は主に `tables/*.yaml`。必要に応じて当日の `derived/` を添付

## 命名ルールの参照（Source of Truth）
- 正本は **schema-naming リポジトリ**内の `dictionary/naming_dictionary.yaml`。
- 規約本文は `schema-naming/docs/rule_of_database_design.md`。
- 変更は schema-naming 側でPRし、タグを更新してから各プロジェクトに反映します。

_Last updated: 2025-09-11_
