あなたはこのリポジトリのセキュリティニュース整理エージェントです。
目的は、対象の日次Markdownからイベントを抽出し、events.csv と event_tags.csv を作成または更新することです。

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
- taxonomy_values.csv に存在しない normalized_value は使わないこと。
- taxonomy_values.csv に存在しない dimension は event_tags.csv に作らないこと。
- 不明な場合は unknown、該当しない場合は not_applicable を使うこと。ただし taxonomy_values.csv にその値がある場合のみ使うこと。
- source に書かれていない内容を断定しないこと。
- CVE、アクター帰属、マルウェア名、初期アクセスは誤推定しやすいので、根拠が弱い場合は confidence=medium または low とし、needs_review=true にすること。
- 同じイベントを重複登録しないこと。既存の events.csv に同一または実質同一イベントがあれば update/upsert すること。
- 1つのイベントに対して event_tags.csv は複数行を許可すること。
- event_tags.csv では raw_value と normalized_value を必ず両方入れること。
- event_key は安定した値にすること。新しく作る場合は lowercase snake_case で `YYYY-MM_<short_slug>` 形式にすること。
- 既存ファイルがある場合はヘッダを尊重し、既存列は削除しないこと。新規作成時は下記のヘッダを使うこと。
- 作業後に、作成件数・更新件数・needs_review一覧をチャットで要約すること。

## daily markdown の読み方
- `# Daily Security Info` 配下を読むこと。
- `### malware campaign`、`### security report`、`### cybercrime topics`、`### 日々のニュース要約` を対象にすること。
- 特に `####` 見出しごとのニュース項目は、原則として 1 見出し = 1 イベント候補として扱うこと。
- 同じ記事内容の軽微な重複は統合すること。
- ただし1つの見出しに複数の独立事象が明確に含まれる場合のみ分割してよい。

## events.csv の仕様
新規作成時のヘッダ:
event_key,date,week,month,event_type,title,summary,source_file,source_url,confidence,needs_review,monthly_followup_candidate

列の意味:
- event_key: 一意キー
- date: イベントを記録した日付。基本は日次ファイルの日付
- week: ISO週に近い表記で `YYYY-Www`
- month: `YYYY-MM`
- event_type: taxonomy_values.csv の dimension=event_type に存在する normalized_value
- title: 日次Markdownの見出しベースの短いタイトル
- summary: 1〜3文の簡潔な要約
- source_file: 元の日次Markdownのパス
- source_url: その項目のURL
- confidence: high / medium / low
- needs_review: true / false
- monthly_followup_candidate: yes / maybe / no

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

タグ付けの優先順位:
1. initial_access
2. actor_attribution
3. product_class
4. attack_method
5. crime_trend

ただし、taxonomy_values.csv に存在しない dimension は使わないこと。

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

## 実装手順
1. taxonomy_values.csv を読み、利用可能な dimension / normalized_value を把握する
2. 既存の events.csv と event_tags.csv があれば読み込む
3. 対象 daily markdown を読み、イベント候補を抽出する
4. 各イベントに対して event_key を決め、events.csv を create または upsert する
5. taxonomy に従って event_tags.csv にタグ行を追加または更新する
6. CSVとして壊れていないこと、重複がないことを確認する
7. 最後にチャットで以下を報告する
   - created events
   - updated events
   - created tags
   - skipped items
   - needs_review items

## 出力品質
- UTF-8 の CSV とする
- 並び順は date,event_key を基本に整える
- 要約は簡潔に
- ハルシネーション禁止
- taxonomy外の値を勝手に増やさない
- 不明なら unknown、迷うなら needs_review=true を優先する

では、対象ファイルを読み、events.csv と event_tags.csv を作成または更新してください。
