"""Simple browser-based chatbot UI for problem discovery results.

Run with:
    python3 productpilot/apps/web_discovery_chatbot.py
Then open http://localhost:8000
"""

from __future__ import annotations

import json
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from productpilot.agents.web_problem_discovery_agent import KeywordWebDiscoveryAgent


HTML_PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Product Discovery Chatbot</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      background: #f3f5f9;
      margin: 0;
      color: #17202a;
    }
    .container {
      max-width: 980px;
      margin: 30px auto;
      background: white;
      border-radius: 14px;
      box-shadow: 0 8px 30px rgba(0,0,0,0.08);
      padding: 24px;
    }
    h1 {
      margin-top: 0;
      font-size: 28px;
    }
    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
    }
    textarea, input, button {
      width: 100%;
      box-sizing: border-box;
      padding: 12px 14px;
      border-radius: 10px;
      border: 1px solid #d9e1ec;
      font-size: 14px;
      margin-top: 8px;
    }
    button {
      background: #1d4ed8;
      color: white;
      border: none;
      cursor: pointer;
      font-weight: 600;
      margin-top: 12px;
    }
    .panel {
      padding: 18px;
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      background: #fafbff;
    }
    .problem-list {
      margin-top: 16px;
      padding-left: 20px;
      line-height: 1.7;
    }
    .chat-box {
      margin-top: 20px;
      background: #f8fafc;
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      min-height: 180px;
      padding: 16px;
    }
    .message {
      margin-bottom: 10px;
      padding: 10px 12px;
      border-radius: 10px;
      line-height: 1.5;
    }
    .user {
      background: #dbeafe;
      margin-left: 20px;
    }
    .bot {
      background: #e5e7eb;
      margin-right: 20px;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Product Discovery Chatbot</h1>

    <div class="grid">
      <div class="panel">
        <label for="contextInput">Context / keyword / problem file text</label>
        <textarea id="contextInput" rows="8" placeholder="Paste a keyword or short problem context here...">project management</textarea>
        <button id="discoverBtn">Fetch problem statements</button>
        <div id="problemBox" class="problem-list"></div>
      </div>

      <div class="panel">
        <label for="questionInput">Ask a question</label>
        <input id="questionInput" type="text" placeholder="Example: What is the biggest issue?" />
        <button id="askBtn">Ask</button>
        <div id="chatBox" class="chat-box"></div>
      </div>
    </div>
  </div>

  <script>
    let discoveredProblems = [];

    function addMessage(sender, text) {
      const box = document.getElementById('chatBox');
      const div = document.createElement('div');
      div.className = 'message ' + sender;
      div.textContent = text;
      box.appendChild(div);
    }

    async function fetchProblems() {
      const value = document.getElementById('contextInput').value.trim();
      if (!value) {
        addMessage('bot', 'Please add some context or a keyword first.');
        return;
      }

      const res = await fetch('/api/discover', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ context: value })
      });

      const data = await res.json();
      discoveredProblems = data.problem_statements || [];

      const problemBox = document.getElementById('problemBox');
      problemBox.innerHTML = '';
      if (discoveredProblems.length === 0) {
        problemBox.textContent = 'No problems were found.';
        return;
      }

      const list = document.createElement('ol');
      discoveredProblems.forEach((problem) => {
        const li = document.createElement('li');
        li.textContent = problem;
        list.appendChild(li);
      });
      problemBox.appendChild(list);

      addMessage('bot', 'I fetched ' + discoveredProblems.length + ' problem statements. Ask a question about them.');
    }

    async function askQuestion() {
      const question = document.getElementById('questionInput').value.trim();
      if (!question) {
        addMessage('bot', 'Please enter a question.');
        return;
      }

      addMessage('user', question);
      const res = await fetch('/api/ask', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ question, problem_statements: discoveredProblems })
      });

      const data = await res.json();
      addMessage('bot', data.answer || 'I could not find an answer in the fetched context.');
    }

    document.getElementById('discoverBtn').addEventListener('click', fetchProblems);
    document.getElementById('askBtn').addEventListener('click', askQuestion);
    document.getElementById('questionInput').addEventListener('keydown', function (event) {
      if (event.key === 'Enter') askQuestion();
    });

    fetchProblems();
  </script>
</body>
</html>
"""


class WebDiscoveryChatbotApp:
    def __init__(self) -> None:
        self.agent = KeywordWebDiscoveryAgent()
        self.last_problem_statements: list[str] = []

    def discover_from_context(self, context: str) -> list[str]:
        context = (context or "").strip()
        if not context:
            raise ValueError("Context cannot be empty")

        result = self.agent.run(context)
        pointers = result.get("problem_statements") or []
        self.last_problem_statements = [str(p) for p in pointers]
        return self.last_problem_statements

    def answer_question(self, question: str, problem_statements: list[str] | None = None) -> str:
        question = (question or "").strip()
        problems = problem_statements or self.last_problem_statements
        if not question:
            return "Please ask a question about the discovered problems."
        if not problems:
            return "No discovery data is available yet. Fetch problem statements first."

        q = question.lower()
        if any(token in q for token in ["what are", "list", "show", "problems", "issues"]):
            return "\n".join(f"{idx + 1}. {problem}" for idx, problem in enumerate(problems[:5]))

        scored: list[tuple[int, str]] = []
        for problem in problems:
            problem_lower = problem.lower()
            score = 0
            for word in re.findall(r"[a-z0-9]+", q):
                if len(word) < 3:
                    continue
                if word in problem_lower:
                    score += 2
                if problem_lower.count(word) > 0:
                    score += 1
            scored.append((score, problem))

        scored.sort(key=lambda item: item[0], reverse=True)
        best = scored[0][1] if scored and scored[0][0] > 0 else problems[0]
        if scored and scored[0][0] == 0:
            return (
                "Based on the fetched context, the main themes are: "
                + "; ".join(problem for problem in problems[:3])
            )

        return (
            "The most relevant issue is: "
            + best
            + "\n\nRelated themes: "
            + "; ".join(problem for _, problem in scored[:3])
        )


def _json_response(handler: BaseHTTPRequestHandler, payload: dict[str, Any], status: int = 200) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


app = WebDiscoveryChatbotApp()


class DiscoveryRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            page = HTML_PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()
            self.wfile.write(page)
            return
        self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        body = json.loads(raw.decode("utf-8")) if raw else {}

        if parsed.path == "/api/discover":
            try:
                context = str(body.get("context") or "")
                problems = app.discover_from_context(context)
                _json_response(self, {"problem_statements": problems})
                return
            except Exception as exc:  # pragma: no cover - runtime safety
                _json_response(self, {"error": str(exc)}, status=400)
                return

        if parsed.path == "/api/ask":
            try:
                question = str(body.get("question") or "")
                problems = body.get("problem_statements") or app.last_problem_statements
                answer = app.answer_question(question, list(problems))
                _json_response(self, {"answer": answer})
                return
            except Exception as exc:  # pragma: no cover - runtime safety
                _json_response(self, {"error": str(exc)}, status=400)
                return

        self.send_error(404)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), DiscoveryRequestHandler)
    print("Product discovery chatbot running at http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()
