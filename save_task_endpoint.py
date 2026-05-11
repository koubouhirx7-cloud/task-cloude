#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Save Endpoint - スマホから送信されたタスクを保存するバックエンドサーバー
task_input.html からの POST リクエストを受け取り、JSON ファイルとして tasks/ に保存

デプロイ環境対応：
- ローカル実行：~/Documents/会計情報/tasks に保存
- Railway（クラウド）実行：ローカルMacの webhook に送信
"""

import json
import os
import requests
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # CORS 対応

# 環境変数から設定を読み込み
TASKS_DIR = os.getenv(
    'TASKS_DIR',
    '/Users/murakamidaisuke/Documents/会計情報/tasks'
)
LOCAL_WEBHOOK_URL = os.getenv('LOCAL_WEBHOOK_URL', None)
IS_CLOUD = os.getenv('RAILWAY_ENVIRONMENT') == 'production'

# ローカル実行時のみディレクトリを作成
if not IS_CLOUD:
    TASKS_DIR = Path(TASKS_DIR)
    TASKS_DIR.mkdir(parents=True, exist_ok=True)


@app.route('/save_task', methods=['POST'])
def save_task():
    """スマートフォンから送信されたタスクを保存"""
    try:
        # request.json からタスクデータを取得
        data = request.get_json()

        if not data:
            return jsonify({
                "status": "error",
                "message": "No JSON data received"
            }), 400

        # 必須フィールドの確認
        required_fields = ['name', 'category', 'description']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": "error",
                    "message": f"Missing required field: {field}"
                }), 400

        # タイムスタンプでファイル名生成
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        category = data.get('category', 'unknown')
        file_name = f"{timestamp}_{category}.json"

        # メタデータ追加
        data['timestamp'] = datetime.now().isoformat()
        data['status'] = '未処理'

        # クラウド環境とローカル環境で処理を分岐
        if IS_CLOUD:
            # Railway（クラウド）実行時：ローカルMacのwebhookに送信
            if not LOCAL_WEBHOOK_URL:
                return jsonify({
                    "status": "error",
                    "message": "LOCAL_WEBHOOK_URL is not configured"
                }), 500

            try:
                response = requests.post(
                    LOCAL_WEBHOOK_URL,
                    json={"file_name": file_name, "data": data},
                    timeout=10
                )
                if response.status_code == 200:
                    print(f"✅ ローカルMacに送信: {file_name}")
                    return jsonify({
                        "status": "success",
                        "message": "Task sent to local Mac successfully",
                        "file": file_name,
                        "timestamp": data['timestamp']
                    }), 200
                else:
                    print(f"❌ ローカルMac通信エラー: {response.status_code}")
                    return jsonify({
                        "status": "warning",
                        "message": f"Task queued, but local webhook returned {response.status_code}",
                        "file": file_name
                    }), 202  # Accepted（非同期処理）
            except requests.exceptions.RequestException as e:
                print(f"❌ ローカルMac通信失敗: {e}")
                return jsonify({
                    "status": "warning",
                    "message": "Task received, but could not reach local Mac. Will be retried.",
                    "file": file_name
                }), 202  # Accepted（非同期処理）
        else:
            # ローカル実行時：直接ファイル保存
            file_path = Path(TASKS_DIR) / file_name

            # JSON ファイルとして保存
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"✅ タスク保存: {file_path}")
            print(f"   タスク名: {data['name']}")
            print(f"   分野: {category}")

            return jsonify({
                "status": "success",
                "message": "Task saved successfully",
                "file": file_name,
                "timestamp": data['timestamp']
            }), 200

    except Exception as e:
        print(f"❌ エラー: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/task_input.html', methods=['GET'])
def serve_task_input():
    """task_input.html をサーブ"""
    try:
        html_path = Path("/Users/murakamidaisuke/Documents/会計情報/task_input.html")
        with open(html_path, 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        return f"Error: {e}", 500


@app.route('/dashboard.html', methods=['GET'])
def serve_dashboard():
    """dashboard.html をサーブ"""
    try:
        html_path = Path("/Users/murakamidaisuke/Documents/会計情報/dashboard.html")
        with open(html_path, 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        return f"Error: {e}", 500


@app.route('/status', methods=['GET'])
def get_status():
    """サーバーステータス確認"""
    return jsonify({
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "tasks_dir": str(TASKS_DIR),
        "tasks_count": len(list(TASKS_DIR.glob("*.json")))
    }), 200


@app.route('/', methods=['GET'])
def root():
    """ルートエンドポイント"""
    return jsonify({
        "name": "🚀 Task Save Endpoint",
        "version": "1.0",
        "endpoints": {
            "POST /save_task": "Save task from smartphone",
            "GET /task_input.html": "Serve task input form",
            "GET /dashboard.html": "Serve operations center dashboard",
            "GET /status": "Check server status"
        }
    }), 200


if __name__ == '__main__':
    # ポート番号を環境変数から読み込み（Railway は PORT 環境変数を設定）
    port = int(os.getenv('PORT', '8888'))
    debug = not IS_CLOUD

    print("\n🚀 Task Save Endpoint サーバー起動中...")
    print(f"   環境: {'Railway（クラウド）' if IS_CLOUD else 'ローカル'}")
    print(f"   タスク保存ディレクトリ: {TASKS_DIR}")
    print(f"   ポート: {port}")
    if IS_CLOUD:
        print(f"   ローカルMac webhook: {LOCAL_WEBHOOK_URL}")
        print(f"   URL: https://xxxxx.railway.app/task_input.html\n")
    else:
        print(f"   URL: http://localhost:{port}/task_input.html\n")

    app.run(host='0.0.0.0', port=port, debug=debug)
