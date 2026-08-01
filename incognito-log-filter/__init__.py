"""Incognito-mode log redaction filter (v2.5.6).

While the incognito sentinel (/tmp/.hermes-incognito-active) exists, redact
sensitive fields IN MEMORY before they reach disk:
- user-message preview in `conversation turn: ... msg=%r` (args[5])
- web-search queries (Web search via %s: '%s', Firecrawl/Exa/Tavily/Parallel/
  SearXNG/Brave provider lines)
- URLs anywhere in args

This is the *pre-write* defense; the skill's 4.6b post-write scrub remains as
backstop. The filter must NEVER break logging: any exception degrades to pass.
"""

import logging
import re
from pathlib import Path

SENTINEL = Path("/tmp/.hermes-incognito-active")

_URL_RE = re.compile(r"(https?://[^\s'\"\)]+)")


class IncognitoRedactFilter(logging.Filter):
    """Redact sensitive log args while the incognito sentinel is active."""

    _PROVIDER_KEYS = (
        "Firecrawl search", "Exa search", "Tavily search",
        "Parallel search", "SearXNG search", "Brave Search",
    )

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if not SENTINEL.exists():
                return True  # 快速路径：非无痕，放行
            msg = str(record.msg)
            args = record.args
            if not (isinstance(args, tuple) and args):
                return True
            new_args = list(args)
            redacted = False
            # 1. conversation turn: msg=%r → args[5] 用户消息 preview（turn_context.py:497）
            if "conversation turn:" in msg and len(new_args) > 5 and isinstance(new_args[5], str):
                new_args[5] = "[REDACTED_INCOGNITO_QUERY]"
                redacted = True
            # 2. Web search via %s: '%s' (limit: %d) → args[1] 是 query（tools/web_tools.py:720）
            elif "Web search via" in msg and len(new_args) > 1 and isinstance(new_args[1], str):
                new_args[1] = "[REDACTED_INCOGNITO_QUERY]"
                redacted = True
            # 3. provider search: '%s' (limit=%d) → args[0] 是 query（各 provider）
            elif any(k in msg for k in self._PROVIDER_KEYS) and len(new_args) > 0 and isinstance(new_args[0], str):
                new_args[0] = "[REDACTED_INCOGNITO_QUERY]"
                redacted = True
            # 4. 通用 URL 脱敏（scraping/truncated/Blocked URL 等任何带 URL 的 args）
            for i, a in enumerate(new_args):
                if isinstance(a, str) and _URL_RE.search(a):
                    new_args[i] = _URL_RE.sub("[REDACTED_INCOGNITO_URL]", a)
                    redacted = True
            if redacted:
                record.args = tuple(new_args)
        except Exception:
            pass  # 绝不破坏日志
        return True


def register(ctx):
    """Hermes 插件注册：挂载 RedactingFilter 到 root logger（所有 logger 生效）。"""
    logging.getLogger().addFilter(IncognitoRedactFilter())
    logging.getLogger(__name__).info(
        "incognito-log-filter: RedactingFilter mounted (active while sentinel exists)"
    )
