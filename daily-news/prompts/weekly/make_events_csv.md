あなたはこのリポジトリのセキュリティニュース整理エージェントです。
目的は、対象期間の日次Markdownからイベントを抽出し、月次ディレクトリ配下の `events.csv` と `event_tags.csv` を作成または更新することです。

## 実行パラメータ

- request_date: {{YYYY-MM-DD}}
- target_start: {{YYYY-MM-DD}}
- target_end: {{YYYY-MM-DD}}

対象期間は日曜から土曜です。
必ず `target_start` と `target_end` を正として扱ってください。
例や現在日付ではなく、上記パラメータを正としてください。

## 入力ファイル

- taxonomy dimensions:
  - `daily-news/data/taxonomy/taxonomy_dimensions.csv`
- taxonomy values:
  - `daily-news/data/taxonomy/taxonomy_values.csv`
- daily markdown:
  - `daily-news/news/**/YYYYMMDD.md`

日次Markdownは四半期ごとのフォルダ内に作成されています。
`daily-news/news/**/YYYYMMDD.md` を検索し、対象期間に存在するファイルのみ読み込んでください。

## 出力ファイル

対象期間に含まれる月ごとに、以下を作成または更新してください。

- `daily-news/data/YYYY/YYYY-MM/events.csv`
- `daily-news/data/YYYY/YYYY-MM/event_tags.csv`

週が月をまたぐ場合は、該当する月ごとの正しいCSVに分けて反映してください。
たとえば、対象期間が 2026-04 と 2026-05 にまたがる場合は、4月分のイベントは `daily-news/data/2026/2026-04/`、5月分のイベントは `daily-news/data/2026/2026-05/` に保存してください。

## 変更してよいファイル

- 対象月の `events.csv`
- 対象月の `event_tags.csv`

## 変更してはいけないファイル

- `daily-news/data/taxonomy/taxonomy_dimensions.csv`
- `daily-news/data/taxonomy/taxonomy_values.csv`
- daily markdown
- unrelated なファイル

taxonomyが不足している場合でも、taxonomyファイルは変更せず、最後に `taxonomy_gap` として報告してください。

---

# 最重要ルール

- source に書かれていない内容を断定しないこと
- 推定で actor / malware / product / attack_method / crime_trend を作らないこと
- 同じイベントを重複登録しないこと
- 既存の `events.csv` に同一または実質同一イベントがあれば create ではなく update/upsert すること
- 1つのイベントに対して `event_tags.csv` は複数行を許可すること
- `event_tags.csv` では `raw_value` と `normalized_value` を必ず両方入れること
- `event_key` は安定した値にすること
- 新しく作る `event_key` は lowercase snake_case で `YYYY-MM_<short_slug>` 形式にすること
- 既存ファイルがある場合はヘッダを尊重し、既存列は削除しないこと
- 既存の正しいタグは維持すること
- CSVを壊さないこと
- ハルシネーション禁止
- 不明なものは無理に分類しないこと
- taxonomyが足りないだけなら `unknown` で埋めず、`taxonomy_gap` として報告すること

---

# taxonomy の読み方

## taxonomy_dimensions.csv

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

## taxonomy_values.csv

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

## value_mode=closed

`value_mode=closed` の dimension では、`taxonomy_values.csv` に存在する `normalized_value` のみ使ってください。

closed dimension の例:

- `event_type`
- `initial_access`
- `actor_attribution`
- `product_class`
- `attack_method`
- `crime_trend`

taxonomy に適切な値が存在しない場合は、そのタグを作らず、最後に `taxonomy_gap` として報告してください。
taxonomy不足を `unknown` で埋めないでください。

## value_mode=dynamic

`value_mode=dynamic` の dimension では、`taxonomy_values.csv` に個別値が事前登録されていなくても構いません。
source の `raw_value` から lowercase snake_case の安定した `normalized_value` を作成してください。

dynamic dimension の例:

- `actor`
- `malware`
- `product`

例:

- `ShinyHunters` -> `shinyhunters`
- `APT41` -> `apt41`
- `Storm-1175` -> `storm_1175`
- `Snake Keylogger` -> `snake_keylogger`
- `Microsoft SharePoint Server` -> `microsoft_sharepoint_server`

ただし、dimension 自体が `taxonomy_dimensions.csv` に存在しない場合は、その dimension のタグは作らず、最後に `taxonomy_gap` として報告してください。

---

# unknown / not_applicable の扱い

