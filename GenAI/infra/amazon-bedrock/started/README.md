# Amazon Bedrockを試す

AWS(AmazonのIaaS)では、Bedrockという生成AIのサービスがあります。  
今回は、これを使ってみたいと思います。

## 参考元のサイト

そもそもですが、これは既に詳しくご説明されている方がいて、そちらをみてもらった方がいいです。  
以下とか参考になりますので、ぜひみてみてください。  

[Slack×Amazon Bedrock　Slack上にチャットbotを作ってみた](https://business.ntt-east.co.jp/content/cloudsolution/column-556.html)

### 実際に、ここで記載されているものに関連した作業

個人的なメモの意味合いを含め、以下の通り残します。  

- region: us-east-1
- model: Claude 3.5 Sonnet v2
- Agent:
    - name: 任意
    - system prompt: 以下を参照
    - User input: ENABLED
    - Alias:
        - ID: U7MUWNHITH
        - Name: SecurityAgent

推論モデルを試したかったので、Sonnet v2にしました。

- **system prompt**
```
あなたはサイバーセキュリティに関するプロフェッショナルです。
ユーザーに対し、セキュリティにおける推奨事項を回答してあげてください。
もし、ユーザーの質問がITに関するものではなく、サイバーセキュリティの文脈で応答できないものである場合、その旨を応答して適切なエージェントの利用を促してください。
```

ということで、以下のAgentが作成できました。  
![security-agent-capture](./images/security-agent-capture.png)

### ChatBot

これを使い、Amazon Q Developer(旧: AWS Chatbot)でSlackと接続しました。  
- Slack Channel: aws-bedrock-tests-2
- connector名: bedrock

![chatbot-capture](./images/chatbot.png)

これで以下のようなコマンドでコネクタを接続しました。  
- command: @Amazon Q connector add {connector名} {bedrockAgentのARN} {AliasID}

実際のコマンドは以下です。Account IDのところだけマスクしています。
```
@Amazon Q connector add bedrock arn:aws:bedrock:us-east-1:**mask**:agent/G7COXCUZE5 U7MUWNHITH
```

![chatbot-add-capture](./images/chatbot-add.png)

さて、これで実際にSlackで質問したところ、正しく応答が返ってきました。  

![chatbot-ask-capture](./images/chatbot-ask.png)

## 追加で説明

さて、いくつか追加の情報を記載します。  

### IAMポリシーについて

チャット応答以外の権限は与えたくなかったので、以下のIAMポリシーを作成して割り当てました。

```json
{
	"Version": "2025-07-15",
	"Statement": [
		{
			"Sid": "VisualEditor0",
			"Effect": "Allow",
			"Action": [
				"bedrock:InvokeAgent"
			],
			"Resource": "*"
		}
	]
}
```

### ログ

まず、Chatbotを使ってのアクセスであれば、デフォルトで作ればChatbotのInvokeAgentなどの操作ログがCloudWatchに残ります。  

![chatbot-log](./images/chatbot-log.png)

ただ、ここではinput内容がログに残りません。まぁ残らない方がいいとは思いますが、デバッグ時は違いますよね。  
そういう時、以下のようにsettingsでログ取得を有効にできます。  

![bedrock-agent-log-config](./images/bedrock-log-config.png)

実際に設定すると以下のようにログが取れます。  
推論処理のログも入っていますね。

![bedrock-agent-log](./images/bedrock-log.png)

### システムプロンプトを変えたい時

ちょっと詰まった時の情報を追加しておきます。  
私は、最初にジョーク系のエイリアスを作った後、システムプロンプトの変更をしました。  
しかし、その結果が反映されないという状況が起きました。  
確認したところ、変更後に再度「prepair」を押してあげないと行けないことがわかりました。正直、saveした時点で反映されて欲しい感はありますが、そうではないようですね。  

![system-prompt-change](./images/bedrock-systemprompt-change.png)

## 最後に

この内容はとりあえず試したってだけです。  
実際、bedrockとMCPの連携などは個別に試したいと思って今個個別に試したいと思っています。  
これらができたら再度情報をアップしたいと思いまアップしたいと思います。
