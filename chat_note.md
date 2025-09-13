# タチコマチャットノート

命名ルールの検討中に、ProductのDB設計に有効なやりとりがあった場合、そのやりとりをコピペしておきます。
タイトル＋コピペなので、markdownに矛盾が生じるかもしれないけど無視。特別編集もしない。
あとで、読み返せればOK。
コピーの順番が時系列出なくてもOK。とにかく必要な物はのこす。

## jahid の区分マスタの管理

> 区分マスタの部分だけど、ファイルを添付するけど、DB内でいろんな場所で利用する共通区分で、１区分の種類（レコード数）は多くても数十件。で、「区分マスタ」として、何の区分か、値、意味というようにすれば一つのマスタでも管理できると思うけど、joinが長くなることを考えると、やっぱり別が良いかな〜ってのも考えちゃう。タチコマの意見を聞かせて。

**①案が現行の考えに近いので、その方針で進める**

いい流れ！mst_jahid_products / mst_medie_products を軸に、区分マスタも同じ思想でいきましょう。PDFにある区分（滅菌/保管/画像有無/クラス分類/バーコード表示…など）が該当ですね。 ￼

ここでの論点は「①共通1表で運用」か「②区分ごとに表を分ける」か。結論から言うと——

タチコマの結論（実運用向け）

ハイブリッドが最適です。
まずは共通1表で “早く/安全に” 回す → 参照頻度が高い（JOINが増えがち）な区分だけ**個別表（またはVIEW）**を切る。

⸻

① 共通1表（おすすめの土台）

テーブル名：mst_jahid_codes
主キー：(code_set, code)（どの区分か＋区分コード）

```sql
CREATE TABLE mst_jahid_codes (
  code_set text NOT NULL,           -- 'storage','sterilization','barcode_flag',...
  code     text NOT NULL,
  name_jp  text NOT NULL,
  name_en  text,                    -- 任意。海外連携や画面多言語の余地
  sort_order int NOT NULL DEFAULT 0,
  is_active boolean NOT NULL DEFAULT true,
  valid_from date,                  -- 任意。将来の改定に耐えるための枠
  valid_to   date,
  provider   text NOT NULL DEFAULT 'jahid', -- 'jahid','medie',...
  remarks    text,
  PRIMARY KEY (code_set, code)
);
CREATE INDEX ON mst_jahid_codes (code_set, is_active, sort_order);
```

使い方（FKをちゃんと効かせる）

PostgreSQLなら複合FKで厳格に守れます。参照側は「コード列＋固定のセット名」を持つのがコツ。

```sql
-- 例：商品テーブルに「保管区分」をぶら下げる
ALTER TABLE prd_products
ADD COLUMN storage_type_code text NOT NULL,
ADD COLUMN storage_type_set  text GENERATED ALWAYS AS ('storage') STORED,
ADD CONSTRAINT fk_storage_type
  FOREIGN KEY (storage_type_set, storage_type_code)
  REFERENCES mst_jahid_codes (code_set, code);
```

	•	storage_type_set は生成列で常に 'storage'。アプリ側が毎回セット名を書く必要なし。
	•	JOINは ... JOIN mst_jahid_codes c ON (c.code_set='storage' AND c.code=p.storage_type_code) で統一。

メリット
	•	区分の追加・修正が一箇所で完結（運用ラク）。
	•	JAHID/Medie/将来の社内マスタも provider で同居可能（横展開しやすい）。
	•	1表なのでETLや投入スクリプトもシンプル。

デメリット
	•	参照時に (code_set, code) の複合条件が必要になり、SQLがやや冗長。
	•	区分名に対して強い型（ENUM等）は持たない（ただし柔軟性は増す）。

⸻

② 区分ごとに表を分ける（JOIN短縮＆厳格運用）

テーブル名（例）：
	•	mst_jahid_storage_types
	•	mst_jahid_sterilization_types
	•	mst_jahid_barcode_display_flags
	•	mst_jahid_class_categories …など（PDFの区分名に対応） ￼

共通スキーマを揃えれば移行も容易：

CREATE TABLE mst_jahid_storage_types (
  code text PRIMARY KEY,
  name_jp text NOT NULL,
  name_en text,
  sort_order int NOT NULL DEFAULT 0,
  is_active boolean NOT NULL DEFAULT true,
  provider text NOT NULL DEFAULT 'jahid'
);

メリット
	•	参照側のFKは単一列で済む → SQLが短く読みやすい。
	•	区分ごとに個別制約やユニーク条件を作れる。

