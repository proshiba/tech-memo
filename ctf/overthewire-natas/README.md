# overthewire natas に関するメモ  

以下のOver The WireというCTFでnatasというタイプをやった結果のメモを書きます。    

https://overthewire.org/wargames/natas/

## natasとは？  

natasはoverthewireの中でも初歩的なweb系のCTFです。  
ちなみに細かいwrapupは以下に書いてます。勉強目的で英語で書いてます。  
https://github.com/proshiba/wrapups/tree/master/ctf_overthewire/natas


### この記事で書くこと  

この記事ではザクっと何をしてそれぞれ解いたか書いていきます。  
また、対象はlv0からlv09までです。  
natasは、lv0からlv33までありますので、続きはまた別に書いていきます。  

### lv00
最初です。webページのソースを見ればわかります。  

-----

### lv01
lv00と同じですが、右クリックが防止されてます。  
curl、lynx、ブラウザの開発ツールなどソースが見れるものを使えば解決します。  

-----

### lv02

開発ツールなどを使ってwebページアクセス時の挙動を見ると以下へのアクセスの存在が見れます。  
`http://natas2.natas.labs.overthewire.org/files/pixel.png`

このURIは`files/`の下であり、同ルート内のファイルを見てみると解決します。  

-----

### lv03

robots.txtを見てみたところ、以下の存在が確認できました。  
`Disallow: /s3cr3t/`  

このルートを見て解決しました。  

-----

### lv04

アクセスすると、アクセス元が制限されている旨のメッセージが出ました。  

> Access disallowed. You are visiting from "" while authorized users should come only from "http://natas5.natas.labs.overthewire.org/"

このため、refererを指定してアクセスして解決しました。

curl http://natas4.natas.labs.overthewire.org -u natas4:Z9tkRkWmpt9Qr7XrR5jWRkgOU901swEZ -H Referer:http://natas5.natas.labs.overthewire.org/

-----

### lv05

アクセスすると、ログオンが必要と記載されている旨のメッセージが出ました。  

> Access disallowed. You are visiting from "" while authorized users should come only from "http://natas5.natas.labs.overthewire.org/"

しかし、ログオンするようなものもなく、dirbで見てもそれらしいログオン関連のページはありませんでした。  
ヘッダを確認しCookieを見てみたところ、`loggedin=0`というものがあったため、1に変更してアクセス(開発ツールで編集して再送)したところ、解決しました。

-----

### lv06

secretを入力しろと出ているページになりました。  
なんとなく、a||trueとかで行けたりするかと思いましたが、それはNG。  
で、ソースをもう一度見てみた結果、secretが書かれていると思われる以下のファイルを直接確認。  
`includes/secret.inc`

これで解決しました。  

-----

### lv07

アクセスすると、以下2つのリンクが存在しているだけのページ。  
- Home
- About

また、ページのソースに以下が存在。  
hint: "password for webuser natas8 is in /etc/natas_webpass/natas8"

このページリンクは、クエリパラメータの`page`を利用している状態。
`http://natas7.natas.labs.overthewire.org/index.php?page=Home`

このpageを使ってファイルアクセスが可能ではないかと考え、../../../../etc/省略のような形でアクセスし、解決しました。  

-----

### lv08

secretを入力する問題であるが、encodeされたシークレットとのチェックとエンコード関数の内容が判明している。  
```php
$encodedSecret = "3d3d516343746d4d6d6c315669563362";
function encodeSecret($secret) {
    return bin2hex(strrev(base64_encode($secret)));
}
```

そのままひっくり返してデコード関数を使って解決しました。  
```php
function dec($dec) {
    return base64_decode(strrev(hex2bin($dec)));
}
```

-----

### lv09

以下のラベルによる入力のみが存在するページ。  

`Find words containing`

このページのソースを見ると以下のようになっていることが判明。  
```php
if(array_key_exists("needle", $_REQUEST)) {
    $key = $_REQUEST["needle"];
}

if($key != "") {
    passthru("grep -i $key dictionary.txt");
}
```

そのままOSコマンドを使っているため、インジェクションが可能。以下のように行い、passwdのnatas10に関する記載も判明。  
`natas10 /etc/passwd ||`

このあと、以下のようにして/etcのファイルを確認。  
`a|| ls -la /etc ||`

natas_passとnatas_webpassがあり、この中のnatas10を見て解決しました。  


いかがでしたでしょうか？
ちなみに私はこれらをやったのは3年前で思い出しながら肩慣らしぐらいの気持ちでやってましたが、ほんとに覚えてなくて苦労しました。。  
※私はこういう系は業務でやらないので、プライベートでやるようにしていかないとすぐに忘れてしまいますね。。  

やってみて思うのはとても重要な内容であることを知れるのと同時に、継続しないと自分の力にならないことを感じます。  

この先もやっていきますが、他のCTFも進めながらのんびりやっていきます。  

### それでは終了します！ありがとうございました！


