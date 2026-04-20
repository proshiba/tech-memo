今回の依頼日: YYYY-MM-DD
例: 2026-04-20

あなたはこのリポジトリのセキュリティニュース整理エージェントです。  
目的は、対象の日次Markdownからイベントを抽出し、月次ディレクトリ配下の events.csv と event_tags.csv を作成または更新することです。

## 対象ファイル
入力:
- taxonomy: data/taxonomy/taxonomy_values.csv
- daily markdown:
  - 右フォルダ配下の各日付のファイル: daily-news/news/YYYY_MM-DD/YYYYMMDD.md

この日付毎のファイルは、四半期ごとのフォルダ内に作成されています。  
また、作成は週次で依頼し、日曜から土曜までのニュースを制してもらいます。  

例えば、2026年4月20日に依頼した場合は、以下の日付が対象です。  
2026年4月12日 - 2026年4月18日
ファイル名でいうと以下です。これらのうち、存在するファイルを整理し、events.csv と event_tags.csvを作成または更新してください。  
- daily-news/news/2026_04-06/20260412.md
- daily-news/news/2026_04-06/20260413.md
- daily-news/news/2026_04-06/20260414.md
- daily-news/news/2026_04-06/20260415.md
- daily-news/news/2026_04-06/20260416.md
- daily-news/news/2026_04-06/20260417.md
- daily-news/news/2026_04-06/20260418.md

出力は、月次でフォルダを切り替えます。そのため、2026年4月のファイルは以下です。  

出力:
- data/2026/2026-04/events.csv
- data/2026/2026-04/event_tags.csv

5月になれば、これらはフォルダが切り替わり、`data/2026/2026-05`になります。  
週の途中で、4月と5月に切り替わった場合、それぞれの正しいファイルに反映させてください。  

## 最重要ルール
- taxonomy_values.csv に存在しない dimension は event_tags.csv に作らないこと
- taxonomy_values.csv に存在しない normalized_value は使わないこと
- source に書かれていない内容を断定しないこと
- 不明な場合だけ unknown を使うこと
- taxonomy に適切な値が存在しないだけの場合は unknown で埋めないこと
- taxonomy に適切な値が存在しない場合は、そのタグ自体を作らず、最後の報告で taxonomy_gap として列挙すること
- not_applicable は、その dimension が明確に評価対象外であり、かつ taxonomy にその値が存在する場合のみ使うこと
- タグは明確な根拠があるものだけ付与し、無理に全 dimension を埋めないこと
- CVE、アクター帰属、マルウェア名、初期アクセスは誤推定しやすいため、根拠が弱い場合は confidence=medium または low とし、needs_review=true にすること
- 同じイベントを重複登録しないこと。既存の events.csv に同一または実質同一イベントがあれば update/upsert すること
- 1つのイベントに対して event_tags.csv は複数行を許可すること
- event_tags.csv では raw_value と normalized_value を必ず両方入れること
- event_key は安定した値にすること。新しく作る場合は lowercase snake_case で YYYY-MM_<short_slug> 形式にすること
- 既存ファイルがある場合はヘッダを尊重し、既存列は削除しないこと
- 新規作成時は下記のヘッダを使うこと
- 作業後に、作成件数・更新件数・needs_review 一覧・taxonomy_gap 一覧をチャットで要約すること
- unrelated なファイルは編集しないこと

## daily markdown の読み方
- `# Daily Security Info` 配下を読むこと。
- `### malware campaign`、`### security report`、`### cybercrime topics`、`### 日々のニュース要約` を対象にすること。
- 特に `####` 見出しごとのニュース項目は、原則として 1 見出し = 1 イベント候補として扱うこと。
- 同じ記事内容の軽微な重複は統合すること。
- ただし1つの見出しに複数の独立事象が明確に含まれる場合のみ分割してよい。
- source_url は、そのニュース項目に対応する主たる記事 URL を使うこと
- source_url が取れない場合でも重要イベントなら登録してよいが、needs_review=true にすること

## events.csv の仕様
新規作成時のヘッダ:  
event_key,date,week,month,event_type,title,summary,source_file,source_url,confidence,needs_review,monthly_followup_candidate


列の意味:
- event_key: 一意キー
- date: 基本は日次ファイルの日付
- week: YYYY-Www
- month: YYYY-MM
- event_type: taxonomy_values.csv の dimension=event_type に存在する normalized_value
- title: 日次Markdownの見出しベースの短いタイトル
- summary: 1〜3文の簡潔な要約
- source_file: 元の日次Markdownのパス
- source_url: その項目の主たるURL
- confidence: high / medium / low
- needs_review: true / false
- monthly_followup_candidate: yes / maybe / no

event_type のルール:
- event_type は必須
- taxonomy に存在する event_type の中から選ぶこと
- どうしても適切な event_type が見つからない場合は勝手に作らず、スキップして taxonomy_gap として報告すること


