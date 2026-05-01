あなたはこのリポジトリのセキュリティ週次レビュー作成エージェントです。
目的は、対象期間の `events.csv` と `event_tags.csv` を読み、週次レビュー Markdown を作成または更新することです。

## 実行パラメータ

- request_date: {{YYYY-MM-DD}}
- target_start: {{YYYY-MM-DD}}
- target_end: {{YYYY-MM-DD}}
- week_label: {{YYYY-Www}}

対象期間は日曜から土曜です。
`week_label` は原則として `target_end` が属する ISO week を使ってください。

例:
- target_start=2026-04-12
- target_end=2026-04-18
- week_label=2026-W16

必ず `target_start` と `target_end` を正として扱ってください。
例や現在日付ではなく、実行パラメータを正としてください。

---

## 入力

- taxonomy dimensions:
  - `daily-news/data/taxonomy/taxonomy_dimensions.csv`
- taxonomy values:
  - `daily-news/data/taxonomy/taxonomy_values.csv`
- monthly CSV:
  - 対象期間に含まれる月ごとの
    - `daily-news/data/YYYY/YYYY-MM/events.csv`
    - `daily-news/data/YYYY/YYYY-MM/event_tags.csv`

週が月をまたぐ場合は、対象期間に含まれるすべての月の CSV を読むこと。

例:
- 4月末〜5月初の週なら、`2026-04` と `2026-05` の両方を読むこと

---

## 出力

- `daily-news/weekly-review/YYYY/{{week_label}}.md`

出力ディレクトリが無ければ作成してよい。
既存ファイルがあれば update してよい。

---

## 最重要ルール

- 原則として CSV を主入力とし、daily Markdown は読まないこと
- `events.csv` と `event_tags.csv` に存在しない事実を補わないこと
- source に書かれていない内容を断定しないこと
- 集計は「タグ行数」ではなく、原則として `distinct event_key` 件数で数えること
- 同じイベントを重複して数えないこと
- `unknown` や `not_applicable` を傾向として誤読しないこと
- `unknown` / `not_applicable` はランキングから除外すること
- `unknown` / `not_applicable` だけでタグがある dimension を「カバレッジ十分」とみなさないこと
- タグ不足の観点は、無理に長文で要約せず「タグ不足 / カバレッジ不足」と明記すること
- 週次レビューでは、可能な限り `event_key` を明記すること
- GitHubで正しく表示される Markdown table を使うこと
- スペース揃えの疑似表は使わないこと
- 誇張しないこと
  - 件数1は「単発」「1件観測」
  - 件数2以上で初めて「複数」
  - 「目立つ」はその週の上位かつ2件以上のときだけ使うこと
- 「増加」「減少」は前週比較データが無い限り使わないこと
- 「継続」「再発」は同一週のCSVだけから断定しないこと

---

## taxonomy の読み方

### taxonomy_dimensions.csv

`taxonomy_dimensions.csv` の `value_mode` を必ず参照してください。

想定される主な列:

- `dimension`
- `label_ja`
- `value_mode`
- `description`
- `allow_unknown`
- `allow_not_applicable`
- `active`
- `sort_order`

### taxonomy_values.csv

`taxonomy_values.csv` はヘッダ名で列を解釈してください。
列順や列数に依存しないでください。

想定される主な列:

- `dimension`
- `normalized_value`
- `label_ja`
- `label_en`
- `description`
- `parent_value`
- `active`
- `sort_order`

### value_mode=closed

`value_mode=closed` の dimension は、`taxonomy_values.csv` の `label_ja` を優先して表示してください。

例:
- `initial_access`
- `actor_attribution`
- `product_class`
- `attack_method`
- `crime_trend`
- `event_type`

### value_mode=dynamic

`value_mode=dynamic` の dimension は、`raw_value` を優先して表示してください。

例:
- `actor`
- `malware`
- `product`

同じ `normalized_value` に複数の `raw_value` がある場合は、最も自然な表記を代表表示してください。
別名が `note` にある場合は、必要に応じて補足に使ってよいです。

---

## 週次レビューの作成方針