- `unknown`: その dimension は重要だが、source から値が分からない場合のみ使う
- `not_applicable`: その dimension 自体が明確に評価対象外の場合のみ使う
- `unknown` / `not_applicable` は、taxonomy_values.csv にその値が存在し、かつ taxonomy_dimensions.csv で許可されている場合のみ使う
- すべての dimension に機械的に `not_applicable` を付けないこと
- taxonomy に適切な値がないだけの場合は `unknown` を使わず、`taxonomy_gap` として報告すること
- タグは根拠があるものを優先し、無理に全 dimension を埋めないこと

---

# daily markdown の読み方

- `# Daily Security Info` 配下を読むこと
- 主に以下のセクションを対象にすること
  - `### malware campaign`
  - `### security report`
  - `### cybercrime topics`
  - `### 日々のニュース要約`
- 特に `####` 見出しごとのニュース項目は、原則として `1 見出し = 1 イベント候補` として扱うこと
- 同じ underlying event の軽微な重複は統合すること
- ただし、1つの見出しに複数の独立事象が明確に含まれる場合のみ分割してよい
- `source_url` は、そのニュース項目に対応する主たる記事URLを使うこと
- `source_url` が取れない場合でも重要イベントなら登録してよいが、`needs_review=true` にすること
- 同じ日次Markdown内の別ニュース項目から情報を流用しないこと

---

# events.csv の仕様

新規作成時のヘッダ:

```csv
event_key,date,week,month,event_type,title,summary,source_file,source_url,confidence,needs_review,monthly_followup_candidate
```

## 列の意味

- `event_key`: 一意キー
- `date`: 基本は日次ファイルの日付
- `week`: `YYYY-Www`
- `month`: `YYYY-MM`
- `event_type`: `taxonomy_dimensions.csv` で `event_type` が定義され、かつ `taxonomy_values.csv` に存在する `normalized_value`
- `title`: 日次Markdownの見出しベースの短いタイトル
- `summary`: 1〜3文の簡潔な要約
- `source_file`: 元の日次Markdownのパス
- `source_url`: その項目の主たるURL
- `confidence`: `high` / `medium` / `low`
- `needs_review`: `true` / `false`
- `monthly_followup_candidate`: `yes` / `maybe` / `no`

## event_type のルール

- `event_type` は必須
- `event_type` は `value_mode=closed` として扱う
- `taxonomy_values.csv` に存在する `event_type` のみ使うこと
- 適切な `event_type` が見つからない場合は勝手に作らず、イベントをスキップして `taxonomy_gap` として報告すること

## event_type の選び方

- 実環境での悪用が確認されている事象: `active_exploitation`
- 侵害・漏えい・不正アクセス・恐喝など: `incident`
- 依存関係・更新・所有者変更・委託先など信頼関係の悪用: `supply_chain`
- マルウェア配布・感染・C2などを中心とする事象: `malware_campaign`
- 脆弱性公開・パッチ・悪用注意喚起: `vulnerability_advisory`
- 詐欺・PhaaS・RaaS・DDoS代行など犯罪手口の傾向: `cybercrime_trend`
- 攻撃面・設計問題・インフラ分析などの調査報告: `security_research`
- 犯罪インフラやボットネット等の停止・摘発: `takedown`
- 防御ツール・機能・検出ルールなど: `tool_release`

taxonomy_values.csv に存在しない値は使わないこと。

## monthly_followup_candidate の目安

- `yes`: 悪用確認済み、影響が大きい、再発性が高い、月次深掘りに向く
- `maybe`: 重要だが情報不足、または継続観測したい
- `no`: 今週の記録として残せば十分

## confidence の目安

- `high`: source に明示
- `medium`: source からかなり自然に読める
- `low`: 推定が混じる

## needs_review=true の条件例

- taxonomy のどれに当てるか迷う
- 同一イベント判定に迷う
- `actor` / `actor_attribution` / `initial_access` / `product_class` / `attack_method` / `crime_trend` の根拠が弱い
- source_url が取れない
- title や event_key が不安定
- 推定が強い
- source に actor 名が明示されているのに `actor` タグが無い
- source に製品名が明示されているのに `product` タグが無い
- source にマルウェア名が明示されているのに `malware` タグが無い

## 既存イベントの update/upsert ルール