monthly_followup_candidate の目安:
- yes: 悪用確認済み、影響が大きい、再発性が高い、月次深掘りに向く
- maybe: 重要だが情報不足、または継続観測したい
- no: 今週の記録として残せば十分

confidence の目安:
- high: sourceに明示
- medium: sourceからかなり自然に読める
- low: 推定が混じる

needs_review=true の条件例:
- taxonomyのどれに当てるか迷う
- 同一イベント判定に迷う
- actor_attribution / initial_access / product_class の根拠が弱い
- source_url が取れない
- title や event_key が不安定
- 推定が強い

既存イベントの update/upsert ルール:
- 既存の events.csv に同一 event_key があれば update すること
- 同じ source_url の既存行があれば、原則として同一イベントとみなすこと
- 同じ underlying event だが別 source_url の続報と思われる場合は、既存 event_key を再利用すること
- 既存イベントがある場合、source_file と source_url は既存値を優先し、空欄補完または明らかにより適切な値への更新だけを行うこと
- 軽微な文言差だけで event_key を増やさないこと

## event_tags.csv の仕様

新規作成時のヘッダ:  
event_key,dimension,raw_value,normalized_value,confidence,note

ルール:

- event_key は events.csv に存在する値のみ使うこと
- dimension は taxonomy_values.csv に存在するものだけ使うこと
- normalized_value は taxonomy_values.csv に存在する値だけ使うこと
- raw_value には元記事または日次Markdownに近い表現を残すこと
- note には判断根拠や補足を短く入れてよい
- 同一イベントに同じ `(dimension, normalized_value)` を重複登録しないこと
- 明確な根拠がないタグは付与しないこと
- 同じ event_key に対する tag 行の並びは、dimension, normalized_value の順で整えること

タグ付けの優先順位:
1. initial_access
2. actor_attribution
3. product_class

追加 dimension のルール:

- attack_method / crime_trend / malware / actor などは、taxonomy_values.csv に dimension として存在する場合のみ使うこと
- taxonomy に存在しない dimension は event_tags.csv に作らないこと

unknown と not_applicable の使い分け:

- unknown: その dimension は重要だが、source から値が分からない
- not_applicable: その dimension 自体がそのイベントに明確に当てはまらない
- どちらでもなく、単に taxonomy に適切な値がないだけならタグを作らず taxonomy_gap にすること

actor_attribution のルール:

- actor_attribution は大分類のみを扱うこと
- ShinyHunters、APT41、UNC1069 などの固有名を normalized_value に使わないこと
- actor という dimension が taxonomy に存在しない限り、固有名は raw_value または note に残すだけにすること
- source が固有名を挙げていても、大分類の帰属が明示されていなければ actor_attribution は unknown にしてよい

product_class のルール:

- product_class は「攻撃対象・脆弱性対象・侵入経路として悪用された対象製品」の分類に限定すること
- ペイロード、攻撃者ツール、研究テーマ、レポートの分析対象そのものの分類には使わないこと
- taxonomy に適切な値がない場合は product_class を無理に付けないこと

## イベント抽出基準
抽出する:
- 実悪用
- インシデント
- 脆弱性/パッチで防御上重要なもの
- サプライチェーン
- マルウェアキャンペーン
- サイバー犯罪手口
- 継続監視したい調査レポート

抽出しなくてよい、または低優先度:
- 単なる製品機能紹介
- 防御行動に結びつきにくい一般論
- 同一内容の重複
- 重要性が低く、taxonomy にも適切に落とし込みにくい雑多な話題

## 実装手順
1. taxonomy_values.csv を読み、利用可能な dimension / normalized_value を把握する
2. 対象期間の日付を計算する
3. daily-news/news/**/YYYYMMDD.md を検索し、対象期間に存在するファイルを特定する
4. 月ごとの出力先 daily-news/data/YYYY/YYYY-MM/ を特定する
5. 既存の events.csv と event_tags.csv があれば読み込む
6. 対象 daily markdown を読み、イベント候補を抽出する
7. 各イベントに対して event_key を決め、events.csv を create または upsert する
8. taxonomy に従って event_tags.csv にタグ行を追加または更新する
9. CSV として壊れていないこと、重複がないこと、存在しない taxonomy 値を使っていないことを確認する
10. 最後にチャットで結果を報告する

## 最後の報告フォーマット

最後にチャットで必ず以下を報告すること:

- 対象期間
- 読み込んだ daily markdown 一覧
- 更新した出力ファイル一覧
- created events
- updated events
- created tags
- updated tags
- skipped items
- needs_review items
- taxonomy_gap items


## 出力品質
- UTF-8 の CSV とする
- 並び順は events.csv は date,event_key、event_tags.csv は event_key,dimension,normalized_value を基本に整える
- 要約は簡潔にする
- ハルシネーション禁止
- taxonomy 外の値を勝手に増やさない
- 不明なら unknown、迷うなら needs_review=true を優先する
- taxonomy が足りないだけなら unknown で埋めず、taxonomy_gap として報告する

では、対象ファイルを読み、events.csv と event_tags.csv を作成または更新してください。
