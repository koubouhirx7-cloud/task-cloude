# 🚀 Railway へのクイックデプロイガイド

## 📍 前提条件

✅ GitHub リポジトリに push 完了
- Repository: https://github.com/koubouhirx7-cloud/task-cloude.git
- Main branch にファイルが push されています

---

## 🎯 5 分で完了するデプロイ手順

### **Step 1: Railway.app にアクセス**

1. ブラウザで https://railway.app にアクセス
2. **Login** をクリック
3. **Continue with GitHub** を選択
4. GitHub 認証を完了

---

### **Step 2: GitHub リポジトリを接続**

1. Railway ダッシュボードで **+ New Project** をクリック
2. **Deploy from GitHub repo** を選択
3. 「Authorize Railway」をクリック（GitHub と連携）
4. `koubouhirx7-cloud/task-cloude` リポジトリを検索・選択
5. **Deploy Now** をクリック

> ⏳ ビルド・デプロイが開始されます（2～5分）

---

### **Step 3: 環境変数を設定**

1. Railway プロジェクトダッシュボードで **Variables** をクリック
2. 以下の環境変数を追加：

```
【Discord Webhooks】
DISCORD_WEBHOOK_SECRETARY=https://discord.com/api/webhooks/1503267868412874824/57SnShsbG3lfiFHpjGEESYObxEs8hPR6TQ1DSzMsVxppeRA5EG_ortTofVOH7aQpnTvm

DISCORD_WEBHOOK_FINANCE=https://discord.com/api/webhooks/1503267498374729741/YGIs8vQ0QhDQApER0bEDkrpnleIt8BESZoWkddbBRwCNp76PXndjRhS28i1vwnrqUV6k

【ローカルMac 通信】
LOCAL_WEBHOOK_URL=http://192.168.50.187:9000/receive_task
```

> 📝 **重要:** `LOCAL_WEBHOOK_URL` のIP アドレスを確認
> ```bash
> ipconfig getifaddr en0
> # 出力例: 192.168.50.187
> ```

3. **Save Variables** をクリック

---

### **Step 4: デプロイ URL を確認**

1. Railway ダッシュボードで **Deployments** をクリック
2. 最新のデプロイが **Success** になっていることを確認
3. **Domains** タブで公開 URL を確認

```
例：https://task-cloude-production.railway.app
```

---

### **Step 5: 動作確認**

#### A. ローカル Mac で webhook リスナーを起動

```bash
cd ~/Documents/会計情報
python3 task_receive_webhook.py
```

#### B. ブラウザで Railway URL にアクセス

```
https://task-cloude-production.railway.app/task_input.html
```

> 📱 モバイル最適化フォームが表示されます

#### C. テストタスクを送信

1. フォーム画面でテストタスクを入力
2. **送信** をクリック
3. ローカル Mac のターミナルで以下が表示されることを確認：
   ```
   ✅ タスク受信・保存: /Users/murakamidaisuke/Documents/会計情報/tasks/xxx.json
   ```

#### D. タスク処理を実行

```bash
python3 task_processor.py
```

> Discord に通知が送信されることを確認

---

## 🎉 デプロイ完了！

### 公開 URL（スマートフォンからアクセス）

```
https://task-cloude-production.railway.app/task_input.html
```

### ローカル環境（既存通り）

```
http://192.168.50.187:8888/task_input.html
```

---

## ⚙️ トラブルシューティング

### Q: Railway でビルドエラー

**症状:** "Build failed" メッセージ

**解決策:**
1. Railway ダッシュボード > **Logs** でエラーを確認
2. 通常は依存関係不足
3. `requirements.txt` が正しく push されているか確認
   ```bash
   git log --oneline
   cat requirements.txt
   ```

### Q: ローカル Mac で webhook が受け取れない

**症状:** "Connection refused" エラー

**解決策:**
1. Mac のファイアウォール設定でポート 9000 を開放
   - System Preferences > Security & Privacy > Firewall Options
2. `LOCAL_WEBHOOK_URL` が正しいか確認
   ```bash
   ipconfig getifaddr en0
   ```
3. webhook リスナーが起動しているか確認
   ```bash
   ps aux | grep task_receive_webhook
   ```

### Q: Discord に通知が送信されない

**症状:** "Discord 通知失敗" メッセージ

**解決策:**
1. Railway の環境変数を確認
   - ダッシュボード > Variables
   - `DISCORD_WEBHOOK_SECRETARY` が正しく設定されているか
2. webhook URL が有効か確認
   - Discord サーバーで確認

---

## 📊 デプロイ後の確認項目

- [x] GitHub にコード push 完了
- [ ] Railway デプロイ実行
- [ ] 環境変数を Railway で設定
- [ ] デプロイが "Success" になったことを確認
- [ ] ローカル Mac で webhook リスナー起動
- [ ] Railway URL でブラウザアクセス
- [ ] テストタスク送信
- [ ] ローカル Mac で受信確認
- [ ] task_processor で処理
- [ ] Discord に通知が送信されたことを確認

---

## 🔗 重要なリンク

- **GitHub リポジトリ:** https://github.com/koubouhirx7-cloud/task-cloude.git
- **Railway ダッシュボード:** https://railway.app/dashboard
- **詳細ドキュメント:** `RAILWAY_DEPLOYMENT.md`

---

## 📞 サポート

何か問題が発生した場合：
1. このドキュメントの「トラブルシューティング」を参照
2. Railway ダッシュボード > **Logs** でエラーを確認
3. 詳細は `RAILWAY_DEPLOYMENT.md` を参照