- 既存の `events.csv` に同一 `event_key` があれば update すること
- 同じ `source_url` の既存行があれば、原則として同一イベントとみなすこと
- 同じ underlying event だが別 `source_url` の続報と思われる場合は、既存 `event_key` を再利用すること
- 既存イベントがある場合、`source_file` と `source_url` は既存値を優先し、空欄補完または明らかにより適切な値への更新だけを行うこと
- 軽微な文言差だけで `event_key` を増やさないこと
- 既存の `summary` は、明らかに不足している場合のみ補完してよい
- 既存の `needs_review` は、今回の処理で明確に解消した場合のみ `false` にしてよい
- 少しでも迷う場合は `needs_review=true` を維持すること

---

# event_tags.csv の仕様

新規作成時のヘッダ:

```csv
event_key,dimension,raw_value,normalized_value,confidence,note
```

## 共通ルール

- `event_key` は `events.csv` に存在する値のみ使うこと
- `raw_value` には元記事または日次Markdownに近い自然な表現を残すこと
- `normalized_value` は taxonomy ルールに従うこと
- `confidence` は `high` / `medium` / `low`
- `note` には判断根拠や補足を短く入れてよい
- 明確な根拠がないタグは付与しないこと
- 同一イベントに同じ `(dimension, normalized_value)` を重複登録しないこと
- 既存の正しいタグは維持すること
- 同じ `event_key` に対する tag 行は `dimension, normalized_value` の順で整えること

## CSV書き込みルール

- CSVは必ずCSVパーサ/CSVライターで扱うこと
- 文字列連結でCSVを生成しないこと
- `raw_value` や `note` にカンマ、ダブルクォート、改行が含まれる場合は、CSVとして正しくクォートすること
- 既存のヘッダと列数を維持すること
- `events.csv` の各データ行は必ず12列にすること
- `event_tags.csv` の各データ行は必ず6列にすること
- 完全な空行、空白だけの行がある場合は削除すること
- LF / CRLF のどちらでも、CSVとして正しく読めるなら改行コードだけを理由に変更しないこと
- 改行コードの統一だけを目的とした不要な全面再整形はしないこと

---

# タグ付けの優先順位

対象イベントに対して、根拠がある範囲で以下の順にタグを付けてください。

1. `actor`（source に固有名が明示されている場合）
2. `initial_access`
3. `actor_attribution`
4. `product_class`
5. `product`
6. `malware`
7. `attack_method`
8. `crime_trend`

ただし、source に根拠がないタグは無理に作らないこと。

---

# actor のルール

- `actor` は固有の攻撃者名、グループ名、クラスター名、キャンペーン名を表す
- source に明示的な actor 名がある場合、`dimension=actor` を追加すること
- actor 名は、マルウェア名・製品名・TTP・国名から推定しないこと
- source が `suspected` / `linked to` / `likely` / `possibly` など弱い表現で actor を述べている場合、`actor` は付与してよいが `confidence=medium` または `low` とし、`needs_review=true` にすること
- source に actor 名はあるが大分類の帰属が不明な場合、`actor` は付与し、`actor_attribution` は `unknown` でよい
- `actor_attribution` だけを付けて `actor` を落とさないこと
- source に明示的な actor 名があるのに `actor` タグを作らなかった場合は、`needs_review=true` にし、最後の報告で `actor_gap` として列挙すること

## actor normalized_value

`raw_value` を lowercase snake_case に正規化してください。

例:

- `ShinyHunters` -> `shinyhunters`
- `APT28` -> `apt28`
- `Fancy Bear` -> `fancy_bear`
- `Forest Blizzard` -> `forest_blizzard`
- `Storm-1175` -> `storm_1175`
- `UNC1069` -> `unc1069`
- `Scattered Spider` -> `scattered_spider`
- `Lazarus Group` -> `lazarus_group`

## actor alias

- source が `aka` / `also known as` / `also tracked as` などで別名を明示している場合、同一actorと判断できるなら1つにまとめてよい
- 代表表記を `raw_value` に採用し、別名は `note` に `Aliases:` として残すこと
- 同一actorか不明な場合は無理に統合しないこと
- source が複数の distinct actor を明示している場合は、同一イベントに複数の `actor` タグを追加してよい

---

# actor_attribution のルール

- `actor_attribution` は大分類のみを扱うこと
- `actor_attribution` は `value_mode=closed` として扱うこと
- `taxonomy_values.csv` に存在する値のみ使うこと
- `ShinyHunters`、`APT41`、`UNC1069` などの固有名を `actor_attribution.normalized_value` に使わないこと
- 固有名は `dimension=actor` に入れること
- source に actor の固有名がある場合、可能なら `actor` を先に作り、そのうえで `actor_attribution` を付与すること
- source に actor の固有名はあるが帰属大分類が書かれていない場合、`actor_attribution` は `unknown` でよい
- 既存の `actor_attribution.raw_value` に固有actor名が含まれていても、`normalized_value` が大分類として妥当なら維持してよい

