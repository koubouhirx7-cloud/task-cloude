# 🚀 最終デプロイステップ（ユーザー実施）

## 準備完了状況

✅ コード実装：完了
✅ GitHub push：完了
✅ GitHub Actions 設定：完了（自動デプロイ用）
⏳ Vercel デプロイ：以下の手順を実施
⏳ Railway デプロイ：以下の手順を実施
⏳ 環境変数設定：以下の手順を実施

---

## 🌐 Step 1: Vercel にデプロイ（5分）

### 1.1 Vercel ダッシュボードにアクセス

1. https://vercel.com にブラウザでアクセス
2. ログイン（既存アカウント）
3. **Dashboard** を表示

### 1.2 GitHub リポジトリをインポート

1. "+ Add New" ボタンをクリック
2. **Project** を選択
3. **Import Git Repository** をクリック
4. GitHub リポジトリを検索：
   ```
   koubouhirx7-cloud/task-cloude
   ```
5. リポジトリを選択

### 1.3 プロジェクト設定（自動設定済み）

以下の設定が自動で読み込まれます：

- **Project Name:** `highlander-task-input`
- **Framework Preset:** Other
- **Build Command:** `npm run build`
- **Output Directory:** `public`

> ℹ️ これらは `vercel.json` と `package.json` で既に設定されています

### 1.4 デプロイ実行

1. **Deploy** ボタンをクリック
2. デプロイの進行を待機（2～5分）

> ✅ デプロイが完了すると Vercel がお知らせします

### 1.5 デプロイ URL を確認

1. ダッシュボードで **Deployments** をクリック
2. 最新のデプロイが **Ready** になっていることを確認
3. URL を確認（例：`https://highlander-task-input.vercel.app`）

---

## 🚆 Step 2: Railway にデプロイ（5分）

### 2.1 Railway ダッシュボードにアクセス

1. https://railway.app にブラウザでアクセス
2. **Login** をクリック
3. **Continue with GitHub** を選択
4. GitHub 認証を完了

### 2.2 GitHub リポジトリをインポート

1. Railway ダッシュボードで **+ New Project** をクリック
2. **Deploy from GitHub repo** を選択
3. **Authorize Railway** をクリック（GitHub 連携）
4. GitHub リポジトリを検索・選択：
   ```
   koubouhirx7-cloud/task-cloude
   ```

### 2.3 デプロイ実行

1. リポジトリを選択して **Deploy Now** をクリック
2. デプロイの進行を待機（2～5分）

> ✅ デプロイが完了すると Railway がお知らせします

### 2.4 デプロイ URL を確認

1. Railway ダッシュボードで **Deployments** をクリック
2. 最新のデプロイが **Success** になっていることを確認
3. **Domains** タブで公開 URL を確認

---

## ⚙️ Step 3: Railway で環境変数を設定（3分）

### 3.1 Variables セクションを開く

1. Railway プロジェクトで **Variables** をクリック

### 3.2 環境変数を追加

以下の4つの環境変数を追加：

```
【変数名】 DISCORD_WEBHOOK_SECRETARY
【値】 https://discord.com/api/webhooks/1503267868412874824/57SnShsbG3lfiFHpjGEESYObxEs8hPR6TQ1DSzMsVxppeRA5EG_ortTofVOH7aQpnTvm

【変数名】 DISCORD_WEBHOOK_FINANCE
【値】 https://discord.com/api/webhooks/1503267498374729741/YGIs8vQ0QhDQApER0bEDkrpnleIt8BESZoWkddbBRwCNp76PXndjRhS28i1vwnrqUV6k

【変数名】 LOCAL_WEBHOOK_URL
【値】 http://192.168.50.187:9000/receive_task

【変数名】 RAILWAY_ENVIRONMENT
【値】 production
```

### 3.3 変数を保存

1. 全ての変数を入力後、**Save** をクリック
2. Railway が自動的に再デプロイします（1～2分）

> ✅ "Deployment ready" が表示されたら完了

---

## 🧪 Step 4: ローカル Mac で webhook リスナーを起動（1分）

### 4.1 ターミナルを開く

```bash
cd ~/Documents/会計情報
python3 task_receive_webhook.py
```

