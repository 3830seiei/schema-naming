# データベース命名・設計規約（フル版 / 日本語）
_最終更新: 2025-09-11

本書は長期運用を前提とした **国際対応の命名規約** と **スキーマ設計の原則** を定義します。識別子は英語（ASCII, snake_case, 単数形）を正とし、日本語は説明（title/description）で補います。

---

## 1. スコープ / 対象
- 対象RDBMS: PostgreSQL（前提）
- 対象: **テーブル / カラム / 制約 / インデックス / ビュー / マスタ（コード表） / n:n 中間表**
- 言語・記法: **英語の snake_case・単数形**（`medical_device`, `medical_facility` など）

## 2. 設計原則
1. **Clarity over brevity**：省略よりも明確さを優先。曖昧語・略語は避ける。
2. **Deterministic naming**：人と機械が同じルールで名前を一意に導出できること。
3. **Canonical English + Multilingual meta**：識別子は英語、説明は多言語メタ（`title.ja/en`, `description.ja/en`）。
4. **Separation of concerns**：マスタ / 業務データ / ログ / 中間表を明確に分離。
5. **Validation-first**：Lint/CI による自動検証を前提とする。

## 3. 規制用語ポリシー（PMDA/MHLW 整合）

### 規制用語ポリシー（日本語版）
_最終更新: 2025-09-11

本プロジェクトの命名は **日本の規制当局（PMDA/厚生労働省）で用いられる用語** に整合させます。

### 基本方針

- 正規の用語は **`medical_device`（医療機器）** を用います。
  - ドキュメント上の説明として *medical equipment* を許容しますが、**識別子**では使用しません。特別意味が無ければ **medical device** で統一。
  - 略語 **ME** は **識別子で禁止**（Medical Engineer/Engineering との混同を避ける）。
- 規制上のリスク区分は **`risk_class`** とし、値は **`I`/`II`/`III`/`IV`** を採用します。
- 一般的名称（JMDN）は **`jmdn_code`** と **`jmdn_name_ja` / `jmdn_name_en`** を保持します。
- **`classification`** は階層的タクソノミー専用の語とし、規制の **「Class」**（リスク区分）とは用途を分離します。
  - 階層を列で持つ場合は **`classification_level1..N`** を使用します。
- n:n の表名は **`map_<a>_<b>`**（アンダースコア1個）。
  - **特例**：ユーザーが医療機関/ディーラー/メーカー等に属しうる多態関連は **`map_user_entity`** を許容し、当該表の外部キー名も **`entity_id`** を維持します。

## 4. スキーマ／テーブル命名（差し替え）

### 4.1 レイヤ（スキーマ）
- **raw** … 供給元そのまま（スナップショット保存庫）
- **cur** … キュレーション／正規化後（重複解消・型／命名統一）
- **core** … 業務コア（台帳＝ledger、履歴＝history、業務マスタ＝mst 等）
- **xref** … 対照・名寄せ（外部プロバイダやシステム間の対応関係）
- **mart** … 集計／分析（dim/fact/agg、BI向け）
- **util** … 補助（ユーティリティ／設定／ジョブ管理）※任意

> 形式：`<schema>.<table>`

### 4.2 テーブル命名の基本
- 形式：`<domain>_<entity>[_<suffix>]`
- **domain**：業務ドメイン（例：`product`, `equipment`, `medical_facility`）
- **entity**：対象（例：`ledger`, `history`, `mst`, `codes`, `crosswalk`）
- **suffix**：必要時のみ（例：`daily`, `monthly`, `pi`, `packaging_units` など）
- **複数形**：集合（行が増える“名簿系”）は **複数形**を原則
  - 例：`products`, `facilities`, `vendors`
  - ただし `ledger/history` は慣例的に単数ベースでも可
- **予約接頭辞**
  - ビュー：`v_`（例：`core.v_products_with_provider_ids`）
  - マテビュー：`mv_`
  - 業務マスタ：`mst_`（例：`core.mst_provider_codes`）

### 4.3 レイヤ別の命名・用語
- **raw**：`raw.<provider>_<source>_<yyyymm>`
  - 例：`raw.jahid_products_202311`, `raw.medie_facilities_202311`
- **cur**：`cur.<domain>[ _<detail> ]`
  - 例：`cur.products`, `cur.product_pi`, `cur.packaging_units`, `cur.facilities`
- **core（台帳／履歴／業務マスタ）**
  - 台帳：`<domain>_ledger`
    - 例：`core.equipment_ledger`
  - 履歴：`<domain>_history`
    - 例：`core.equipment_rental_history`, `core.equipment_repair_history`
  - 業務マスタ：`mst_<domain>` / `mst_<domain>_<detail>`
    - 例：`core.mst_jahid_products`, `core.mst_medie_packaging_units`
    - 共通区分：`core.mst_provider_codes`（＋`core.v_mst_jahid_codes` 等ビュー）