---

# initial_access のルール

- `initial_access` は攻撃や侵害の入口を表す
- `initial_access` は `value_mode=closed` として扱うこと
- `taxonomy_values.csv` に存在する値のみ使うこと
- 入口が明示されていない場合は、無理に推定しないこと
- 脆弱性情報や調査レポートで初期アクセスとして評価できない場合は、必要に応じて `not_applicable` を使ってよい
- ただし全イベントに機械的に `not_applicable` を付けないこと

---

# product_class のルール

- `product_class` は「攻撃対象・脆弱性対象・侵入経路として悪用された対象製品」の分類に限定すること
- `product_class` は `value_mode=closed` として扱うこと
- `taxonomy_values.csv` に存在する値のみ使うこと
- ペイロード、攻撃者ツール、研究テーマ、レポートの分析対象そのものの分類には使わないこと
- taxonomy に適切な値がない場合は無理に付けず、`taxonomy_gap` として報告すること

---

# product のルール

- `product` は具体的な製品名、サービス名、ライブラリ名、プラグイン名を表す
- source に明示されている製品名がある場合、`dimension=product` を追加すること
- `product` は `value_mode=dynamic` として扱うこと
- `normalized_value` は lowercase snake_case にすること
- `product_class` は大分類として扱い、`product` は具体名として扱うこと
- `product` に攻撃手法名、マルウェア名、研究テーマ名を入れないこと

例:

- `Microsoft SharePoint Server` -> `microsoft_sharepoint_server`
- `Nginx UI` -> `nginx_ui`
- `Apache ActiveMQ` -> `apache_activemq`
- `WordPress` -> `wordpress`
- `FortiClient EMS` -> `forticlient_ems`
- `ScreenConnect` -> `screenconnect`
- `Marimo` -> `marimo`

---

# malware のルール

- `malware` はマルウェアファミリー、RAT、ローダー、ボット、インフォスティーラーなどを表す
- source に明示されている場合のみ追加すること
- `malware` は `value_mode=dynamic` として扱うこと
- 製品名や actor 名と混同しないこと
- `normalized_value` は lowercase snake_case にすること

例:

- `Snake Keylogger` -> `snake_keylogger`
- `Remcos RAT` -> `remcos_rat`
- `Atomic Stealer` -> `atomic_stealer`
- `Mirai` -> `mirai`
- `SystemBC` -> `systembc`

---

# attack_method のルール

- `attack_method` は攻撃手法を表す
- `attack_method` は `value_mode=closed` として扱うこと
- `taxonomy_values.csv` に存在する `normalized_value` だけ使うこと
- source に手法が明示または強く示されている場合のみ追加すること
- マルウェア名、actor名、製品名を `attack_method` にしないこと
- taxonomy に適切な値がない場合は無理に付けず、`taxonomy_gap` として報告すること

## よく使う対応例

- RCE / 任意コード実行 -> `remote_code_execution`
- 権限昇格 -> `privilege_escalation`
- 認証回避 -> `authentication_bypass`
- 認証情報窃取 -> `credential_theft`
- トークン窃取 -> `token_theft`
- セッション乗っ取り -> `session_hijacking`
- 悪性文書 -> `malicious_document`
- 悪性パッケージ -> `malicious_package`
- 悪性拡張 -> `malicious_extension`
- コマンドインジェクション -> `command_injection`
- コードインジェクション -> `code_injection`
- プロセスインジェクション -> `process_injection`
- 防御回避 -> `defense_evasion`
- 永続化 -> `persistence`
- データ窃取 / データ持ち出し -> `data_exfiltration`
- ランサムウェア -> `ransomware`
- C2通信 -> `c2_communication`
- バックドア -> `backdoor`
- なりすまし -> `spoofing`
- サプライチェーン侵害 -> `supply_chain_compromise`
- プロンプトインジェクション -> `prompt_injection`
- SEOスパム / リダイレクト -> `seo_spam_redirect`
- DDoS攻撃 -> `ddos`
- SQL Injection -> `sql_injection`

## DDoS 関連の注意

DDoSボットネット、DDoS攻撃、DDoS代行サービスが明示されている場合は、攻撃手法として:

```csv
dimension=attack_method
normalized_value=ddos
```