デメリット
	•	テーブルが増殖（運用と権限管理が煩雑に）。
	•	区分追加のたびにDDL作業が必要。

⸻

ハイブリッド運用プラン（おすすめ）
	1.	まずは共通1表 mst_jahid_codes を導入して、全区分をここで一元管理。
	2.	参照頻度が高く、JOINがボトルネックになりやすい区分だけ
	•	① VIEW（読みやすいエイリアス）を用意

```sql
CREATE VIEW v_jahid_storage_types AS
  SELECT code, name_jp, name_en, sort_order, is_active, provider
  FROM mst_jahid_codes
  WHERE code_set='storage';
```

→ アプリ側は v_jahid_storage_types を読むだけでOK（SQLが短くなる）

	•	② どうしてもFKを単一列にしたい箇所は個別表に昇格
	•	ETLで mst_jahid_codes → 個別表へ同期
	•	参照は個別表、マスタの一次ソースは共通1表（ガバナンスを1か所に）

VIEWはFKの参照先になれないため、FKが必要なら個別表か「複合FK＋生成列」を選びます。

⸻

命名のガイド（あなたの方針に合わせて）
	•	共通1表：mst_jahid_codes（Medieなら mst_medie_codes も同型でOK）
	•	個別表：mst_jahid_<domain>_<types|classes|flags>
例：
	•	滅菌区分 → mst_jahid_sterilization_types
	•	保管区分 → mst_jahid_storage_types
	•	画像有無区分 → mst_jahid_image_presence_flags
	•	クラス分類区分 → mst_jahid_class_categories
	•	バーコード表示有無区分 → mst_jahid_barcode_display_flags（PDF参照）。 ￼

⸻

運用Tips
	•	表示名のキャッシュ：高頻度画面は、表示用ラベルを商品テーブル等に冗長保持（更新時にトリガ/アプリで整合）。画面描画のJOINを減らせる。
	•	改定余地：将来のコード改廃に備え、is_active と valid_from/to を持たせてソフトデリート/将来予約に対応。
	•	データプロバイダ混在：provider カラムで jahid/medie/internal を持たせ、同名コードの衝突は (code_set, provider, code) のユニークで防止可能。

⸻

最後に
	•	まずは 共通1表＋VIEW で始めて、本当に重い/読みにくい箇所だけ個別表に切り出すのが、スピードと保守性のバランスが良いです。
	•	命名はこれまで通り mst_jahid_* / mst_medie_* を踏襲して統一。

必要なら、あなたが添付したCSV（例：クラス分類区分・保管区分・バーコード有無・画像有無）をこのスキーマにすぐ流し込める投入SQLもこちらで作ります。どう入れたい（共通1表/個別表）かだけ教えてくれれば、DDL＋COPY/INSERTスクリプトを一式出します！

> mst_jahid_code で中にproviderが入るとなんだか気持ち悪いね。そうすると、mst_provider_codes とかの方が良いのかな？
> medieは最初から利用想定。で、medieは区分マスタが無いけど、仕様書の説明部分に区分の情報が羅列されているので、それを登録する場所があるのは良いと思う。それ以外は時期未定。


いいね、その事情なら**③ハイブリッド（実体は共通1表＋プロバイダ別VIEW）**がドンピシャです。
	•	Medieは最初から使う → 横断も個別もどっちも必要
	•	Medieは仕様書に“羅列情報”があるだけ → 共通1表に吸い上げて正規化
	•	将来の社内マスタは時期未定 → VIEWを増やすだけで拡張OK

以下、そのままコピペできる最小構成を置きます（PostgreSQL想定）。

⸻

1) 実体テーブル（共通1表）

```sql
CREATE TABLE mst_provider_codes (
  provider     text    NOT NULL,          -- 'jahid','medie','group'...
  code_set     text    NOT NULL,          -- 'storage','sterilization','barcode_flag',...
  code         text    NOT NULL,          -- '01','A','Y' など
  name_jp      text    NOT NULL,
  name_en      text,
  sort_order   int     NOT NULL DEFAULT 0,
  is_active    boolean NOT NULL DEFAULT true,
  valid_from   date,
  valid_to     date,
  remarks      text,
  PRIMARY KEY (provider, code_set, code)
);

-- よく使う参照パターン用
CREATE INDEX ON mst_provider_codes (provider, code_set, is_active, sort_order);
```

これで JAHID / MEDIE / 将来マスタ を一箇所に集約。
Medieの“仕様書羅列”も、provider='medie' として同じ枠に投入できます。

⸻

