import ipaddress
import json
import logging
import os
import re
import smtplib
import socket
from datetime import datetime
from email.message import EmailMessage
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from tavily import TavilyClient


SYSTEM_PROMPT = (
    "You are Loid, the calm research and intelligence agent inside ResearchOps AI. "
    "You are professional, precise, discreet, and concise. Do not mention, copy, "
    "or imitate any copyrighted character, franchise, or protected style. "
    "Use tools when needed, especially when the user asks for real-time information. "
    "When you use web information, cite intelligence sources with exact links. "
    "In mission mode, treat the task as a mission, the query as an objective, "
    "and the final answer as a research brief. "
    "In normal mode (when not in mission mode), always restrict your answer to exactly 5-6 lines and format your response in Markdown."
)


logger = logging.getLogger(__name__)
MAX_WEBPAGE_BYTES = 1_000_000
ALLOWED_CONTENT_TYPES = ("text/html", "text/plain", "application/xhtml+xml")


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Perform basic arithmetic operations on two numbers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number"},
                    "b": {"type": "number"},
                    "operation": {
                        "type": "string",
                        "enum": ["add", "subtract", "multiply", "divide"],
                    },
                },
                "required": ["a", "b", "operation"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "Get the current time.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for information.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_webpage",
            "description": "Read the content of a webpage.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
        },
    },
]


def calculator(a, b, operation):
    if operation == "add":
        return a + b
    if operation == "subtract":
        return a - b
    if operation == "multiply":
        return a * b
    if operation == "divide":
        try:
            return a / b
        except ZeroDivisionError:
            return "Error: Division by zero is not allowed."
    return "Error: Unsupported operation."


