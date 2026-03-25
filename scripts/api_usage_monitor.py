#!/usr/bin/env python3
"""
OpenClaw API Usage Monitor v1.0

Tracks Anthropic API usage from gateway logs and auth-profiles.json.
Compares against configurable budget thresholds (50%, 75%, 90%).
Sends Telegram alerts on threshold breaches.
Updates memory/api-usage-state.json for cost-gate checks by agents.

Run: python3 scripts/api_usage_monitor.py
Integrated into: selfheal.sh (every 10 min) or standalone LaunchAgent (hourly)
"""

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── Configuration ────────────────────────────────────────────────────
WORKSPACE = Path.home() / ".openclaw" / "workspace"
STATE_FILE = WORKSPACE / "memory" / "api-usage-state.json"
USAGE_LOG = WORKSPACE / "logs" / "api_usage.jsonl"
INCIDENTS_FILE = WORKSPACE / "memory" / "incidents.jsonl"
AUTH_PROFILES = Path.home() / ".openclaw" / "agents" / "main" / "agent" / "auth-profiles.json"
GW_LOG = Path.home() / ".openclaw" / "logs" / "gateway.log"
GW_ERR_LOG = Path.home() / ".openclaw" / "logs" / "gateway.err.log"
CONFIG_FILE = Path.home() / ".openclaw" / "openclaw.json"

# Budget defaults (can be overridden in openclaw.json under "budget")
DEFAULT_MONTHLY_BUDGET_USD = 100.0
DEFAULT_WARN_THRESHOLD = 0.75  # 75%
DEFAULT_CRITICAL_THRESHOLD = 0.90  # 90%
DEFAULT_INFO_THRESHOLD = 0.50  # 50%

# Approximate token pricing (per 1M tokens, as of March 2026)
PRICING = {
    "anthropic": {"input": 15.00, "output": 75.00},   # Opus 4.6
    "anthropic_sonnet": {"input": 3.00, "output": 15.00},  # Sonnet 4.6
    "openai": {"input": 5.00, "output": 15.00},
    "xai": {"input": 2.00, "output": 10.00},
}


def load_config():
    """Load budget config from openclaw.json."""
    try:
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        budget = cfg.get("budget", {})
        return {
            "monthly_limit": budget.get("monthlyLimitUsd", DEFAULT_MONTHLY_BUDGET_USD),
            "warn_pct": budget.get("warnThreshold", DEFAULT_WARN_THRESHOLD),
            "critical_pct": budget.get("criticalThreshold", DEFAULT_CRITICAL_THRESHOLD),
            "info_pct": budget.get("infoThreshold", DEFAULT_INFO_THRESHOLD),
        }
    except Exception:
        return {
            "monthly_limit": DEFAULT_MONTHLY_BUDGET_USD,
            "warn_pct": DEFAULT_WARN_THRESHOLD,
            "critical_pct": DEFAULT_CRITICAL_THRESHOLD,
            "info_pct": DEFAULT_INFO_THRESHOLD,
        }


def load_previous_state():
    """Load previous usage state."""
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def estimate_usage_from_profiles():
    """Extract usage signals from auth-profiles.json."""
    try:
        with open(AUTH_PROFILES) as f:
            ap = json.load(f)
        stats = ap.get("usageStats", {})
        result = {}
        for pid, stat in stats.items():
            result[pid] = {
                "last_used": stat.get("lastUsed", 0),
                "error_count": stat.get("errorCount", 0),
                "failure_counts": stat.get("failureCounts", {}),
            }
        return result
    except Exception:
        return {}


def parse_gateway_logs_for_tokens():
    """Parse gateway logs for token usage patterns.

    Looks for patterns like:
    - "tokens used: input=N output=N"
    - "usage": {"input_tokens": N, "output_tokens": N}
    """
    today = datetime.now(timezone.utc).date()
    month_start = today.replace(day=1)

    daily_input = 0
    daily_output = 0
    monthly_input = 0
    monthly_output = 0

    token_pattern = re.compile(
        r'(?:"input_tokens":\s*(\d+).*?"output_tokens":\s*(\d+))|'
        r'(?:tokens used:\s*input=(\d+)\s*output=(\d+))|'
        r'(?:inputTokens["\s:]+(\d+).*?outputTokens["\s:]+(\d+))'
    )
    date_pattern = re.compile(r'(\d{4}-\d{2}-\d{2})')

    for log_path in [GW_LOG, GW_ERR_LOG]:
        if not log_path.exists():
            continue
        try:
            with open(log_path) as f:
                for line in f:
                    match = token_pattern.search(line)
                    if not match:
                        continue

                    # Extract token counts from whichever group matched
                    groups = match.groups()
                    inp = int(groups[0] or groups[2] or groups[4] or 0)
                    out = int(groups[1] or groups[3] or groups[5] or 0)

                    # Try to extract date from the line
                    date_match = date_pattern.search(line)
                    if date_match:
                        try:
                            line_date = datetime.strptime(date_match.group(1), "%Y-%m-%d").date()
                        except ValueError:
                            line_date = today
                    else:
                        line_date = today

                    if line_date >= month_start:
                        monthly_input += inp
                        monthly_output += out
                    if line_date == today:
                        daily_input += inp
                        daily_output += out
        except Exception:
            continue

    return {
        "daily": {"input_tokens": daily_input, "output_tokens": daily_output},
        "monthly": {"input_tokens": monthly_input, "output_tokens": monthly_output},
    }