2) プロバイダ別VIEW（名前の気持ち悪さを解消）

```sql
CREATE VIEW mst_jahid_codes AS
  SELECT * FROM mst_provider_codes WHERE provider='jahid';

CREATE VIEW mst_medie_codes AS
  SELECT * FROM mst_provider_codes WHERE provider='medie';
```

ふだんは mst_jahid_codes / mst_medie_codes だけ見ればOK。
横断集計したいときだけ mst_provider_codes を使う運用が自然。

⸻

3) 参照側テーブルのFK（冗長書き回避の定石）

生成列で provider と code_set を固定化し、FKは複合で厳格に。

```sql
-- 商品テーブル例（JAHIDの保管区分を参照）
ALTER TABLE mst_jahid_products
ADD COLUMN storage_code text NOT NULL,
ADD COLUMN storage_set  text GENERATED ALWAYS AS ('storage') STORED,
ADD COLUMN storage_provider text GENERATED ALWAYS AS ('jahid') STORED,
ADD CONSTRAINT fk_jahid_storage
  FOREIGN KEY (storage_provider, storage_set, storage_code)
  REFERENCES mst_provider_codes (provider, code_set, code);
```

アプリ側はコードだけ入れれば良い（provider/setは自動）。
SQLも短く、型安全かつ命名も崩れない。

⸻

4) 利便VIEW（任意）

JOINを短くしたい区分は“見出し用VIEW”を用意。

```sql
CREATE VIEW v_jahid_storage_types AS
  SELECT code, name_jp, name_en, sort_order
  FROM mst_jahid_codes WHERE code_set='storage' AND is_active;
```

⸻

5) 命名ガイド（このルールで統一）
	•	共通1表：mst_provider_codes
	•	プロバイダ別VIEW：mst_jahid_codes, mst_medie_codes
	•	コードセット名（code_set）：英小文字スネーク（例）
	•	storage, sterilization, barcode_flag, image_presence, class_category, data_origin, …
	•	個別の参照型VIEW（任意）：v_<provider>_<code_set>_types|flags|categories

⸻

6) 初期投入の型（CSV取り込みの雛形）

```sql
-- JAHID: 保管区分の例
INSERT INTO mst_provider_codes (provider, code_set, code, name_jp, sort_order)
VALUES
('jahid','storage','01','常温',1),
('jahid','storage','02','冷蔵',2),
('jahid','storage','03','冷凍',3);

-- MEDIE: 仕様書羅列から同様に整形
INSERT INTO mst_provider_codes (provider, code_set, code, name_jp, sort_order)
VALUES
('medie','storage','A','常温',1),
('medie','storage','B','冷蔵',2);
```

⸻

まとめ
	•	テーブル名と中身のねじれをVIEWで解消
	•	横断性・拡張性は実体1表で確保
	•	参照側の書き味は生成列＋複合FKで快適に

このまま命名ドキュメント化（Markdown）もいけます。必要なら、あなたが持っているCSVの列見出しに合わせたCOPY/INSERTスクリプトの雛形も作るよ。

## 商品マスタ間の対比表（jahid, medieの関連付け）

> キュレーションしたときに、台帳の商品情報にJAHIDならこのコード、MEDIEならこのコード・・というように情報を載せておきたい。実際両方の情報は共通部分も多いけど、各々にしか無い情報もあるからね。その時に、各々でマッチするのを探すよりは、jahideで検索、マッチしたら、まずこのテーブルからmedieがヒットするかを検索することで、時間短縮になると思う。

その使い方、まさに crosswalk 対照表が効きます。台帳 products を“正”にして、JAHID/MEDIE 等の外部IDを横持ちで引けるようにしておくと、検索→即座に相互参照ができます。

推し構成
	•	台帳（正規）：products（社内の正規 product_id を採番）
	•	対照表：product_crosswalk（provider 別の外部IDをぶら下げる）
	•	便利ビュー：v_products_with_provider_ids（台帳に JAHID/MEDIE のIDを横持ちで付けたビュー）
	•	高速化：product_crosswalk にユニーク／部分インデックス

⸻

DDL（最小で強い形）

