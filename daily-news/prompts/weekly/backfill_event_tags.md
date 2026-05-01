あなたはこのリポジトリのセキュリティニュースCSV補正エージェントです。
目的は、既存の `events.csv` と `event_tags.csv` を再生成し直すのではなく、拡張taxonomyを前提に、過去生成済みの `event_tags.csv` を必要最小限で補正・追記することです。

## 実行パラメータ
- target_month: {{YYYY-MM}}
- target_year: {{YYYY}}
- target_data_dir: daily-news/data/{{YYYY}}/{{YYYY-MM}}

例:
- target_month: 2026-04
- target_year: 2026
- target_data_dir: daily-news/data/2026/2026-04

## 入力ファイル
- taxonomy dimensions:
  - `daily-news/data/taxonomy/taxonomy_dimensions.csv`
- taxonomy values:
  - `daily-news/data/taxonomy/taxonomy_values.csv`
- existing monthly CSV:
  - `{{target_data_dir}}/events.csv`
  - `{{target_data_dir}}/event_tags.csv`
- source daily markdown:
  - `events.csv` の `source_file` に記載された日次Markdown

## 出力ファイル
- `{{target_data_dir}}/event_tags.csv`
- 必要な場合のみ:
  - `daily-news/data/taxonomy/taxonomy_values.csv`

## 変更してはいけないファイル
- `{{target_data_dir}}/events.csv`

`events.csv` は今回変更しないこと。
新しいイベントも作成しないこと。
既存の `event_key` も変更しないこと。

---

## 作業目的

既存の `event_tags.csv` に対して、以下を行ってください。

1. `actor` タグの不足を補正する
2. `product` タグの不足を補正する
3. `malware` タグの不足を補正する
4. `attack_method` タグの不足を補正する
5. `crime_trend` タグの不足を補正する
6. closed dimension が taxonomy と整合しているか確認する
7. dynamic dimension の slug が安定しているか確認する
8. 重複タグがあれば削除する
9. 完全な空行や空白だけの行があれば削除する
10. 必要に応じて `event_key,dimension,normalized_value` 順に並べ替える

再生成ではなく、既存データへの補正・追記として扱ってください。

---

## 改行・空行の扱い

- CSVとして正しく読める場合、改行コードだけを理由に変更しないこと
- LF / CRLF のどちらでも、CSVとして正しく読めるなら問題なしとすること
- 完全な空行、空白だけの行がある場合のみ削除すること
- 改行コードの統一だけを目的とした不要な全面再整形はしないこと

---

## taxonomy の扱い

### taxonomy_dimensions.csv

`taxonomy_dimensions.csv` の `value_mode` を必ず参照してください。

#### value_mode=closed

- `taxonomy_values.csv` に存在する `normalized_value` のみ使用可能
- taxonomy に存在しない値を `event_tags.csv` で使ってはいけない
- taxonomy に適切な値がない場合は、無理に `unknown` で埋めず `taxonomy_gap` として報告すること

#### value_mode=dynamic

- `taxonomy_values.csv` に値が事前登録されていなくてもよい
- source の `raw_value` から lowercase snake_case の `normalized_value` を作ってよい

### 想定される dynamic dimension

- `actor`
- `malware`
- `product`

### 想定される closed dimension

- `initial_access`
- `actor_attribution`
- `product_class`
- `attack_method`
- `crime_trend`

---

## taxonomy_values.csv の扱い

`taxonomy_values.csv` はヘッダ名で列を解釈してください。
列順に依存しないでください。

期待する主な列:

- `dimension`
- `normalized_value`
- `label_ja`
- `label_en`
- `description`
- `parent_value`
- `active`
- `sort_order`

### taxonomy_values.csv に追加してよいもの

`event_tags.csv` で実際に必要になっている、かつ今後も汎用的に使える closed value だけ追加してよいです。

例:

- 新しい攻撃手法
- 新しい犯罪手口
- 新しい製品分類

ただし、以下は個別名を大量登録しないこと。
これらは dynamic dimension です。

- `actor`
- `malware`
- `product`

`actor / malware / product` は、`unknown` / `not_applicable` 程度が taxonomy にあれば十分です。

### taxonomy値を追加する場合のルール

- 同じ `(dimension, normalized_value)` を重複追加しないこと
- 既存の sort_order と自然につながる値にすること
- label や description は簡潔でよい
- 判断が難しい場合は追加せず、最後に `taxonomy_gap` として報告すること