### 4.2 リスナーが起動したことを確認

以下のログが表示されることを確認：

```
🔗 Task Receive Webhook サーバー起動中...
   ポート: 9000
   webhook URL: http://localhost:9000/receive_task
```

> ℹ️ このターミナルはそのまま起動させておいてください

---

## 📱 Step 5: 本番環境テスト（3分）

### 5.1 Vercel URL でアクセス

ブラウザで以下を開く：

```
https://highlander-task-input.vercel.app/task_input.html
```

> ✅ モバイル最適化フォームが表示されることを確認

### 5.2 テストタスクを送信

1. フォームに以下を入力：
   - **タスク名:** "本番環境テスト"
   - **優先度:** "中"
   - **分野:** "agent"
   - **説明:** "Vercel + Railway のオンラインデプロイが成功したかテスト"
   - **スコープ:** "中"

2. **送信** ボタンをクリック

### 5.3 ローカル Mac で受信確認

別のターミナルを開いて確認：

```bash
ls -la ~/Documents/会計情報/tasks/*.json
```

> ✅ 最新のタスク JSON ファイルが作成されていることを確認

### 5.4 タスク自動処理を実行

```bash
cd ~/Documents/会計情報
python3 task_processor.py
```

> ✅ 以下が表示されることを確認：
> ```
> ✅ Discord 通知送信完了
> ✓ 分析結果保存: ~/Documents/会計情報/tasks/processed/xxx_analysis.json
> ```

### 5.5 Discord で通知を確認

Discord サーバーで、タスク分析結果の通知が送信されていることを確認

> ✅ チーム構成、工数見積もり、行動計画が表示されていることを確認

---

## 🎉 デプロイ完了！

### 公開 URL

スマートフォン・外部からのアクセス：

```
https://highlander-task-input.vercel.app/task_input.html
```

ダッシュボード：

```
https://highlander-task-input.vercel.app/dashboard.html
```

### ローカル環境（既存通り）

```
http://192.168.50.187:8888/task_input.html
```

---

## ✅ 完成チェックリスト

- [ ] Vercel へデプロイ完了
- [ ] Railway へデプロイ完了
- [ ] 環境変数を Railway で設定
- [ ] ローカル Mac で webhook リスナー起動
- [ ] Vercel URL でブラウザアクセス確認
- [ ] テストタスクを送信・受信確認
- [ ] Discord に通知が送信されたことを確認
- [ ] タスク自動処理が動作したことを確認

---

## 📊 デプロイ後のシステム構成

```
【スマートフォン / 外部PC】
         ↓ HTTPS
【Vercel】 (task_input.html, dashboard.html)
         ↓
【Railway】 (Flask バックエンド)
         ↓ webhook
【ローカルMac】 (task_processor.py, Discord 通知)
```

---

## 🚀 これで完成！

世界中のどこからでも、スマートフォンからワンタップで
ハイランダーにタスク入力できるようになりました！

次からは以下の URL でアクセス：

```
https://highlander-task-input.vercel.app/task_input.html
```

---

## 📞 トラブルシューティング

### Vercel デプロイが失敗した場合

1. Vercel ダッシュボード > **Deployments** > **View**
2. ビルドログを確認
3. 以下を確認：
   - `package.json` が存在するか
   - `task_input.html` が存在するか

### Railway デプロイが失敗した場合

1. Railway ダッシュボード > **Logs** をクリック
2. エラーメッセージを確認
3. 通常は依存関係のエラー
   - `requirements.txt` が正しく push されているか確認

### タスク送信がエラーになる場合

1. Railway のデプロイが Running になっているか確認
2. ローカル webhook リスナーが起動しているか確認
3. ローカル Mac の IP アドレスが正しいか確認（`ipconfig getifaddr en0`）

### Discord に通知が送信されない場合

1. Railway の環境変数を確認
   - `DISCORD_WEBHOOK_SECRETARY` が正しく設定されているか
2. Discord webhook URL が有効か確認
   - Discord サーバー設定で webhook を確認

---

## 🎊 お疲れさまでした！

完全なオンラインタスク管理システムが完成しました！

何かご質問やトラブルがあれば、お知らせください。
