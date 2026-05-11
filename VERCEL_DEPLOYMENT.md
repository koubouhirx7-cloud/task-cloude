# 🚀 Vercel へのデプロイ手順書

## 📋 概要

このドキュメントでは、ハイランダー タスク入力フロントエンド（task_input.html, dashboard.html）を Vercel にデプロイする手順を説明します。

**デプロイ後のアクセス URL:**
```
https://[プロジェクト名].vercel.app/task_input.html
```

---

## 🎯 Vercel + Railway 構成

```
【スマートフォン / 外部PC】
        ↓ HTTPS
【Vercel】← 高速 CDN で配信
├─ task_input.html
├─ dashboard.html
└─ /save_task → Railway にリダイレクト
        ↓
【Railway】← バックエンド（Flask）
├─ /save_task エンドポイント
└─ webhook リスナー
        ↓
【ローカルMac】
├─ task_receive_webhook.py
├─ task_processor.py（自動処理）
└─ Discord 通知
```

---

## 📖 Step 1: GitHub にプッシュ確認

既に GitHub に push されていることを確認：

```bash
git log --oneline | head -3
# 結果：
# ea036db 🎯 Railway クイックデプロイガイド追加
# 5fec8ba 📚 Railway デプロイ手順書・サマリー追加
# 53d10e8 🚀 Railway デプロイ用ファイル追加（オンラインアクセス対応）
```

> ✅ GitHub リポジトリ: https://github.com/koubouhirx7-cloud/task-cloude.git

---

## 🌐 Step 2: Vercel にプロジェクトを作成

### 2.1 Vercel ダッシュボードにアクセス

1. https://vercel.com にアクセス
2. ログイン（既存アカウント使用）
3. ダッシュボードから **Add New** → **Project** をクリック

### 2.2 GitHub リポジトリをインポート

1. **Import Git Repository** を選択
2. GitHub リポジトリを検索・選択
   ```
   koubouhirx7-cloud/task-cloude
   ```
3. リポジトリを選択

### 2.3 プロジェクト設定

1. **Project Name:** `highlander-task-input`（または好きな名前）
2. **Framework Preset:** Other（選択しない）
3. **Root Directory:** ./（ルートディレクトリ）
4. **Build Command:** `npm run build`
5. **Output Directory:** `public`

> 📝 これらの設定は `package.json` と `vercel.json` で既に定義されています

### 2.4 環境変数の設定

特に必要な環境変数はありませんが、Railway のバックエンド URL を設定できます：

1. **Environment Variables** セクションで以下を追加（オプション）：
   ```
   RAILWAY_API_URL=https://task-cloude-production.railway.app
   ```

2. **Deploy** をクリック

> ⏳ デプロイが開始されます（2～5分）

---

## ✅ Step 3: デプロイ完了確認

1. Vercel ダッシュボードで **Deployments** をクリック
2. 最新のデプロイが **Production** で **Ready** になっていることを確認
3. **Visit** をクリックして、プロジェクト URL を確認

```
例：https://highlander-task-input.vercel.app
```

---

## 🔗 Step 4: Railway バックエンドとの連携確認

### 4.1 Railway でバックエンドをデプロイ（既に完了している場合）

Railway のダッシュボードで：
1. プロジェクトが **Running** になっていることを確認
2. **Domains** タブで公開 URL を確認（例：`https://task-cloude-production.railway.app`）

### 4.2 Vercel の API Rewrite を確認

Vercel は以下のリクエストを Railway に自動的にリダイレクトします：

```
Vercel: POST /api/save_task
  ↓ リダイレクト
Railway: POST /api/save_task
```

> これは `vercel.json` の `rewrites` セクションで定義されています

---

## 🌐 Step 5: 動作確認

### 5.1 Vercel URL でアクセス

```
https://highlander-task-input.vercel.app/task_input.html
```

> ✅ モバイル最適化フォームが表示されることを確認

### 5.2 ローカル Mac で webhook リスナーを起動