---

## event_tags.csv の仕様

ヘッダ:

```csv
event_key,dimension,raw_value,normalized_value,confidence,note
````

### 基本ルール

* 既存の正しいタグは維持すること
* 全消し再生成しないこと
* 不要なタグ削除をしないこと
* 新しいイベントを作らないこと
* `event_key` は既存の `events.csv` に存在するものだけ使うこと
* `raw_value` は source に近い自然な表記を維持すること
* `normalized_value` は taxonomy ルールに従うこと
* `confidence` は `high` / `medium` / `low`
* `note` は必要な場合のみ短く書くこと
* 同じ `(event_key, dimension, normalized_value)` を重複追加しないこと

---

## source の読み方

分類修正・タグ追加に迷う場合は、`events.csv` の `source_file` を開いて該当項目を確認してください。

確認手順:

1. `events.csv` で対象 `event_key` の `source_file` と `source_url` を確認する
2. 対応する日次Markdownを開く
3. `source_url` または `title` に対応するニュース項目だけを見る
4. 同じ日次Markdown内の別ニュース項目から情報を流用しない

source に書かれていない内容を推定で補完しないこと。

---

## 補正対象の優先順位

対象月の全イベントについて、以下の順で確認してください。

1. source に actor 名があるが `actor` タグがないイベント
2. source に製品名があるが `product` タグがないイベント
3. source にマルウェア名があるが `malware` タグがないイベント
4. source に攻撃手法があるが `attack_method` タグがないイベント
5. source に犯罪手口があるが `crime_trend` タグがないイベント

---

## actor の補正ルール

* `actor` は固有の攻撃者名、グループ名、クラスター名、キャンペーン名を表す
* source に明示的な actor 名がある場合、`dimension=actor` を追加すること
* `actor_attribution` に固有名を入れないこと
* `actor_attribution` は `nation_state` / `cybercrime` / `insider` / `hacktivist` などの大分類のみ
* source に actor 名はあるが大分類が不明な場合、`actor` は追加し、`actor_attribution` は既存値を維持すること
* `actor_attribution` だけを付けて `actor` を落とさないこと

### actor normalized_value

`raw_value` を lowercase snake_case に正規化してください。

例:

* `ShinyHunters` -> `shinyhunters`
* `APT28` -> `apt28`
* `Fancy Bear` -> `fancy_bear`
* `Forest Blizzard` -> `forest_blizzard`
* `Storm-1175` -> `storm_1175`
* `UNC1069` -> `unc1069`
* `Scattered Spider` -> `scattered_spider`
* `Lazarus Group` -> `lazarus_group`

### actor alias

* source が `aka` / `also known as` / `also tracked as` などで別名を明示している場合、同一actorと判断できるなら1つにまとめてよい
* 代表表記を `raw_value` に採用し、別名は `note` に `Aliases:` として残すこと
* 同一actorか不明な場合は無理に統合しないこと
* source が複数の distinct actor を明示している場合は、複数の `actor` タグを追加してよい

---

## product の補正ルール

* `product` は具体的な製品名、サービス名、ライブラリ名、プラグイン名を表す
* source に明示されている製品名がある場合、`dimension=product` を追加すること
* `normalized_value` は lowercase snake_case にすること

例:

* `Microsoft SharePoint Server` -> `microsoft_sharepoint_server`
* `Nginx UI` -> `nginx_ui`
* `Apache ActiveMQ` -> `apache_activemq`
* `WordPress` -> `wordpress`
* `FortiClient EMS` -> `forticlient_ems`
* `ScreenConnect` -> `screenconnect`
* `Marimo` -> `marimo`

注意:

* `product_class` は大分類として既存値を維持すること
* product が取れる場合でも、product_class を上書きしないこと
* product に攻撃手法名、マルウェア名、研究テーマ名を入れないこと

---

## malware の補正ルール

* `malware` はマルウェアファミリー、RAT、ローダー、ボット、インフォスティーラーなどを表す
* source に明示されている場合のみ追加すること
* 製品名や actor 名と混同しないこと
* `normalized_value` は lowercase snake_case にすること

例:

* `Snake Keylogger` -> `snake_keylogger`
* `Remcos RAT` -> `remcos_rat`
* `Atomic Stealer` -> `atomic_stealer`
* `Mirai` -> `mirai`
* `SystemBC` -> `systembc`

---

## attack_method の補正ルール

`attack_method` は `value_mode=closed` です。
`taxonomy_values.csv` に存在する `normalized_value` だけ使ってください。

source に手法が明示または強く示されている場合のみ追加してください。
マルウェア名、actor名、製品名を attack_method にしないでください。

### よく使う対応例

* RCE / 任意コード実行 -> `remote_code_execution`
* 権限昇格 -> `privilege_escalation`
* 認証回避 -> `authentication_bypass`
* 認証情報窃取 -> `credential_theft`
* トークン窃取 -> `token_theft`
* セッション乗っ取り -> `session_hijacking`
* 悪性文書 -> `malicious_document`
* 悪性パッケージ -> `malicious_package`
* 悪性拡張 -> `malicious_extension`
* コマンドインジェクション -> `command_injection`
* コードインジェクション -> `code_injection`
* プロセスインジェクション -> `process_injection`
* 防御回避 -> `defense_evasion`
* 永続化 -> `persistence`
* データ窃取 / データ持ち出し -> `data_exfiltration`
* ランサムウェア -> `ransomware`
* C2通信 -> `c2_communication`
* バックドア -> `backdoor`
* なりすまし -> `spoofing`
* サプライチェーン侵害 -> `supply_chain_compromise`
* プロンプトインジェクション -> `prompt_injection`
* SEOスパム / リダイレクト -> `seo_spam_redirect`
* DDoS攻撃 -> `ddos`
* SQL Injection -> `sql_injection`

### DDoS 関連の注意

DDoSボットネット、DDoS攻撃、DDoS代行サービスが明示されている場合は、攻撃手法として:

```csv
dimension=attack_method
normalized_value=ddos
```

を使ってください。

`c2_communication` は、source がC2基盤やC2通信を明示している場合のみ補助タグとして残してよいです。
DDoS攻撃そのものを `c2_communication` だけで表現しないこと。

### SQL Injection 関連の注意

SQL Injection が攻撃手法として明示されている場合は:

```csv
dimension=attack_method
normalized_value=sql_injection
```

を使ってください。

「未認証SQLインジェクション」のような表現について、単に未認証であることだけを理由に `authentication_bypass` としないこと。
source が認証回避そのものを明示している場合のみ `authentication_bypass` を残してください。

SQLi によるデータ窃取が source に明示されている場合は、追加で:

```csv
dimension=attack_method
normalized_value=data_exfiltration
```

を残してよいです。

---

## crime_trend の補正ルール

`crime_trend` は `value_mode=closed` です。
`taxonomy_values.csv` に存在する `normalized_value` だけ使ってください。

サイバー犯罪の手口や収益化モデルが明示されている場合のみ追加してください。
単なる incident や event_type の言い換えを crime_trend にしないこと。

### よく使う対応例

* ランサム恐喝 -> `ransomware_extortion`
* データ恐喝 -> `data_extortion`
* フィッシングキット / PhaaS -> `phishing_kit_ecosystem`
* ビッシング -> `vishing`
* スミッシング -> `smishing`
* QRコード詐欺 -> `qr_code_scam`
* 暗号資産窃取 -> `crypto_theft`
* 投資詐欺 -> `investment_scam`
* BEC -> `business_email_compromise`
* クレデンシャルスタッフィング -> `credential_stuffing`
* アカウント乗っ取り -> `account_takeover`
* DDoS代行 -> `ddos_for_hire`
* MaaS -> `malware_as_a_service`
* RaaS -> `ransomware_as_a_service`
* インフォスティーラー市場 -> `infostealer_market`
* 内部者勧誘型恐喝 -> `insider_recruitment_extortion`
* 偽求人・採用詐欺 -> `fake_job_recruitment`
* デバイスコードフィッシング -> `device_code_phishing`
* ClickFix -> `clickfix`

### DDoS犯罪手口の注意

DDoS代行サービス、booter/stresser、DDoS-as-a-service が明示されている場合は:

```csv
dimension=crime_trend
normalized_value=ddos_for_hire
```

を使ってください。

DDoS攻撃そのものは `attack_method=ddos`、DDoS代行や販売モデルは `crime_trend=ddos_for_hire` として分けてください。

---

## 既存タグの扱い

* 既存の正しいタグは維持すること
* 既存の `actor_attribution` に固有actor名が `raw_value` として残っている場合でも、`normalized_value` が大分類として妥当なら原則維持してよい
* ただし、`actor_attribution.normalized_value` が固有名になっている場合は修正すること
* 既存の `initial_access` / `product_class` は明らかな誤りがない限り変更しないこと
* 既存の `unknown` は、source から明確に値が取れる場合のみ置換または補完してよい
* 既存の `not_applicable` は、明らかに不適切な場合のみ修正すること

---

## closed dimension の検証

`value_mode=closed` の dimension について、`event_tags.csv` の `normalized_value` が `taxonomy_values.csv` に存在するか確認してください。

対象:

* `initial_access`
* `actor_attribution`
* `product_class`
* `attack_method`
* `crime_trend`

taxonomyに存在しない値がある場合は、次の順で対応してください。

1. 明らかな typo なら、既存taxonomyの正しい値に修正する
2. 汎用的に必要な値なら、`taxonomy_values.csv` に追加する
3. 判断が難しい場合は、タグは変更せず、最後に `taxonomy_gap` として報告する

---

## dynamic dimension の検証

`value_mode=dynamic` の dimension は、`normalized_value` が taxonomy_values.csv に事前登録されていなくてもよいです。

対象:

* `actor`
* `malware`
* `product`

確認事項:

* `normalized_value` が lowercase snake_case になっているか
* 同じ raw_value が毎回同じ slug になっているか
* actor / malware / product が混同されていないか
* actor 名を `actor_attribution` に入れていないか
* 製品名を `malware` に入れていないか
* マルウェア名を `product` に入れていないか

---

## 並び順・重複の修正

以下を行ってください。

1. 完全な空行があれば削除する
2. 空白だけの行があれば削除する
3. `(event_key, dimension, normalized_value)` が同じ重複行を削除する
4. 同じ event_key のタグがまとまるように、以下の順で並び替える

並び順:

```text
event_key ASC
dimension ASC
normalized_value ASC
```

ただし、改行コードの統一だけを目的とした不要な全面再整形はしないこと。

---

## events.csv の扱い

* `events.csv` は変更しないこと
* `needs_review` も変更しないこと
* 新規イベントを作らないこと
* 既存イベントを削除しないこと

---

## 品質チェック

保存前に以下を確認してください。

* `events.csv` を変更していない
* 新しい event_key を作っていない
* `event_tags.csv` の全 `event_key` が `events.csv` に存在する
* `(event_key, dimension, normalized_value)` の重複がない
* `value_mode=closed` の dimension で taxonomy 外の値を使っていない
* `value_mode=dynamic` の dimension で slug が安定している
* `actor_attribution.normalized_value` に固有アクター名が入っていない
* `product_class.normalized_value` に製品名や攻撃手法名が入っていない
* `malware` に製品名やactor名が入っていない
* `product` にマルウェア名や攻撃手法名が入っていない
* DDoS事象が `c2_communication` だけで表現されていない
* SQL Injection事象が `authentication_bypass` だけで表現されていない
* `taxonomy_values.csv` に同じ `(dimension, normalized_value)` が重複していない

---

## 最後にチャットで報告する内容

必ず以下を報告してください。

* 対象月
* 読み込んだ taxonomy files
* 読み込んだ `events.csv` / `event_tags.csv`
* `events.csv` を変更していないこと
* 追加した actor タグ件数
* 追加した product タグ件数
* 追加した malware タグ件数
* 追加した attack_method タグ件数
* 追加した crime_trend タグ件数
* 修正した既存タグ件数
* 削除した重複タグ数
* 削除した空行数
* 追加した taxonomy_values 件数
* 追加した taxonomy_values 一覧
* actor を追加した event_key 一覧
* product を追加した event_key 一覧
* malware を追加した event_key 一覧
* attack_method を追加した event_key 一覧
* crime_trend を追加した event_key 一覧
* DDoS関連で確認・修正した event_key 一覧
* SQL Injection関連で確認・修正した event_key 一覧
* unresolved taxonomy_gap items
* unresolved classification_review items

## 出力品質

* 既存データの補正として扱うこと
* 全面再生成しないこと
* 変更は最小限にすること
* UTF-8 の CSV とすること
* ハルシネーション禁止
* 推定禁止
* 不明なものは無理に分類しないこと

では、`{{target_data_dir}}/event_tags.csv` と、必要な場合のみ `daily-news/data/taxonomy/taxonomy_values.csv` を必要最小限で補正してください。