```sql
-- 台帳（正規）: カラムは例
CREATE TABLE products (
  product_id uuid PRIMARY KEY,
  name_jp text NOT NULL,
  name_en text,
  jmdn_code text,
  -- ここに台帳として保持したい属性を追加
  created_at timestamptz DEFAULT now()
);

-- 対照表（JAHID/MEDIE等の外部IDを結び付ける）
CREATE TABLE product_crosswalk (
  product_id       uuid    NOT NULL,     -- 台帳の正規ID
  provider         text    NOT NULL,     -- 'jahid','medie', ...（将来追加OK）
  provider_item_id text    NOT NULL,     -- 先方のID（商品ID, GTIN/JAN, 内部キーなど）
  match_method     text    NOT NULL,     -- 'exact_gtin','exact_pi','manual' 等
  confidence_score numeric(4,3),
  is_primary       boolean NOT NULL DEFAULT true, -- 複数候補がある場合の主従
  valid_from       date,
  valid_to         date,
  remarks          text,
  PRIMARY KEY (provider, provider_item_id),
  FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- よく使う参照パターンを想定したインデックス
CREATE INDEX ON product_crosswalk (product_id);
CREATE INDEX ON product_crosswalk (provider, is_primary);

-- “1製品×1providerにつき主リンクは1つ”を保証（任意）
CREATE UNIQUE INDEX ux_crosswalk_primary_one_per_provider
  ON product_crosswalk (product_id, provider)
  WHERE is_primary = true;
```

⸻

よくやる検索パターン（JAHID→MEDIE を即時に）

1) JAHIDのIDから台帳を引き、MEDIEを取る

```sql
-- :jahid_id を先に見つけたケース
WITH base AS (
  SELECT product_id
  FROM product_crosswalk
  WHERE provider='jahid' AND provider_item_id = :jahid_id AND is_primary
)
SELECT cw_medie.provider_item_id AS medie_id
FROM base
JOIN product_crosswalk cw_medie
  ON cw_medie.product_id = base.product_id
 AND cw_medie.provider = 'medie'
 AND cw_medie.is_primary;
```

2) JAHIDのIDだけで横持ち一発取得（ビュー経由が楽）

```sql
SELECT p.product_id, p.name_jp, x.jahid_id, x.medie_id
FROM v_products_with_provider_ids x
JOIN products p ON p.product_id = x.product_id
WHERE x.jahid_id = :jahid_id;
```

⸻

便利ビュー（台帳にプロバイダIDを横持ち）

（将来 provider が増えてもVIEWを足すだけ／変更も容易）

```sql
CREATE VIEW v_products_with_provider_ids AS
SELECT
  p.product_id,
  MAX(CASE WHEN c.provider='jahid' AND c.is_primary THEN c.provider_item_id END) AS jahid_id,
  MAX(CASE WHEN c.provider='medie'  AND c.is_primary THEN c.provider_item_id END) AS medie_id
FROM products p
LEFT JOIN product_crosswalk c ON c.product_id = p.product_id
GROUP BY p.product_id;
```

画面やAPIはこのビューを使えば、「台帳を1回見るだけで JAHID/MEDIE のキーを同時に取得」できます。

⸻

命名について
	•	対照表：product_crosswalk（または product_provider_xref）
“map_”は不要。台帳と外部IDの正式な対照台帳であることが伝わります。
	•	台帳と結合した横持ちビュー：v_products_with_provider_ids
（用途がひと目で分かる・将来 provider が増えても命名の一貫性が保てる）

⸻

実運用の小ワザ
	•	冪等アップサート：外部供給の再取込でも PRIMARY KEY(provider, provider_item_id) に対して UPSERT すれば安全。
	•	監査性：match_method / confidence_score / remarks に根拠を残す（後からの差分検証が楽）。
	•	片方向開始：まず JAHID→MEDIE の探索を既定にし、見つかればビューで横持ち返却（あなたのフローに合致）。

この形にしておけば、**「JAHIDで当ててからMEDIEを即参照」**が最短手数で回りますし、将来プロバイダが増えても既存スキーマはそのまま、VIEWだけ足していけばOKです。

> そうなると、医療機関のテーブルもpocだとmedie列とjahid列があるけど、プロバイダー増えることを考えるとjson型とかにしておく方が良いね。

いい発想！PoCのうちは medie 列・jahid 列みたいな横持ちで済みますが、将来プロバイダ追加を考えると可変長で持てる形が便利です。
結論だけ先に言うと——
	•	本命（推奨）：台帳は正規化、**対照表（crosswalk）**でプロバイダ別IDをぶら下げる
	•	PoCで素早く：台帳に jsonb の provider_ids を持たせる（＋最小限の制約）

両方の設計を置きます。お好みと段階で選べます。

⸻

A. 正規化（推奨）— facility_crosswalk 方式

将来の拡張性と一意性保証が最強。product_crosswalk と同じ思想です。

