# Azureでログ解析(pt1:LogAnalytics編)


私のブログサイトはAzure上でWordPressを動かしている。  
で、Azureにはログを解析するためのSIEMとしてSentinelがあり、監視機能としてAzure Insights(Azure Monitor)がある。  
なので、これを使って見たい！  

ということで、私のサイトのアクセスログその他をSentinelで解析させてみようという話となる。  
ただ、内容はかなり長くなりうると思うため、まず本記事ではLogAnalyticsでログの可視化までを記載する。  

[雑談はいらねーからコスト管理の設定だけ見たい！て人はクリック](#anchor1)  

## まずはAzureの構成に関する説明  

Azureでは、LogAnalyticsというモジュールがある。  
これはいってみればログ管理ツールであり、ログの収集と別システムへのログ送信などが行える。  
このログをAzure Insightsなどといったもので監視することとなる。  
![AzureImage](https://docs.microsoft.com/ja-jp/azure/azure-monitor/media/overview/overview.png)
参考: https://docs.microsoft.com/ja-jp/azure/azure-monitor/agents/data-sources

このログの収集と検索ができるLogAnalyticsや監視機能であるInsightsなどを統合した大きな機能がAzure Monitorとなる。（らしい）  

補足:書いてる人はなんとなく自分の理解を書いていますが、Azureは触り始めたばかりで**素人レベル**です。なので**間違ってるかも**、ということをご理解ください。

<div id="anchor1" />
## ログの取り込みをおこなう

まずは、簡単にデータソースの仮想マシンに接続する。  
データソースのVirtual Machinesで該当ホストをクリックし、接続する、をクリックすると接続できる。  
![LogAnalyticsの設定](https://raw.githubusercontent.com/proshiba/tech-memo/main/azure/images/loganalysis01.png)

個人的には、これでaccessログの取り込みができる！はっぴー！となったりするのか！？と期待したがそうはならなかった。  

さて、ということで次にログの取り込み設定を行う。
方法は、いくつかありそうであるが、カスタムログの取り込みでいってみよう！  

まずは、LogAnalyticsで検索し、LogAnalyticsワークスペースに移動。そこで以下のようにカスタムログの設定を開き、カスタムログの追加をクリックする。  
![設定を開く](https://raw.githubusercontent.com/proshiba/tech-memo/main/azure/images/loganalytics01_01.png)

カスタムログの追加をする上で、まずはサンプルログのアップロードを求められる。  
私は、access_logを取り込みたいのでこれをアップロード。  
![サンプルの取り込み](https://raw.githubusercontent.com/proshiba/tech-memo/main/azure/images/loganalytics01_02.png)

つぎに、レコードの区切りは改行を選択し、先に進む。  
つぎに、ログのコレクションパスを指定する。ここではaccess_logの保管場所なので、/var/log/httpd/access_log(デフォルト)を指定。  
![サンプルの取り込み](https://raw.githubusercontent.com/proshiba/tech-memo/main/azure/images/loganalytics01_03.png)

最後にカスタムログ名を指定して、作成・保存で完了となる。  
![カスタムログ名の指定](https://raw.githubusercontent.com/proshiba/tech-memo/main/azure/images/loganalytics01_04.png)

作成後、作成したカスタムログの取り込み設定が一覧に表示されている。  
![カスタムログの一覧表示](https://raw.githubusercontent.com/proshiba/tech-memo/main/azure/images/loganalytics01_05.png)

実際に取り込まれ、ログを見ることができるまでは少々時間がかかる。少し待った上で以下のようにログを見ることができる。  
![ログ内容](https://raw.githubusercontent.com/proshiba/tech-memo/main/azure/images/loganalytics01_06.png)

これで、ログの取り込みは行えた。
さて、次はSentinelでログの調査を行おう。ありがとうございました！  
