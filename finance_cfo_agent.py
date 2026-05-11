#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CFO Agent - 月次財務分析・長期トレンドレポート
毎月1日に実行し、前月の損益・KPI・長期トレンドを Discord に送信
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

import urllib.request
import urllib.error

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_FINANCE", "")
LOG_DIR = Path("/Users/murakamidaisuke/Documents/会計情報/finance-logs")
TREND_FILE = LOG_DIR / "monthly_trend.json"


# ─────────────────────────────────────────────
# 季節性プロファイル（自転車工房向け）
# ─────────────────────────────────────────────
SEASONAL_PROFILE = {
    1:  0.55,   # 1月：低
    2:  0.60,
    3:  0.95,   # 3月：春繁忙期開始
    4:  1.30,   # 4月：最高峰
    5:  1.35,   # 5月：GW
    6:  1.10,
    7:  1.05,
    8:  1.00,
    9:  0.90,
    10: 0.90,
    11: 0.70,
    12: 0.65,   # 12月：低
}

# KPI 目標値（要調整）
KPI_TARGETS = {
    "monthly_revenue":   500_000,   # 月次売上目標（円）
    "gross_margin_pct":  40.0,      # 粗利率目標 (%)
    "expense_ratio_pct": 55.0,      # 経費率上限 (%)
    "cash_reserve_days": 60,        # 手元現金の目安日数
}