-- 正規の医療機関台帳
CREATE TABLE facilities (
  facility_id uuid PRIMARY KEY,
  name_jp text NOT NULL,
  addr1 text, addr2 text, ...
  created_at timestamptz DEFAULT now()
);

-- プロバイダ別の外部ID対照
CREATE TABLE facility_crosswalk (
  facility_id uuid NOT NULL,
  provider text NOT NULL,               -- 'jahid','medie', ...
  provider_facility_id text NOT NULL,   -- 先方の医療機関ID
  match_method text NOT NULL,           -- 'exact','manual' など
  is_primary boolean NOT NULL DEFAULT true,
  valid_from date, valid_to date,
  remarks text,
  PRIMARY KEY (provider, provider_facility_id),
  FOREIGN KEY (facility_id) REFERENCES facilities(facility_id)
);

CREATE UNIQUE INDEX ux_facility_primary_one
  ON facility_crosswalk (facility_id, provider)
  WHERE is_primary = true;

-- 横持ちビュー（便利）
CREATE VIEW v_facilities_with_provider_ids AS
SELECT
  f.*,
  MAX(CASE WHEN c.provider='jahid' AND c.is_primary THEN c.provider_facility_id END) AS jahid_id,
  MAX(CASE WHEN c.provider='medie' AND c.is_primary THEN c.provider_facility_id END) AS medie_id
FROM facilities f
LEFT JOIN facility_crosswalk c ON c.facility_id = f.facility_id
GROUP BY f.facility_id;

ポイント
	•	外部IDの一意割当を (provider, provider_facility_id) 主キーで保証。
	•	検索フローは、JAHID→台帳→MEDIE を JOIN 1回で辿れます。
	•	プロバイダ追加は 行が増えるだけ（スキーマ変更不要）。

⸻

B. PoC最速— jsonb で横持ち可変

当面はテーブル1枚で運びたいならこれ。最低限の健全性も仕込めます。

-- PoC: 施設台帳に可変のプロバイダIDをjsonbで
CREATE TABLE facilities (
  facility_id uuid PRIMARY KEY,
  name_jp text NOT NULL,
  provider_ids jsonb NOT NULL DEFAULT '{}'::jsonb,  -- {"jahid":"...", "medie":"..."}
  created_at timestamptz DEFAULT now(),
  CHECK (jsonb_typeof(provider_ids) = 'object')
);

-- よく使うキー取り出し用の生成列（任意）
ALTER TABLE facilities
  ADD COLUMN jahid_id text GENERATED ALWAYS AS (provider_ids->>'jahid') STORED,
  ADD COLUMN medie_id text GENERATED ALWAYS AS (provider_ids->>'medie') STORED;

-- GINインデックスでキー検索を高速化
CREATE INDEX idx_facilities_provider_ids_gin ON facilities USING GIN (provider_ids jsonb_path_ops);

-- “特定プロバイダのIDはユニーク”を部分ユニークで保証（任意）
CREATE UNIQUE INDEX ux_facilities_jahid_unique
  ON facilities ((provider_ids->>'jahid'))
  WHERE provider_ids ? 'jahid';

CREATE UNIQUE INDEX ux_facilities_medie_unique
  ON facilities ((provider_ids->>'medie'))
  WHERE provider_ids ? 'medie';

長所
	•	スキーマ変更不要でプロバイダを増やせる（キーを足すだけ）。
	•	生成列で従来の jahid_id / medie_id と同じ使い勝手に。
	•	部分ユニークで疑似一意性も確保できる。

短所
	•	外部キー制約が張れない（jsonbはFKの対象外）。
	•	必要ならトリガで擬似FK検査、または将来A方式へ移行。
	•	JSONバリデーションはCHECKの自作が必要（キー制限など）。

⸻

どっちを採る？
	•	長期運用／監査・整合性が大事 → A. 正規化（crosswalk）
	•	PoCの実装速度優先 → B. jsonb（＋生成列＆部分ユニークで最低限守る）
	•	将来は B → A へ移行してもOK（jsonbを展開して crosswalk へUPSERT）。

⸻

命名の一貫性
	•	対照表：facility_crosswalk（または facility_provider_xref）
	•	ビュー：v_facilities_with_provider_ids
	•	JSONキー：'jahid', 'medie', …（英小文字スネーク固定）

この方針でいけば、商品も医療機関も同じ発想（台帳＋対照）で揃えられて、実装も保守も迷いません。
必要なら、既存のPoCデータから jsonb → crosswalk へ移行するSQL も用意します！
