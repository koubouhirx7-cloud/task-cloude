# Railway へのデプロイ手順書

## 📋 概要

このドキュメントでは、「ハイランダー タスク入力システム」を Railway（クラウド環境）にデプロイして、インターネット経由でアクセスできるようにする手順を説明します。

**デプロイ後のアクセス URL:**
```
https://[プロジェクト名].railway.app/task_input.html
```

---

## 🔧 前提条件

- ✅ GitHub アカウント（未取得の場合は https://github.com で作成）
- ✅ Railway アカウント（GitHub で簡単にログイン可能）
- ✅ このリポジトリが GitHub に push されている状態

---

## 📖 Step 1: GitHub にリモートリポジトリを作成

### 1.1 GitHub で新規リポジトリを作成

1. https://github.com/new にアクセス
2. 以下の内容で作成：
   - **Repository name:** `highlander-task-api`
   - **Description:** Highlander Task Input System (Cloud)
   - **Public / Private:** Public（または Private）
3. **Create repository** をクリック

### 1.2 ローカルリポジトリを GitHub に push

```bash
cd ~/Documents/会計情報

# リモートリポジトリを追加
git remote add origin https://github.com/[YOUR_USERNAME]/highlander-task-api.git

# main ブランチに rename（必要に応じて）
git branch -M main

# GitHub に push
git push -u origin main
```

GitHub で確認：ファイルが push されていることを確認

---

## 🚀 Step 2: Railway でプロジェクトを作成＆デプロイ

### 2.1 Railway にアカウントログイン

1. https://railway.app にアクセス
2. **Login** をクリック
3. **GitHub で続ける** を選択
4. GitHub 認証を完了

### 2.2 新規プロジェクト作成

1. Railway ダッシュボードで **New Project** をクリック
2. **Deploy from GitHub repo** を選択
3. GitHub リポジトリを接続
   - 「Authorize Railway」をクリック
   - `highlander-task-api` リポジトリを選択
4. **Deploy Now** をクリック

### 2.3 ビルド・デプロイの確認

- Railway が自動的に以下を実行：
  - ✅ `Procfile` を読み込み
  - ✅ `requirements.txt` から dependencies をインストール
  - ✅ Flask アプリを起動
  - ✅ 自動 HTTPS 設定

---

## 🔐 Step 3: 環境変数を Railway に設定

### 3.1 Railway ダッシュボードで環境変数を設定

1. Railway プロジェクトを開く
2. 左メニューから **Variables** をクリック
3. 以下の環境変数を追加：

```
Discord Webhooks:
DISCORD_WEBHOOK_SECRETARY=https://discord.com/api/webhooks/1503267868412874824/57SnShsbG3lfiFHpjGEESYObxEs8hPR6TQ1DSzMsVxppeRA5EG_ortTofVOH7aQpnTvm
DISCORD_WEBHOOK_FINANCE=https://discord.com/api/webhooks/1503267498374729741/YGIs8vQ0QhDQApER0bEDkrpnleIt8BESZoWkddbBRwCNp76PXndjRhS28i1vwnrqUV6k

ローカル Mac との通信:
LOCAL_WEBHOOK_URL=http://[YOUR_MAC_IP_ADDRESS]:9000/receive_task
（例：http://192.168.50.187:9000/receive_task）
```

> **重要：** `YOUR_MAC_IP_ADDRESS` を実際の Mac の IP アドレスに置き換えて下さい
> 確認方法：ターミナルで `ipconfig getifaddr en0` を実行

### 3.2 Railway の自動 URL を確認

1. プロジェクト設定 > **Domains** を確認
2. 自動生成された URL が表示（例：`https://highlander-task-api-production.railway.app`）

---

## ✅ Step 4: 動作確認

### 4.1 Web ブラウザでアクセス

```
https://highlander-task-api-production.railway.app/task_input.html
```

フォーム画面が表示されることを確認

### 4.2 テストタスク送信