- **xref（対照・名寄せ）**
  - 外部ID対照：`<domain>_crosswalk` または `<domain>_xref`
    - 例：`xref.product_crosswalk`, `xref.facility_crosswalk`
  - `map_` は使用しない（処理用マッピングの印象が強いため）
- **mart（分析）**
  - 次元：`dim_<domain>`
  - 事実：`fact_<domain>`
  - 集約：`agg_<domain>_<grain>`
  - 例：`mart.dim_equipment`, `mart.fact_rentals`, `mart.agg_rentals_daily`

### 4.4 n:n 中間表（純粋な内部関係）
- 形式：`link_<a>_<b>`
- アンダースコアは1個
- 語順はビジネス優先度を優先、同格ならアルファベット昇順
- 例：`core.link_user_role`, `core.link_product_category`
- 外部プロバイダや他システムとの対応は **xref/crosswalk** を使用
  - 例：`xref.product_crosswalk`（JAHID/MEDIE/将来プロバイダ）

### 4.5 ドメイン語彙のルール
- 医療機関は必ず `medical_facility` を用いる（`facility` 単独は不可）
  - 例：`cur.medical_facilities`, `xref.facility_crosswalk`, `core.mst_medical_facility_types`
- 物流単位は `packaging_unit`
- 梱包バリエーション（JAN+PI 等）は `product_pi`
- プロバイダ名は必要箇所のみ使用
  - 例：`mst_jahid_*`, `mst_medie_*`
  - `xref` は列で識別

### 4.6 例（まとめ）
- 台帳：`core.equipment_ledger`
- 貸出履歴：`core.equipment_rental_history`
- 修理履歴：`core.equipment_repair_history`
- 商品（キュレーション）：`cur.products`
- 梱包単位（マスタ）：`core.mst_medie_packaging_units`, `core.mst_jahid_packaging_units`
- JAN+PI：`cur.product_pi`
- 区分共通表：`core.mst_provider_codes`（ビュー：`core.v_mst_jahid_codes`）
- 外部ID対照：`xref.product_crosswalk`, `xref.facility_crosswalk`
- BI：`mart.dim_product`, `mart.fact_rentals`, `mart.agg_rentals_monthly`

---

※ 単一スキーマ運用の場合は `cur_*/raw_*/core_*/xref_*/mart_*` の接頭辞方式に読み替えても同義です。

## 5. カラム命名
- **主キー**：`<table_short>_id`
  - `table_short` はプレフィックス（`mst_`, `map_`, `log_` 等）を除いた残り。短縮せずに用いる。
  - 例: `mst_medical_facility.medical_facility_id`
- **外部キー**：`<referenced_table_short>_id`
  - 例: `medical_facility_id`, `medical_device_id`
- **日時**：`*_at`（timestamptz）, **日付のみ**：`*_on`（date）
  - 置換の目安：`*_datetime → *_at`, `regdate → created_at`, `lastupdate → updated_at`
- **真偽**：`is_` / `has_` / `can_`
- **コード/名称/説明**：`*_code` / `*_name` / `*_label` / `*_desc`
- **監査**：`created_at`, `created_by`, `updated_at`, `updated_by`（必要に応じ `deleted_*`）
- **禁止/注意**：`*_type` / `*_kind` / `*_class` は原則禁止（`classification` と `risk_class` を使い分け）。

### 「区分」の見直し

1. category（区分）をデフォルト。
2. 公式体系が絡めば classification / 体系名を付ける。
3. 手段・方式なら type。
4. 時間変化・工程は status。
5. 真偽なら is_ / has_。

### 必要な英語の省略

- mhlw : Ministry of Health, Labour and Welfare
  - 厚生労働省
- 地域情報
  - 都道府県 : Prefecture
  - 市町村 : municipality
  - 一次医療圏 : primary_medical_area
  - 二次医療圏 : secondary_medical_area
  - エリアの組み合わせ : combined_area
    - ex: 二次医療圏と市町村の組み合わせなら、secondary_medical_area_municipality とかの方が明確
- 親子・グループ化
  - 親 : parent
    - ex: mst_medical_device_classification_parent_id
  - 共通 : common
    - ex : mst_medical_device_classification_common_id


