from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import urllib.error
import os
import datetime

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_SECRETARY", "")

def extract_requirements(description):
    keywords = {
        "デザイン": ["色", "デザイン", "UI", "レイアウト", "見た目"],
        "機能": ["機能", "画面", "ボタン", "入力", "出力"],
        "統合": ["統合", "連携", "API", "データベース"],
        "パフォーマンス": ["高速", "最適化", "キャッシュ"],
        "セキュリティ": ["セキュリティ", "認証", "暗号化", "安全"],
        "ドキュメント": ["ドキュメント", "説明書", "ガイド", "マニュアル"]
    }
    reqs = [k for k, kws in keywords.items() if any(kw in description for kw in kws)]
    return reqs if reqs else ["基本実装"]

def select_team(category, scope):
    team = ["Plan Agent"]
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
    if scope in ["medium", "large"]:
        team.append("Code Review Agent")
    return list(dict.fromkeys(team))

def estimate_duration(description, scope):
    mapping = {"small": (1, 2), "medium": (3, 8), "large": (8, 24)}
    mn, mx = mapping.get(scope, (3, 8))
    if len(description) > 500:
        mx = int(mx * 1.5)
    return {"min_hours": mn, "max_hours": mx, "estimated_days": max(1, mx // 8)}

def send_discord(task, analysis):
    if not DISCORD_WEBHOOK:
        return False

    priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.get("priority", "medium"), "🟡")
    scope_label = {"small": "小", "medium": "中", "large": "大"}.get(task.get("scope", "medium"), "中")
    dur = analysis["duration"]

    embed = {
        "embeds": [{
            "title": f"🚀 新規タスク受信: {task.get('name', 'Unknown')}",
            "color": 0x00b4d8,
            "fields": [
                {"name": "📋 タスク名", "value": task.get("name", "-"), "inline": True},
                {"name": f"{priority_emoji} 優先度", "value": task.get("priority", "medium"), "inline": True},
                {"name": "📁 分野", "value": task.get("category", "-"), "inline": True},
                {"name": "📏 スコープ", "value": scope_label, "inline": True},
                {"name": "⏱ 工数見積もり", "value": f"{dur['min_hours']}〜{dur['max_hours']}時間（約{dur['estimated_days']}日）", "inline": True},
                {"name": "👥 チーム構成", "value": " / ".join(analysis["team"]), "inline": False},
                {"name": "🔧 要件", "value": " / ".join(analysis["requirements"]), "inline": False},
                {"name": "📝 説明", "value": task.get("description", "-")[:500], "inline": False},
                {"name": "📅 行動計画", "value": "\n".join([f"Step {s['step']}: {s['action']} ({s['agent']})" for s in analysis["plan"]]), "inline": False},
            ],
            "footer": {"text": f"受信時刻: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} JST"}
        }]
    }

    body = json.dumps(embed).encode("utf-8")
    req = urllib.request.Request(
        DISCORD_WEBHOOK,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            return res.status in (200, 204)
    except Exception:
        return False

class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        try:
            task = json.loads(body.decode("utf-8"))

            if not task.get("name") or not task.get("category") or not task.get("description"):
                self._respond(400, {"status": "error", "message": "name / category / description は必須です"})
                return

            analysis = {
                "requirements": extract_requirements(task["description"]),
                "team": select_team(task.get("category", "other"), task.get("scope", "medium")),
                "duration": estimate_duration(task["description"], task.get("scope", "medium")),
                "plan": [
                    {"step": 1, "action": "要件定義・設計", "agent": "Plan Agent"},
                    {"step": 2, "action": "実装", "agent": "Development Team"},
                    {"step": 3, "action": "テスト・レビュー", "agent": "QA & Review"},
                    {"step": 4, "action": "納品", "agent": "Secretary AI"},
                ]
            }

            sent = send_discord(task, analysis)

            self._respond(200, {
                "status": "success",
                "message": "タスク受信・Discord通知送信完了 ✅" if sent else "タスク受信完了（Discord未設定）",
                "analysis": analysis
            })

        except Exception as e:
            self._respond(500, {"status": "error", "message": str(e)})

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _respond(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def log_message(self, format, *args):
        pass