1. ブラウザでタスク送信フォームを開く
2. テストタスクを入力：
   - タスク名：「Railway テスト」
   - 分野：「web」
   - 説明：「Railway クラウドデプロイテスト」
3. **送信** をクリック

### 4.3 ローカル Mac で受信確認

1. ローカル Mac で webhook リスナーを起動：
   ```bash
   python3 task_receive_webhook.py
   ```

2. ブラウザで Railway からテスク送信

3. ローカル Mac のターミナルで以下のログが表示されることを確認：
   ```
   ✅ タスク受信・保存: /Users/murakamidaisuke/Documents/会計情報/tasks/20260511_153206_web.json
   ```

4. `~/Documents/会計情報/tasks/` にファイルが作成されているか確認：
   ```bash
   ls -la ~/Documents/会計情報/tasks/
   ```

### 4.4 完全なワークフローテスト

1. ローカル Mac で webhook リスナーを起動
2. Railway からタスク送信
3. ローカル Mac が受信・保存
4. task_processor.py が自動解析
5. Discord に通知が送信される

---

## 🌐 Step 5: スマートフォン・外部からのアクセス

### デバイスから Railway URL でアクセス：

```
https://highlander-task-api-production.railway.app/task_input.html
```

- 🔒 **HTTPS で保護**（自動）
- 📱 **モバイル最適化済み**
- 🌍 **インターネット経由でどこからでもアクセス可能**
- 🚀 **24/7 稼働**

---

## 🔧 トラブルシューティング

### 問題 1: Railway のビルドが失敗

**原因:** `requirements.txt` が見つからない

**解決:** リポジトリのルートに `requirements.txt` があることを確認

```bash
ls -la ~/Documents/会計情報/requirements.txt
```

### 問題 2: Railway 上でエラーが発生

**原因:** 環境変数が設定されていない

**解決:** Railway ダッシュボードの **Variables** で設定を確認

### 問題 3: ローカル Mac で受信できない

**原因:** `LOCAL_WEBHOOK_URL` が正しくない、またはファイアウォールでポート 9000 が遮断されている

**解決:**
1. Mac の IP アドレスを確認：`ipconfig getifaddr en0`
2. Railway の `LOCAL_WEBHOOK_URL` を更新
3. Mac のファイアウォール設定でポート 9000 を開放

### 問題 4: "Connection refused" エラー

**原因:** ローカル Mac の webhook リスナーが起動していない

**解決:** 以下のコマンドで webhook リスナーを起動

```bash
python3 ~/Documents/会計情報/task_receive_webhook.py
```

---

## 📊 監視・ログ確認

### Railway のログを確認

1. Railway ダッシュボード > **Logs** をクリック
2. リアルタイムでアクセスログ・エラーを確認

### ローカル Mac のログを確認

```bash
# webhook リスナーのログ
python3 task_receive_webhook.py

# task_processor のログ
python3 task_processor.py
```

---

## 🔄 Code Update 後の再デプロイ

1. ローカルで変更をコミット：
   ```bash
   git add .
   git commit -m "Fix: update Flask endpoint"
   ```

2. GitHub に push：
   ```bash
   git push origin main
   ```

3. Railway が自動的に再デプロイ（数分で完了）

---

## 📚 参考リンク

- Railway 公式ドキュメント：https://docs.railway.app
- Flask ドキュメント：https://flask.palletsprojects.com
- Gunicorn ドキュメント：https://gunicorn.org

---

## 💡 Tips

- **カスタムドメイン設定：** Railway で独自ドメインを設定可能（有料）
- **環境分離：** 本番環境とステージング環境を分離可能
- **CI/CD：** GitHub Actions で自動テスト・デプロイを実装可能
- **スケーリング：** Railway は自動スケーリング対応

---

## ❓ サポート

何か問題が発生した場合：

1. Railway のステータスページを確認：https://status.railway.app
2. Railway コミュニティに質問：https://discord.gg/railway
3. このプロジェクトの Issues を確認