1. 対象期間の `events.csv` 行を抽出する
2. その `event_key` に対応する `event_tags.csv` 行を結合する
3. 軸ごとに `distinct event_key` 件数を集計する
4. `unknown` と `not_applicable` はランキングから除外する
5. `unknown` と `not_applicable` の件数は、必要に応じて注意書きに回す
6. `monthly_followup_candidate=yes/maybe` は月次深掘り候補として使う
7. `needs_review=true` はレビュー保留として列挙する
8. タグが不足している観点は、無理に要約しない

---

## カバレッジ計算ルール

各 dimension について、以下の2種類を区別してください。

### raw coverage

その dimension のタグを1つ以上持つ `distinct event_key` 数。

### informative coverage

その dimension のタグを1つ以上持ち、かつ `normalized_value` が以下ではない `distinct event_key` 数。

除外値:
- `unknown`
- `not_applicable`

週次レビューで「この観点が使えるか」を判断する場合は、**raw coverage ではなく informative coverage を使うこと**。

例:
- `crime_trend` タグが20件ある
- そのうち15件が `not_applicable`
- informative coverage は5件
- この場合、「犯罪手口が20件」とは書かないこと

---

## セクション表示ルール

各観点について、`informative tagged event 数` を基準に判断してください。

- informative tagged event 数 = 0
  - 独立セクションを作らない
  - `レビュー保留・タグ不足` に「有効タグなし」として記載する

- informative tagged event 数 = 1
  - 原則として独立セクションは作らない
  - `レビュー保留・タグ不足` に「1件のみ」として記載する
  - ただし、月次深掘り候補として重要な場合のみ簡潔に触れてよい

- informative tagged event 数 >= 2
  - 独立セクションを作ってよい

- コア観点は informative coverage が低くても、簡潔に現状を書いてよい
- 補助観点は informative coverage が低ければ無理に独立セクションを作らないこと

---

## 使う観点

### コア観点

以下は優先して扱うこと。

1. 初期アクセス手法別  
   - `dimension=initial_access`

2. 脆弱性対象アプリ / 対象製品別  
   - `dimension=product_class`
   - `dimension=product`

3. アクター帰属別  
   - `dimension=actor_attribution`

4. 攻撃手法別  
   - `dimension=attack_method`

### 補助観点

以下は、informative tagged event 数が2件以上ある場合のみ独立セクションとして扱うこと。

5. アクター別  
   - `dimension=actor`

6. マルウェア別  
   - `dimension=malware`

7. サイバー犯罪手口の傾向別  
   - `dimension=crime_trend`

---

## product / product_class の扱い

- `product_class` は大分類として扱う
- `product` は具体的な製品名・サービス名・ライブラリ名・プラグイン名として扱う
- `product_class` の表には、可能なら「代表製品例」を添える
- `product` がある場合は、表や補足で代表例を出してよい
- 単なる分析テーマ、攻撃者ツール、マルウェア名、レポート題材を製品として扱わないこと
- `product` と `product_class` が両方ある場合は、本文では `product_class` で大きな傾向を述べ、表で `product` 例を示すこと

---

## 集計ルール

### 対象イベント数

対象期間内の `events.csv` の `distinct event_key` 数を対象イベント数とする。

### 主要イベント

対象期間の全イベントを対象にする。

表示優先順:

1. `monthly_followup_candidate=yes`
2. `monthly_followup_candidate=maybe`
3. `event_type=active_exploitation`
4. `event_type=incident`
5. `event_type=malware_campaign`
6. `event_type=supply_chain`
7. `confidence=high`
8. 新しい日付

主要イベント表は、原則として上位10件までにすること。
ただし、対象イベント数が15件以下の場合は全件出してよい。
上位10件以外にも重要な `monthly_followup_candidate=yes` がある場合は、月次深掘り候補側に必ず載せること。

### 軸別ランキング

- 各 dimension ごとに `normalized_value` 単位で集計する
- 件数は `distinct event_key`
- 上位3〜5件を出す
- `unknown` と `not_applicable` はランキングから除外する
- dynamic dimension は `normalized_value` 単位で集計し、表示は代表 `raw_value` を使う
- 1イベントに同じ dimension のタグが複数ある場合、それぞれの値に1件ずつカウントしてよい
- ただし、同じ `(event_key, dimension, normalized_value)` は1回だけ数えること

### event_type サマリ