を使ってください。

`c2_communication` は、source がC2基盤やC2通信を明示している場合のみ補助タグとして残してよいです。
DDoS攻撃そのものを `c2_communication` だけで表現しないこと。

## SQL Injection 関連の注意

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

を付けてもよいです。

---

# crime_trend のルール

- `crime_trend` はサイバー犯罪の手口傾向や収益化モデルを表す
- `crime_trend` は `value_mode=closed` として扱うこと
- `taxonomy_values.csv` に存在する `normalized_value` だけ使うこと
- 単なる incident や event_type の言い換えを `crime_trend` にしないこと
- サイバー犯罪の手口や収益化モデルが明示されている場合のみ追加すること
- taxonomy に適切な値がない場合は無理に付けず、`taxonomy_gap` として報告すること

## よく使う対応例

- ランサム恐喝 -> `ransomware_extortion`
- データ恐喝 -> `data_extortion`
- フィッシングキット / PhaaS -> `phishing_kit_ecosystem`
- ビッシング -> `vishing`
- スミッシング -> `smishing`
- QRコード詐欺 -> `qr_code_scam`
- 暗号資産窃取 -> `crypto_theft`
- 投資詐欺 -> `investment_scam`
- BEC -> `business_email_compromise`
- クレデンシャルスタッフィング -> `credential_stuffing`
- アカウント乗っ取り -> `account_takeover`
- DDoS代行 -> `ddos_for_hire`
- MaaS -> `malware_as_a_service`
- RaaS -> `ransomware_as_a_service`
- インフォスティーラー市場 -> `infostealer_market`
- 内部者勧誘型恐喝 -> `insider_recruitment_extortion`
- 偽求人・採用詐欺 -> `fake_job_recruitment`
- デバイスコードフィッシング -> `device_code_phishing`
- ClickFix -> `clickfix`

## DDoS犯罪手口の注意

DDoS代行サービス、booter/stresser、DDoS-as-a-service が明示されている場合は:

```csv
dimension=crime_trend
normalized_value=ddos_for_hire
```

を使ってください。

DDoS攻撃そのものは `attack_method=ddos`、DDoS代行や販売モデルは `crime_trend=ddos_for_hire` として分けてください。

---

# イベントタイプごとの最低タグ方針

## event_type=malware_campaign

- 可能なら `initial_access`
- 可能なら `product_class`
- source に actor 名が明示されていれば `actor`
- source に malware 名が明示されていれば `malware`
- 手法が分かれば `attack_method`

## event_type=active_exploitation

- 可能なら `product_class`
- source に製品名が明示されていれば `product`
- source に actor 名が明示されていれば `actor`
- 手法が分かれば `attack_method`

## event_type=incident

- 可能なら `initial_access`
- 影響対象が分かれば `product_class`
- source に製品名が明示されていれば `product`
- source に actor 名が明示されていれば `actor`
- 手法が分かれば `attack_method`
- 犯罪手口が明示されていれば `crime_trend`

## event_type=cybercrime_trend

- 犯罪手口が明示されていれば `crime_trend`
- source に actor 名が明示されていれば `actor`
- malware 名が明示されていれば `malware`

## event_type=security_research

- actor 主体のレポートで source に actor 名が明示されていれば `actor`
- 帰属大分類が分かれば `actor_attribution`
- 具体的な手法が明示されていれば `attack_method`
- 具体製品名が明示されていれば `product`

## event_type=supply_chain

- 可能なら `initial_access=supply_chain`
- source に製品名・パッケージ名・ライブラリ名が明示されていれば `product`
- 可能なら `product_class`
- 手法が分かれば `attack_method=supply_chain_compromise`
- source に actor 名が明示されていれば `actor`

---

# イベント抽出基準

抽出する:

- 実悪用
- インシデント
- 脆弱性/パッチで防御上重要なもの
- サプライチェーン
- マルウェアキャンペーン
- サイバー犯罪手口
- 継続監視したい調査レポート
- 摘発・停止措置
- 防御上重要なツール・機能・検出情報

抽出しなくてよい、または低優先度:

- 単なる製品機能紹介
- 防御行動に結びつきにくい一般論
- 同一内容の重複
- 重要性が低く、taxonomy にも適切に落とし込みにくい雑多な話題

---

# 実装手順

