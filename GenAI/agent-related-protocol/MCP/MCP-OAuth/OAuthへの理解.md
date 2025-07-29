# OAuthがどう動くかを理解する

そもそも、OAuthがどう動くかを理解するために検証を行います。  
今回、Auth0 + ALBで認証を試しました。  

## OAuthについて学ぶ

まずはOAuthを理解します。  
以下はいくつか書いてますが、正直参考サイトをそのまま書いているレベルです。(自分の理解のために抽出して書いただけ)  
なので、ちゃんと理解したい人は以下の参考サイトをみましょう。個人メモ的に私のメモも残しますが。  

[参考サイト]

- https://qiita.com/TakahikoKawasaki/items/200951e5b5929f840a1f
- https://zenn.dev/edash_tech_blog/articles/5c82b868c7a781

### OAuthのプロトコルフロー

以下の想定で記載します。  
- OAuthClient: cline
- Authorization Server: IAM Identity Center
- ReourceServer: MCP Server

```mermaid
sequenceDiagram
  actor User
  participant Cline as OAuth Client
  participant IdentityCenter as Authorization Server
  participant MCP as Resource Server

  User->>Cline: Open Cline (triggers login)
  Cline->>IdentityCenter: /authorize?client_id&code_challenge
  IdentityCenter->>User: Login & consent screen
  User->>IdentityCenter: Credentials
  IdentityCenter-->>Cline: code + state (302)
  Cline->>IdentityCenter: /token + code + code_verifier
  IdentityCenter-->>Cline: access_token (JWT) + refresh_token
  Cline->>MCP: HTTPS + Authorization: Bearer <access_token>
  MCP->>IdentityCenter: fetch signing keys (caches)
  MCP-->>Cline: 200 OK  (authenticated)
```

以下のサイトが非常にわかりやすいです。  
https://qiita.com/TakahikoKawasaki/items/200951e5b5929f840a1f


以下の図がわかりやすい。  
- **OAuth 2.0 認可 flow**  

![OAuth 2.0 認可 flow](https://qiita-user-contents.imgix.net/https%3A%2F%2Fqiita-image-store.s3.amazonaws.com%2F0%2F106044%2Fd9119f21-736d-d5ed-964d-3068af0fcde9.png?ixlib=rb-4.0.0&auto=format&gif-q=60&q=75&s=f29f173560cb67bd7360018323ca750c)  


認可サーバについて。  
認可サーバは複数の役割があり、 ロールによってアクセス先(APIエンドポイント)が異なる。  

1. 認可エンドポイント: clientからの認可リクエストを受け付ける
2. トークンエンドポイント: アクセストークンの払い出しを行う
3. イントロスペクションエンドポイント: リソースサーバ(認可を受ける側)でのアクセストークン情報を取得


認可エンドポイントには、関連して認可決定エンドポイントがある。  

認可リクエストでは以下のようなリクエストを受け付けている。  

```
GET {認可エンドポイント}
  ?response_type=code            // 必須
  &client_id={クライアントID}      // 必須
  &redirect_uri={リダイレクトURI}  // 条件により必須
  &scope={スコープ群}              // 任意
  &state={任意文字列}              // 推奨
  &code_challenge={チャレンジ}     // 任意
  &code_challege_method={メソッド} // 任意
  HTTP/1.1
HOST: {認可サーバー}
```

認可サーバは以下を返す。  

```
HTTP/1.1 302 Found
Location: {リダイレクトURI}
  ?code={認可コード}        // 必須
  &state={任意文字列}       // 認可リクエストに state が含まれていれば必須
```

トークンエンドポイントのレスポンス

```
HTTP/1.1 200 OK
Content-Type: application/json;charset=UTF-8
Cache-Control: no-store
Pragma: no-cache

{
  "access_token":"{アクセストークン}",       // 必須
  "token_type":"{トークンタイプ}",           // 必須
  "expires_in":{有効秒数},                  // 任意
  "refresh_token":"{リフレッシュトークン}",   // 任意
  "scope":"{スコープ群}"                    // 要求したスコープ群と差異があれば必須
}
```

- **OAuth 2.0 implicit flow**  

トークンエンドポイントからのトークン取得が個別リクエストとして送らなくてもいいフロー。  
認可エンドポイントからのレスポンスに最終的にアクセストークンが渡されている。  

![implicit flow](https://qiita-user-contents.imgix.net/https%3A%2F%2Fqiita-image-store.s3.amazonaws.com%2F0%2F106044%2F743e2d27-512d-f2b8-ee72-1a8c315b7f76.png?ixlib=rb-4.0.0&auto=format&gif-q=60&q=75&s=884f74fe5c5b2007858fc154dd92e277)

implicit flowではリフレッシュトークンは発行されない。  

- **OAuth 2.0 Resource Owner Password Credentials Grant**  

クライアントアプリがID・パスワードを受け取る形。  

![Resource Owner Password Credentials Grant](https://qiita-user-contents.imgix.net/https%3A%2F%2Fqiita-image-store.s3.amazonaws.com%2F0%2F106044%2Ff86d2e7c-6eb8-a4d4-05a8-b6fe367ea25e.png?ixlib=rb-4.0.0&auto=format&gif-q=60&q=75&w=1400&fit=max&s=5f85feaa15fa4a2532c87b71d7b93ee2)

前２つは認可の画面を受け取って、そこで認証させる形(クライアントアプリはこの認証フローを直接処理しない)だった。  
この場合は、リクエストにもユーザ名とパスワードを渡してリクエストする方式になる.  

```
POST {トークンエンドポイント} HTTP/1.1
Host: {認可サーバー}
Content-Type: application/x-www-form-urlencoded

grant_type=password     // 必須
&username={ユーザーID}    // 必須
&password={パスワード}    // 必須
&scope={スコープ群}       // 任意
```

- **OAuth 2.0 Client Credentials Grant**  

ユーザーの認証は行わず、トークンベースでのアプリ認証のみが行われる。  
（事前発行のトークンが使われる)  

![Client Credentials Grant](https://qiita-user-contents.imgix.net/https%3A%2F%2Fqiita-image-store.s3.amazonaws.com%2F0%2F106044%2F60324980-13ea-2138-2f8e-65e980cfccb3.png?ixlib=rb-4.0.0&auto=format&gif-q=60&q=75&w=1400&fit=max&s=c39ed599f76318520269d2327bbe5bc8)

- **OAuth 2.0 Refresh Token Flow**  

事前に発行されているリフレッシュトークンを使う方法。

![Refresh Token Flow](https://qiita-user-contents.imgix.net/https%3A%2F%2Fqiita-image-store.s3.amazonaws.com%2F0%2F106044%2F98fd8730-5007-8ffa-d743-81e951582532.png?ixlib=rb-4.0.0&auto=format&gif-q=60&q=75&w=1400&fit=max&s=279a05b4a197d1976a51c9c8d6fd65b9)


## OAuthを試す

OAuthの場合、どうやらIAM Identity CenterはIdPになれないようですので(間違ってたらごめんなさい)、別を使ってみます。  
まず、Auth0でやってみました。  

これは以下を見るとわかりやすいです。  
https://zenn.dev/edash_tech_blog/articles/5c82b868c7a781

なお、いくつか重要な点を補足します。  
1. IssuerURLの末尾のスラッシュは必須
2. ALBのセキュリティグループで、HTTPSの外部アクセスを許可してください。(トークンの検証用だと思われます)

この２つはどっちも間違えると401 Authorizationエラーになりました。  

## 終わり

OAuthについてはざっくり理解できたいので、このドキュメント自体はこれで終わりです。
