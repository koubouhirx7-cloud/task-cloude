from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import os
import datetime
import base64

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_SECRETARY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


# ─────────────────────────────────────────────
# Claude Vision でマルチモーダル解析
# ─────────────────────────────────────────────
def analyze_image_with_claude(image_b64: str, media_type: str, task_context: str) -> dict:
    """画像を Claude Vision で解析してタスク情報を抽出"""
    if not ANTHROPIC_API_KEY:
        return {"error": "ANTHROPIC_API_KEY が未設定", "summary": "", "extracted_text": "", "suggestions": []}

    prompt = f"""この画像を分析して、タスク管理のために以下を日本語で返答してください。

タスクのコンテキスト（ユーザーが入力した説明）: {task_context or "なし"}

以下の形式で JSON のみを返してください（他のテキストは不要）:
{{
  "extracted_text": "画像内のテキストをすべて書き起こし",
  "summary": "画像の内容を2〜3文で要約",
  "task_type": "web開発/デザイン/データ/文書/その他 から最も近いもの",
  "key_points": ["重要なポイント1", "重要なポイント2", "重要なポイント3"],
  "suggested_requirements": ["自動抽出した要件1", "自動抽出した要件2"],
  "suggested_team": ["推奨チームメンバー1", "推奨チームメンバー2"],
  "priority_hint": "high/medium/low の推奨（画像の内容から判断）"
}}"""

    payload = {
        "model": "claude-opus-4-5",
        "max_tokens": 1024,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64,
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    }

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "User-Agent": "Mozilla/5.0"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            result = json.loads(res.read().decode("utf-8"))
            text = result["content"][0]["text"].strip()
            # JSON部分を抽出
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            return json.loads(text)
    except Exception as e:
        return {
            "error": str(e),
            "summary": "解析エラー",
            "extracted_text": "",
            "key_points": [],
            "suggested_requirements": [],
            "suggested_team": [],
            "priority_hint": "medium"
        }


# ─────────────────────────────────────────────
# タスク分析ロジック
# ─────────────────────────────────────────────
def extract_requirements(description: str) -> list:
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


def select_team(category: str, scope: str) -> list:
    team = ["Plan Agent"]
    config = {
        "web": ["Frontend Dev", "Backend Dev", "Design Agent"],
        "agent": ["AI Engineer", "Integration Specialist"],
        "integration": ["Integration Specialist", "DevOps Engineer"],
        "automation": ["Automation Engineer", "DevOps Engineer"],
        "document": ["Tech Writer", "Content Specialist"],
        "design": ["Design Agent", "Frontend Dev"],
        "other": ["General Engineer"]
    }
    team.extend(config.get(category, ["General Engineer"]))
    if scope in ["medium", "large"]:
        team.append("Code Review Agent")
    return list(dict.fromkeys(team))


