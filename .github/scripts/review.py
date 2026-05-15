import anthropic
import subprocess
import requests
import os
import sys

try:
    diff = subprocess.check_output([
        'git', 'diff', 'HEAD~1', 'HEAD',
        '--',
        ':(exclude).env',
        ':(exclude).env.*',
        ':(exclude)*.key',
        ':(exclude)*.pem',
    ]).decode()
except subprocess.CalledProcessError as e:
    print(f"git diff error: {e}")
    sys.exit(1)

if not diff.strip():
    print("No diff found")
    sys.exit(0)

if len(diff) > 3000:
    diff = diff[:3000] + "\n\n...(truncated)"

try:
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"Please review the following code in Japanese:\n\n{diff}"
        }]
    )
    review = response.content[0].text
except anthropic.APIError as e:
    print(f"Claude API error: {e}")
    sys.exit(1)

MAX_SLACK_LENGTH = 2900
if len(review) > MAX_SLACK_LENGTH:
    review = review[:MAX_SLACK_LENGTH] + "\n...(truncated)"

try:
    webhook_url = os.environ['SLACK_WEBHOOK_URL']
    result = requests.post(webhook_url, json={
        "text": f"*Claude Code Review*\n\n{review}"
    }, timeout=10)
    result.raise_for_status()
except requests.RequestException as e:
    print(f"Slack error: {e}")

print(review)