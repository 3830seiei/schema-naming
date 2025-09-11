# Schema-Naming 作業チェックリスト

This checklist tracks schema-naming governance setup (rules/dictionary/tools) before Product development.

## 概要

- **国際対応の命名ルールを決める**
- **変換辞書（＝ルール + 旧→新の機械適用ロジック）を作る**
- **PoCリポを複製 → 自動変換（Excel→YAML→Python/SQL）して Product 版の土台にする**

- 命名ルールは、今後の新規プロジェクトでも利用することが前提
  - PoCからProductの変換のみ今回限りの作業となる

## スコープ（再確認）

- ✅ 既存PoCのDBは**使わない／触らない**
- ✅ まずは**ルール→辞書→変換ライン**を整える（DB構築は次フェーズ）
- ✅ 旧→新の**全件対比は alias_map.csv**（YAML本体は新命名だけ）

## 実行計画（1時間タスクで細切れ）

### Phase 0 — ルール“最終確定”（計3h）

1. **Non-negotiables一枚化（1h）**
   `map_<a>__<b>`, `<table_short>_id`, `medical_facility`, `medical_equipment`, `classification/category/status`, `*_at/*_on`, 制約名ルール を1ページに。

2. **語彙の最終合意（1h）**
   `medical_entity → medical_equipment`、`facility`は汎用予約、Booleansは `is_/has_/can_`。

3. **命名の自動判定仕様（1h）**
    - `table_short` 抽出（`mst_/map_/log_/stg_`を除去→残りをそのまま採用）
    - n\:n 正規表現 `^map_[a-z0-9_]+__[_a-z0-9]+$`
    - PK/FK/日時/禁止語のチェック順

### Phase 1 — devbase（辞書とツールの土台）（計6h）

4. **devbaseツリーの雛形作成（1h）**
   `schema/naming/{naming_dictionary.yaml,schema.json,tools/*}` と `ci/pre_commit_hook.yaml` を配置。
5. **`naming_dictionary.yaml v0.1` 初版（1h）**
   `MEDICAL_FACILITY / MEDICAL_EQUIPMENT / N_TO_N_TABLE / PRIMARY_KEY_STYLE / TIMESTAMP_STYLE / AUDIT_COLUMNS` を登録（JP/ENコメント付き）。
6. **`schema.json`（辞書のスキーマ）作成（1h）**
   `canonical/synonyms/forbidden/lint/migration` をバリデート。
7. **`build_alias_map.py` 叩き台（1h）**
   辞書ルール→旧→新の置換候補CSVを吐く（規則マッチ + 文字列置換）。
8. **`dictionary_flat.py`（一覧CSV）作成（1h）**
   人間レビュー用にフラット化（id, kind, canonical, forbidden, notes）。
9. **devbase READMEの該当節ドラフト（1h）**
   「参照はサブモジュール固定」「例外は期限付きallowlist」「CIでLint」を明記。

### Phase 2 — Excel→YAML 変換ライン（計6h）

10. **Excel見出し→標準キーのマッピング表（1h）**
    例：`ColumnName→name`, `DataType→type`, `PK→is_pk`, `FK→references`, `Description→description`。
11. **`xlsx_to_yaml.py` プロトタイプ（1h）**
    1シート=1 YAML（**新命名のみ**出力。旧名は出さない）。
12. **辞書適用（リネーム）ロジック実装（1h）**
    例：`medical_id→medical_facility_id`, `*_datetime→*_at`, `*_link→map_<a>__<b>`, `entity→medical_equipment`。
13. **ユニーク衝突検知 & 自動サフィックス提案（1h）**
    生成前に重複検出し、候補を提示（要手確認）。
14. **代表1表の試験変換→レビュー（1h）**
    出力YAMLの体裁/命名を目視チェック。
15. **複数表の一括変換 + 生成物書き出し（1h）**
    `schema/tables/*.yaml`、`alias_map.csv`（全件対比）、`conversion_report.md`（件数サマリ）。

### Phase 3 — コード自動変換（PoC複製リポ）（計6h）

16. **対象リポの複製 & ブランチ準備（1h）**
    `product-<repo>` を作り、`devbase` をサブモジュール固定、`schema.lock` 記録。
17. **コードスキャン（1h）**
    grep/ASTで Python/SQL に出る旧名を抽出 → `occurrences.csv` に集計。
18. **置換プラン生成（1h）**
    `alias_map.csv` と突き合わせ → `.patch` or `sed` スクリプトを生成。
19. **安全域で適用トライ（1h）**
    まずコメント/定数/テスト用SQLなどから当てて差分確認。
20. **広範囲適用 & import/起動チェック（1h）**
    FastAPI/SQLAlchemyが起動・型チェックを通るかを確認（DB接続は不要）。
21. **変換手順書の追記（1h）**
    置換スクリプトの使い方、ロールバック、差分レビューの観点を `CONTRIBUTING.md` に。

### Phase 4 — ドキュメント仕上げ（計4h）

22. **rule\_of\_database\_design.md 改稿（1h）**
    冒頭に Non-negotiables を固定。**Alembic/既存DBリネームの記述は削除**。
23. **devbase README 追記（1h）**
    「Excel→YAML→コード変換」の**パイプライン図**と“DB構築は次フェーズ”を明記。
24. **Top50対訳表（EN/JA）作成（1h）**
    `medical_facility / medical_equipment / classification / category / status / is_/has_/can_` など。
25. **変換チュートリアル（1h）**
    **Excel投入→実行→生成物→コード置換**の手順を1ページ。

## 成果物チェックリスト

- [ ] **命名辞書（YAML）**：JP/EN説明付き、`MEDICAL_FACILITY` / `MEDICAL_EQUIPMENT` ほか
- [ ] **schema.json**：辞書のスキーマ
- [ ] **Excel→YAML 変換ツール** & **config（見出しマップ）**
- [ ] **alias_map.csv**（旧→新の全件対比）
- [ ] **occurrences.csv**（コード内出現一覧） & **置換スクリプト**
- [ ] **rule_of_database_design.md**（Non-negotiables固定、移行記述を削除）
- [ ] **devbase/README**（参照・固定・パイプライン明記）
- [ ] **Top50対訳表** / **変換チュートリアル**

## 更新履歴（2025-09-11）
- alias_map 初期版を生成: 0 件の置換候補（規則別: ）
- 生成物: [alias_map.csv](alias_map.csv) / [alias_report.json](alias_report.json)
- 次アクション:
  - 高確度（confidence >= 0.95）を先にレビュー
  - `*_entity_link` 系は Left 側の正規語確認の上で `map_<left>__medical_equipment` へ確定
  - `equipment_id -> medical_equipment_id` は文脈確認後に一括適用