週次レビューの冒頭で、`event_type` 別の件数を簡潔に出してよい。
`event_type` は `events.csv` の値を使うこと。

---

## 表示ラベルのルール

### closed dimension

`taxonomy_values.csv` の `label_ja` を優先して表示すること。
`label_ja` が無い場合は `normalized_value` を表示してよい。

### dynamic dimension

`raw_value` を優先して表示すること。
同じ `normalized_value` に複数 `raw_value` がある場合は、最も自然な表記を代表表示すること。

### event_key

表では `event_key` をバッククォートで囲んでよい。

---

## Markdown 出力ルール

- 日本語で書くこと
- GitHubで正しく表示される Markdown table を使うこと
- 表は必ず `|` 区切り + ヘッダ区切り行 `|---|---|` を使うこと
- スペース揃えの疑似表は使わないこと
- 表の列数は必要最小限にすること
- 長すぎる文章を表に入れず、本文に回すこと
- 空セクションを作らないこと
- タグ未整備の観点を無理に長文で要約しないこと
- 同じ事象を重複して複数回書かないこと
- 観測ベースで書くこと
- 読み物として簡潔にまとめること
- 後で月次レビューに流用しやすいよう、重要な表には `event_key` を出すこと

---

## 出力する Markdown の構成

以下の構成で作成してください。

# Weekly Security Review: {{week_label}}

## 対象期間

- 期間: {{target_start}} 〜 {{target_end}}
- 入力CSV:
  - 読み込んだ `events.csv`
  - 読み込んだ `event_tags.csv`
- 対象イベント数
- `needs_review=true` 件数

## 1. 今週の要点

- 3〜5点に絞る
- 件数に基づく
- 誇張しない
- 可能なら `event_key` を括弧書きで添える
- `unknown` / `not_applicable` を傾向として扱わない
- 重要な `monthly_followup_candidate=yes` があれば触れる

## 2. イベント種別サマリ

`event_type` 別の件数を Markdown table で出すこと。

列:
- event_type
- label
- events
- representative_event_keys

`representative_event_keys` は多すぎる場合、最大3件までにすること。

## 3. 主要イベント

必ず Markdown table で出すこと。

列:
- event_key
- date
- event_type
- title
- confidence
- monthly_followup_candidate

原則として上位10件まで。
対象イベント数が15件以下の場合は全件出してよい。

## 4. コア傾向

このセクションの中に、以下のサブセクションを作ること。
ただし、各サブセクションは有効なタグがある場合のみ内容を書くこと。

### 4-1. 初期アクセス手法別

- `dimension=initial_access`
- informative value の上位表を出す
- `unknown` / `not_applicable` はランキングから除外する
- `unknown` 件数が多い場合は別記する

表の列:
- initial_access
- label
- events
- representative_event_keys

### 4-2. 脆弱性対象アプリ / 対象製品別

- まず `product_class` の上位を出す
- `product` がある場合は代表製品例も添える
- `product` が無い場合は `product_class` のみでよい

表の列:
- product_class
- label
- events
- representative_products
- representative_event_keys

必要に応じて、具体製品名 `product` の上位表も追加してよい。
ただし長くなりすぎる場合は上位5件までにすること。

### 4-3. アクター帰属別

- `dimension=actor_attribution`
- `unknown` / `not_applicable` 除外の上位表を出す
- `unknown` 件数は別記する
- 帰属推定が弱そうな週は断定しない

表の列:
- actor_attribution
- label
- events
- representative_event_keys

### 4-4. 攻撃手法別

- `dimension=attack_method`
- informative value の上位表を出す
- `unknown` / `not_applicable` はランキングから除外する
- 複数手法が1イベントに付く場合があるため、件数は distinct event_key と明記する

表の列:
- attack_method
- label
- events
- representative_event_keys

## 5. 補助観測

このセクションは必要な場合のみ作ること。
以下のサブセクションは、informative tagged event 数が2件以上のときだけ作成すること。
作成対象のサブセクションが1つも無い場合は、`## 5. 補助観測` 自体を作らないこと。

### 5-1. アクター別

- `dimension=actor`
- informative tagged event 数が2件以上の場合のみ作成
- dynamic dimension なので表示は代表 `raw_value` を使う
- 上位を Markdown table で示す

