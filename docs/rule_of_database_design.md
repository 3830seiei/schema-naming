# Database Naming & Schema Conventions
> 本書は、長期運用を前提とした **国際対応の命名規約** と **スキーマ設計の原則** を定義します。  
> This document defines durable, internationally-consistent naming and schema conventions.

---

## 1. スコープ / Audience
- RDBMS: PostgreSQL（想定）
- 対象: テーブル／カラム／制約／インデックス／ビュー／コード表（マスタ）／n:n マッピング
- 表記: **英語を正（Canonical）**、識別子は ASCII の **snake_case**、**単数形**

## 2. 設計原則 / Design Principles
1. **Clarity over brevity** — 可読性を優先（曖昧語・省略形を避ける）  
2. **Deterministic naming** — 人と機械で一意に導出できる命名  
3. **Canonical English + Multilingual meta** — 識別子は英語、説明は多言語メタで保持  
4. **Separation of concerns** — マスタ／業務データ／ログ／中間表の分離  
5. **Validation-first** — Lint/CIで規約順守を自動検証

## 3. テーブル命名 / Table Names
**形式**: `<prefix_optional><domain>_<object>`
- `mst_`（マスタ）, `map_`（n:n）, `log_`（ログ/イベント）, `stg_`（ステージング）, `vw_`/`mv_`（ビュー）
- **n:n 中間表**: `map_<entity_a>__<entity_b>`（ダブルアンダースコアで順序固定）
- 例: `mst_medical_facility`, `map_medical_facility__equipment`

## 4. カラム命名 / Column Names
- **主キー**: `<table_short>_id`（`table_short` は接頭辞除去後の残り。短縮しない）  
  例: `mst_medical_facility.medical_facility_id`
- **外部キー**: `<referenced_table_short>_id`（例: `medical_facility_id`）
- **コード/名称/説明**: `*_code` / `*_name` / `*_label` / `*_desc`
- **真偽**: `is_` / `has_` / `can_`
- **日時**: `*_at`（timestamptz）, 日付のみ `*_on`（date）
- **監査**: `created_at`, `created_by`, `updated_at`, `updated_by`（必要に応じ `deleted_*`）

## 5. 制約・インデックス / Constraints & Indexes
- PK: `pk_<table>`  
- FK: `fk_<table>__<column>`  
- UQ: `uq_<table>__<column(s)>`  
- CHECK: `ck_<table>__<name>`  
- INDEX: `idx_<table>__<column(s)>`

## 6. コントロールド・ボキャブラリ / Controlled Vocabulary
| Canonical (en)    | 日本語   | OK in docs (synonyms) | Forbidden (識別子不可)       | Notes |
|---|---|---|---|---|
| medical_facility  | 医療機関 | hospital, clinic      | facility（医療の意味では不可）| 施設一般は別語 |
| medical_equipment | 医療機器 | equipment, device     | medical_entity, entity       | “ME”は説明のみ |
| classification    | 分類     | taxonomy              | type, kind                   | 階層的分類 |
| category          | 区分     | group                 | type, kind                   | 平坦なグループ |
| status            | 状態     | state                 | phase（設計により）          | ライフサイクル |
| boolean prefixes  | —        | is_, has_, can_       | —                            | 真偽接頭辞 |

## 7. 多言語メタ / Multilingual Metadata
- テーブル/カラムに `title.en/ja`, `description.en/ja` を付与可能。識別子は英語固定。

## 8. YAML 定義の最小形 / Minimal YAML
```yaml
table: mst_medical_facility
title: { en: Medical Facility, ja: 医療機関 }
description: { en: Master of healthcare provider sites., ja: 医療機関マスタ }
columns:
  - { name: medical_facility_id, type: bigint, identity: true, nullable: false }
  - { name: facility_code, type: text, unique: true, nullable: false }
  - { name: facility_name, type: text, nullable: false }
  - { name: is_active, type: boolean, default: true }
  - { name: created_at, type: timestamptz, nullable: false }
  - { name: created_by, type: bigint, nullable: false }
  - { name: updated_at, type: timestamptz, nullable: false }
  - { name: updated_by, type: bigint, nullable: false }
constraints:
  - { name: pk_mst_medical_facility, type: primary_key, columns: [medical_facility_id] }
indexes:
  - { name: idx_mst_medical_facility__facility_code, columns: [facility_code] }
```

### n:n 例
```yaml
table: map_medical_facility__equipment
title: { en: Facility–Equipment Mapping, ja: 医療機関と医療機器の関連 }
columns:
  - { name: medical_facility_id, type: bigint, nullable: false }
  - { name: medical_equipment_id, type: bigint, nullable: false }
  - { name: created_at, type: timestamptz, nullable: false }
constraints:
  - { name: pk_map_medical_facility__equipment, type: primary_key, columns: [medical_facility_id, medical_equipment_id] }
```

## 9. 決定性アルゴリズム / Deterministic Rules
- `table_short` = テーブル名から `mst_/map_/log_/stg_/vw_/mv_` を除去した残り（短縮しない）
- PK 名: `<table_short>_id`／FK 名: `<referenced_table_short>_id`
- n:n: `^map_[a-z0-9_]+__[_a-z0-9]+$`
- 予約・禁止語は `dictionary/naming_dictionary.yaml` で管理

## 10. ガバナンス / Governance
- Source of Truth: `dictionary/naming_dictionary.yaml`
- SemVer: MAJOR/MINOR/PATCH
- PR レビュー: 規約変更／語彙追加は必須レビュー
- Lint/CI: 禁止語・パターン違反・表記ゆれを検出