def estimate_cost(tokens, provider="anthropic"):
    """Estimate cost in USD from token counts."""
    pricing = PRICING.get(provider, PRICING["anthropic"])
    input_cost = (tokens.get("input_tokens", 0) / 1_000_000) * pricing["input"]
    output_cost = (tokens.get("output_tokens", 0) / 1_000_000) * pricing["output"]
    return round(input_cost + output_cost, 4)


def send_telegram_alert(message):
    """Send a Telegram alert."""
    try:
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        tg = cfg.get("channels", {}).get("telegram", {})
        token = tg.get("botToken", "")
        chat_id = tg.get("chatId", "")
        if not token or not chat_id:
            return

        import urllib.request
        import urllib.parse
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": chat_id, "text": message}).encode()
        urllib.request.urlopen(url, data, timeout=10)
    except Exception:
        pass


def log_usage_snapshot(state):
    """Append usage snapshot to api_usage.jsonl."""
    try:
        USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "daily_cost_usd": state.get("daily_cost_usd", 0),
            "monthly_cost_usd": state.get("monthly_cost_usd", 0),
            "monthly_pct": state.get("monthly_pct", 0),
            "daily_tokens": state.get("daily_tokens", {}),
            "monthly_tokens": state.get("monthly_tokens", {}),
        }
        with open(USAGE_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def main():
    config = load_config()
    prev_state = load_previous_state()

    # Parse token usage from logs
    tokens = parse_gateway_logs_for_tokens()
    profile_stats = estimate_usage_from_profiles()

    # Estimate costs
    daily_cost = estimate_cost(tokens["daily"])
    monthly_cost = estimate_cost(tokens["monthly"])

    # Calculate percentages
    monthly_limit = config["monthly_limit"]
    monthly_pct = round((monthly_cost / monthly_limit) * 100, 1) if monthly_limit > 0 else 0

    # Days remaining in month
    today = datetime.now(timezone.utc).date()
    if today.month == 12:
        month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    days_remaining = (month_end - today).days + 1
    days_elapsed = today.day

    # Project monthly spend
    if days_elapsed > 0:
        projected_monthly = round((monthly_cost / days_elapsed) * (days_elapsed + days_remaining), 2)
    else:
        projected_monthly = monthly_cost

    # Determine alert level
    prev_alert = prev_state.get("alert_level", "none")
    if monthly_pct >= config["critical_pct"] * 100:
        alert_level = "critical"
    elif monthly_pct >= config["warn_pct"] * 100:
        alert_level = "warning"
    elif monthly_pct >= config["info_pct"] * 100:
        alert_level = "info"
    else:
        alert_level = "none"

    # Build state
    state = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "monthly_limit_usd": monthly_limit,
        "monthly_cost_usd": monthly_cost,
        "monthly_pct": monthly_pct,
        "daily_cost_usd": daily_cost,
        "projected_monthly_usd": projected_monthly,
        "days_remaining": days_remaining,
        "days_elapsed": days_elapsed,
        "alert_level": alert_level,
        "daily_tokens": tokens["daily"],
        "monthly_tokens": tokens["monthly"],
        "profile_stats": profile_stats,
        "thresholds": {
            "info_pct": config["info_pct"] * 100,
            "warn_pct": config["warn_pct"] * 100,
            "critical_pct": config["critical_pct"] * 100,
        },
    }

    # Save state
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

    # Log snapshot
    log_usage_snapshot(state)

    # Send alerts on threshold escalation (don't re-alert at same level)
    alert_order = {"none": 0, "info": 1, "warning": 2, "critical": 3}
    if alert_order.get(alert_level, 0) > alert_order.get(prev_alert, 0):
        if alert_level == "critical":
            msg = (
                f"🔴 API Budget CRITICAL: ${monthly_cost:.2f} / ${monthly_limit:.2f} "
                f"({monthly_pct}% used, {days_remaining}d remaining)\n"
                f"Projected: ${projected_monthly:.2f}/mo\n"
                f"Action: Non-essential work paused. Opus → Sonnet for all tasks."
            )
            send_telegram_alert(msg)
            # Log incident
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "category": "budget",
                "severity": "critical",
                "description": f"API spend at {monthly_pct}% of monthly limit (${monthly_cost:.2f}/${monthly_limit:.2f})",
                "auto_action": "Alert sent, non-essential work should pause",
            }
            with open(INCIDENTS_FILE, "a") as f:
                f.write(json.dumps(entry) + "\n")
        elif alert_level == "warning":
            msg = (
                f"⚠️ API Budget Warning: ${monthly_cost:.2f} / ${monthly_limit:.2f} "
                f"({monthly_pct}% used, {days_remaining}d remaining)\n"
                f"Action: Downgrading non-critical tasks from Opus to Sonnet."
            )
            send_telegram_alert(msg)
        elif alert_level == "info":
            msg = (
                f"📊 API Budget: ${monthly_cost:.2f} / ${monthly_limit:.2f} "
                f"({monthly_pct}% used, {days_remaining}d remaining)"
            )
            send_telegram_alert(msg)

    # Print summary
    print(f"API Usage: ${monthly_cost:.2f}/${monthly_limit:.2f} ({monthly_pct}%) | "
          f"Today: ${daily_cost:.4f} | Projected: ${projected_monthly:.2f}/mo | "
          f"Alert: {alert_level}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
