---
enabled: false
channels:
  discord:
    enabled: false
    webhook_url_env: "DISCORD_WEBHOOK_URL"
    events: [high, normal]
  telegram:
    enabled: false
    bot_token_env: "TELEGRAM_BOT_TOKEN"
    chat_id_env: "TELEGRAM_CHAT_ID"
    events: [all]
  slack:
    enabled: false
    webhook_url_env: "SLACK_WEBHOOK_URL"
    events: [high]
  terminal:
    enabled: true
    events: [all]
---

# Messenger Configuration

This file controls pipeline notification delivery. The lead agent reads this
to determine where and when to send notifications.

## Severity Levels
- **high**: blocked, crashed, failed events
- **normal**: task advanced, role assigned
- **low**: task queued, dependency waiting
- **info**: batch completions, session summaries

## Setup
1. Set `enabled: true` at the top level.
2. Enable desired channels.
3. Set environment variables for each channel.
4. The lead agent handles formatting and delivery.