^(\s*new:\s*[^#\n]*?)gov    $1_mhlw_
^(\s*new:\s*[^#\n]*?)hospital    $1_medical_facility_
new: pref   new: prefecture_
^(\s*new:\s*[^#\n]*?)pref    $1
^(\s*new:\s*[^#\n]*?)medarea    $1_secondary_medical_area_
^(\s*new:\s*[^#\n]*?)jahid    $1_jahid_
^(\s*new:\s*[^#\n]*?)towncode    $1municipality_code
^(\s*new:\s*[^#\n]*?)hpname    $1_medical_facility_name
^(\s*new:\s*[^#\n]*?)recvdate    $1
^(\s*new:\s*[^#\n]*?)    $1
^(\s*new:\s*[^#\n]*?)    $1
^(\s*new:\s*[^#\n]*?)    $1

## 6. 制約・インデックス命名
- PK：`pk_<table>`
- FK：`fk_<table>__<column>`（表名と列名の間にダブルアンダースコアを用いて可読性を確保）
- UQ：`uq_<table>__<column(s)>`
- CHECK：`ck_<table>__<name>`
- INDEX：`idx_<table>__<column(s)>`

## 7. コントロールド・ボキャブラリ（抜粋）
| 正規語 (識別子) | 日本語 | 説明/注記 | 禁止・注意 |
|---|---|---|---|
| `medical_device` | 医療機器 | 規制用語に整合した主語。 | `medical_equipment` は識別子で不可（ドキュメントのみ許容）。`ME` 禁止。 |
| `medical_facility` | 医療機関 | 病院・クリニック等を含む。 | `facility` 単独は禁止。 |
| `classification` | 分類（階層） | 例：`classification_level1..N` | `type`/`kind`/`class` を避ける。 |
| `risk_class` | リスククラス | 値：`I`/`II`/`III`/`IV` | `class` 単独は不可。 |
| `jmdn_code` | JMDNコード | 一般的名称コード | — |

## 8. YAML テンプレート（最小例）
```yaml
table: mst_medical_facility
title: {{ ja: 医療機関, en: Medical Facility }}
description: {{ ja: 医療機関のマスタ, en: Master of healthcare provider sites. }}
columns:
  - {{ name: medical_facility_id, type: bigint, identity: true, nullable: false }}
  - {{ name: facility_code, type: text, unique: true, nullable: false }}
  - {{ name: facility_name, type: text, nullable: false }}
  - {{ name: risk_class, type: text, nullable: true }}               # I/II/III/IV
  - {{ name: jmdn_code, type: text, nullable: true }}
  - {{ name: is_active, type: boolean, default: true }}
  - {{ name: created_at, type: timestamptz, nullable: false }}
  - {{ name: created_by, type: bigint, nullable: false }}
  - {{ name: updated_at, type: timestamptz, nullable: false }}
  - {{ name: updated_by, type: bigint, nullable: false }}
constraints:
  - {{ name: pk_mst_medical_facility, type: primary_key, columns: [medical_facility_id] }}
indexes:
  - {{ name: idx_mst_medical_facility__facility_code, columns: [facility_code] }}
```

### n:n 例（汎用）
```yaml
table: map_medical_facility_medical_device
title: {{ ja: 医療機関と医療機器の関連, en: Facility–Device Mapping }}
columns:
  - {{ name: medical_facility_id, type: bigint, nullable: false }}
  - {{ name: medical_device_id, type: bigint, nullable: false }}
  - {{ name: created_at, type: timestamptz, nullable: false }}
constraints:
  - {{ name: pk_map_medical_facility_medical_device, type: primary_key, columns: [medical_facility_id, medical_device_id] }}
```

### n:n 例（特例：ユーザー多態関連）
```yaml
table: map_user_entity
title: {{ ja: ユーザーとエンティティの関連（多態）, en: User–Entity (polymorphic) Mapping }}
columns:
  - {{ name: user_id, type: bigint, nullable: false }}
  - {{ name: entity_id, type: bigint, nullable: false }}  # 特例として名称を維持
  - {{ name: entity_kind, type: text, nullable: false }}  # facility/dealer/manufacturer 等の区別（実装に応じて）
  - {{ name: created_at, type: timestamptz, nullable: false }}
constraints:
  - {{ name: pk_map_user_entity, type: primary_key, columns: [user_id, entity_id] }}
```

## 9. 決定性ルール（要約）
- `table_short` = テーブル名 − プレフィックス（`mst_`, `map_`, `log_`, `stg_`, `vw_`, `mv_`）。
- PK：`<table_short>_id`、FK：`<referenced_table_short>_id`
- n:n：`map_<a>_<b>`（特例 `map_user_entity`）
- 日時接尾辞：`*_at` / `*_on`、真偽接頭辞：`is_` / `has_` / `can_`
- 禁止語：`facility`（医療機関の意味では禁止）、`type`/`kind`/`class`（classification/risk_class で置換）、`ME`（曖昧）

## 10. 運用・ガバナンス
- **Source of Truth**：`dictionary/naming_dictionary.yaml`（schema-naming リポ）
- **Versioning**：SemVer（MAJOR 破壊的／MINOR 語彙追加／PATCH 誤字訂正等）
- **レビュー**：辞書・規約の変更は必須レビュー（CODEOWNERS 推奨）
- **CI/Lint**：禁止語・命名パターン・接尾辞・FK語幹統一などを自動検証

---

## 付録：変換の目安（参考）
- `medical_equipment` / `medical_entity` → `medical_device`
- `*_datetime` → `*_at`
- `regdate` → `created_at` / `lastupdate` → `updated_at`
- `update_date` (情報公開日) → `published_at`
- `*_link`（中間表）→ `map_<a>_<b>`（`user_entity` は特例として名称固定）
