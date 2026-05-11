#!/bin/bash
# 財務チームの cron ジョブを登録するスクリプト

SCRIPTS_DIR="/Users/murakamidaisuke/Documents/会計情報"
LOG_DIR="$SCRIPTS_DIR/finance-logs"

mkdir -p "$LOG_DIR"

# 既存の cron に追加
(crontab -l 2>/dev/null; cat <<'CRON'

# ─── 財務チーム（ハイランダー） ───
# Finance AI: 毎朝 9:00 に freee 仕訳提案
0 9 * * * cd /Users/murakamidaisuke/Documents/会計情報 && source .env 2>/dev/null; python3 finance_ai.py >> finance-logs/finance_ai.log 2>&1

# Cash Flow Agent: 毎週月曜 9:30 にキャッシュフロー分析
30 9 * * 1 cd /Users/murakamidaisuke/Documents/会計情報 && source .env 2>/dev/null; python3 finance_cashflow_agent.py >> finance-logs/cashflow.log 2>&1

# CFO Agent: 毎月1日 10:00 に月次レポート（前月分）
0 10 1 * * cd /Users/murakamidaisuke/Documents/会計情報 && source .env 2>/dev/null; python3 finance_cfo_agent.py >> finance-logs/cfo.log 2>&1
CRON
) | crontab -

echo "✅ 財務チーム cron 登録完了"
echo ""
echo "登録されたジョブ:"
crontab -l | grep -A1 "財務チーム" | grep -v "^#"
