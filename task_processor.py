#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Processor - スマホ入力タスクの自動解析・処理エンジン
ユーザーが入力したタスクを分析して、自動的に開発チームを編成
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import urllib.request
import urllib.error
import subprocess
from dotenv import load_dotenv

# .env ファイルを読み込み
load_dotenv()


class TaskProcessor:
    """タスク自動処理エンジン"""

    def __init__(self):
        self.task_dir = Path("/Users/murakamidaisuke/Documents/会計情報/tasks")
        self.task_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir = self.task_dir / "processed"
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.discord_webhook = os.environ.get("DISCORD_WEBHOOK_SECRETARY", "")

    def read_task(self, task_file: Path) -> Dict[str, Any]:
        """タスクファイルを読み込み"""
        try:
            with open(task_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ タスク読み込みエラー: {e}")
            return None

    def analyze_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """タスクを自動分析"""
        print(f"\n🔍 タスク分析中: {task['name']}")

        analysis = {
            "original_task": task,
            "analyzed_at": datetime.now().isoformat(),
            "requirements": self._extract_requirements(task['description']),
            "team_members": self._select_team(task['category'], task['scope']),
            "estimated_duration": self._estimate_duration(task['description'], task['scope']),
            "action_plan": self._generate_action_plan(task),
            "status": "準備中"
        }

        return analysis

    def _extract_requirements(self, description: str) -> List[str]:
        """要件を自動抽出"""
        requirements = []

        # キーワードベースの抽出
        keywords = {
            "デザイン": ["色", "デザイン", "UI", "レイアウト", "見た目"],
            "機能": ["機能", "画面", "ボタン", "入力", "出力"],
            "統合": ["統合", "連携", "API", "データベース"],
            "パフォーマンス": ["高速", "最適化", "キャッシュ"],
            "セキュリティ": ["セキュリティ", "認証", "暗号化", "安全"],
            "ドキュメント": ["ドキュメント", "説明書", "ガイド", "マニュアル"]
        }

        for category, keywords_list in keywords.items():
            if any(kw in description for kw in keywords_list):
                requirements.append(category)

        return requirements if requirements else ["基本実装"]

    def _select_team(self, category: str, scope: str) -> List[str]:
        """タスク内容に応じてチームメンバーを選定"""
        team = ["Plan Agent"]  # 常に計画エージェント

        # カテゴリに応じた適切なメンバーを追加
        team_config = {
            "web": ["Frontend Dev", "Backend Dev", "Design Agent"],
            "agent": ["AI Engineer", "Integration Specialist"],
            "integration": ["Integration Specialist", "DevOps Engineer"],
            "automation": ["Automation Engineer", "DevOps Engineer"],
            "document": ["Tech Writer", "Content Specialist"],
            "design": ["Design Agent", "Frontend Dev"],
            "other": ["General Engineer"]
        }

        team.extend(team_config.get(category, ["General Engineer"]))

        # スコープに応じてレビュアーを追加
        if scope in ["medium", "large"]:
            team.append("Code Review Agent")

        return list(dict.fromkeys(team))  # 重複を削除

    def _estimate_duration(self, description: str, scope: str) -> Dict[str, Any]:
        """所要時間を見積もり"""
        scope_mapping = {
            "small": (1, 2),
            "medium": (3, 8),
            "large": (8, 24)
        }

        min_hours, max_hours = scope_mapping.get(scope, (3, 8))

        # 説明文の長さで調整
        if len(description) > 500:
            max_hours = max_hours * 1.5

        return {
            "min_hours": int(min_hours),
            "max_hours": int(max_hours),
            "estimated_days": max(1, int(max_hours / 8))
        }

    def _generate_action_plan(self, task: Dict[str, Any]) -> List[Dict[str, str]]:
        """行動計画を自動生成"""
        plan = [
            {
                "step": 1,
                "action": "要件定義・設計",
                "agent": "Plan Agent",
                "description": f"'{task['name']}' の詳細計画を作成"
            },
            {
                "step": 2,
                "action": "実装",
                "agent": "Development Team",
                "description": "計画に基づいて実装を開始"
            },
            {
                "step": 3,
                "action": "テスト・レビュー",
                "agent": "QA & Review",
                "description": "品質確保とコードレビュー"
            },
            {
                "step": 4,
                "action": "納品",
                "agent": "Secretary AI",
                "description": "完成物をユーザーに報告"
            }
        ]

        return plan

    def launch_development_team(self, analysis: Dict[str, Any]) -> bool:
        """開発チームを自動起動"""
        print(f"\n🚀 開発チーム起動中...")
        print(f"   チームメンバー: {', '.join(analysis['team_members'])}")

        # Plan Agent を最初に実行
        team_config = analysis['team_members']

        # チーム起動メッセージを作成
        message = self._build_team_launch_message(analysis)

        # Discord に通知
        if self.send_to_discord(message):
            # タスク実行スクリプトを生成・実行
            script_path = self._generate_execution_script(analysis)
            print(f"✅ 実行スクリプト生成: {script_path}")
            return True
        else:
            print("❌ Discord 通知失敗")
            return False

    def _build_team_launch_message(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """チーム起動メッセージを構築"""
        task = analysis['original_task']
        duration = analysis['estimated_duration']
        team = analysis['team_members']

        message = {
            "username": "🚀 Development Team Launcher",
            "avatar_url": "https://img.icons8.com/color/96/000000/rocket.png",
            "embeds": [
                {
                    "title": f"🎯 新規タスク: {task['name']}",
                    "description": f"優先度: **{task['priority'].upper()}** | 分野: **{task['category']}**",
                    "color": 16711680 if task['priority'] == 'high' else 16776960 if task['priority'] == 'medium' else 3394560,
                    "fields": [
                        {
                            "name": "📝 説明",
                            "value": task['description'][:200] + "..." if len(task['description']) > 200 else task['description'],
                            "inline": False
                        },
                        {
                            "name": "⏰ 所要時間",
                            "value": f"{duration['min_hours']}-{duration['max_hours']}時間 (~{duration['estimated_days']}日)",
                            "inline": True
                        },
                        {
                            "name": "📅 期限",
                            "value": task.get('deadline', '指定なし'),
                            "inline": True
                        },
                        {
                            "name": "👥 チームメンバー",
                            "value": "\n".join([f"• {member}" for member in team]),
                            "inline": False
                        },
                        {
                            "name": "📋 行動計画",
                            "value": "\n".join([f"**Step {p['step']}**: {p['action']} ({p['agent']})" for p in analysis['action_plan']]),
                            "inline": False
                        }
                    ],
                    "footer": {
                        "text": f"Task ID: {datetime.now().strftime('%Y%m%d%H%M%S')}"
                    }
                }
            ]
        }

        return message

    def _generate_execution_script(self, analysis: Dict[str, Any]) -> Path:
        """タスク実行スクリプトを生成"""
        task_id = datetime.now().strftime('%Y%m%d%H%M%S')
        script_path = self.task_dir / f"{task_id}_execution.sh"

        script_content = f"""#!/bin/bash
# 自動生成タスク実行スクリプト
# Task: {analysis['original_task']['name']}
# Generated: {datetime.now().isoformat()}

cd ~/Documents/会計情報

# Plan Agent を実行
echo "📋 実装計画を作成中..."
# python3 plan_agent.py --task '{analysis['original_task']['name']}'

# Development Team を起動
echo "🚀 開発チームを起動..."
# python3 dev_team.py --config '{script_path.stem}.json'

# 完了通知
echo "✅ タスク実行完了"
"""

        try:
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            os.chmod(script_path, 0o755)
        except Exception as e:
            print(f"❌ スクリプト生成エラー: {e}")

        return script_path

    def send_to_discord(self, message: Dict[str, Any]) -> bool:
        """Discord に送信"""
        if not self.discord_webhook:
            print("⚠️ DISCORD_WEBHOOK_SECRETARY が設定されていません")
            return False

        data = json.dumps(message, ensure_ascii=False).encode('utf-8')

        try:
            req = urllib.request.Request(
                self.discord_webhook,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 TaskProcessor/1.0"
                }
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 204:
                    print("✅ Discord 通知送信完了")
                    return True
                else:
                    print(f"⚠️ Discord 送信: ステータス {response.status}")
                    return False

        except Exception as e:
            print(f"❌ Discord 送信エラー: {e}")
            return False

    def save_analysis(self, task_file: Path, analysis: Dict[str, Any]):
        """分析結果を保存"""
        try:
            processed_file = self.processed_dir / f"{task_file.stem}_analysis.json"
            with open(processed_file, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, ensure_ascii=False, indent=2)
            print(f"✓ 分析結果保存: {processed_file}")
        except Exception as e:
            print(f"❌ 分析結果保存エラー: {e}")

    def process_tasks(self):
        """スケジュール実行: 新規タスクを検出して処理"""
        print("\n📥 新規タスクをスキャン中...")

        # タスク保存ディレクトリから新規タスクを検出
        task_files = list(self.task_dir.glob("*.json"))

        if not task_files:
            print("📭 新規タスクなし")
            return

        for task_file in task_files:
            # 既に処理済みのファイルはスキップ
            if (self.processed_dir / f"{task_file.stem}_analysis.json").exists():
                continue

            print(f"\n🔄 処理中: {task_file.name}")

            task = self.read_task(task_file)
            if not task:
                continue

            # タスク分析
            analysis = self.analyze_task(task)

            # 開発チーム起動
            if self.launch_development_team(analysis):
                # 分析結果を保存
                self.save_analysis(task_file, analysis)
                print(f"✅ タスク処理完了")
            else:
                print(f"❌ タスク処理失敗")


def main():
    processor = TaskProcessor()
    processor.process_tasks()


if __name__ == "__main__":
    main()
