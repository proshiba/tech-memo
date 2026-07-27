# デイリーニュース UI

`daily-news/news`（日々のニュース要約）と `daily-news/iocs`（そこから収集した IOC）を
1 つの画面で読むための GitHub Pages。単体でも使うが、
[research_bench](https://github.com/proshiba/research_bench) ポータルへの iframe 埋め込みも前提にしている。

    https://proshiba.github.io/tech-memo/daily-news/ui/

サーバーは立てない。Markdown と CSS を静的 JSON に落として、依存ゼロのバニラ JS が読む。
ビルド工程は無い。

## 4 つの画面

| ルート | 中身 |
| --- | --- |
| `#/` | 概要。収録範囲・月ごとの推移・直近の日・よく出るアクター/マルウェア/CVE |
| `#/news` | 全期間の記事を横断検索。年・月・「IOCあり」「CVE言及」で絞り込む |
| `#/day/<YYYYMMDD>[/<n>]` | その日のまとめ。元の Markdown の節と記事内ラベルをそのまま出す |
| `#/ioc` | IOC 一覧。値・アクター・マルウェア・分類で絞り、CSV で書き出せる |

`#/day/20260722/3` のように末尾に記事の位置を付けると、その記事にスクロールする。
ポータルからの deep link はこの形で入ってくる。

## データの作り方

```bash
python3 daily-news/ui/build_ui_data.py           # data/ と api/ を生成
python3 daily-news/ui/build_ui_data.py --check   # 生成せず解析結果の統計だけ出す
```

標準ライブラリだけで動く。生成物は約 22 MB あり、ニュースが増えるたびに作り直すので
**リポジトリにはコミットしない**（`.gitignore` 済み）。配信時に CI が作る。

| 出力 | 用途 | 目安 |
| --- | --- | --- |
| `data/index.json` | 日付一覧・統計・ファセット。起動時に必ず読む | 70 KB |
| `data/articles.json` | 全期間の記事の軽量索引。一覧と検索の土台 | 2.8 MB |
| `data/news/<四半期>.json` | 記事の本文。日を開いたときだけ読む | 全 14 本で 12 MB |
| `data/iocs.json` | IOC 全件（列指向の配列） | 1.9 MB |
| `api/v1/meta.json` | ポータル連携仕様 v1 の自己紹介 | 1 KB |
| `api/v1/search.json` | 同上・索引本体（14,360 エンティティ） | 5.0 MB (gzip 0.85) |

`SOURCE_DATE_EPOCH` を渡すと `generated_at` をその時刻に固定できる（CI で使っている）。

### Markdown の解析について

`daily-news/news` の書式は 3 年ぶんで 3 種類ある。パーサーは全部を受ける。

| 書式 | 例 | 記事の見出し |
| --- | --- | --- |
| 現行 | `# Daily Security Info` + `### 日々のニュース要約` | `#### タイトル` |
| 2023 後半〜 | `# 日々のニュース要約` + `## ニュース` | `### タイトル` |
| 2023 前半 | 同上 | `1. <URL>` + `- タイトル: "…"` |

942 日 7,077 記事のうち、タイトル・要約が取れなかったものは 0 件、
URL が無いものが 4 件（元の Markdown 側に記載が無い）。

## 手元で動かす

```bash
python3 daily-news/ui/build_ui_data.py
python3 -m http.server 8000            # リポジトリのルートで
# → http://localhost:8000/daily-news/ui/
```

## 配信

`.github/workflows/deploy-pages.yml` が `main` への push で走り、索引を生成して
`_site/daily-news/ui/` として Pages に上げる。`daily-news/news/**`・`daily-news/iocs/**`・
`daily-news/ui/**` のいずれかが変わったときだけ動く。

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
| `report` | 7,077 | 記事 1 件 | 記事の URL |
| `ioc.*` | 5,533 | IOC CSV（同じ値は 1 件に畳む） | refang 済みの値 |
| `cve` | 1,390 | 記事本文から抽出 | `CVE-YYYY-NNNN` |
| `malware` | 263 | IOC の `malware` 列を分割 | ファミリ名 |
| `actor` | 97 | IOC の `actor` 列を分割 | アクター名 |

`Vidar Stealer, XMRig` や `Macsync / Shub Stealer / AMOS` のような複合値は個別の名前に割り、
`(high confidence)` のような確度注記は落としてから結合キーにしている。
表記ゆれ（`Macsync` / `MacSync`）は小文字化して 1 件に畳み、別表記は `aliases` に残す。

## 中身

```
index.html            外枠
redirect.html         Pages のルート → この画面への案内（配信時に配置）
build_ui_data.py      Markdown / CSV → 静的 JSON
assets/style.css      配色トークンはポータルと同じ組
assets/js/
  main.js             起動・ルーティング・テーマ・埋め込み判定
  store.js            静的 JSON の取得とキャッシュ
  util.js             DOM 生成・Markdown 風レンダラ・整形
  view-overview.js    概要
  view-news.js        記事一覧・横断検索
  view-day.js         1 日分のまとめ
  view-ioc.js         IOC 一覧
```