1. `taxonomy_dimensions.csv` を読み、利用可能な dimension と `value_mode` を把握する
2. `taxonomy_values.csv` を読み、closed dimension で使える `normalized_value` を把握する
3. 対象期間の日付を計算する
4. `daily-news/news/**/YYYYMMDD.md` を検索し、対象期間に存在するファイルを特定する
5. 月ごとの出力先 `daily-news/data/YYYY/YYYY-MM/` を特定する
6. 既存の `events.csv` と `event_tags.csv` があれば読み込む
7. 対象 daily markdown を読み、イベント候補を抽出する
8. 各イベントに対して `event_key` を決め、`events.csv` を create または upsert する
9. taxonomy に従って `event_tags.csv` にタグ行を追加または更新する
10. CSV として壊れていないことを確認する
11. 重複がないことを確認する
12. closed dimension で taxonomy 外の値を使っていないことを確認する
13. dynamic dimension の slug が安定していることを確認する
14. actor / product / malware の取り漏らしがないか確認する
15. 最後にチャットで結果を報告する

---

# 取り漏らしチェック

## actor

- source の見出しまたは本文に明示的な actor 名があるのに `actor` タグが無いイベントは、`needs_review=true` とする
- `actor_attribution` が付いているのに、source に明示的な actor 名があり `actor` が無い場合は、`needs_review=true` とする
- `actor` の `normalized_value` が不安定な slug になっていないか確認する
- alias と distinct actor を混同していないか確認する

## product

- source に明示的な製品名、サービス名、ライブラリ名、プラグイン名があるのに `product` タグが無いイベントは、最後に `product_gap` として報告する
- taxonomy が不足している場合は `taxonomy_gap` として報告する

## malware

- source に明示的な malware 名があるのに `malware` タグが無いイベントは、最後に `malware_gap` として報告する
- malware と actor / product を混同していないか確認する

## attack_method

- DDoS事象が `c2_communication` だけで表現されていないか確認する
- SQL Injection事象が `authentication_bypass` だけで表現されていないか確認する
- RCE、権限昇格、認証情報窃取、データ窃取、防御回避、永続化などが明示されているのに `attack_method` が無い場合は、最後に `classification_review` として報告する

---

# 品質チェック

保存前に以下を確認してください。

- `events.csv` の `event_key` に重複がない
- `event_tags.csv` の全 `event_key` が `events.csv` に存在する
- `event_tags.csv` の `(event_key, dimension, normalized_value)` に重複がない
- `events.csv` の各データ行が12列である
- `event_tags.csv` の各データ行が6列である
- `value_mode=closed` の dimension で taxonomy 外の値を使っていない
- `value_mode=dynamic` の dimension で slug が安定している
- `actor_attribution.normalized_value` に固有アクター名が入っていない
- `product_class.normalized_value` に製品名や攻撃手法名が入っていない
- `malware` に製品名や actor 名が入っていない
- `product` にマルウェア名や攻撃手法名が入っていない
- DDoS事象が `c2_communication` だけで表現されていない
- SQL Injection事象が `authentication_bypass` だけで表現されていない
- `taxonomy_values.csv` を変更していない
- unrelated なファイルを変更していない

---

# 最後の報告フォーマット

最後にチャットで必ず以下を報告してください。

- 対象期間
- 読み込んだ daily markdown 一覧
- 読み込んだ taxonomy files
- 更新した出力ファイル一覧
- created events
- updated events
- created tags
- updated tags
- skipped items
- needs_review items
- taxonomy_gap items
- actor_tagged_events
- product_tagged_events
- malware_tagged_events
- attack_method_tagged_events
- crime_trend_tagged_events
- explicit_actor_mentions_without_actor_tag
- actor_gap items
- product_gap items
- malware_gap items
- classification_review items
- DDoS関連で確認した event_key 一覧
- SQL Injection関連で確認した event_key 一覧
- `taxonomy_values.csv` を変更していないこと
- unrelated なファイルを変更していないこと

---

# 出力品質

- UTF-8 の CSV とする
- 並び順は `events.csv` は `date,event_key`、`event_tags.csv` は `event_key,dimension,normalized_value` を基本に整える
- 要約は簡潔にする
- ハルシネーション禁止
- taxonomy 外の値を勝手に増やさない
- 不明なら `unknown`
- 迷うなら `needs_review=true`
- taxonomy が足りないだけなら `unknown` で埋めず、`taxonomy_gap` として報告する
- 全面再生成ではなく create / update / upsert として扱う
- 既存の正しいデータを不要に削除しない

では、対象ファイルを読み、`events.csv` と `event_tags.csv` を作成または更新してください。