class ResearchAssistant:
    def __init__(self):
        self.client = OpenAI()
        tavily_key = os.getenv("TAVILY_API_KEY") or os.getenv("TRAVILY_API_KEY")
        self.tavily_client = TavilyClient(api_key=tavily_key) if tavily_key else None
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.seen_urls = set()
        self.seen_url_order = []
        self.read_sources = []
        self.webpage_cache = {}

    def get_time(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def web_search(self, query, current_search_limit):
        if not self.tavily_client:
            return {"error": "Tavily API key is not configured."}

        response = self.tavily_client.search(query=query, max_results=current_search_limit)
        results = []

        for item in response.get("results", []):
            url = item.get("url")
            if not url:
                continue

            try:
                safe_url = self.normalize_public_url(url)
            except ValueError:
                continue

            if safe_url not in self.seen_urls:
                self.remember_source(safe_url)
                results.append(
                    {
                        "title": item.get("title", "Untitled"),
                        "url": safe_url,
                        "snippet": item.get("content", ""),
                    }
                )

        return results

    def read_webpage(self, url):
        try:
            safe_url = self.normalize_public_url(url)
        except ValueError:
            return "Error fetching the webpage: that URL is not available for research."

        self.remember_source(safe_url)

        if safe_url in self.webpage_cache:
            if safe_url not in self.read_sources:
                self.read_sources.append(safe_url)
            return self.webpage_cache[safe_url]

        try:
            page_text = self.fetch_public_webpage(safe_url)
            soup = BeautifulSoup(page_text, "html.parser")
            text = soup.get_text(separator=" ", strip=True)
            self.webpage_cache[safe_url] = text[:3000]

            if safe_url not in self.read_sources:
                self.read_sources.append(safe_url)

            return self.webpage_cache[safe_url]
        except (ValueError, requests.exceptions.RequestException):
            logger.info("Blocked or failed webpage read for %s", safe_url, exc_info=True)
            return "Error fetching the webpage: that page could not be read."

    def normalize_public_url(self, url):
        parsed = urlparse((url or "").strip())
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("Only HTTP and HTTPS URLs are supported.")
        if parsed.username or parsed.password:
            raise ValueError("URLs with embedded credentials are not supported.")
        if not parsed.hostname:
            raise ValueError("URL host is required.")

        hostname = parsed.hostname.lower().rstrip(".")
        if (
            hostname == "localhost"
            or hostname.endswith(".localhost")
            or hostname.endswith(".local")
        ):
            raise ValueError("Private hosts are not available for research.")

        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        try:
            addresses = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
        except socket.gaierror as error:
            raise ValueError("URL host could not be resolved.") from error

        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])
            if not ip.is_global:
                raise ValueError("Private network addresses are not available for research.")

        return parsed.geturl()

    def fetch_public_webpage(self, url):
        current_url = self.normalize_public_url(url)

        for _redirect in range(4):
            current_url = self.normalize_public_url(current_url)
            with requests.get(
                current_url,
                timeout=10,
                allow_redirects=False,
                stream=True,
                headers={"User-Agent": "ResearchOpsAI-Loid/1.0"},
            ) as response:
                if 300 <= response.status_code < 400:
                    location = response.headers.get("Location")
                    if not location:
                        raise requests.exceptions.TooManyRedirects("Redirect without a location header.")
                    current_url = urljoin(response.url, location)
                    continue

                response.raise_for_status()
                content_type = response.headers.get("Content-Type", "").lower()
                if content_type and not any(value in content_type for value in ALLOWED_CONTENT_TYPES):
                    raise ValueError("Only text webpages can be read.")

                chunks = []
                total_size = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    total_size += len(chunk)
                    if total_size > MAX_WEBPAGE_BYTES:
                        break
                    chunks.append(chunk)

                encoding = response.encoding or response.apparent_encoding or "utf-8"
                return b"".join(chunks).decode(encoding, errors="replace")

        raise requests.exceptions.TooManyRedirects("Too many redirects.")

    def remember_source(self, url):
        if not url or url in self.seen_urls:
            return

        self.seen_urls.add(url)
        self.seen_url_order.append(url)

    def source_urls(self):
        urls = list(self.seen_url_order)
        for url in self.read_sources:
            if url not in self.seen_urls:
                urls.append(url)
        return urls

    def send_email(self, to, subject, body):
        sender = os.getenv("EMAIL_ADDRESS")
        password = os.getenv("EMAIL_APP_PASSWORD")

        if not sender or not password:
            return False, "Email credentials are not configured."

        msg = EmailMessage()
        msg["From"] = sender
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(sender, password)
                smtp.send_message(msg)
            return True, None
        except Exception:
            logger.exception("Email send failed.")
            return False, "Email could not be sent right now."

    def build_source_context(self):
        if not self.seen_urls:
            return None

        lines = [
            f"- {url} (read in full)" if url in self.read_sources else f"- {url} (search snippet only)"
            for url in self.source_urls()
        ]
        return "Known intelligence sources. If you cite sources, use only these exact URLs:\n" + "\n".join(lines)

    def replace_sources_section(self, content):
        source_urls = self.source_urls()
        if not source_urls:
            return content

        source_lines = ["Intelligence sources:"] + [f"- {url}" for url in source_urls]
        lines = content.strip().splitlines()
        source_heading = re.compile(
            r"^\s*(?:#+\s*)?\*{0,2}\s*(?:intelligence\s+)?sources?\s*:?\s*\*{0,2}\s*$",
            re.I,
        )
        next_heading = re.compile(
            r"^\s*(?:#+\s*)?\*{0,2}\s*(research brief|summary|key intelligence|key points?|limitations?(?:\s*\([^)]*\))?|conclusion|notes?)\s*:?\s*\*{0,2}\s*$",
            re.I,
        )

        start = None
        for index, line in enumerate(lines):
            if source_heading.match(line):
                start = index
                break

        if start is None:
            return content.strip() + "\n\n" + "\n".join(source_lines)

        end = len(lines)
        for index in range(start + 1, len(lines)):
            line = lines[index].strip()
            if line and next_heading.match(line):
                end = index
                break

        replacement = lines[:start] + source_lines
        if end < len(lines):
            replacement += [""] + lines[end:]

        return "\n".join(replacement).strip()

    def cleanup_messages(self):
        system_message = self.messages[0]
        user_assistant_messages = []

        for msg in self.messages[1:]:
            if isinstance(msg, dict):
                role = msg["role"]
                has_tool_calls = False
            else:
                role = msg.role
                has_tool_calls = bool(msg.tool_calls)

            if role in ["user", "assistant"] and not has_tool_calls:
                user_assistant_messages.append(msg)

        self.messages = [system_message] + user_assistant_messages[-6:]

    def execute_tool_call(self, tool_call, current_search_limit):
        tool_map = {
            "calculator": calculator,
            "get_time": self.get_time,
            "web_search": self.web_search,
            "read_webpage": self.read_webpage,
        }

        try:
            tool_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments or "{}")

            if tool_name == "web_search":
                args["current_search_limit"] = current_search_limit

            return json.dumps(tool_map[tool_name](**args))
        except Exception:
            logger.exception("Tool call failed.")
            return json.dumps({"error": "The tool could not complete that request."})

    def build_user_message(self, prompt, mode):
        if mode != "research":
            return prompt, 3

        return (
            f"""
You are Loid in MISSION MODE.

Objective: {prompt}

Required operation:
1. Call web_search to identify relevant intelligence sources.
2. Call read_webpage on useful URLs from search results.
3. Prepare the research brief only from tool results.

Required intelligence brief format:
Research brief: 3-4 lines

Key intelligence: bullet points

Intelligence sources: links to the sources used for the brief

Limitations (if any): bullet points

Mission complete.
""",
            5,
        )

    def chat(self, prompt, mode="chat", email_to=None):
        self.read_sources.clear()
        self.seen_urls.clear()
        self.seen_url_order.clear()

        user_message, current_search_limit = self.build_user_message(prompt, mode)
        self.messages.append({"role": "user", "content": user_message})

        response = self.client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=self.messages,
            tools=TOOLS,
        )
        message = response.choices[0].message

        step_count = 0
        while message.tool_calls and step_count < 5:
            step_count += 1
            self.messages.append(message)

            for tool_call in message.tool_calls:
                result = self.execute_tool_call(tool_call, current_search_limit)
                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result),
                    }
                )

            source_context = self.build_source_context()
            if source_context:
                self.messages.append({"role": "system", "content": source_context})

            response = self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=self.messages,
                tools=TOOLS,
            )
            message = response.choices[0].message

        if message.tool_calls:
            stop_message = "Stop executing operations now. Prepare the intelligence brief from the available tool results."
            source_context = self.build_source_context()
            if source_context:
                stop_message += "\n\n" + source_context

            self.messages.append({"role": "user", "content": stop_message})
            final_response = self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=self.messages,
            )
            message = final_response.choices[0].message

        content = message.content or "(no content generated)"
        content = self.replace_sources_section(content)
        email_status = None

        if email_to:
            sent, error = self.send_email(
                to=email_to,
                subject=f"ResearchOps AI brief: {prompt}",
                body=content,
            )
            email_status = {"sent": sent, "error": error}

        self.messages.append({"role": "assistant", "content": content})
        self.cleanup_messages()

        return {
            "answer": content,
            "sources": self.source_urls(),
            "read_sources": list(self.read_sources),
            "email": email_status,
        }