def estimate_duration(description: str, scope: str) -> dict:
    mapping = {"small": (1, 2), "medium": (3, 8), "large": (8, 24)}
    mn, mx = mapping.get(scope, (3, 8))
    if len(description) > 500:
        mx = int(mx * 1.5)
    return {"min_hours": mn, "max_hours": mx, "estimated_days": max(1, mx // 8)}


# ─────────────────────────────────────────────
# Discord 通知
# ─────────────────────────────────────────────
def send_discord(task: dict, analysis: dict, image_analysis: dict | None) -> bool:
    if not DISCORD_WEBHOOK:
        return False

    priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.get("priority", "medium"), "🟡")
    scope_label = {"small": "小", "medium": "中", "large": "大"}.get(task.get("scope", "medium"), "中")
    dur = analysis["duration"]

    fields = [
        {"name": "📋 タスク名", "value": task.get("name", "-"), "inline": True},
        {"name": f"{priority_emoji} 優先度", "value": task.get("priority", "medium"), "inline": True},
        {"name": "📁 分野", "value": task.get("category", "-"), "inline": True},
        {"name": "📏 スコープ", "value": scope_label, "inline": True},
        {"name": "⏱ 工数見積もり", "value": f"{dur['min_hours']}〜{dur['max_hours']}時間（約{dur['estimated_days']}日）", "inline": True},
        {"name": "👥 チーム構成", "value": " / ".join(analysis["team"]), "inline": False},
        {"name": "🔧 要件", "value": " / ".join(analysis["requirements"]), "inline": False},
        {"name": "📝 説明", "value": (task.get("description") or "-")[:500], "inline": False},
    ]

    # 画像解析結果を追加
    if image_analysis and not image_analysis.get("error"):
        if image_analysis.get("extracted_text"):
            fields.append({
                "name": "🖼 画像の文字起こし",
                "value": image_analysis["extracted_text"][:500],
                "inline": False
            })
        if image_analysis.get("summary"):
            fields.append({
                "name": "🔍 画像サマリー",
                "value": image_analysis["summary"],
                "inline": False
            })
        if image_analysis.get("key_points"):
            fields.append({
                "name": "💡 画像から抽出したポイント",
                "value": "\n".join([f"• {p}" for p in image_analysis["key_points"]]),
                "inline": False
            })

    fields.append({
        "name": "📅 行動計画",
        "value": "\n".join([f"Step {s['step']}: {s['action']} ({s['agent']})" for s in analysis["plan"]]),
        "inline": False
    })

    embed = {
        "embeds": [{
            "title": f"🚀 新規タスク: {task.get('name', 'Unknown')}",
            "color": 0x00b4d8 if not image_analysis else 0x7b2ff7,
            "fields": fields,
            "footer": {"text": f"{'📸 画像付き' if image_analysis else '📝 テキストのみ'} | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} JST"}
        }]
    }

    body = json.dumps(embed).encode("utf-8")
    req = urllib.request.Request(
        DISCORD_WEBHOOK, data=body,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            return res.status in (200, 204)
    except Exception:
        return False


# ─────────────────────────────────────────────
# Vercel Serverless Function エントリポイント
# ─────────────────────────────────────────────
class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        try:
            data = json.loads(body.decode("utf-8"))

            if not data.get("name") or not data.get("category") or not data.get("description"):
                self._respond(400, {"status": "error", "message": "name / category / description は必須です"})
                return

            # 画像が含まれている場合は Claude Vision で解析
            image_analysis = None
            images = data.get("images", [])
            if images:
                img = images[0]  # 最初の画像を解析（複数対応可能）
                b64 = img.get("data", "")
                media_type = img.get("media_type", "image/jpeg")
                if b64:
                    image_analysis = analyze_image_with_claude(
                        b64, media_type, data.get("description", "")
                    )
                    # 画像解析から優先度ヒントがある場合は反映
                    if image_analysis.get("priority_hint") and not data.get("priority"):
                        data["priority"] = image_analysis["priority_hint"]

            # タスク分析
            desc = data.get("description", "")
            # 画像の文字起こしがあれば説明に追記
            if image_analysis and image_analysis.get("extracted_text"):
                desc += "\n\n【画像から抽出】\n" + image_analysis["extracted_text"]

            analysis = {
                "requirements": extract_requirements(desc),
                "team": select_team(data.get("category", "other"), data.get("scope", "medium")),
                "duration": estimate_duration(desc, data.get("scope", "medium")),
                "plan": [
                    {"step": 1, "action": "要件定義・設計", "agent": "Plan Agent"},
                    {"step": 2, "action": "実装", "agent": "Development Team"},
                    {"step": 3, "action": "テスト・レビュー", "agent": "QA & Review"},
                    {"step": 4, "action": "納品", "agent": "Secretary AI"},
                ]
            }

            sent = send_discord(data, analysis, image_analysis)

            self._respond(200, {
                "status": "success",
                "message": "タスク受信・Discord通知完了 ✅" if sent else "タスク受信完了（Discord未設定）",
                "image_analyzed": image_analysis is not None,
                "analysis": analysis,
                "image_analysis": image_analysis
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
