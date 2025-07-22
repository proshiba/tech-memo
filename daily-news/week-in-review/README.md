# Weekly Reportについて

2025年以降、このWeekly ReportはChatGPTエージェント利利用して作成しています。  

## プロンプト

```
[依頼したいタスク]
あなたはセキュリティに関する週次レポートをユーザーが指定した期間で作成してください。
なお、特に期間の指定がなければ先週で作成をしてください。その際、先週とは以下のように期間を定めます。
指定：日曜日から土曜日で作成。
例) 依頼日が2025-07-21である場合 -> 2025-07-13 to 2025-07-19

[情報ソース]
以下のGitHubリポジトリは私のリポジトリであり、この中に毎日のセキュリティニュースの要約を入れています。
https://github.com/proshiba/tech-memo/blob/main/daily-news

この情報をメインでチェックし、情報の整理を行なってください。

[出力して欲しい情報]

以下の項目を出力してください。
--------
[TL;DR]
- 特に重要な3点の要約

[レポート全体]
- malware activity
- attack campaigns
- vulnerability
- trends
  - cybercrime
  - initial access
- stats
  - by attacker
  - by initial access TTPs
- notable Events
  - in Japan
  - in East Asia
  - in WorldWide
- notable TTPs

notable incident の要約には以下を含める:
- 何が重要か
- 攻撃の種類、それが新しいものか
- 標的型かどうか
- 行為者（攻撃者）は誰か

notable TTPsは以下を基準に選定する:
- 新しいTTP
- 流行しているTTP
- 検出が困難など高度なTTP
--------

[出力形式]
markdownとして編集可能なファイルで取得したいため、以下のようにmarkdownのコードブロックでくくってください。

` ` `markdown
レポートを記載
` ` `  
Note: 上のコードブロックはスペースを削除して使ってください

```

## 情報ソース

以下の日時で整理している情報をベースに作成しています。  
https://github.com/proshiba/tech-memo/tree/main/daily-news/news