```bash
python3 task_receive_webhook.py
```

### 5.3 テストタスク送信

1. Vercel URL のフォームでテストタスクを入力
2. **送信** をクリック
3. ローカル Mac のターミナルで以下が表示されることを確認：
   ```
   ✅ タスク受信・保存: /Users/murakamidaisuke/Documents/会計情報/tasks/xxx.json
   ```

### 5.4 タスク自動処理

```bash
python3 task_processor.py
```

> ✅ Discord に通知が送信されることを確認

---

## 🎉 デプロイ完了！

### 公開 URL（スマートフォン・外部からのアクセス）

```
https://highlander-task-input.vercel.app/task_input.html
```

### ダッシュボード

```
https://highlander-task-input.vercel.app/dashboard.html
```

### ローカル環境（既存通り）

```
http://192.168.50.187:8888/task_input.html
```

---

## 🔄 Code Update 後の再デプロイ

1. ローカルで変更をコミット：
   ```bash
   git add .
   git commit -m "Fix: update HTML"
   ```

2. GitHub に push：
   ```bash
   git push origin main
   ```

3. Vercel が自動的に再デプロイ（2～3分で完了）

> ✅ Vercel ダッシュボードで再デプロイを確認

---

## 📊 運用スケジュール

| サービス | 機能 | URL |
|:---|:---|:---|
| **Vercel** | フロントエンド | https://highlander-task-input.vercel.app |
| **Railway** | バックエンド（Flask） | https://task-cloude-production.railway.app |
| **ローカル Mac** | タスク処理・Discord通知 | http://192.168.50.187:9000 |

---

## ⚙️ トラブルシューティング

### Q: Vercel でビルドエラー

**症状:** "Build failed" メッセージ

**解決策:**
1. Vercel ダッシュボード > **Deployments** > **View**
2. ビルドログを確認
3. 通常は `package.json` の `build` コマンドが失敗
4. 以下を確認：
   - `task_input.html` が存在するか
   - `public/` ディレクトリが作成されているか

### Q: タスク送信がエラーになる

**症状:** "API Error" メッセージ

**解決策:**
1. Railway バックエンドが Running になっているか確認
2. Vercel の environment variables を確認
3. Railway の CORS 設定を確認

### Q: ローカル Mac で webhook が受け取れない

**症状:** "Connection refused" エラー

**解決策:**
1. Mac のファイアウォール設定でポート 9000 を開放
2. webhook リスナーが起動しているか確認：
   ```bash
   ps aux | grep task_receive_webhook
   ```

---

## 🔐 セキュリティ

### Vercel 側
- ✅ 自動 HTTPS（Let's Encrypt）
- ✅ DDoS 保護
- ✅ CDN で高速配信

### Railway 側
- ✅ 自動 HTTPS
- ✅ 環境変数で機密情報管理

---

## 📚 関連ドキュメント

- `QUICK_RAILWAY_DEPLOY.md` - Railway デプロイ手順
- `RAILWAY_DEPLOYMENT.md` - Railway 詳細ガイド
- `ONLINE_DEPLOYMENT_SUMMARY.md` - システムアーキテクチャ

---

## 🎯 確認チェックリスト

- [ ] GitHub にコード push 完了
- [ ] Vercel プロジェクトを作成
- [ ] デプロイが "Ready" になったことを確認
- [ ] Vercel URL でブラウザアクセス確認
- [ ] ローカル Mac で webhook リスナー起動
- [ ] テストタスク送信
- [ ] ローカル Mac で受信確認
- [ ] Discord に通知が送信されたことを確認

---

## 🎉 完成！

**Vercel + Railway で完全なオンラインシステムが完成しました！**

スマートフォンからいつでもどこからでも
ハイランダーにタスク入力できます！ 🚀

---

## 📞 サポート

何か問題が発生した場合：
1. Vercel のビルドログを確認
2. Railway のログを確認
3. このドキュメントのトラブルシューティングを参照
