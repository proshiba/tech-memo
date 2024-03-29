# 2022年第3四半期のレポートを見てみる

2022年7月1日から9月30日の期間における統計データを出してくれてるのがあったので、確認していきたいと思います。  
ちなみに、今回は2つ紹介していきます。

1 Quarterly Report: Incident Response Trends in Q3 2022（Cisco Talos）
  - https://blog.talosintelligence.com/quarterly-report-incident-response-trends-in-q3-2022/

cisco社の脅威インテリジェンスチーム「talos」が観測した脅威情報に関するレポートです。  

2 インターネット定点観測レポート（JPCERT）
  - https://www.jpcert.or.jp/tsubame/report/report202207-09.html

JPCERTがTSUBAME（インターネット定点観測システム）で観測したデータです。

cisco talosが出してくれているデータは全般的な攻撃に関するトレンド、JPCERT
JJPCERTが紹介してくれているデータはハニーポットで観測されたデータになるため、切り口は大きく変わります。  

### Cisco Talosレポート

##### Q3ではランサムウェア関連の攻撃が40％発生

ランサムウェアとpre-ransomware(ランサムウェア事前活動)で併せて40％とのことですね。  
どうやら、ランサムウェア事前活動についてはCobaltStrikeやMimikatzの利用などからランサムウェアアクターの活動と考えてるようです。  
どっちもこれだけだと普通に別の攻撃でもありそうですけどね？まぁtalosが言うのだから書いてないだけで他の観点なども含めた総合判断なんでしょうね。  

![Q3でのトレンド・ターゲット](https://blog.talosintelligence.com/content/images/size/w1000/2022/10/TopThreats-dark.jpg)  
引用元：https://blog.talosintelligence.com/quarterly-report-incident-response-trends-in-q3-2022/  

##### 攻撃ターゲットのトップが教育機関

ViceSocietyのようなランサムウェアグループが教育機関を狙って攻撃してますし、まぁ納得できる感じですね。。  

![Q3でのトレンド・ターゲット](https://blog.talosintelligence.com/content/images/size/w1000/2022/10/Target-dark.jpg)   
引用元：https://blog.talosintelligence.com/quarterly-report-incident-response-trends-in-q3-2022/  

ちなみに教育機関が攻撃される理由は何なのか？についてtalosとしては不明、としてます。実際攻撃しても金になりがたいのではっきりとわからないですよね。。  

ただ、アカウントセキュリティがまともに保護されずに放置されているものが多い、など狙いやすいという理由があるのではないか、という話もありましたね。  

実際、理由は難しいですが、狙われていることだけは確かです。少なくともしばらくは教育機関は特に注意しないといけないですね。。

##### その他

その他、ランサムウェアに関する様々な攻撃活動や利用されるツールの情報などがまとまっています。  
個人的に、使ってみようと思うものが多いのですが、全然触れてないなぁ。。と思わされますね。(sliverとか)  

また、初期アクセスとしてアカウント管理の不備などが大きく取り上げられてます。IABなどが活発に動いている今の時代を感じますね。  
とはいえ、RDP等でのブルートフォース対策機能がリリースされたことでちょっとは改ざんされると信じたいです。（まぁアカウントが放置されている環境ではアップデートもおざなりになってる懸念がありますが。。）  

##### 対策

対策にまずMFAが出てるのはわかりやすく重要ですね。  
最近、SIMスワッピング攻撃やMFA疲労攻撃などあるにしてもMFAは有効な対策です。

### JPCERT レポート

こちらは定点観測における攻撃通信のトレンドです。  
分野は違いますが、いい情報なので見ていきましょう。

##### 様々な観点での通信分析

- ポート別  

telnetの攻撃通信が引き続き多く検出されているようですね。  
私はちょっと意外なのですが、sshとかHTTPよりtelnetが多いんですよね。  
しかも、かなり差があります。  

![ポート別](https://www.jpcert.or.jp/tsubame/report/img/2022Q2-20220701-20220930_01.png)
引用元：https://www.jpcert.or.jp/tsubame/report/report202207-09.html

他に地域別ではアメリカが1位で2位がロシアですね。  
ロシアは通信が増えて中国を抜いて2位になったようですが、killnetの影響で通信増えたりはしてないのですね。  
※killnetのDDoS攻撃が9月にあったので。  

まぁ、ターゲットを絞ってDDoSしてるでしょうからね。インターネット上にあるセンサーで検出できるものではない、て感じですよね。  

こういうのは私はあまり見てこなかったですが、ネットワーク全体としての傾向を見るのにはよさげですね。  

### 終わりに

2つのレポートを合わせて見ましたが、振り返りにとてもいいですね。  
今後も定期的に見ていきたいと思います！

それでは、今回は終了としますー。ありがとうございました！
