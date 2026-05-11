#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Receive Webhook - Railway（クラウド）から送信されたタスクをローカルMacで受け取る
ポート 9000 で listen し、受け取ったタスク JSON を ~/Documents/会計情報/tasks/ に保存
"""

import json
import os
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# .env ファイルを読み込み
load_dotenv()

app = Flask(__name__)

# タスク保存ディレクトリ
TASKS_DIR = Path("/Users/murakamidaisuke/Documents/会計情報/tasks")
TASKS_DIR.mkdir(parents=True, exist_ok=True)


@app.route('/receive_task', methods=['POST'])
def receive_task():
    """Railway から送信されたタスクを受け取り、ローカルファイルに保存"""
    try:
        payload = request.get_json()

        if not payload:
            return jsonify({
                "status": "error",
                "message": "No JSON data received"
            }), 400

        file_name = payload.get('file_name')
        data = payload.get('data')

        if not file_name or not data:
            return jsonify({
                "status": "error",
                "message": "Missing file_name or data"
            }), 400

        # ファイルパス
        file_path = TASKS_DIR / file_name

        # JSON ファイルとして保存
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ タスク受信・保存: {file_path}")
        print(f"   タスク名: {data.get('name', 'Unknown')}")
        print(f"   分野: {data.get('category', 'Unknown')}")
        print(f"   送信元: Railway")

        return jsonify({
            "status": "success",
            "message": "Task received and saved successfully",
            "file": file_name,
            "timestamp": datetime.now().isoformat()
        }), 200

    except Exception as e:
        print(f"❌ エラー: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/webhook_status', methods=['GET'])
def webhook_status():
    """Webhook のステータス確認"""
    return jsonify({
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "tasks_dir": str(TASKS_DIR),
        "tasks_count": len(list(TASKS_DIR.glob("*.json")))
    }), 200


if __name__ == '__main__':
    port = int(os.getenv('WEBHOOK_PORT', '9000'))

    print("\n🔗 Task Receive Webhook サーバー起動中...")
    print(f"   ポート: {port}")
    print(f"   タスク保存ディレクトリ: {TASKS_DIR}")
    print(f"   webhook URL: http://localhost:{port}/receive_task")
    print(f"   ステータス確認: http://localhost:{port}/webhook_status\n")
    print("   Railway からのリクエストを待機中...\n")

    app.run(host='0.0.0.0', port=port, debug=True)
