#!/bin/bash
# Task Processor Runner - タスク自動処理スクリプト
# cron から毎時間実行される

cd /Users/murakamidaisuke/Documents/会計情報
export $(grep -v '^#' .env | xargs)

echo "📋 ===== Task Processor 実行開始 ====="
echo "⏰ 実行時刻: $(date '+%Y-%m-%d %H:%M:%S')"

python3 task_processor.py

echo "✅ Task Processor 実行完了"
echo ""
