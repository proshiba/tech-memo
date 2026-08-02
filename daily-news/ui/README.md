# デイリーニュース UI

`daily-news` の 3 つの層 — `news`（日々のニュース要約）、`data`（それを構造化したイベント）、
`iocs`（一次ソースから収集した IOC）— を 1 つの画面で読むための GitHub Pages。単体でも使うが、
[research_bench](https://github.com/proshiba/research_bench) ポータルへの iframe 埋め込みも前提にしている。

    https://proshiba.github.io/tech-memo/daily-news/ui/

サーバーは立てない。Markdown と CSS を静的 JSON に落として、依存ゼロのバニラ JS が読む。
ビルド工程は無い。

## 3 つの層

同じ事象を 3 つの粒度で持っている。UI はこれを 1 本に繋ぐ。

```
  news/*.md          記事の要約（本文・IOC の列挙・推奨事項）  ← 大元
    └ data/**        イベントとして構造化（9 次元のタグ付き）
    └ iocs/*.csv     一次ソースを当たって収集した IOC
```

イベントの `source_url` を記事の URL と突き合わせて、1,073 件中 890 件（82%）が
記事に紐づいている。残りは `日本のインシデント事例` など記事節以外から起こしたもので、
日付までで留めている。

## 4 つの画面

| ルート | 中身 |
| --- | --- |
| `#/` | 概要。収録範囲・月ごとの推移・直近の日・イベント種別・よく出るアクター/マルウェア/攻撃手法/CVE |
| `#/news` | 全期間の記事を横断検索。年・月・「IOCあり」「CVE言及」で絞り込む |
| `#/events` | 構造化イベント。種別と 8 つの分類軸、要確認・月次フォロー候補で絞り込む |
| `#/day/<YYYYMMDD>[/<n>]` | その日のまとめ。元の Markdown の節と記事内ラベルをそのまま出し、記事ごとにイベントのタグを添える |
| `#/ioc` | IOC 一覧。値・アクター・マルウェア・分類で絞り、CSV で書き出せる |

`#/day/20260722/3` のように末尾に記事の位置を付けると、その記事にスクロールする。
ポータルからの deep link はこの形で入ってくる。

イベントと IOC は名前（アクター・マルウェア）で行き来できる。片方で 0 件だったときは、
もう片方の同じ名前への導線をその場に出す。

## データの作り方

```bash
python3 daily-news/ui/build_ui_data.py           # data/ と api/ を生成
python3 daily-news/ui/build_ui_data.py --check   # 生成せず解析結果の統計だけ出す
python3 daily-news/ui/check_output.py            # 生成物を元データと突き合わせる
```

標準ライブラリだけで動く。生成物は約 23 MB あり、ニュースが増えるたびに作り直すので
**リポジトリにはコミットしない**（`.gitignore` 済み）。配信時に CI が作る。

| 出力 | 用途 | 目安 |
| --- | --- | --- |
| `data/index.json` | 日付一覧・統計・ファセット・分類の定義。起動時に必ず読む | 119 KB |
| `data/articles.json` | 全期間の記事の軽量索引。一覧と検索の土台 | 2.8 MB |
| `data/news/<四半期>.json` | 記事の本文。日を開いたときだけ読む | 全 14 本で 12 MB |
| `data/iocs.json` | IOC 全件（列指向の配列） | 1.9 MB |
| `data/events.json` | イベントとタグ全件 | 1.3 MB |
| `api/v1/meta.json` | ポータル連携仕様 v1 の自己紹介 | 1 KB |
| `api/v1/search.json` | 同上・索引本体（15,273 エンティティ） | 5.5 MB (gzip 0.93) |

`SOURCE_DATE_EPOCH` を渡すと `generated_at` をその時刻に固定できる（手元で差分を見るとき用）。

### Markdown の解析について

`daily-news/news` の書式は 3 年ぶんで 3 種類ある。パーサーは全部を受ける。

| 書式 | 例 | 記事の見出し |
| --- | --- | --- |
| 現行 | `# Daily Security Info` + `### 日々のニュース要約` | `#### タイトル` |
| 2023 後半〜 | `# 日々のニュース要約` + `## ニュース` | `### タイトル` |
| 2023 前半 | 同上 | `1. <URL>` + `- タイトル: "…"` |

942 日 7,077 記事のうち、タイトル・要約が取れなかったものは 0 件、
URL が無いものが 4 件（元の Markdown 側に記載が無い）。

### 記事との対応付け

IOC もイベントも「どの記事から起こしたか」を持つ。ここが外れると調査の起点にならないので、
**当てにいく順番を決め、決められなければ対応を付けない**（誤った対応は無いことより悪い）。

| | IOC（`reference` を使う） | イベント（`source_url` を使う） |
| --- | --- | --- |
| 1 | 同じ日の記事の URL に一致 | `source_file` の日の記事の URL に一致 |
| 2 | 同じ日の記事本文の URL に一致（一次ソース） | — |
| 3 | 同じ日のイベントのタグに malware / actor 名が一致し、候補が 1 件 | — |
| 付けない | 上記で決まらないとき | 同じ日に候補が複数 / 見つからない |

**別の日の記事は候補にしない。** IOC もイベントもその日のニュースファイルから起こしたもので、
別の日に同じ URL の記事があってもそれは同じ話題の再掲であって出所ではない。

現在の内訳は IOC 5,231/5,724 件（91%）、イベント 866/1,073 件（81%）。残りは対応を付けない。

`check_output.py` が、付けた対応が収集日と矛盾していないかを毎回確かめる。
`build_ui_data.py` 側にも、収集元が 1 つの記事番号に固定されていたら生成を止める検査を入れてある
（以前ここは「その日の 1 本目の記事」を無条件に指していて、ほとんどの参照が誤っていた）。

### イベントの読み方

`daily-news/data` には月まとめの `events.csv` と日ごとの `events/<日付>.csv` が併存する時期があり、
同じ事象が別の `event_key` で両方に入っている。**日ごとのファイルがある日はそちらを正とし、
月まとめからはその日を採らない。** これで 1,090 行から 1,073 件に落ちる。

タグの `normalized_value` は `taxonomy_values.csv` の日本語ラベルで表示する。
actor / malware / product は動的な次元でラベルが無いので、記事に書かれていた元表記から
名前らしいもの（`xmrig` → `XMRig`、`microsoft_teams` → `Microsoft Teams`）を選んで表示する。
`teampcp` と `team_pcp` のような表記ゆれは英数字だけに潰して 1 つに畳む。

## 手元で動かす

```bash
python3 daily-news/ui/build_ui_data.py
python3 -m http.server 8000            # リポジトリのルートで
# → http://localhost:8000/daily-news/ui/
```

## 配信

`.github/workflows/deploy-pages.yml` が索引を生成し、`_site/daily-news/ui/` として Pages に上げる。
トリガーは 3 つある。

| トリガー | 拾うもの |
| --- | --- |
| `push`（main、`daily-news/{news,data,iocs,ui}/**`） | ニュース md の直接 push |
| `schedule`（08:30 / 20:30 JST） | IOC・イベント CSV の取りこぼし（下記） |
| `workflow_dispatch` | 手動 |

**IOC とイベントの CSV は push だけでは拾えないことがある。** これらは Claude ルーチンが PR で入れ、
`enable-claude-*-automerge.yml` が `GITHUB_TOKEN` で auto-merge を有効にしている。GitHub は
`GITHUB_TOKEN` 由来のイベントで新しいワークフローを起動しない仕様なので、この経路のマージ push は
`push` トリガーを発火させない可能性がある。加えて、ニュースを push した時点ではその日の CSV は
まだ生成されていないため、どのみち後追いの再生成が要る。定期実行がこの両方を埋めている。

即時性を上げたい場合は、automerge 側の `GH_TOKEN` を PAT（`workflow` スコープ）に替えると、
マージ push が `push` トリガーを起動するようになり、定期実行は不要になる。

**初回だけリポジトリの設定が要る。** Settings → Pages → Build and deployment の
Source を **GitHub Actions** にする。これをしないとワークフローの deploy が失敗する。

生成した `api/v1/*.json` は、配信前に research_bench の
[`validate-index.py`](https://github.com/proshiba/research_bench/blob/main/docs/validate-index.py)
で検査している。エラーが 1 件でもあればデプロイは止まる。

## ポータル（research_bench）への登録

ポータル側の `apps.json` の `sources` に次を足すと、ダッシュボード・クロスサーチ・
ワークベンチの全てで使えるようになる。ポータル側の変更はこれだけ。

```jsonc
{
  "app_id": "tech-memo-daily-news",
  "name": "デイリーニュース",
  "short": "ニュース",
  "accent": "tool",
  "repository": "https://github.com/proshiba/tech-memo",
  "site_url": "https://proshiba.github.io/tech-memo/daily-news/ui/",
  "dashboard_url": "https://proshiba.github.io/tech-memo/daily-news/ui/#/",
  "adapter": "spec-v1",
  "meta_url": "https://proshiba.github.io/tech-memo/daily-news/ui/api/v1/meta.json",
  "approx_bytes": 5000000
}
```

`deep_links` と `capabilities` は `meta.json` から来るので `apps.json` には書かなくてよい。

### 埋め込みの扱い

`embed_css`（ポータルが iframe の DOM に CSS を注入する繋ぎの仕組み）は**使わない**。
この UI は `?embed=1` か「iframe の中にいること」を自分で見て、
ブランドと外部リンクとフッターを畳み、タブだけ残す（仕様 §4 の `embed-mode`）。

同一オリジンなら親のテーマ切り替えにも追従する。ポータルで表示テーマを変えると
iframe の中も一緒に変わる。別オリジンのときは `prefers-color-scheme` に従う。

### 索引に載せているエンティティ

| type | 件数 | 元 | `value`（結合キー） |
| --- | --- | --- | --- |
| `report` | 7,284 | 記事 1 件 ＋ 記事に対応が無いイベント 207 件 | 記事・一次ソースの URL |
| `ioc.*` | 5,533 | IOC CSV（同じ値は 1 件に畳む） | refang 済みの値 |
| `cve` | 1,390 | 記事本文から抽出 | `CVE-YYYY-NNNN` |
| `product` | 429 | イベントの `product` タグ | 製品名 |
| `malware` | 407 | IOC の `malware` 列 ＋ イベントの `malware` タグ | ファミリ名 |
| `actor` | 230 | IOC の `actor` 列 ＋ イベントの `actor` タグ | アクター名 |

記事の `report` エンティティには、対応するイベントの種別とタグを `attrs` として添える。
ポータルの検索結果で「イベント種別: インシデント / アクター: ShinyHunters」まで見える。

`Vidar Stealer, XMRig` や `Macsync / Shub Stealer / AMOS` のような複合値は個別の名前に割り、
`(high confidence)` のような確度注記は落としてから結合キーにしている。
表記ゆれ（`Macsync` / `MacSync`、`lazarus_group` / `Lazarus Group`）は
ポータルと同じ潰し方（英数字だけ・小文字）で 1 件に畳み、別表記は `aliases` に残す。
`aliases` も結合キーとして索引されるので、他ソースがどちらの表記でも横串が刺さる。

## 中身

```
index.html            外枠
redirect.html         Pages のルート → この画面への案内（配信時に配置）
build_ui_data.py      Markdown / CSV → 静的 JSON
check_output.py       生成物と元データの突き合わせ
assets/style.css      配色トークンはポータルと同じ組
assets/js/
  main.js             起動・ルーティング・テーマ・埋め込み判定
  store.js            静的 JSON の取得とキャッシュ
  util.js             DOM 生成・Markdown 風レンダラ・整形
  controls.js         一覧画面で共通の部品（絞り込みのセレクトなど）
  view-overview.js    概要
  view-news.js        記事一覧・横断検索
  view-events.js      構造化イベント
  view-day.js         1 日分のまとめ
  view-ioc.js         IOC 一覧
```
