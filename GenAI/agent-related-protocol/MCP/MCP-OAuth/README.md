# MCPでのOAuthを試したい

OAuthでの認証・認可をMCP Server間で行いたいと思います。  

## MCPサーバは開発環境では一旦HTTPにする

まず、OAuthの認証を行うとしても、ローカル開発環境ではHTTPにします。  
理由は、簡単にHTTPSにできないからです(わからないとも言います)。  
python sdkを使う際に証明書情報などを渡すやり方が少なくともmcp.runで起動する際になく(これはfunctionの引数になかった)、さらにuvicornを別途動かすとしてもその際にsseモードで動かす方法が分からなかったからです。  

本番環境はALBなどによるHTTPSを介するとして、ローカルはHTTPでやってみます。  

## MCPにおけるOAuth

まず、以下が公式のドキュメントです。  
https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization

これと、以下の公式サンプルMCPサーバを見てみましょう。  
[python-sdk/examples/servers/simple-auth/mcp_simple_auth/server.py](https://github.com/modelcontextprotocol/python-sdk/blob/main/examples/servers/simple-auth/mcp_simple_auth/server.py)


まず、MCPサーバはRFC 9728を使われます。あわせて、認可コードの横取り対策のためにchallengeを使った検証(PKCE)の組み込みが必須です。  
https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization

```mermaid
sequenceDiagram
    participant Client
    participant ResourceServer
    participant AuthorizationServer

    %% ステップ 1: アクセストークンなしのリクエスト
    Client->>ResourceServer: リソース要求 (アクセストークンなし)
    ResourceServer-->>Client: 401 Unauthorized<br/>WWW-Authenticate: resource_metadata=url

    %% ステップ 2: メタデータ取得
    Client->>ResourceServer: GET /.well-known/oauth-protected-resource
    ResourceServer-->>Client: JSON metadata (resource, authorization_servers, jwks_uri …)

    %% ステップ 3: 認可サーバメタデータ取得
    Client->>AuthorizationServer: GET /.well-known/oauth-authorization-server
    AuthorizationServer-->>Client: AS metadata (authorization_endpoint, token_endpoint …)

    %% --- PKCE 開始 ---
    Note over Client: code_verifier ← ランダム 32byte 生成<br/>code_challenge = BASE64URL(SHA256(code_verifier))
    
    %% ステップ 4-A: 認可リクエスト (ブラウザ)
    Client->>AuthorizationServer: GET authorization_endpoint?<br/>  client_id &response_type=code<br/>  redirect_uri=...<br/>  scope=…&code_challenge=code_challenge<br/>  code_challenge_method=S256
    AuthorizationServer-->>Client: 302 redirect_uri?code=AUTH_CODE&state=…

    %% ステップ 4-B: トークンエンドポイント (PKCE 検証)
    Client->>AuthorizationServer: POST token_endpoint<br/>  grant_type=authorization_code<br/>  code=AUTH_CODE<br/>  redirect_uri=…<br/>code_verifier=...
    AuthorizationServer-->>Client: { access_token, id_token, … }

    %% --- PKCE 検証完了 ---

    %% ステップ 5: アクセストークン付きリソース要求
    Client->>ResourceServer: リソース要求<br/>  Authorization: Bearer access_token
    ResourceServer-->>Client: リソースレスポンス
```

## python-sdkにあるauthentication用のClientを試す

この件、いろいろ試そうとしていましたがClineとかで動かすことができず、よくわからない。。となりました。  
そのため、python-sdkにある以下のサンプル用Clientを試してみたいと思います。  
ちなみに、この際にサーバも上記したサンプルのAuth Serverを利用しています。  

- Client: https://github.com/modelcontextprotocol/python-sdk/tree/main/examples/clients/simple-auth-client
- Server: https://github.com/modelcontextprotocol/python-sdk/blob/main/examples/servers/simple-auth

これで試すと、サーバ側で確かにauthentication(らしき動き)が発生していることがわかります。  

ちなみにまともに動くものではないので、あくまでサンプル用ですね。  

![oauth-sample](./images/oauth-sample.png)

これを見ると、ちゃんと401が返され、その後にauthorizationサーバへの情報をmetadataから取得するようになっていますね。  

## 個人的な感想

私はMCP Serverにauthenticationをつける場合は、今の所ALBでやろうかな、と思っています。  
どっちにしてもMCP Serverを自前で建てる場合はAWSのECSを使うつもりですし。  
HTTPSにすることも含め、その方が楽でいいな、と感じています。  