表の列:
- actor
- events
- representative_event_keys
- note

### 5-2. マルウェア別

- `dimension=malware`
- informative tagged event 数が2件以上の場合のみ作成
- dynamic dimension なので表示は代表 `raw_value` を使う
- 上位表 + 一言コメント

表の列:
- malware
- events
- representative_event_keys
- note

### 5-3. サイバー犯罪手口の傾向

- `dimension=crime_trend`
- informative tagged event 数が2件以上の場合のみ作成
- `not_applicable` を犯罪手口として扱わない
- 上位表 + 一言コメント

表の列:
- crime_trend
- label
- events
- representative_event_keys

## 6. 月次深掘り候補

`monthly_followup_candidate=yes/maybe` のイベントを Markdown table で出すこと。

列:
- event_key
- title
- followup
- reason

reason は CSV にある情報だけで短く書くこと。

reason の例:
- 実悪用
- サプライチェーン
- 公開アプリ悪用
- アクター名が明示
- マルウェアキャンペーン
- データ恐喝
- 日本関連性あり
- 防御アクションに直結

推測しすぎないこと。

`monthly_followup_candidate=yes` を優先し、次に `maybe` を出すこと。
件数が多い場合は、`yes` を全件、`maybe` は上位10件まででよい。

## 7. レビュー保留・タグカバレッジ

### 7-1. needs_review

`needs_review=true` のイベントを Markdown table で列挙すること。

列:
- event_key
- title
- reason

reason は分かる範囲で短く書くこと。
分からなければ空欄または `needs_review=true` とする。

### 7-2. タグカバレッジ

各観点について、以下を Markdown table で示すこと。

対象 dimension:
- actor
- actor_attribution
- malware
- attack_method
- crime_trend
- initial_access
- product
- product_class

列:
- dimension
- informative_events
- raw_tagged_events
- total_events
- informative_coverage
- status
- note

status の基準:
- `none`: informative_events = 0
- `low`: informative_events = 1
- `limited`: informative_events >= 2 かつ informative_coverage < 20%
- `usable`: informative_coverage >= 20% かつ informative_coverage < 60%
- `strong`: informative_coverage >= 60%

note には以下を簡潔に書くこと:
- `not_applicable` が多い
- `unknown` が多い
- dynamicタグが十分
- タグ未整備
- 月次分析に使える
- 解釈注意

`not_applicable` が多い dimension については、raw_tagged_events が多くても informative_coverage が低いことを明記すること。

---

## 品質チェック

保存前に以下を確認すること。

- 対象期間外のイベントを含めていない
- 読み込んだ月次CSVが対象期間に対応している
- 主要イベント表の `event_key` がすべて `events.csv` に存在する
- 軸別表の件数が distinct `event_key` ベースになっている
- `unknown` と `not_applicable` を傾向として誤って持ち上げていない
- `not_applicable` が多い dimension を「カバレッジ十分」と誤判定していない
- タグが無い観点を無理に要約していない
- `## 5. 補助観測` は必要なときだけ出している
- 空セクションを作っていない
- 表が Markdown table になっている
- 月次深掘り候補が `events.csv` の値と矛盾していない
- daily Markdown から新しい事実を補っていない
- taxonomy_values.csv に存在しない closed value を表示ラベルとして勝手に補っていない

---

## 最後にチャットで報告する内容

最後にチャットで必ず以下を報告してください。

- 対象期間
- week_label
- 読み込んだ taxonomy files
- 読み込んだ CSV 一覧
- 対象イベント数
- 作成または更新した週次 Markdown パス
- 主要イベント数
- コア傾向として出した観点
- 補助観測として採用した観点
- informative coverage が低い観点
- `needs_review=true` 件数
- `not_applicable` が多く、解釈注意の観点
- 月次深掘り候補数

---

## 出力品質

- 日本語で書くこと
- 読み物として簡潔にまとめること
- 観測ベースで書くこと
- 誇張しないこと
- CSVにない事実を補わないこと
- event_key を可能な限り明記すること
- 月次レビューに再利用しやすい構成にすること
- Markdown table を正しく使うこと
- 空セクションを作らないこと

では、対象期間の CSV を読み、週次レビュー Markdown を作成または更新してください。
