from openai import OpenAI
from dotenv import load_dotenv
import json
from tavily import TavilyClient
import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.message import EmailMessage

load_dotenv()
client = OpenAI()
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY") or os.getenv("TRAVILY_API_KEY"))


def send_email(to, subject, body):
    sender = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_APP_PASSWORD")

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
    except Exception as e:
        return False, str(e)


def get_time():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calculator(a, b, operation):
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        try:
            return a / b
        except ZeroDivisionError:
            return "Error: Division by zero is not allowed."


seen_urls = set()

def web_search(query, current_search_limit):
    response = tavily_client.search(
        query=query,
        max_results=current_search_limit
    )

    results = []

    for item in response["results"]:
        if item["url"] not in seen_urls:
            seen_urls.add(item["url"])
            results.append({
                "title": item["title"],
                "url": item["url"],
                "snippet": item["content"]
            })

    return results


webpage_cache = {}
read_sources = []

def read_webpage(url):
    if url in webpage_cache:
        if url not in read_sources:
            read_sources.append(url)
        return webpage_cache[url]

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)

        webpage_cache[url] = text[:3000]

        if url not in read_sources:
            read_sources.append(url)

        return webpage_cache[url]

    except requests.exceptions.RequestException as e:
        return f"Error fetching the webpage: {e}"


tools = [
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
                        "enum": ["add", "subtract", "multiply", "divide"]
                    }
                },
                "required": ["a", "b", "operation"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "Get the current time.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_webpage",
            "description": "Read the content of a webpage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"}
                },
                "required": ["url"]
            }
        }
    }
]


tool_map = {
    "calculator": calculator,
    "get_time": get_time,
    "web_search": web_search,
    "read_webpage": read_webpage
}


def execute_tool_call(tool_call, current_search_limit):
    try:
        tool_name = tool_call.function.name
        tool_func = tool_map[tool_name]

        args = json.loads(tool_call.function.arguments)

        if tool_name == "web_search":
            args["current_search_limit"] = current_search_limit

        return json.dumps(tool_func(**args))

    except Exception as e:
        return json.dumps({
            "error": str(e)
        })


def build_source_context():
    if not seen_urls:
        return None

    lines = [
        f"- {url} (read in full)" if url in read_sources else f"- {url} (search snippet only)"
        for url in seen_urls
    ]

    return "Known sources - if you cite sources, use only these exact URLs:\n" + "\n".join(lines)


def cleanup_messages(messages):
    system_message = messages[0]
    user_assistant_messages = []

    for msg in messages[1:]:
        if isinstance(msg, dict):
            role = msg["role"]
            has_tool_calls = False
        else:
            role = msg.role
            has_tool_calls = bool(msg.tool_calls)

        if role in ["user", "assistant"] and not has_tool_calls:
            user_assistant_messages.append(msg)

    return [system_message] + user_assistant_messages[-4:]


messages = [
    {
        "role": "system",
        "content": "Use tools when needed especially when it involves real time information and answer in 5-6 lines but if you have accessed web information then provide source as well. If it does not need tool calling then answer in 4-5 sentences."
    }
]


user_input = input("Type a message or type 'exit' to quit: ")

while user_input.strip().lower() != "exit":
    read_sources.clear()
    seen_urls.clear()

    is_email_request = False
    email_to = None

    if user_input.lower().startswith("research:"):
        query = user_input[9:].strip()
        current_search_limit = 5

        is_email_request = input("Do you want to send the research results via email? (yes/no): ").strip().lower() == "yes"
        if is_email_request:
            email_to = input("Enter the email address: ").strip()

        user_message = f"""
You are in RESEARCH MODE.

Topic: {query}

Required workflow:
1. Call web_search.
2. Call read_webpage on useful URLs from search results.
3. Write the final answer only from tool results.

Required final format:
Summary: 3-4 lines

Key Points: bullet points

Sources: links to the sources used for the answer

Limitations (if any): bullet points
"""
    else:
        user_message = user_input
        current_search_limit = 3

    messages.append({
        "role": "user",
        "content": user_message
    })

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools
    )

    message = response.choices[0].message

    max_steps = 5
    step_count = 0

    while message.tool_calls and step_count < max_steps:
        step_count += 1
        messages.append(message)

        for tool_call in message.tool_calls:
            result = execute_tool_call(tool_call, current_search_limit)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            })

        source_context = build_source_context()
        if source_context:
            messages.append({
                "role": "system",
                "content": source_context
            })

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools
        )

        message = response.choices[0].message

    if message.tool_calls:
        stop_message = "Stop using tools now. Summarize the findings from the tool results already available."

        source_context = build_source_context()
        if source_context:
            stop_message += "\n\n" + source_context

        messages.append({
            "role": "user",
            "content": stop_message
        })

        final_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        message = final_response.choices[0].message

    if is_email_request:
        email_subject = f"Research Results for: {query}"
        email_body = message.content or "(no content generated)"
        sent, error = send_email(to=email_to, subject=email_subject, body=email_body)
        if sent:
            print(f"Research results sent via email to {email_to}.")
        else:
            print(f"Failed to send email: {error}")
            print(message.content)
    else:
        print(message.content)

    messages.append(message)
    messages = cleanup_messages(messages)

    user_input = input("Type a message or type 'exit' to quit: ")