class CFOAgent:
    def __init__(self):
        self.log_dir = LOG_DIR
        self.log_dir.mkdir(parents=True, exist_ok=True)

    # ──────────────────────────────────────────
    # ログ集計
    # ──────────────────────────────────────────
    def load_monthly_logs(self, year: int, month: int) -> List[Dict]:
        """指定月の日次ログをすべて読み込む"""
        records = []
        prefix = f"{year}-{month:02d}-"
        for f in self.log_dir.glob(f"{prefix}*.json"):
            try:
                with open(f, encoding="utf-8") as fp:
                    data = json.load(fp)
                    records.extend(data.get("transactions", []))
            except Exception:
                pass
        return records

    def aggregate_month(self, transactions: List[Dict]) -> Dict[str, Any]:
        """月次集計"""
        revenue = 0
        expenses: Dict[str, int] = {}

        REVENUE_ACCOUNTS = {"売上高", "売上値引き"}
        EXPENSE_ACCOUNTS = {
            "運送料", "ガソリン代", "部品購入費", "地代家賃",
            "支払手数料", "給与", "保険料", "電気代", "水道代",
            "ガス代", "通信費", "広告宣伝費", "消耗品費", "租税公課"
        }

        for txn in transactions:
            account = txn.get("proposed_account", "")
            amount = txn.get("amount", 0)
            if account in REVENUE_ACCOUNTS:
                revenue += amount
            elif account in EXPENSE_ACCOUNTS:
                expenses[account] = expenses.get(account, 0) + abs(amount)

        total_expense = sum(expenses.values())
        operating_profit = revenue - total_expense
        gross_margin_pct = (operating_profit / revenue * 100) if revenue > 0 else 0.0
        expense_ratio_pct = (total_expense / revenue * 100) if revenue > 0 else 0.0

        return {
            "revenue": revenue,
            "total_expense": total_expense,
            "operating_profit": operating_profit,
            "gross_margin_pct": round(gross_margin_pct, 1),
            "expense_ratio_pct": round(expense_ratio_pct, 1),
            "expense_breakdown": expenses,
            "transaction_count": len(transactions),
        }

    # ──────────────────────────────────────────
    # 長期トレンド管理
    # ──────────────────────────────────────────
    def load_trend(self) -> Dict:
        if TREND_FILE.exists():
            with open(TREND_FILE, encoding="utf-8") as f:
                return json.load(f)
        return {"monthly": {}}

    def save_trend(self, trend: Dict):
        with open(TREND_FILE, "w", encoding="utf-8") as f:
            json.dump(trend, f, ensure_ascii=False, indent=2)

    def update_trend(self, year: int, month: int, agg: Dict[str, Any]) -> Dict:
        trend = self.load_trend()
        key = f"{year}-{month:02d}"
        trend["monthly"][key] = {
            "revenue": agg["revenue"],
            "operating_profit": agg["operating_profit"],
            "gross_margin_pct": agg["gross_margin_pct"],
            "expense_ratio_pct": agg["expense_ratio_pct"],
        }
        self.save_trend(trend)
        return trend

    # ──────────────────────────────────────────
    # インサイト生成
    # ──────────────────────────────────────────
    def generate_insights(self, agg: Dict, month: int, trend: Dict) -> List[str]:
        insights = []
        monthly = trend.get("monthly", {})

        # 季節調整済み売上評価
        seasonal_factor = SEASONAL_PROFILE.get(month, 1.0)
        adjusted_target = KPI_TARGETS["monthly_revenue"] * seasonal_factor
        if agg["revenue"] >= adjusted_target * 1.1:
            insights.append(f"🟢 売上が季節調整目標を **{((agg['revenue']/adjusted_target-1)*100):.0f}%** 上回りました")
        elif agg["revenue"] >= adjusted_target * 0.9:
            insights.append(f"🟡 売上は季節調整目標のほぼ通り（{(agg['revenue']/adjusted_target*100):.0f}%）")
        else:
            insights.append(f"🔴 売上が季節調整目標を **{((1-agg['revenue']/adjusted_target)*100):.0f}%** 下回りました。集客施策を検討してください")

        # 粗利率チェック
        if agg["gross_margin_pct"] >= KPI_TARGETS["gross_margin_pct"]:
            insights.append(f"🟢 粗利率 {agg['gross_margin_pct']}%：目標達成")
        else:
            insights.append(f"🔴 粗利率 {agg['gross_margin_pct']}%：目標 {KPI_TARGETS['gross_margin_pct']}% を下回っています。部品コスト見直しを推奨")

        # 経費率チェック
        if agg["expense_ratio_pct"] <= KPI_TARGETS["expense_ratio_pct"]:
            insights.append(f"🟢 経費率 {agg['expense_ratio_pct']}%：適正範囲内")
        else:
            insights.append(f"🔴 経費率 {agg['expense_ratio_pct']}%：上限 {KPI_TARGETS['expense_ratio_pct']}% 超過。コスト削減が必要")

        # 前月比較
        keys = sorted(monthly.keys())
        if len(keys) >= 2:
            prev_key = keys[-2]
            prev = monthly[prev_key]
            mom_change = ((agg["revenue"] - prev["revenue"]) / prev["revenue"] * 100) if prev["revenue"] > 0 else 0
            arrow = "📈" if mom_change >= 0 else "📉"
            insights.append(f"{arrow} 前月比売上: **{mom_change:+.1f}%**")

        # トップ経費
        if agg["expense_breakdown"]:
            top_exp = sorted(agg["expense_breakdown"].items(), key=lambda x: x[1], reverse=True)[:3]
            top_str = " / ".join([f"{k} ¥{v:,}" for k, v in top_exp])
            insights.append(f"💸 主要経費 TOP3: {top_str}")

        # 来月予測（季節係数ベース）
        next_month = (month % 12) + 1
        next_factor = SEASONAL_PROFILE.get(next_month, 1.0)
        avg_revenue = sum(m["revenue"] for m in monthly.values()) / max(len(monthly), 1)
        predicted_next = int(avg_revenue * next_factor)
        insights.append(f"🔮 来月（{next_month}月）売上予測: ¥{predicted_next:,}（季節係数 {next_factor}×）")

        return insights

    # ──────────────────────────────────────────
    # Discord 通知
    # ──────────────────────────────────────────
    def send_discord(self, agg: Dict, insights: List[str], year: int, month: int, trend: Dict):
        if not DISCORD_WEBHOOK:
            print("⚠️ DISCORD_WEBHOOK_FINANCE が未設定")
            return False

        monthly = trend.get("monthly", {})
        # 直近6ヶ月のトレンドバー
        keys = sorted(monthly.keys())[-6:]
        if keys:
            max_rev = max(monthly[k]["revenue"] for k in keys) or 1
            trend_bar = ""
            for k in keys:
                ratio = monthly[k]["revenue"] / max_rev
                bar = "█" * int(ratio * 8) + "░" * (8 - int(ratio * 8))
                trend_bar += f"`{k[-5:]}` {bar} ¥{monthly[k]['revenue']:,}\n"
        else:
            trend_bar = "データ蓄積中..."

        profit_color = 0x2ecc71 if agg["operating_profit"] >= 0 else 0xe74c3c

        embed = {
            "embeds": [{
                "title": f"📊 {year}年{month}月 CFO レポート",
                "color": profit_color,
                "fields": [
                    {
                        "name": "💰 月次損益サマリー",
                        "value": (
                            f"売上高: **¥{agg['revenue']:,}**\n"
                            f"総経費: ¥{agg['total_expense']:,}\n"
                            f"営業利益: **¥{agg['operating_profit']:,}**\n"
                            f"粗利率: {agg['gross_margin_pct']}% | 経費率: {agg['expense_ratio_pct']}%"
                        ),
                        "inline": False
                    },
                    {
                        "name": "📈 売上トレンド（直近6ヶ月）",
                        "value": trend_bar or "データ蓄積中...",
                        "inline": False
                    },
                    {
                        "name": "💡 CFO インサイト",
                        "value": "\n".join(insights) if insights else "分析データ不足",
                        "inline": False
                    },
                ],
                "footer": {"text": f"CFO Agent | {datetime.now().strftime('%Y-%m-%d %H:%M')} | 自転車工房ハイランダー"}
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
    # メイン
    # ──────────────────────────────────────────
    def run(self, year: int = None, month: int = None):
        now = datetime.now()
        # デフォルトは「先月」
        target = datetime(now.year, now.month, 1) - timedelta(days=1)
        year = year or target.year
        month = month or target.month

        print(f"\n📊 CFO Agent 起動 — {year}年{month}月 分析開始")

        transactions = self.load_monthly_logs(year, month)
        if not transactions:
            print(f"⚠️ {year}-{month:02d} のログが見つかりません（freee AI を先に実行してください）")
            # テスト用ダミーデータで動作確認
            transactions = self._dummy_transactions(year, month)

        agg = self.aggregate_month(transactions)
        trend = self.update_trend(year, month, agg)
        insights = self.generate_insights(agg, month, trend)

        print(f"   売上: ¥{agg['revenue']:,} / 営業利益: ¥{agg['operating_profit']:,}")
        for ins in insights:
            clean = re.sub(r'\*\*|`', '', ins)
            print(f"   {clean}")

        self.send_discord(agg, insights, year, month, trend)
        print("✅ CFO Agent 完了\n")

    def _dummy_transactions(self, year: int, month: int) -> List[Dict]:
        """ログ未作成時のサンプルデータ"""
        import random
        factor = SEASONAL_PROFILE.get(month, 1.0)
        base = 450_000 * factor
        return [
            {"proposed_account": "売上高", "amount": int(base * random.uniform(0.9, 1.1))},
            {"proposed_account": "部品購入費", "amount": -int(base * 0.35 * random.uniform(0.9, 1.1))},
            {"proposed_account": "給与", "amount": -80_000},
            {"proposed_account": "地代家賃", "amount": -50_000},
            {"proposed_account": "通信費", "amount": -8_000},
            {"proposed_account": "消耗品費", "amount": -int(12_000 * random.uniform(0.8, 1.2))},
            {"proposed_account": "広告宣伝費", "amount": -int(15_000 * random.uniform(0.5, 1.5))},
        ]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CFO Agent - 月次財務レポート")
    parser.add_argument("--year",  type=int, default=None)
    parser.add_argument("--month", type=int, default=None)
    args = parser.parse_args()
    CFOAgent().run(args.year, args.month)
