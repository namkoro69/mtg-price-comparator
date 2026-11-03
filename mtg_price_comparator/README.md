# MTG売却価格比較 Webアプリ v0.2

iPhone・Mac・Windowsのブラウザから使えるStreamlitアプリです。

## 公開する方法（Streamlit Community Cloud）

1. GitHubで新しいリポジトリを作り、`app.py`、`requirements.txt`、`.streamlit/config.toml`をアップロードします。
2. https://share.streamlit.io/ からGitHub連携し、リポジトリを選択します。Main file path は `app.py` に設定しDeployします。
3. 発行された `https://...streamlit.app` のURLをiPhone・Mac・Windowsで開きます。iPhoneではSafariの「ホーム画面に追加」でショートカット化できます。
4. 自動検索を使う場合、https://serper.dev/ でAPIキーを取得します。Streamlit Cloudのアプリ設定→Secretsに `SERPER_API_KEY = "取得したキー"` を登録します。API料金・無料枠は公式サイトで確認してください。

**重要：** 公開URLを知る人がアプリを開ける設定になる場合があります。秘密情報・個人データをコードやGitHubへ書かないでください。GitHubにはAPIキーをアップロードしないでください。

## PCでローカル実行

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 仕様・制限

- カード名、セット、言語、Foil、枚数で検索条件を指定。
- Serper APIを使いGoogleの公開検索結果に含まれる「円」表記を価格候補として抽出（**未確認**）。
- 晴れる屋・カードラッシュの買取ページとメルカリ・Yahoo!フリマへのリンク。
- 確認済みの価格を手入力して、手数料・送料等を控除した手取りを比較。
- CSVダウンロード。
- サイト本体の自動スクレイピングは行いません。出品価格と成約価格、販売価格と買取価格の自動判別も未対応です。
- 同名カードの別セット・言語・状態の照合は未対応です。検索結果の価格候補は誤認識や古い価格を含むため、必ず現物と各サイトで照合してください。
- フリマの手数料率は例示値です。各サイトの最新条件を確認してください。
- 入力データは永続保存されません。CSVで保存してください。
