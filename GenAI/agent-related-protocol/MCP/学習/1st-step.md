# MCPプロトコルとは何か

生成AIはもはや誰でも使っているようなものになりつつありますが、その中でもここ最近はエージェントが非常に注目されていますね。(2025-06の話)  
そんな中、MCPというプロトコルが注目を集めています。しかし、MCPについて何も知らないため、最低限のことは理解できるようにしたいと考えここにまとめます。  


## MCPの3つの要素

MCPサーバはMCPクライアントから以下の機能を持っています。
1. Tool: MCPサーバで特定の操作をすることを許します
2. Resource: MCPサーバが持つデータなどリソースへのアクセスを許可します
3. Prompt: MCPサーバの操作を効果的に行えるようにするためのPromptを提供します
4. Image: 画像データを処理するクラス
5. Context: ツールとリソースに MCP 機能へのアクセスを提供
6. Completion: プロンプト引数とリソーステンプレートパラメータの補完候補の提供をサポート
7. Elicitation: Tool実行中にユーザーから追加情報を取得

## 認証

MCPプロトコルでは、認証・認可にはOAuth 2.1への準拠が明記されています。   
正規のMCP Python sdkもOAuth認証用の機能がありますね。  

## お試し

以下のチュートリアルがありますのでこれでお試ししてみましょう。  
https://modelcontextprotocol.io/quickstart/server

これで試すと、標準入出力で天気情報を聞く最低限の機能が搭載できます。  

さらに、トランスポートをSSEにしてみます。  

- Client側の設定

```json
{
  "mcpServers": {
    "weather": {
      "autoApprove": [],
      "disabled": true,
      "timeout": 60,
      "url": "http://127.0.0.1:8000/sse",
      "transportType": "sse"
    }
  }
}
```

- サーバ側の追加コード

```python
def main(transport: str, port: int, host: str) -> None:
    """Main function to run the MCP server."""
    if transport == "sse":
        mcp.settings.host = host
        mcp.settings.port = port
        print(f"Running MCP server on {host}:{port} using SSE transport...")
        mcp.run(transport='sse')
    elif transport == "stdio":
        mcp.run(transport='stdio')
    else:
        raise ValueError("Unsupported transport method. Use 'sse' or 'stdio'.")
```

これでMCPサーバを動かす準備はある程度完了です。  

さて、それでは、VirusTotalへのアクセスをMCP経由で試してみましょう。  

### VirusTotalへのアクセスをMCP経由にしてみる

以下を作ってみました。  
https://github.com/proshiba/vt-mcp-server

ちなみに、MCPサーバはmcpmarketとかあるので、わざわざ作らずにそれを使うのもありです。  
とはいえ怖いので今のところ私は使ってませんが(怪しいものがありそうなので)。  

内容は、VirusTotalへのAPI呼び出しをMCP経由にして、IP・ドメインなどのレピュテーションを取得できるようにしました。  

```python
@mcp.tool()
async def get_ip_reputation(ip_address: str) -> str:
```

みたいなfunctionを作る形ですね。これで、MCPにおけるtoolとして呼び出せます。  

## トランスポートレイヤについて

現在、トランスポートプロトコルとしてはstdio(標準入出力)とSSE、StreamableHTTPがサポートされています。
元々は、stdioとSSEだけでしたが、その後にStreamableHTTPが追加、現在はstdioかStreamableHTTPが推奨のようです。

## 今後

このドキュメントは一旦ここで終わりにします。次回はAWSのMCPなどを試したいと思います。  
