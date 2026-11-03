# AIによるログ分析と原因・対処方法の提案

PythonとStreamlitで作った、OpenAIのAIにログを読ませて障害調査を支援する個人制作アプリです。
原因候補だけでなく、根拠となるログ行と次に確認することを表示します。

## 制作の目的

インフラ・運用の経験を、AIを使ったアプリ開発に結び付けるポートフォリオとして制作しました。
株式会社ルートゼロへの応募を念頭に、参照チャットで紹介されたAI関連開発・運用経験という観点を踏まえています。同社の公式製品ではありません。
生成AIを開発支援にも使用し、画面は制作者の希望に沿って調整しています。

## 機能

- ログの選択・貼り付け・UTF-8テキストファイルの読込み
- ログ行数、ERROR等・WARNの件数を表示
- 一部の秘密情報を伏せ字にした送信内容のプレビュー
- OpenAI APIによる原因候補・根拠行・確認手順の生成
- 解析完了と使用モデル名の表示
- Markdown形式のレポート保存

**画面はAI解析専用です。APIキーが必要で、解析ボタンを押すたびにAPIを利用します。**
キー未設定・接続失敗時に、ルールの結果をAIの回答として代わりに表示することはありません。
内部にはAPI不要のルール処理をテスト用として残していますが、画面からは使用しません。

## 起動手順（Mac）

Python 3.13を推奨します。Cursorなどの専用エディタは不要です。
このREADMEがあるフォルダにターミナルで移動し、次を実行します。

```sh
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

最初の1回だけ、設定ファイルを作って編集します。

```sh
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
vi .streamlit/secrets.toml
```

すでにsecrets.tomlがある場合はコピーせず、既存ファイルを使ってください。

```toml
OPENAI_API_KEY = "自分のキーをローカルで設定"
OPENAI_MODEL = "利用権限のあるモデルID"
```

APIキーをチャットやGitHubに貼らないでください。
モデルはResponses APIとStructured Outputsへの対応、利用権限、料金を確認して指定します。
環境変数OPENAI_API_KEY・OPENAI_MODELでも設定でき、環境変数が優先されます。
.envは自動では読み込みません。旧版のENABLE_LLMは不要で、残っていても参照しません。

```sh
python -m streamlit run app.py --server.address 127.0.0.1
```

ブラウザで `http://localhost:8501` を開きます。停止はControl+Cです。

## 操作とサンプル

「分析用ログを選ぶ」からログを選び、内容と「AIに送るログを確認」を見て「ログを解析」を押します。
同梱ログはすべて架空です。実際の設定変更・復旧操作をアプリが行うことはありません。

| サンプル | 想定した状況 |
|---|---|
| 接続タイムアウト | 接続先ポートの不一致、修正後の復旧 |
| ディスク逼迫 | 容量不足による書込み失敗、容量拡張後の復旧 |
| 認証失敗 | 資格情報の期限切れ、有効な情報への切替後の復旧 |
| 通常ログ | 60秒間の観測範囲で障害の兆候なし |

[答え合わせと評価方法](docs/scenarios.md)に、想定正解と根拠行を記載しています。
この資料はAIへ送信せず、ログだけを送ります。
入力を変更した場合、以前の結果は表示しません。ファイルを選んだ場合はファイル内容を優先します。

## APIの料金とデータの取扱い

ChatGPT Plusの契約とAPIの認証・課金は別に確認が必要です。
API側のクレジット・特典の適用条件は自身のアカウントで確認してください。
[OpenAI公式料金表](https://developers.openai.com/api/docs/pricing)、[ChatGPT側の説明](https://learn.chatgpt.com/docs/pricing)を参照してください。

概算は `入力トークン数÷100万×入力単価 + 出力トークン数÷100万×出力単価` です。
実際の費用はモデルと処理量により変わり、失敗時にも料金が発生する場合があります。
アプリを開くだけではAPIを呼びません。解析を押したときだけ呼び、勝手な再試行はしません。

- 個人情報や機密情報を含むログは入力しないでください
- メール・IPv4・一部のパスワード等を伏せ字にしますが、完全な匿名化ではありません
- 入力は24,000バイト・200行まで。出力上限2,200トークン、タイムアウト30秒
- アプリから入力をファイルやDBに保存せず、明示的にログ出力しません。ブラウザのセッションには入力・結果が残ります
- レポート保存時には端末にファイルができます。内容を確認してから共有してください
- APIはstore=Falseで呼びますが、サービス全体のゼロ保持を保証する設定ではありません
- ログ内の命令に従わないようAIに指示し、コマンド実行などの機能を与えていません。攻撃への完全な耐性は保証できません

## 限界と公開について

根拠行が存在していても、AIの解釈が正しいとは限りません。監視情報・設定変更履歴などと照合して判断します。
重要度はAIの提案であり業務影響の計測値ではありません。正常ログもシステム全体の正常性を保証しません。
認証・利用回数制限・監視連携・自動復旧は未実装です。
**現状は自分のMacで使用してください。共有キーを設定したままインターネットに公開しないでください。**
Web公開するなら、認証と費用・利用回数の制限を追加する必要があります。

## テストと構成

```sh
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

入力制限、伏せ字、根拠行、不完全なAPI応答、画面操作、キー未設定、失敗時の表示などを検証します。
APIは模擬応答を使うためテストで料金はかかりません。実APIの接続と回答品質は別途確認が必要です。
[検証記録](docs/verification.md)に確認範囲を記載しています。

```text
app.py              画面とAPI呼出し
analyzer.py         入力検証、伏せ字、構造化出力、レポート
samples/            架空ログ4種類
tests/              API不要の自動テスト
docs/               検証記録、シナリオの想定正解
.streamlit/         表示設定と秘密情報の設定雛形
.github/workflows/  GitHub Actionsでのテスト
```

OpenAIの[Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)とPydanticで結果の構造を検査し、存在しない根拠行はエラーにします。
依存関係は互換範囲指定です。StreamlitのDeployとメニューは画面用のCSSで隠しています。Streamlit更新で表示構造が変わる場合は再確認します。

## GitHubへの公開手順

GitHubへのアップロードはこの成果物の作成時には行っていません。
GitHubで空のリポジトリを作り、**このREADMEのあるフォルダ**で実行します。親のCodexフォルダ全体を登録しないでください。

```sh
git init -b main
git add app.py analyzer.py requirements.txt requirements-dev.txt README.md .gitignore .env.example .streamlit/config.toml .streamlit/secrets.toml.example samples tests docs .github
git diff --cached --stat
git diff --cached
git check-ignore .streamlit/secrets.toml
python -m pytest -q
git commit -m "Build AI log analysis app"
```

登録内容にキー・個人情報・実務ログがないことを確認します。
続いてURLを自身のGitHubリポジトリのものに置換して実行します。

```sh
git remote add origin https://github.com/YOUR_USERNAME/ai-incident-log-analyzer.git
git push -u origin main
```

一度でもキーを公開した場合は削除だけでは不十分です。キーを失効・再発行してください。
コードを公開することと、動くWebアプリを公開することは別です。

## 応募時に説明すること

制作目的、画面や設計で工夫した点、生成AIを開発支援に使った範囲、実際に試したログとAIの結果、改善したい点を自身の言葉で説明してください。
「架空ログの検証シナリオで確認」と「実業務の障害を解決した実績」を区別します。
実APIで確認していない内容や、GitHub公開前のURLを実績として記載しないでください。
