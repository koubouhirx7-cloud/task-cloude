#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cash Flow Agent - 週次キャッシュフロー分析・収支予測・アラート
毎週月曜 9:00 に実行。今週の予測・残高警告を Discord に送信
"""

import json
import os
import re
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import List, Dict, Any, Tuple

import urllib.request

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_FINANCE", "")
LOG_DIR = Path("/Users/murakamidaisuke/Documents/会計情報/finance-logs")
CASHFLOW_FILE = LOG_DIR / "cashflow_state.json"

# 固定費スケジュール（毎月発生する支出）
FIXED_EXPENSES = [
    {"name": "地代家賃",   "day": 25, "amount": 50_000},
    {"name": "給与",       "day": 25, "amount": 80_000},
    {"name": "通信費",     "day": 27, "amount": 8_000},
    {"name": "保険料",     "day": 20, "amount": 15_000},
    {"name": "電気代",     "day": 10, "amount": 12_000},
]

# キャッシュアラート閾値（円）
ALERT_THRESHOLDS = {
    "critical": 200_000,   # 🔴 危険：即対応必要
    "warning":  500_000,   # 🟡 注意：節約モード
    "healthy": 1_000_000,  # 🟢 健全
}

# 季節性プロファイル（収入予測用）
SEASONAL_PROFILE = {
    1: 0.55, 2: 0.60, 3: 0.95, 4: 1.30, 5: 1.35,
    6: 1.10, 7: 1.05, 8: 1.00, 9: 0.90, 10: 0.90,
    11: 0.70, 12: 0.65,
}
BASE_WEEKLY_REVENUE = 112_500  # 月次目標50万÷4.5週


class CashFlowAgent:
    def __init__(self):
        LOG_DIR.mkdir(parents=True, exist_ok=True)

    # ──────────────────────────────────────────
    # 状態管理（残高・履歴）
    # ──────────────────────────────────────────
    def load_state(self) -> Dict:
        if CASHFLOW_FILE.exists():
            with open(CASHFLOW_FILE, encoding="utf-8") as f:
                return json.load(f)
        # 初期状態
        return {
            "current_balance": 800_000,
            "history": [],
            "last_updated": None,
        }

    def save_state(self, state: Dict):
        state["last_updated"] = datetime.now().isoformat()
        with open(CASHFLOW_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    # ──────────────────────────────────────────
    # 今週・来週の収支予測
    # ──────────────────────────────────────────
    def get_upcoming_fixed_expenses(self, days: int = 30) -> List[Dict]:
        """今後 N 日間に発生する固定費一覧"""
        today = date.today()
        upcoming = []
        for exp in FIXED_EXPENSES:
            for month_offset in range(2):  # 今月と来月
                year = today.year + (today.month + month_offset - 1) // 12
                month = (today.month + month_offset - 1) % 12 + 1
                try:
                    pay_date = date(year, month, exp["day"])
                except ValueError:
                    # 月末が存在しない日（2月30日など）
                    import calendar
                    last_day = calendar.monthrange(year, month)[1]
                    pay_date = date(year, month, last_day)

                delta = (pay_date - today).days
                if 0 <= delta <= days:
                    upcoming.append({
                        "name": exp["name"],
                        "date": pay_date.strftime("%m/%d"),
                        "days_until": delta,
                        "amount": exp["amount"],
                    })
        return sorted(upcoming, key=lambda x: x["days_until"])

    def predict_weekly_revenue(self) -> Tuple[int, int]:
        """今週の収入予測（最小値、最大値）"""
        month = datetime.now().month
        factor = SEASONAL_PROFILE.get(month, 1.0)
        expected = int(BASE_WEEKLY_REVENUE * factor)
        return int(expected * 0.7), int(expected * 1.3)

    def predict_next_30days(self, current_balance: int) -> List[Dict]:
        """30日間のキャッシュフロー予測"""
        balance = current_balance
        today = date.today()
        projections = []
        month = today.month

        for week in range(4):
            week_start = today + timedelta(weeks=week)
            rev_min, rev_max = self.predict_weekly_revenue()

            # その週に発生する固定費
            week_expenses = sum(
                e["amount"]
                for e in self.get_upcoming_fixed_expenses(days=30)
                if week * 7 <= e["days_until"] < (week + 1) * 7
            )

            balance_after_min = balance + rev_min - week_expenses
            balance_after_max = balance + rev_max - week_expenses
            balance = balance + (rev_min + rev_max) // 2 - week_expenses

            projections.append({
                "week": f"第{week+1}週 ({week_start.strftime('%m/%d')}〜)",
                "revenue_range": (rev_min, rev_max),
                "fixed_expenses": week_expenses,
                "balance_range": (balance_after_min, balance_after_max),
            })

        return projections

    # ──────────────────────────────────────────
    # アラート判定
    # ──────────────────────────────────────────
    def get_alert_level(self, balance: int) -> Tuple[str, str]:
        if balance <= ALERT_THRESHOLDS["critical"]:
            return "🔴 CRITICAL", f"残高 ¥{balance:,} が危険水準を下回っています！即時対応が必要です"
        elif balance <= ALERT_THRESHOLDS["warning"]:
            return "🟡 WARNING", f"残高 ¥{balance:,} が注意水準です。固定費の支払いに注意してください"
        elif balance >= ALERT_THRESHOLDS["healthy"]:
            return "🟢 HEALTHY", f"残高 ¥{balance:,} は健全な水準です"
        else:
            return "🔵 NORMAL", f"残高 ¥{balance:,} は通常範囲内です"

    def generate_recommendations(self, balance: int, upcoming: List[Dict], projections: List[Dict]) -> List[str]:
        recs = []

        # 7日以内の大口支出チェック
        urgent = [e for e in upcoming if e["days_until"] <= 7]
        if urgent:
            total_urgent = sum(e["amount"] for e in urgent)
            recs.append(f"⚠️ 今週の支払い予定: ¥{total_urgent:,}（{', '.join(e['name'] for e in urgent)}）")
            if balance < total_urgent * 1.5:
                recs.append("🚨 今週の支払いに対して現金バッファが少なめです。売上回収を優先してください")

        # 季節性アドバイス
        month = datetime.now().month
        factor = SEASONAL_PROFILE.get(month, 1.0)
        next_month = (month % 12) + 1
        next_factor = SEASONAL_PROFILE.get(next_month, 1.0)

        if next_factor > factor * 1.15:
            recs.append(f"📈 来月は繁忙期（係数{next_factor}×）。部品在庫の先行仕入れを検討してください")
        elif next_factor < factor * 0.85:
            recs.append(f"📉 来月は閑散期（係数{next_factor}×）。固定費の見直しと集客施策を準備してください")

        # 最低残高予測チェック
        min_projected = min(p["balance_range"][0] for p in projections)
        if min_projected < ALERT_THRESHOLDS["warning"]:
            recs.append(f"📊 30日後の最悪ケース残高: ¥{min_projected:,}。売上強化または経費抑制が必要です")

        if not recs:
            recs.append("✅ 現在の財務状況は安定しています。このまま維持してください")

        return recs

    # ──────────────────────────────────────────
    # Discord 送信
    # ──────────────────────────────────────────
    def send_discord(self, state: Dict, upcoming: List[Dict], projections: List[Dict], alert: Tuple, recs: List[str]):
        if not DISCORD_WEBHOOK:
            print("⚠️ DISCORD_WEBHOOK_FINANCE が未設定")
            return False

        balance = state["current_balance"]
        alert_level, alert_msg = alert

        # 支払いスケジュール
        if upcoming:
            schedule_text = "\n".join([
                f"`{e['date']}` {e['name']} **¥{e['amount']:,}** （{e['days_until']}日後）"
                for e in upcoming[:5]
            ])
        else:
            schedule_text = "今後30日間に予定された固定費はありません"

        # 30日予測
        projection_text = ""
        for p in projections:
            min_b, max_b = p["balance_range"]
            bar = "█" * min(8, max(0, int(min_b / 200_000))) + "░" * max(0, 8 - int(min_b / 200_000))
            projection_text += f"{p['week']}\n  収入予測 ¥{p['revenue_range'][0]:,}〜¥{p['revenue_range'][1]:,} | 残高 ¥{min_b:,}〜¥{max_b:,}\n"

        color = 0xe74c3c if "CRITICAL" in alert_level else (0xf39c12 if "WARNING" in alert_level else 0x2ecc71)

        embed = {
            "embeds": [{
                "title": f"💵 週次キャッシュフローレポート — {datetime.now().strftime('%Y/%m/%d')}",
                "color": color,
                "fields": [
                    {
                        "name": f"{alert_level}：現在残高",
                        "value": f"**¥{balance:,}**\n{alert_msg}",
                        "inline": False
                    },
                    {
                        "name": "📅 今後の支払いスケジュール（30日以内）",
                        "value": schedule_text,
                        "inline": False
                    },
                    {
                        "name": "🔮 30日間キャッシュフロー予測",
                        "value": projection_text.strip() or "データ不足",
                        "inline": False
                    },
                    {
                        "name": "💡 CFO レコメンデーション",
                        "value": "\n".join(recs),
                        "inline": False
                    },
                ],
                "footer": {"text": f"Cash Flow Agent | {datetime.now().strftime('%Y-%m-%d %H:%M')} | 自転車工房ハイランダー"}
            }]
        }

        data = json.dumps(embed).encode("utf-8")
        req = urllib.request.Request(
            DISCORD_WEBHOOK, data=data,
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as res:
                ok = res.status in (200, 204)
                print("✅ Discord 送信成功" if ok else f"⚠️ status {res.status}")
                return ok
        except Exception as e:
            print(f"❌ Discord 送信エラー: {e}")
            return False

    # ──────────────────────────────────────────
    # 残高更新コマンド（手動入力用）
    # ──────────────────────────────────────────
    def update_balance(self, new_balance: int, note: str = ""):
        state = self.load_state()
        old = state["current_balance"]
        state["current_balance"] = new_balance
        state["history"].append({
            "date": datetime.now().isoformat(),
            "old_balance": old,
            "new_balance": new_balance,
            "note": note,
        })
        self.save_state(state)
        print(f"✅ 残高更新: ¥{old:,} → ¥{new_balance:,}")

    # ──────────────────────────────────────────
    # メイン
    # ──────────────────────────────────────────
    def run(self):
        print(f"\n💵 Cash Flow Agent 起動 — {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        state = self.load_state()
        balance = state["current_balance"]

        upcoming = self.get_upcoming_fixed_expenses(days=30)
        projections = self.predict_next_30days(balance)
        alert = self.get_alert_level(balance)
        recs = self.generate_recommendations(balance, upcoming, projections)

        print(f"   現在残高: ¥{balance:,} | {alert[0]}")
        print(f"   今後30日の支払い: {len(upcoming)}件")

        self.send_discord(state, upcoming, projections, alert, recs)
        self.save_state(state)
        print("✅ Cash Flow Agent 完了\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Cash Flow Agent")
    parser.add_argument("--update-balance", type=int, help="残高を手動で更新（例: --update-balance 750000）")
    parser.add_argument("--note", type=str, default="", help="更新メモ")
    args = parser.parse_args()

    agent = CashFlowAgent()
    if args.update_balance:
        agent.update_balance(args.update_balance, args.note)
    else:
        agent.run()
