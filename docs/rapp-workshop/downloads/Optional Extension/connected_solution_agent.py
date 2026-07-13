"""
Connected Solution Agent — turn a set of agents into ONE Microsoft Copilot Studio
connected-agent solution (an orchestrator + one connected sub-agent per agent).

WHAT IT DOES
------------
Given an "agent stack" (a folder of BasicAgent `*.py` files + an optional
`metadata.json`) or an explicit list of sub-agents, this agent emits a single,
import-ready Copilot Studio solution `.zip` shaped as:

    orchestrator bot  +  one connected SUB-AGENT bot per agent
    wired by componenttype=9 InvokeConnectedAgentTaskAction components

Instead of cramming every capability into one base agent's instructions, each
agent becomes its own separately-registerable connected agent (the unit
OneTrust / Agent 365 govern), and a generative orchestrator routes to them.

Every bot is a GPT agent (gpt.default instructions + code interpreter); no Azure
Function / custom connector. AND — when a sub-agent's source agent.py carries its
compiled CapIR (t2p-capir/1.0), or one can be recompiled from its seeded data —
that sub-agent ALSO gets a REAL deterministic capability FLOW (what the Copilot
Studio UI calls a "flow"/"workflow": a solution-packaged Power Automate workflow
on the agent-callable "When an agent calls the flow" Skills trigger — the
platform's forward-looking replacement for custom topics) wired to the sub-agent
as a TOOL (TaskDialog -> InvokeFlowTaskAction). The flow runs the same steps as
the agent.py's perform(): typed inputs (user_query [+ threshold]) -> a Compose of
the SEEDED records -> a Query filter by the real query -> fallback examples ->
"Respond to the agent" with message / matches_json / match_count [+
document_text]. The control flow is real; only the DATA is mocked, so swapping
the single Get_records_STATIC_DATA Compose for a live connector action
(Dataverse "List rows", SQL, an IoT API, ...) is the one-step move to production
and the same logic runs unchanged — and until then the flow has ZERO connection
references, so the solution imports with no connection dependency. (The legacy
deterministic topic remains available via capability_mode="topic".) The emitted
package uses the exact structure of a real exported Copilot Studio solution, so
it imports with no code.

PROVEN LIVE — and the two non-obvious fixes baked in
----------------------------------------------------
This was imported AND published end-to-end into a real Copilot Studio
environment. The live test surfaced two things static checks cannot, both now
handled automatically:

  1. Bot-name 42-char limit. Dataverse rejects any bot whose display name is
     longer than 42 characters (error 10004). Bot names are capped to 42 here,
     keeping a trailing "Orchestrator" intact.

  2. Orchestrator publish + channels. A headless `pac copilot publish` cannot
     do the Bot Framework / M365 channel app-registration, so an orchestrator
     that declares channels fails publish with a 409 ExternalServiceException.
     Channels are therefore OFF by default (the whole solution then imports and
     publishes fully headlessly). Set orchestrator_channels=true only if you
     will publish the orchestrator in the maker portal (where the channel
     registration + consent happens) to expose it on M365 Copilot / Teams.

USAGE (as a RAPP agent)
-----------------------
    perform(stack_dir="path/to/my_stack")              # build from a stack
    perform(subagents=[{...}, {...}], solution_name="MyPack")   # or explicit

DEPLOY THE RESULT
-----------------
    Autonomous (built in — PURE Web API, stdlib only):
      perform(stack_dir="my_stack", deploy=true)
      Imports the solution into your Microsoft Copilot Studio (Dataverse)
      environment via the Web API ImportSolution action, then publishes every bot
      via PvaPublish (SUB-AGENTS FIRST, ORCHESTRATOR LAST — a connected-agent root
      409s if its children are not published yet). NO pac CLI, NO subprocess, NO
      binary — the IDENTICAL code runs in a local brainstem AND an
      Azure-Function-hosted brainstem. App-registration credentials are read ONLY
      from env (DYNAMICS_365_CLIENT_ID / DYNAMICS_365_CLIENT_SECRET /
      DYNAMICS_365_TENANT_ID / DYNAMICS_365_RESOURCE) or a settings file
      (credentials_path=, ~/.rapp_deploy_settings.json, RAPP_DEPLOY_SETTINGS, or
      ./local.settings.json) — the secret NEVER travels through chat.

    M365 Copilot / Teams exposure:
      regenerate with orchestrator_channels=true, import, then open the
      orchestrator in Copilot Studio and Publish (handles channel registration).

Self-contained: standard library only. Drop into any RAPP agents/ directory.
"""

__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@kody-w/connected_solution_agent",
    "version": "1.0.0",
    "display_name": "ConnectedSolution",
    "description": "Turn any agent stack (BasicAgent *.py files) into ONE import-ready "
                   "Microsoft Copilot Studio connected-agents solution: an orchestrator plus one "
                   "connected sub-agent per agent, each with a deterministic agent-callable FLOW "
                   "(solution-packaged workflow, wired as a tool) that runs the agent's perform() "
                   "logic on synthetic stand-in data — swap one Compose for the real connector to go "
                   "live — and declares its perform() params as typed inputs. Optionally imports AND "
                   "publishes into your own Copilot Studio (Dataverse) environment via the Web API "
                   "(no pac CLI; credentials read only from env/settings, never chat).",
    "author": "Kody Wildfeuer",
    "tags": ["copilot_studio", "connected_agents", "power_platform", "deploy", "integration", "converter"],
    "category": "integrations",
    "quality_tier": "official",
    "requires_env": [],
    "dependencies": ["@rapp/basic_agent"],
}

import io
import os
import re
import sys
import json
import ast
import base64
import hashlib
import uuid
import zipfile
import logging
import urllib.request
import urllib.parse
import urllib.error
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("connected_solution_agent")

# BasicAgent base — use the RAPP runtime's when present, else a minimal shim so
# this file also runs standalone (python connected_solution_agent.py <stack_dir>).
try:  # the RAPP runtime's base when hosted; a minimal shim when standalone
    from agents.basic_agent import BasicAgent  # type: ignore
except ImportError:
    try:
        from basic_agent import BasicAgent  # type: ignore
    except ImportError:
        class BasicAgent:  # minimal fallback
            def __init__(self, name=None, metadata=None):
                self.name = name or getattr(self, "name", self.__class__.__name__)
                self.metadata = metadata or getattr(self, "metadata", {})

# ============================================================================
# Embedded Copilot Studio solution templates (verbatim from the proven packager)
# ============================================================================

DEFAULT_ICON_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAKAAAACgCAYAAACLz2ctAAAACXBIWXMAAAsTAAALEwEAmpwYAAAA"
    "AXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAADiGSURBVHgB7X1rjF3ZldZa+7rclXeFJFL+9W0N"
    "A8oMMM4PgoKY9DUiAw0MVS0BQySkcqNJmABKuyEJCQnYFYYJYhBth0ciAtj+AZFgkNMZQovMCFdP"
    "hCIBI3cGhdYwKK7+1zAdUk3aHcf2PYu993ru606yXa7HNTqru3zvPfecffbZ+9vfep5zAUYZZZRR"
    "RhlllFFGGWWUUUYZZZRRRhlllFFGGWWUUUYZZZRRRhlllFFGGWWUUUYZZZRRRhlllFFGGWWUUUa5"
    "3wTh/wN5/T/8L7N8JeuJaEZEUyJYy5sJBkIkyC/EF5pf8//1PQ3EB5O+yj/6fz62vCbIr+Uw4rb4"
    "EG5P96vtQmkXd2iCJ2+cPbkDe5C1s5fXrv/f1Y0JwMM0DCdyv6cJcI2bp5fyea7ld8/nrnxxsjJ5"
    "5sa5R3bgPpf7FoBrF66uDTduP05zOl0+MtAqWpAcVOU/FJDxZmLAYN1MAYAMTv5H4UUCTAjvy6sc"
    "iwWAZduAdfMkPbQX8K1++OlZ7vtmflsW0Ztp4bw05DPmDhvwyfp7cXJ8Zet+BuJ9CcA3/JP/upFH"
    "/0KehTUDUpmfPIsFgGUfm0SmrwoaWGQusIk2hhMuk+/tO6hsyk1QBXHeGwcBO/+d/+7P/5HTcBdS"
    "GO+7L7/mTD74NBj4wYBegCfvsWJ9qFcR+y0dwouTYb5143OP7sB9JgnuM3nj5379yTwbl/M0rCEy"
    "8fDkDfhqy6lAsn6BMpXEG3lflD9AAaYBFRLaLJejMSFDWgDOQBcUYFa9xybn4C5k5SNfOfHd76xe"
    "zW9Pe8eRwAgZK+sVnMfP/GXer64G2XugzQHTldWfuzyD+0zuKwC+8Z/++oUMtNPCZ5XZTBUysEQ7"
    "CouZ1Saf0EjNmM80cQGqwxAr4zlKGXjkKoNCv3IDW3ejelc/+h82c2P/MYN8Csqw5Gulqlo5eb0S"
    "XieyCevyITKLgvLiKFcxnQNeWfngU5twH8l9o4Lf+PmrZ7IOOsM2nqtYsYlIbTtTu5VNSO0/djrk"
    "/0SgdmLdp+K2vhbVOwjLgKvEIgPZ5noADfIF7nx36+RD0CmF+SZIV8WGkyXD56qMrjw7kE5OBZtc"
    "a9tv6R/qePA3hb1P3frs+iW4D+S+YMC1z2cvdxjOgoCPkYfGgiLtG2Gs+E3ZP6meY4MOhU3FtKq2"
    "ne4ss4vuOgM4J8qG/O82dMrqx65MM/guK/8ypVXVCoozEazfOQXX9+QUjLoTX15lRWeT+XBu5S9d"
    "PgH3gdwXAKQhXYA6zug0xOCRmXJjrgqK+kV5DzyDxc0w3iQGIXsWclhzUlAwCj6RVMuz2ud2M19u"
    "QfeF3LqQm5oik5YSMt6piCi+U89JjMHogZRtyCuNBIQ8EmtwGy7AfSBLD8A3/rOrj+fhndYP1eCB"
    "6q8q4gwQZNjkqTCV7PMmrogjTr5XuzEoMTD+JLKoC9RzUkALPttr+61+7Cun8svDQBjRxVqVV5SZ"
    "oLK21BnWKFIAqiCNr0VWmGoH0E0njn/g8llYcllqAK599uo0hzpOm9opwKvcRmieR4EjGrtVEbBB"
    "Q4rg6hqF0YC9aFVxdU51ltkgFFVJ+pWoOzlLHr2L0C9n+NTk6pNbLJ0ntv9AyVbZdyfv/5LvH2xS"
    "vUgzB1iVk32s7x+H05fXYIllqQE4rAxnisoC81kDfVQqYoAN5i2gTCG0Xmp0J1DYjTzOx5sx6sQA"
    "YjBPB2OT+fjszDwDHfLaj//qBkC4DmmBV1BElcn519D33nzz3J946Ob5P/nmlCYP5U5dVKtBLtWc"
    "JQwhJV949d3ayisV+EsrCEsqhf2GFfpm440OYu4YnMRrNc8XPPNBjTquezfptwi2gf0A9TDNIyZt"
    "W9qvwedBEbPz3bN93u/qx371Qo7rnCLxfAtl53My9ZGzs+jiT938B4+cfbV2jn/ol8/mk58ZSGhz"
    "MKsB5TpAfGKlU240wR++/blHt2EJZWkZkFaoGtGS2cDAWB41pmFxAVnkgq0r9j1qjoPa1RYjvoAN"
    "YaKFcCzua9YaqiOTB+4p6L0WpA11e6VHlcncZOCFkLftfD/wFbn5mZ8+W4Le6nfFQDU3jws2qjQ7"
    "X14WXEoArv3zq6fyy6y1xsXO03Cw2eNo7oEpHoghGDKV3KAMLAZCbE8yjQRt5lpbGJGBzLvNAb4I"
    "HbL6yV+Z5abWIEZRECx9CIq/iib4Cz+8RXpKnAxiexSlHSFrV8wyPPUqZ5MP/NIGLKEsJwMir1jU"
    "2L9CKBQOAFg4xUx5WrSnUJ0IYvc3hFzEDhTPWNNdDAyBefR22dlxFt7J3u829MiAmyBQ53NgsFdJ"
    "SauAc+fG33/kh7aZNfezYEEAkjXErjRik2Pk6+R4Up7oyZNwavkckqUD4NqFq2dqSZX7uJpaM981"
    "BosVdJqb1QEXZnSnFkOgF9H2oZYYqzh5GrlWXceH5iMTbkOnYGFyzfEyiaPleQHUVMNsznW3qY5L"
    "4hbEq9aO2olJA9UDX9L0+PHhroolDkOWCoAZfNNsWD9e3qOyW8xO8BdE5DE9G2c2htADzzoVWlAC"
    "HvogU8ioDMsYQ8suyIag4kkd5YKXbeiQon7z2acQda91lU+sp0sIl3raRJw8aDljkD4CelKO3EaW"
    "beo5533S0oVllowB8UwerDfzW5lxcSBc/QbmAN0UbDz3Ae0o90xEjaPaTrWYgVOp0gKRVgWAgl1U"
    "PBrbzml4Bnqkql+5GlC2Sm7W2ite61G/dc9sz4VgdnF8dcGJYSvhGKVHB37B6trKdXgSlkiWBoCV"
    "/QA2baJJckykDOf7Vj3mvp8SDEqUF405XTNVPFq0mcx+cuYE4CCzeZK8X5ITSdi6fLndm/3IB8zu"
    "3Ggq2DdgXzxx9fTlaR6cGYbCM35PqN61ML7EnaxYO47f5rElKttaHgZEvFJfYrhFXu9wLmwfc/6i"
    "iwIAUXWCYI9TXi2WPYcfQ7icIdGyFOeq0o8EdAk65HVnv3Ki2LKhR0BmC7pnXkA9IHaFdOZwfKYm"
    "gpgHADG+FOq2eMVRqWNEK3aQfUosEZZElgKAmf1O5eGaWoGBx7KUwEwN1s9KiRIWIdlBclokcJQ5"
    "NyB6PacpQJlAYLIwYErKATDd4aCsrPRVvwzzyabXH2qhAGH0E6R/37759/5oV0gnEW4SBZ4LhTwA"
    "FrGKnlNwvHSFVb0yW3n/5VOwBHLkACz3duSBqivS43CeG8UY5yOyMk0O8TPgsJkBcVrUCw7pOwrQ"
    "488hXsY2onkJjQNU0V3ASM/sfryz8LTeICUeEhcKWPhF4nd6n8evdbVXnIdi/1kKDp3Oxf3SNhXs"
    "5lSZY5XIAFtCXUvgkBw9Ax5Lxeudkpc7sfKQ2B2F7IPYb+okoNlvWibP/3h8r352DIFWSStAEYO9"
    "5Hy4SFKg6a2UulTl6tkr0/xywuNzBhDxXNUGze8nqYv9VuD4hl5jVqtgoSRwIJqbpkxvCxb8Gly3"
    "TI+/whGHo5QjBeDaF57LaleCzkF5gAaNzQHIiX8ZYrLiNwFKKBYlqZZRe0+DD5b6xfb8RiASbxT7"
    "SWxAqS5hX7p+QZN5F1hoPmzwVYCrPsL2AmXz6ur1PvWbcN1cIe6U1EOqDxU0hVyDaQ+0deh6mJfA"
    "6dWfuzyFI5SjZcBb3zujHoZMFksMEKOGWKj1dhHJYizB4RAbEC18Ix6zMiVaop73Bq4NkCSJkCFR"
    "0FpJbyreudGpfvMZ14OqlwJWBkrCiHvc3j376G5Pm8X7Nda0+CFKjQ6afwGouhnk3hGUSJMV6Jo1"
    "k2Uth3GONCxzZADMtt+JPBibgMFR4DyHVrSgq5jwB3aPrAWdIagas+i8yABjGzpT7hlzC5LjjTQZ"
    "ihLqh271W2J16KofY3CbYgAT55d62jz+4S+v50PXWgZHBbXeT4Uh5mc2Iei9Vh5tAmVAfosbR3k3"
    "3dEx4CRd1tlGqQNAm32CEDaxmJ4wANuHHq8z417ScWiWnA24OBRWp+rAbXOnrGndGQJR8nn/NFyE"
    "HpkPM+6i/IFROSM5qcas/253tTmkDTdwXa1GMZWhy0VXMiYNgNp1W8BUUDgHdgKPQo4EgGv/8jdO"
    "FSN4YbM6A2heaBF0KAV0gkVYowoW2614e5IuccAhuDNCmsqSsgMLu4jNB3p3mqo8ev76J04+Cx2S"
    "G94ELZNCcvJbDMBk9Xvj7/Y90QBBA9ru9CsKxQasJolEDkhTdWgxAw2AakSAd9BlXdp/4C8+dSQO"
    "yaEDkB0POhMApSDBJkiCDjeuQ5FyKJlSWphOD/iH4lJsXRs+DoMB6OX84ASCwsDgnztzv8X7LaES"
    "7YvqPvQ+qhOQv7zY1eaHn57lfR+Uw3AhEG2OE4mXo+cEO08tWtB1Z2EhvjBHICU6exRhmSNgwNub"
    "+cKnYsyxj8m2FsSgMYR4KnglIC9xrgm0WygAYqRFIx9s0aUQiNDUnsUIXSWZGJCl1fIpDXgJekTU"
    "r/G10o34BQR+3wrQrWe62kTJJzdFB0lITdmQWktCTisIq8/MMUa00eI/NVjy39rxm3Do1TKHCsC1"
    "L1ydwhDSQJ6vtWxGVFSE4M5JEB8+US8BrJHegpMhTRsXoTUVC/TQLHZ1lMvE7bz8N39yGzokpbQO"
    "CgmPtOgpKdkNSfD1XvVLQwg+K8w0/GkB7dR4ueKQoMUfFwfWQzly2XwAUfpbhx2WOVQApmHljBW5"
    "lA0BWGiFfaxqw/2+QiFw5yLn/QFtaesmDGnfBry0COYQSGt3FpbMk7sNHbJ29spaPmBDl4c42sw8"
    "CaxOQr641NPm6z7y5RNmK9vlLWRS+LLE6Wa701jNq641iEWgt7SiUqJb2eXjHCcX4BDl0AD4ln/1"
    "Gxt5aE7pZx4VCZVoKEbTX/rYCUcDH7MAHh5eeVQHNlFeOSyoWFTy0Y8e5KEGd+hqvzolQ1f45WZx"
    "FNRIqPSXJJCN8ggbMxnKc4+2e9q8jcc22aFC8NSbWhqyaJKbEs1iRL+WWpDARQl8ZWyNkhku9leb"
    "mq3+lV+ewSHJoQFwwPQkxPssEPkJVBQuPwd9PaCnr2CzJtploSihfq8aPLIZaFhGbC8HL6IqSTmA"
    "3E7UO+NYDe++8jfe05WpyLJu14HKeE40Pvm4c/0XfqrLoy75ZPSb9ALFiz+Lxm6NNlG2I0uPCyEC"
    "SH0ZKoBJ2dqPLTfsDYcWnD4UAL7lC984BSClSayCIgOCpNO4uAAsC0GNziXbDzDmOMXOG3RFS7s2"
    "XSmZd6uRQPWXZV+ePPmzaG7ZL/U/96UEdFW9yQbjbfc+a9/7Atofe3qaDzkhKwm1kNWBeIdBgtG5"
    "AAzgT8L+svBAs0MSrLYYlaj1/HrigQ9+6VAckgMHYAm75PE/Uz+IFxvtYU2XLVSxFJG9KH6wmFZg"
    "NGQzC1ABLUa1mEeabtP5954IX4k+0n2t1RyZoN7sxywf/ya9HJCSMEM+SgimACBRXz6ZVtYFFKBP"
    "RfDqFqHaFNSxLlqPEHLiETw6owgGbNKfHi1MaofXxXco1TIHDsA0mRfwTSHkOYqQE1yIpogefZV2"
    "dOWK0gBdzTEksyAStdXjOdSDKUSHZT/pRqBaqGBc+d68t1BgExfZyC4pRfW5c+Pn37vd0ybCsHFH"
    "k9I7MZxjrR+AaYBkLC+ecH5J5Pk6gXUSMIMWB6FeC7COwTetzCdn4IDlQAH49suZ/QhOqaemowLg"
    "F2xbHH9Riy14rUH1yjNhMCrVYBMCs4GEd9g8FNsRie44D9gCwaTTur179mRfoUB2QNQh8jbVPiO9"
    "EMo27nZPe+UxbsDl/JzdAJA6P1XqABaUFpYEjSqrdjU7hh1mOw4sfKNsDcFT00QQ4xPw9Orpp6dw"
    "gHKgALx5a37GKjfUBUQtfQLwAXWNYEzH4rV+UkwpKSQBptk0flIrOJA5YeqLpwMMoQjLKJg3LARJ"
    "fcHn1//tr85KYL32PSGpxwHSL5Tcb3k74O2uNgFuzeTq0cDHKXBSD0eAQ8Z+XnABbjeCq2wGFLkJ"
    "o7YgtvsIqCV9QzSfX4ADlAMD4Fv+9TcK85U/0uKBKjx0C/EUCss4ZImquHYmDWUplFHvxqnsQI5a"
    "JTjSmAs7GKTMIIwA+q/GJt3AX4E+thqQNpGBZh64A8Mur5xk58bZPvWbe7kZk8hkVS1hUMiB6WCz"
    "3Lcey2AjBSdYgNoZUgbVGLH+4ys2M/Hq6YMLyxwYAIsRi+5chIp0yV+CfjQ4CQPy4bjQHraWtkyB"
    "paIUi3Z4c98H8wcHaEMCj6HIdCEnke9we/fj796BnusEmpFBDqEhE4g+UV8+uQS08/4zW6DSUHAa"
    "uPA22ckQxNxVOw8sBGOFChBVLoR9EX3V81iCHYJ1AsuvD+CBseCBAPB3/NJ/fzxfyZRNPi+fBw82"
    "K81TeLYx60u0/JutYEYZufpezOUC3hGkNjQIMqp6rF94XjbuDN6Lwi0XoUNe93f+04l8kgdJ6hgr"
    "24MUToBdacX3beyrJ7xx89YGKd6wDZBX0IEytTK86FaM9xurfej3gJj5LdeOQU035zBmlLGvhQs4"
    "Pf6hL5+BA5B9B2BxPPJLjSFZOlyWZ92h/JvEI9V4nhrsEr6w/ewmIVC1Yr60KyMkY0Mw3esSGa42"
    "qZVIZF6ytcw0gStD3326MNw+xUeS+JtqD1iP1eX69s2zJ7s8akyTdTEJzHy2MaA2e2HRI4BoPljM"
    "iUEnbSljAoDFOsv/ye1UzY4E54aA6wkL+E+vHUBYZt8BeGsYzpSgs1haVt3M35IvL/M6PV2mTImq"
    "axtm0WfFAAVvEyHeySZbgjcMclOHe4ZOjRBsUVFMdcdne9Vvjlk8bL2wlWMxv2hS9AGau/swBGCR"
    "OhaWDWETBkw1gME9mDMyDBqQj2zv46SgFrolYVgJyOu42livXYcH9p0F9xWANewCbEBb5SSq2+Hj"
    "BSGVpms6zB5zn3zEwGqSnA0GZKhDUqZVlYNiByVXudpmVftJJ1K2eXn1JeiQ1U9/LV8rnVDPE8GZ"
    "2cM+mh/su/PttZ+sT1Jd47wtes+sYQOmmibkC055WPR3PSo19X8QQzaqg5N6OH4JvpJlSIQR85Cd"
    "3m+HZF8BeAvggnKM2iICKKM+kO1lp0FdE0uH8dga+AQ1rocoxLdkF7OtfdLJgmG6n5CbMkViRAL6"
    "nHATxTQ4tg0dgnhbMhULDGzrzBYbrHYWNAyE6wwgKWs2Neish6JOESOQ+BJtXaLhzVSBbAssCopg"
    "SqgNgzIpNkaEU0C+2v0NTu8bAN/yb3O+t9yMLR5vsmpjCQjXvQIDysrVi9Z7NuK1m60TLWhs7BRP"
    "4dXAdCKzK91WtOH7Po4H6A3w+eX56x99V1ehQLaMNmJD9TypbV84pDugnY9/WDuO5t0KZSUFJjeu"
    "9Ybs+qNsMwcNOA2n6UAMFrdY5sFdD05PGPdkIA3MWf5mr/1r/37fHna5fwyY0hlWgRp2AYjxP+YK"
    "UYl0R5TFwGjerLkEwmZKLBSydQo+bsAcGfQyL2cmub1SDm5sIiayeltFX+43q9984CxysYViFrzx"
    "nNq62NXmJ6/k9ughY5zaNzOXVRNg1KJ8vWJvlm3JuFwwk6RYVawTUbnBO1Lv2HV+0DZR9Rgo87Y5"
    "4ZPlhxZhH2RfAPjWp36z0PIUzIggM/gZJFqRIq6HQ6hevX5pXjBaWMUCMVZhLJrIlDto0F4sPxld"
    "tGnR85H60f5vcvtGshhdttoEhhlJf42JbQGAgz6/zid9j3JLE9iMCNP4Ekb1CAE5pibA0VjfUxxd"
    "Blhlz3B3HLjHy6Mmf6DOCKt+CvafKB/t3vTGy6v7Ui1zzwAsjscA9LizjVzU4o5qu8XUY91AoIxp"
    "oZRY2xZsPF3KwNrIyIDkPhHyYHawJclPT3rjjqM2yPMvP/HubeiSYRPJDX4ABzqG9/kcz/TezE5y"
    "55vRVWAoBYnatOLkyZlTZHNgoMkiTFpY3rKn28hGmGbS2P5Jv7ZLJCMLBufj+8GC9wzAW5N0Jnfn"
    "zer5+QUiLHpyrFUhblWfV8ZAFC01A8fgMsIDO09QvyFDR8YaUQVrvSBqPMPAIv4i9tX+Ve8XcVbY"
    "U2xH6YMhXa3Z8ii3iz1tvu7slfK7btPIYxDCU0CWK6zkzzYbxXNbaVZKbq3I+BAsLLZalKrwCoyr"
    "40ZyDv5M7vDI/hxThLVXrr/mngtX7wmANehMdMoG3emgdnaQmBIFp0NoXsI00ZoBZTH9BNqatucx"
    "O1GwcrLmpGCfKarCpCdSEJKzCXBG5hJ0yGQyzMxmjNmV0nixM0nNLMSVTvWb5RSEBJBM9aKKpQCU"
    "Ruva2KA8rgRCyVlykJo6VUVh5oOfUk5rEQOIrAsa0uKvctOn6m2j9yD3BMD5JF2xqHqETshr18VJ"
    "4vrHooQF0SHRglWfCf9RQjC15JEuNU7qO1TmwIYw68l54JSdvB/8FK5u9ZuPXPfgMIVUiiwfiQLk"
    "cz3b+yi3AfE9qgHCiAT9mAJYBH2ullFr+/T6azBAestdFvBAeMpY4EkHexOklmHTdkGcnKDLy9/k"
    "3sIyewbg27703Kl8mdOwmmzKGW2aCTfnQvKxFFearUwPyQCE1WtAVhE9IB/08R2k65q1vLvMaCsW"
    "RH0Ym5K31Vmnt/bklbXM6ut6fdZubTqRMKKcua+cSx/l5iVqyVJpFgdUs6JeT9ADtij9ESDVGiFx"
    "JHiYzIYGdDCRORkAbq4AxoXO+IvgdMZ0pqbZ6sd+ZQZ7lD0DkNJk03radJo7amkuapUKaMyJQh1R"
    "3U+dSFczWnRqQPSBImXHaAfqLnIXjpJTBCFCMAeKDqkTP+8Lv8znD8xQqqDiOpH+o5llub/p2K3t"
    "njZxktbF3tW7fY3OxUauY0a+ULFtwFguRKKDExjULITqGG5KE0nuxxAusgN4LMFmcZESaM8suCcA"
    "vv3pa9OCfNA6OwuvKGNRy2r8ORh15iNg1NU1eMrBZTuXgdgBrqAiACuEM0YjivvYILLGxMYxZvWb"
    "t3/niT/QFX7Jjsy6nsvVIUJkBAHPzvWP9j1LJu+8IcOlsLb5hgXi0ssD2+hAMHK3nb0oQb/H0LAx"
    "nx6jRQmksVdkdAj7ieoqTrYPqLc/26tHvCcAzodbM1WrcgU6uWigkouM75u3uHAfhzglqBkUCIBx"
    "NSN4BNDolYcSksTl7uguaHvBgtIvchPDl6BTcisbCnhGO0TQkXY2v+tqsz7KrS5k8CuyK/OQklwp"
    "L3FfU40TJaeGqGsMz6j5YQ2lMKhA83eoKhm4OoZDqKJyxQFHdeOwWXwK8hvfe8M67EH2BMDc63WZ"
    "aBkkM23DIMi8JON5CCsSRX26jRejLKLffP1CsINklzognm6yR7k19hPEJqtqJIxGQdl27DJ0yOt/"
    "8WuzfJ41ir00G9VgqafvC2ivTGagR6pODNde75OOGQpTp1hznTIwzeLWfdVrVbAhLnYUPFwFoQLJ"
    "ZojwDoeF+6BxGYosiqUwYw+yRxuQ1mwZhZRXBQJRMBaAf2I1DpBmO8DSdhBRqBekrCJQ1YOdFQ2x"
    "2My89VDaIgMdgj2LRuc0r/bJrUmX/ZfjOJsWp4wgDM6X2G3XXv5437Nkcq82oz0V6J6XqD63xts3"
    "D07tGFv18txoa08toLJpoRZQNYWynqnsFKwWLI/Eltbt2NpLbG50cqdyCnuQPQEwn2+qPSoxryRP"
    "cAajeDe1SOOAxosCOh2nyFYMorDwhLgMNOo/yCgFtkOI3ORxsIBdYxAd9TyU27tPvLOrUCCVMnnU"
    "SkTUNB7ZGdxReqanvdVPX5lSvfPN7WPhGh4z8DVVPWzjLwaAHkCCnbjK3aN2VSTqiDQ6AZJjXkhY"
    "yuCDHWdpVDOrPZkcX3Ojh2cD8sUB6aPSBiurDyaYEBlDygsUbKLEaSEbADcddRLqWzTKa4Aq2RFW"
    "QxTwrefUPkiWBaLBmdRWTBehQ17/5NcK+KaWABOfB9VaQ+Trqe2mSz1tTiCoX51+DwqHcawLz276"
    "iMSna0rHQxejPA+Q9DtxdwVPwtoJLcQShwbdRZaOaKwzBqLd1pbu35Ft6ZU9AhB3AQKtAxgzUWQf"
    "7W5dbxJhoQgOhqCFSIqoKSfb1dBWA513MyZEZV1V3xF8KMeiPxZXxpR5bIKTZ6DnatF+8837jRBY"
    "CDQT9PzLH3n3dk+b+YB1CKwlTOMqPYLD6MfxCtjAFORYWZj8yZhQmUCHNUS/7GLQlir3T7xo3jl5"
    "6AoNxKJzMD4I5a5lb04IwM4dlK/pOBAWcv0BynR6DbpNQcFt2ljJqwEn3FEn73XAxDlxKpD9pNpZ"
    "JyCqFTtfqdP74Dt3oE9m0cQI9FPPk9QmuIufcc3HrlfGLOm7FAAW/gdcLEpQ9DftgBp7Skr1TTJA"
    "g4b+IngC42KI9YCBTs3MhA6vEEnjU3OvpfGvwx5kbzZgzhy0iV8NHGiME9Bvf0S3uCxXqcEFsH0a"
    "4961QpsvroFei29bKZTNR51MHfh4YGwcqmOCnU+9f90//s+l7H5qPQNwdcSgM2JO0BfQfsMv/Jr8"
    "6AzpUxqIbPIhjgO3byYDuKqr9Y3Y+C0Us1E6vsZcr6ImBZTSCCnjVjwlYBtH7z9WxvXFZ3+s9qEz"
    "7tnK3hiQhq/LBVBzWSk8Bk3pGrhMnntN6HaJHIPoVcyOkwW+AvPc1IVFr6AJekPdBCZAa5MnzvKp"
    "lQjwWF+o5PZwSs0Am1wM81rOx7bf7nc+/Ae72pyXO99URWI7HBBsX7M5In+3jp6NG7mWdSCntlQL"
    "ARrQGEEkWarG8IzM6m8k8BAMsBMCgI1GKSeZT/rSmYuyJwC++MiPbudO7zK5u+uhlxQ9OKOjVsjC"
    "LE06Tb4NdqRPiHlzrXNCFFdlAJ1Shs4KKb7Loc/2qt8hpYcb4khO7pFxBuiufCkyQzNJuK+E4XHC"
    "KVHDhDoAth0bE0fuwkMPxehFe4EugLFYLf0OQXtdsNwygtuR+rUxrdjrofJaXrt/wnZR7sELTufs"
    "wkSit0rhc/Xikte0uRFFAblqynGbtDAoYJMV4orlNBIO0eAt6Xb1TpNFy1EZgDqfer/22a9N8zEn"
    "+Aokwc9lWEI6auhTTun2VVO//tNfzeCjaRMZYJIORhxgZCn5bTgKboKPW3lJSRnRhrwJbcmYBGeP"
    "TSINJXGYByJYMYI59ieZhvP4b+qLJrya7BmAt19J53Ovd8E6Hi4aAuthCLskdUYIEX9w+80OgSF1"
    "OxmG2f5kwJMBGIL1Lp6wPLGgYLbvF4qGOfJvviFaaKcuLuUhdMt1Aqt9+eRJ2qzTn0xRmBOnAGid"
    "OHOiWg+ZkUmLC9dvMzCGJlXMYIH9MhaJHGJeNVTPFW6uiqZS7bD60GihmudvnHm4azxfTfYMwN1H"
    "H9rNemcLaqerHqQQZJYaKZ0z1KchmGXoSzECzUIbZlyjqw3ZJ7h0ZHaLpbAIWlsb3RbgoQfc2f1A"
    "351vyLaaMBIJODRjEIoSsvfbG9DOR870HQmDc9cRzc5VTuTd+DLAmRHMKqTGPmPgxLyRfIthLEFU"
    "s/GuhVt0HzZtEZp8r42vOIx2PMFJuAe5p4LUF//4j57LfdqxwASK7iNfu2ZLu9kKHkAxFJr5oxOg"
    "tiPZf+xI2HveHdT7tplKiSh4h9SCOauLvgeEF/VLxPdpQPAg/URg/IGdPzrz+l/86izvP1UtYMhp"
    "MiGvUqShbKZ9UbvZwOPgkg7ZHzXebwhZGYu1tizE4dJytYQeWQgx1fx3ca+2n8o93xOSe/5YVI3o"
    "g9Pu6L6cryxQbwTCSrb9vZMyumS5XAh2oJ6rLUqw0EOk2zJ+NFyCDpkPk5l5PxhBF21bbnkydDog"
    "mVFVbSureDP+HgNj8dmT2Jsyvrq7mwOwcNegtio3nYNnm3zczGRPcbziK4TBQy1sAB3z3eMrtAX3"
    "KPcMwOoRA2y3j18jsCdg1W3lH3M4jLfkc2Az2eDcwBOuKE0e86PAqWirOYz+Iph5UK/tvv/3b0OH"
    "pJQ2o/0T246BWyqPcnui91FucjN7CvlxHa9g8zmL2ZGKWl1eTnYp5GYVSDYo4CEEH1H7V9lxEDAm"
    "zSyBs7Lsrwvfj07pXPevx/8A2Zf7gnNPt9AmBJqVhgFY8aLqZn96qA0iKOHEeJgONoiaZ7WEFvMS"
    "YxuVITCe0g+nzlBJVb/AxQcgbZLGnlPDIgUAF3vaXH2yeNQ45Y5oDll62YANdByZcVLjeOizcw0N"
    "kfkaz8EXnQ5pTPGp3WwGoTmINZyToppv2+T+7LzyiZ/cgn2QfQFgYUGqLNhihUVZQ158sNsdwJis"
    "TdFZlkQrRBBiC+RZk8XVboBV0Kahr1BgDsdnpngwdk8n00E4udX3m2+TkvsVkBAuLDAAA4WqhLq0"
    "lMUwZjzIrpH7kjwMpYBJHpaSI/hEnD2BsHrDlPFo2g1fDYh9BLgl3IJ9kn17NMcxuP0YaLiCL4ca"
    "g1VBtKByA5zcHqwfgH9ePNTEmedZPzvIsAU2RAB7i/TS7vvfuQ0dkiawHvto4DCWkTR8CWh3qt9s"
    "aK0LrLzD1WECY9l6xuTFFTLf4CGUcGFm3RBG5RjsGkvv6XwooBI0dZyRFUOHdeHGMWST4/on3nMR"
    "9kn2DYAvPPKOndzJ857vBfNW0TkRbRL0QLR/4nqFVs35wGhIx8IE4FkEHU+/Oskb8+2gXXG6tQtX"
    "y2++rZv3J2SjCyuaC/PsBfa0WdRvfjnpC1IQJ+/5mhKHd3QBp2A/o8QB5bMH5FFDL9auNY2+KFGN"
    "FQ2DoQ1646y5GWRsSra/DOwDmIlmH2VfH892+4FjW7m7L6nuMk5SKi8ij8dw50REBzowIrhZw16g"
    "bmrrDknsvsBQYNUgpL8L0vmjM3OCh8u5krToKhJMPaqsrPQ9eHJlUqpp0Ct57OoIzWYlKdZIXmQR"
    "xk11n7ISkT29qvaWbNDcwZHQjQNZztYGxDSHjB7XdE1D0TsulTsX98PxiLKvANw9mYPTBOfuVLW8"
    "YknVsq3CMNDKkyGSrxvtVQDmy5usLWNXOydZq6JGtqFDcIANyQhUqRMhcTA9tyyw7oB2tgA3Ne5i"
    "WjSW0AdnB+MTv0CuQ3YTW66iQtkz7tPahnLl3FfPmNj/wnSySHUVq3KKNqW8fX4FJluwz7Lvj+i9"
    "fePY+cKCZrsx+EDfavxZPns+NTlD8lfoZe8Y0lU1Ie+3QaExJ9gqF9UhrFp2S1/cfawvU5HPv2Ez"
    "peqLXP0awjtzv8WjBpBfUW+S/ABaagVRzSXz6PWmJGY9Oa1oAjkm3KYJ5hGHPC5PL1qEStpPoI4L"
    "qZr11QvB7uNTybnPdz+6+C5k3wFYUnSZxs4GFrNXXuTuYfFgEqhS0ZGqq91IwLBkpja6DQNmz4Sn"
    "KKBPqMSl513qN9t/szx5b+Jf7QRj3NAD0HMOnU89nd+azBRAeg2mBfQaBHSgwySFCqCsy+ck1Htv"
    "wMKSGAYFklReeIxUYrGiimULL120uvp6LlLVHZiPbK5w5/pf/0Pn4ADkQH6m4bf/2I+cz1e5w4sO"
    "zYZw+yLmexyd8RWDSjERK88dDs8EsJmOPq2VeMWGmff+6iVumpdr6hGcZT0/eu3lD/YFtEkrnzEA"
    "WM8WFiKY8gMAM1MErPJTteZ4JS1C0HAKWF/5Di4wrxllHPRY9r49YuVFEa5+VeOYCp5kQjkgObgf"
    "qskpOrct7OoQjeUwDBpGTQIg1pA+ucBWpZTah9BCC2CbCEdxiU9m9bsDHULl93kDuQICRTsIVE0h"
    "PQOdki9jA+BV+ifea9UC6MUUVnoVNQi0iwvBQ1PRLhXq99wumt2oXy20F7Y3Y6f2Y9XxX7z+4Xdf"
    "ggOSAwNgCU7nYXgGwbxXFHVGZjS7pS9emEg9iMT8kpUK0IQlJPTSRvdBsSfeXHk76XtGX1G/ua0p"
    "ADQGPVgQGEEZPM378slv+EdX1w283CZZP2EhwIzQBNVdIziY+BhhshTZOcTwUgCWhnbQXF1oNAy5"
    "qWxj2IAR4PiAT8AByoH+WGFJ0ZVXu25svqOgchpj2gEAjdZSCwg0nh/0hrKreooO1s5CgXLnWwRI"
    "UEa+Sy2I2NntVL84mW+wmSBNCcmpaq19Ts42ykamHFAgp4sh/B6ddsjBR4G4dbgt/y5VQqrCw+2w"
    "Hvj24ILeg4J48SAcjygHCkBN0dWh8M0+2LUHyR8qXj+j7RoMRYeCDprNAzmAm3OUf3F79339d77p"
    "WTCep1HpUCpPt6FfZv5Us7CYFOQJo63VZib0fJGQZZFFdQzW54Xtfi6BIal/591BDcOA2eZkTIs7"
    "OX65BQcsB/6D1TVF53d1sVgaCKKn1Qyy2EONs8Lz4U8JsMkTsuB2kXyQsdf7PZH7+KBRH5oNKlPn"
    "bJ0o9bX5eVXpDC7N1kjnUEwKUtOkyb+GfkjWJ9KajQcEFtNYCvjiCYAMCymq2SSBbyUFZsAaGkoJ"
    "tnrTjPciBw7AkqIb5vAZW66sLZAfxAgGMvT8qth7GmSWhkLONASjg92o8TQwQA846YrVQSmT50kg"
    "bHS+VyjLhO/u/uw7+0rvadjUybYfJ6/3AccYJWDDfHIdEfBoiwvVY4005iGpeG8MOmJRzg/xnFqU"
    "ULrErcQ+lJX3/HeeePdFOAQ5cAAWmb9mcpbKXXQKmMRJkcELn8PyZTFjiT9YTEw9Rt7eHIZgKah6"
    "mp3d9+X8dI/wr5OLZUBSgQNigYUQCvarX+Rq6pCvEbODPN4p14nRlkOwfK2xm8b/MI5VtAttUWME"
    "WsO88tMLYay4S4vpwaKOE6QDdTyiHAoAS4ouDXReU3F1YoF/IkovvfVogdWzqhLgmUwS2Y+qyp5U"
    "L8pSjZu8Z5+q/MLVKZQ739QjdQPc10PSRwFDt/qlon7RMjMQY4vuwTIkteiBHQD1XE3jolUA1f18"
    "yupbBXQsSoBg1ThLquEHen9LCN+gxhsz+C71PrBzP+RQAFjk5uqxc/mCX7IgNPBDSmKKCaMakuNQ"
    "980TNYiNTDFgI+CQ4zibmrfMO3+hKO+4oWlaZQe1CaRJtIB253P/sue9gYGFNPUFFj6iCHA9tYSm"
    "pCgBmLWCXeraQp5mWscvhaKEhTviNLNBSTMdaoMaFxv7idbACc234BDl0ADIhQp4VocdjRXqJx40"
    "fxtUiaxUijWXyQ1zV2F6CNZCgT/7432FAin9Kdf03ka0JeX77d58cqawdQWNpnVBWkqoGhZcVXox"
    "gVUw2xHuiGFzDpCG7dLVvbFBsHFEqYNBLVSVQWrc4vIuwdnDcDyiHBoAi3CKDnfU0A6mjMQqjCnA"
    "h5vA4ldQftKAC7o0Sk1hUdtxqc9WW/vCc9M8ACf5LCwovynXSGWxvt8RyR71NB//YD1M5tWfKe3V"
    "NcG9J0vVGRBrRyRJnv+diOOSQlAa7dEedoM5BtsSQrwxDI4AOzxXJsnT/RGuHbt9vOsa91MOFYBF"
    "snp8zOtxPUkvX6Ol/qOhrstfDBojAwniGnh4dKn3zrcJ3Jq5sSRnl0w9AMaYJHbnkwfYqMotqEPU"
    "BybZ/xq3k7ahuQ+XYIHRFMiRxdSuNLgljFUs0MRHRW2LCQBi0jiQ+cI/tftEd8x03+TQAVjvossB"
    "Yqd+aADAYx0oyAzlSEsUFBIfG8IxOy/+md+7DR0yh/LcP4nIKRBVjSWweCOWgHZnPjkft17uVOOO"
    "ub2LDIKmvErU7GIs04F6xzjoAIEDW1WqwjkJ6yWJl1r+HLxPKFklC+vksMuH3nURjkAOHYBFJnPa"
    "8kBqAJioo+BicKGWvLf5SMnTC/JTAigMkD3DZ3r6UNQvlsfuArTgxkDGAoKsoy52tZnVb0bTw6Gv"
    "7ufbAguncRbkRRTSgHxeoOYZLQpKK68ia1xjo4FWOYQkizXETo19dYENAI/CEcmRAPCFkqLjmJrH"
    "wIqQxsAAFgxyGVVs8CFv7JFwdWA7f3Sm/OQqxELYCBBRd7a98843kHQeh5TQS+qtfArseX8QihJ0"
    "AfK1Bs8Xmke4ATil+gN22qIEvw4M2jv5ry/p9dn7HC24/pfftadn++2HHAkAi0zmk8fKa50sSXnx"
    "o88i/wFEBhFF1dwDonaM7LT7rT/9Y50PCSo/uaVONUILxMDEiM92q99JKWiw/qCFd8TmU/CAQgAR"
    "Fm5UEtWql74ASo0Xen2gt1i/c2dH2yF9Xgz6fmpvlu8S7X+Z/d3IkQHwhUce2smDcU4nwh7Sk7RU"
    "nPdT0EHkJKWDsIsM/DZ0yNrlq2t533UtFABsbicVAgSpVOn7zTcOaONsUeUqU8UbyMUeDOoXwRdU"
    "rOSBZh80IIdsXgr0aIB3lV5HzSpeilgVUXmzdRePKT4QOTIAFrl1LG2VB13yJymA5A+Ixg46UR68"
    "VcvZftdCf9Aldarf+WSG4I+mALAJgRpjtIxCZsrO33yDW7lNBkxTQSMqOVyL/7CgXgtZkBnhjsoW"
    "2U9KqMBsktSoVDVB7OZ9bpOwcVzMIall0zvpeDoPRyxHCsASnM4jcg5sPRNEJgKIRQn8Pb9FCMNv"
    "+71hvtqZqVhZ13yvN2BqChXcUAPa7+yzjzKjWqzF7KukxaPmiWp4CUOYRoCiuV9lPoLopAlRyt6e"
    "/RBVq/eZyEPPCc0EMAqtalsrsbP63eq+UesA5UgBWOT2sbwKMX3btCo2uGqIQCtorOJZmEIMue2d"
    "8szCDslRsA2dIG5Wz4sgT2TRSuzum9nzvhvOXG5CgJkN9lniRpa31mtQ5qOwwNp4ojgdnLXAyLQO"
    "4IWMiFwfhXxwOXbnOz/7zkuwBHLkAKyFCkCfCjaPDaznLbH9rY+UIBrgVAHT99TTt15+bpYPWDOG"
    "ldxxy1qsztLQp9Lh+PGHGydiwR7za1NEgFMlur1GkfGM1Twwb+5Zam1WvRK1pZvz8WeM58cJnoQl"
    "kSMHYJH/9d4fKTez77RsIR5dFE3U0yAspUyYoy8rfQ5IPmJTvEi5TyJ4wXWSVDPj8y++ry+gnTG7"
    "AbGrkf1aVlS1asUBjFLxdiVn2zSO6I8mUUCJV2vKwkI74EweFoRceWXJPIIXu736Q5ClAGCRgYbH"
    "0O07s/MoFEuaJ1ifiQfMVjyNz+4+0ln7B1ynZ6AAdwIaldz5JFU+vtz5hhFsjd0Hdk+QcF2NL6Mx"
    "GC0yZAq1gACBQUlVM8MV0NlQM4jkWSKM48Ztv5RSdvyWSJYGgC++twSny6RTVEcWybeiBBldDT7L"
    "s+ye7zlHVb8IU/1s4Qjw+0CMVDrzyWtf+G+z3MhaMCGseX2ivKpLe8wHInhJGUYV7Y8u0fyxBq0Z"
    "wWqCcLtBFcfSLbRyLTcHeHtaKvYrsjQALJJ165aFIoQbal41GOe+ujWjZKGGH94+P6HeJxOcJVxl"
    "VThe680np4nkk6VNjKqPoHEWMPyKEyjbR+YDQq/4trWGkVltP7PtdEBA2M6y21bZoxXiWc8cedhl"
    "UZYKgIUF8xBuOzhQfn/YTCUHCgvKfj/xw9qeXr62lhubgajamFlopAKlL58sB8wgpLqcTsEfwaFB"
    "Zo3xJfHmI2OamiSP10D4X/EX7/sF3QYGPkgY15P8ilP1ms8uG/sVWSoAFske2mMkRrqyiqxop4QI"
    "Qh7t6Vuf/q3ZD2r35cmtM6p+rRKF1C5j4eri8m3fnW9v/TfPzZDbxEahiv1moPEQS7hQMHWcghNk"
    "RQhGehiyKW4jCtiaqua2fXFnmCev7W7+xCVYQlk6AL5wMqfogM773azg2QrJAVuy3uvdyr3FF97+"
    "9LXpq7X51i//VgYfnUYHhP1Z2qtMajXg0+63Hv3dffnkROtm5IUwkdpeXJSQSK+DPHuDdbvyIjS2"
    "Whsgd9MgmA4UKl0kbrgQplLwS4zzr8KSyjFYQrmVPbXjA53KU7gmlg6oUQVi5dRYhH1XjfYH5zS/"
    "8ran/8fW8Qk8e32+srsy3JplhG4CSeWL7G/kCaBPTwVNl2WU3M0NORtqJnCDaBlDy+oAxAsA/oac"
    "FUnuwisBErEQCQxcFhgHoGDuoWNWd6bF9mt8s5z64u6f/32HdpPR3crSMWCRev9IZkEpS/e8KYaK"
    "FQAM4QvBI03zh39xc45Xj8Htb+bvLgDWp5M6O2A8E0G4qZtZpdP7fdvlb5zIh02dTdXui5+tHB/M"
    "uVBIesiFCRz1WEmZoZgD6sC0KrxxPpQ9tRDVbMSyz+RwbzK6W1lKABa5mdK5PHkv2WTJoFLIB1dB"
    "9PnhG78xTEqopRPnQ8Dgno3uV3e69OKj79ju6d98KJUvXhjh9mq0wwCaFFjwDorw0xfAOkixKqdW"
    "sSTLapDajAIwbdQ+SymWlu3z4qStu3g0yZHI0gKwsGCevMecNURVhQnEJuwgisp/9FR28UmXqlfB"
    "HYB5rbL3ysqwBb2SsmoHJSj2ZfgZK7BQxQMQYnlux6VYHAC+wCTWaWm4EAdsnimtBAt+Z6GAlFtL"
    "eA3ScBGWXJYWgEX+98mHvphH/JIMqUyQpbQUeBS0k7MMf2IHQIvg+MZuv/Ec5N6I+n7YeqEzm1LU"
    "b87FnHBq1dP5I9dQTQPL55LTtvXV+2x2aPDLa5/JMO7FF8myG+aERNavi7JUuyw5+xVZagAWWQU8"
    "XX4OPrkNx++UabSOUNkmVATbfhJDJMFhVMFcWgznX/zpd5zt7BIMeOxxu6ssebpDzQGzNw0QascB"
    "RHsU7DhtC8EWl5oFCY3VNDSlgWZSexEErF68sLX7M7/nEtwHgnAfyPTKtbXvAV3Jg37CbgABrmKR"
    "h6GLdtUHJ+i85LeDP9JXs1+2f91Ol377kd/1GHTK2y8/N701wW+y95n/HQbV/dp2cEe9QCE86sGz"
    "cKJYQZeP7YOa4/ZQjXm6IeJov45CftwAl/7Pn/vx7us5all6Biyyk+3BBwBPJhguuXklj5lRm8rV"
    "T30lBM+NRuM/+YOH8qdP3Q34ityapDNyouCRU8xQBFbDWJQqTgLEegtgp0l7hKrPXbd7n8EatyIK"
    "Pw8vBvrM/QS+IvcFA0Z5+5X/eSrPyJn8dloIYIBQvzQoG0pogzjwRxQ5r37x9UyMT8gvffafO7Pf"
    "7WPpGijRkQTKB5ITgv9kU2Uv82/8WYNOhUxqwWciNMZjKtezuGutZ1yUXRzwsW/9zI8tbbzv+8l9"
    "B8Aib79SMh7zWQ5ynSmxP1JVpS5HVInkk59le5JDLS/81O+8CHuQt/y73yzge7AN+grRVvCRsRyf"
    "WGr39Mfu/T5eBS00fQbSp33JEWZe+DxJaFCKaHO8NJ0b0ur53c5q8GWT+xKAUTIYZ3kq1gciDgxn"
    "gACR1iLtZHfwWcThmfkwPFuKHWCPUtJ5udGz1FiQYJyEFIwxyWpgu5u/mC3Htp5mY7w5wEX7Tj6W"
    "AH2+psl2Gm491VuxM8ooo4wyyiijjDLKKKOMMsooo4wyyiijjDLKKKOMMsooo4wyyiijjDLKKKOM"
    "Msooo4wyyiijjDLKKKOMMsoo+yn/Dz5AVzqUvk9+AAAAAElFTkSuQmCC"
)

SOLUTION_XML_NATIVE = """\
<ImportExportXml version="9.2.26023.151" SolutionPackageVersion="9.2" languagecode="1033" generatedBy="CrmLive" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" OrganizationVersion="9.2.26023.151" OrganizationSchemaType="Standard" CRMServerServiceabilityVersion="9.2.26024.00146">
  <SolutionManifest>
    <UniqueName>{solution_unique_name}</UniqueName>
    <LocalizedNames>
      <LocalizedName description="{solution_display_name}" languagecode="1033" />
    </LocalizedNames>
    <Descriptions />
    <Version>{solution_version}</Version>
    <Managed>{managed_flag}</Managed>
    <Publisher>
      <UniqueName>{publisher_unique_name}</UniqueName>
      <LocalizedNames>
        <LocalizedName description="{publisher_display_name}" languagecode="1033" />
      </LocalizedNames>
      <Descriptions>
        <Description description="Auto-generated publisher" languagecode="1033" />
      </Descriptions>
      <EMailAddress xsi:nil="true"></EMailAddress>
      <SupportingWebsiteUrl xsi:nil="true"></SupportingWebsiteUrl>
      <CustomizationPrefix>{publisher_prefix}</CustomizationPrefix>
      <CustomizationOptionValuePrefix>10000</CustomizationOptionValuePrefix>
      <Addresses>
        <Address>
          <AddressNumber>1</AddressNumber>
          <AddressTypeCode xsi:nil="true"></AddressTypeCode>
          <City xsi:nil="true"></City>
          <County xsi:nil="true"></County>
          <Country xsi:nil="true"></Country>
          <Fax xsi:nil="true"></Fax>
          <FreightTermsCode xsi:nil="true"></FreightTermsCode>
          <ImportSequenceNumber xsi:nil="true"></ImportSequenceNumber>
          <Latitude xsi:nil="true"></Latitude>
          <Line1 xsi:nil="true"></Line1>
          <Line2 xsi:nil="true"></Line2>
          <Line3 xsi:nil="true"></Line3>
          <Longitude xsi:nil="true"></Longitude>
          <Name xsi:nil="true"></Name>
          <PostalCode xsi:nil="true"></PostalCode>
          <PostOfficeBox xsi:nil="true"></PostOfficeBox>
          <PrimaryContactName xsi:nil="true"></PrimaryContactName>
          <ShippingMethodCode xsi:nil="true"></ShippingMethodCode>
          <StateOrProvince xsi:nil="true"></StateOrProvince>
          <Telephone1 xsi:nil="true"></Telephone1>
          <Telephone2 xsi:nil="true"></Telephone2>
          <Telephone3 xsi:nil="true"></Telephone3>
          <TimeZoneRuleVersionNumber xsi:nil="true"></TimeZoneRuleVersionNumber>
          <UPSZone xsi:nil="true"></UPSZone>
          <UTCOffset xsi:nil="true"></UTCOffset>
          <UTCConversionTimeZoneCode xsi:nil="true"></UTCConversionTimeZoneCode>
        </Address>
        <Address>
          <AddressNumber>2</AddressNumber>
          <AddressTypeCode xsi:nil="true"></AddressTypeCode>
          <City xsi:nil="true"></City>
          <County xsi:nil="true"></County>
          <Country xsi:nil="true"></Country>
          <Fax xsi:nil="true"></Fax>
          <FreightTermsCode xsi:nil="true"></FreightTermsCode>
          <ImportSequenceNumber xsi:nil="true"></ImportSequenceNumber>
          <Latitude xsi:nil="true"></Latitude>
          <Line1 xsi:nil="true"></Line1>
          <Line2 xsi:nil="true"></Line2>
          <Line3 xsi:nil="true"></Line3>
          <Longitude xsi:nil="true"></Longitude>
          <Name xsi:nil="true"></Name>
          <PostalCode xsi:nil="true"></PostalCode>
          <PostOfficeBox xsi:nil="true"></PostOfficeBox>
          <PrimaryContactName xsi:nil="true"></PrimaryContactName>
          <ShippingMethodCode xsi:nil="true"></ShippingMethodCode>
          <StateOrProvince xsi:nil="true"></StateOrProvince>
          <Telephone1 xsi:nil="true"></Telephone1>
          <Telephone2 xsi:nil="true"></Telephone2>
          <Telephone3 xsi:nil="true"></Telephone3>
          <TimeZoneRuleVersionNumber xsi:nil="true"></TimeZoneRuleVersionNumber>
          <UPSZone xsi:nil="true"></UPSZone>
          <UTCOffset xsi:nil="true"></UTCOffset>
          <UTCConversionTimeZoneCode xsi:nil="true"></UTCConversionTimeZoneCode>
        </Address>
      </Addresses>
    </Publisher>
    <RootComponents>{root_components}</RootComponents>
    <MissingDependencies />
  </SolutionManifest>
</ImportExportXml>"""

CUSTOMIZATIONS_XML_NATIVE = """\
<ImportExportXml xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" OrganizationVersion="9.2.26023.151" OrganizationSchemaType="Standard" CRMServerServiceabilityVersion="9.2.26024.00146">
  <Entities></Entities>
  <Roles></Roles>
  <Workflows>{workflows}</Workflows>
  <FieldSecurityProfiles></FieldSecurityProfiles>
  <Templates />
  <EntityMaps />
  <EntityRelationships />
  <OrganizationSettings />
  <optionsets />
  <CustomControls />
  <EntityDataProviders />{connectors}
  <connectionreferences>
{connection_references}
  </connectionreferences>
  <Languages>
    <Language>1033</Language>
  </Languages>
</ImportExportXml>"""

# One packaged custom connector (customizations.xml <Connectors> child + the four
# /Connector files + a type-372 RootComponent) — field-for-field the shape of the
# import-verified brainstemswarmv2 solution export.
CONNECTOR_ELEMENT_XML = """\
    <Connector>
      <connectorid>{connector_guid}</connectorid>
      <description>{description}</description>
      <displayname>{display_name}</displayname>
      <iconbrandcolor>#007ee5</iconbrandcolor>
      <name>{encoded_name}</name>
      <connectortype>1</connectortype>
      <openapidefinition>/Connector/{encoded_name}_openapidefinition.json</openapidefinition>
      <connectionparameters>/Connector/{encoded_name}_connectionparameters.json</connectionparameters>
      <policytemplateinstances>/Connector/{encoded_name}_policytemplateinstances.json</policytemplateinstances>
      <iconblob>/Connector/{encoded_name}_iconblob.Png</iconblob>
    </Connector>"""

_CONNECTOR_ROOT_COMPONENT = ('      <RootComponent type="372" id="{{{connector_guid}}}" '
                             'schemaName="{encoded_name}" behavior="0" />')

# A connection reference (customizations.xml), the flow-bound style real
# exports use ({prefix}_shared{api}_{5hex}, iscustomizable 1). For a custom
# connector the optional customconnectorid element links it to the packaged
# <Connector> by GUID.
CONNECTION_REFERENCE_XML = """\
    <connectionreference connectionreferencelogicalname="{logical_name}">
      <connectionreferencedisplayname>{display_name}</connectionreferencedisplayname>
      <connectorid>{connector_id}</connectorid>{custom_connector_element}
      <iscustomizable>1</iscustomizable>
      <promptingbehavior>0</promptingbehavior>
      <statecode>0</statecode>
      <statuscode>1</statuscode>
    </connectionreference>"""

CUSTOM_CONNECTOR_ID_ELEMENT = """
      <customconnectorid>
        <connectorid>{connector_guid}</connectorid>
      </customconnectorid>"""

CONTENT_TYPES_XML_NATIVE = '<?xml version="1.0" encoding="utf-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/octet-stream" /><Default Extension="json" ContentType="application/octet-stream" />{overrides}</Types>'

CONTENT_TYPE_OVERRIDE = '<Override PartName="/{part_name}" ContentType="application/octet-stream" />'

BOT_XML = """\
<bot schemaname="{bot_schema}">
  <authenticationmode>{authentication_mode}</authenticationmode>
  <authenticationtrigger>{authentication_trigger}</authenticationtrigger>
  <iconbase64>{icon_base64}</iconbase64>
  <iscustomizable>0</iscustomizable>
  <language>1033</language>
  <name>{bot_display_name}</name>
  <runtimeprovider>0</runtimeprovider>
  <template>default-2.1.0</template>
</bot>"""

BOT_CONFIGURATION_JSON_NATIVE = """{{
  "$kind": "BotConfiguration",
  "settings": {{
    "GenerativeActionsEnabled": true
  }},
  "isAgentConnectable": true,
  "gPTSettings": {{
    "$kind": "GPTSettings",
    "defaultSchemaName": "{gpt_schema}"
  }},
  "isLightweightBot": false,
  "aISettings": {{
    "$kind": "AISettings",
    "useModelKnowledge": true,
    "isFileAnalysisEnabled": true,
    "isSemanticSearchEnabled": true,
    "contentModeration": "High",
    "optInUseLatestModels": false
  }},
  "recognizer": {{
    "$kind": "GenerativeAIRecognizer"
  }}
}}"""

ORCHESTRATOR_CHANNELS_BLOCK = """
  "channels": [
    {
      "$kind": "ChannelDefinition",
      "channelId": "MsTeams"
    },
    {
      "$kind": "ChannelDefinition",
      "channelId": "Microsoft365Copilot"
    }
  ],"""

ORCHESTRATOR_CONFIGURATION_JSON = """{{
  "$kind": "BotConfiguration",{channels_block}
  "settings": {{
    "GenerativeActionsEnabled": true
  }},
  "isAgentConnectable": true,{publish_on_import_line}
  "gPTSettings": {{
    "$kind": "GPTSettings",
    "defaultSchemaName": "{gpt_schema}"
  }},
  "isLightweightBot": false,
  "aISettings": {{
    "$kind": "AISettings",
    "useModelKnowledge": true,
    "isFileAnalysisEnabled": true,
    "isSemanticSearchEnabled": true,
    "contentModeration": "High",
    "optInUseLatestModels": true
  }},
  "recognizer": {{
    "$kind": "GenerativeAIRecognizer"
  }}
}}"""

GPT_BOTCOMPONENT_XML = """\
<botcomponent schemaname="{schema_name}">
  <componenttype>15</componenttype>{description_element}
  <iscustomizable>0</iscustomizable>
  <name>{display_name}</name>
  <parentbotid>
    <schemaname>{bot_schema}</schemaname>
  </parentbotid>
  <statecode>0</statecode>
  <statuscode>1</statuscode>
</botcomponent>"""

GPT_DATA_YAML = """\
kind: GptComponentMetadata
displayName: {display_name}
instructions: |-
{instructions_indented}
{conversation_starters}gptCapabilities:
  webBrowsing: true
  codeInterpreter: true

aISettings:
  model:
    modelNameHint: GPT5Chat

  extensionData:
    lastUsedCustomModel: {{}}

declarativeSkillsMetadata:"""

BOTCOMPONENT_XML = """\
<botcomponent schemaname="{schema_name}">
  <componenttype>{component_type}</componenttype>{description_element}
  <iscustomizable>0</iscustomizable>
  <name>{display_name}</name>
  <parentbotid>
    <schemaname>{bot_schema}</schemaname>
  </parentbotid>
  <statecode>0</statecode>
  <statuscode>1</statuscode>
</botcomponent>"""

CONN_REF_SET_XML = """\
<botcomponent_connectionreferenceset>
{entries}
</botcomponent_connectionreferenceset>"""

# The botcomponent <-> workflow M:N association (Assets/botcomponent_workflowset.xml):
# declares each capability flow as a dependency of the tool that invokes it, so the
# import wires them together (shape verbatim from a real Dataverse export).
WORKFLOW_SET_XML = """\
<botcomponent_workflowset>
{entries}
</botcomponent_workflowset>"""

WORKFLOW_SET_ENTRY_XML = """\
  <botcomponent_workflow botcomponentid.schemaname="{component_schema}" workflowid.workflowid="{workflow_id}">
    <iscustomizable>1</iscustomizable>
  </botcomponent_workflow>"""

INVOKE_CONNECTED_AGENT_BOTCOMPONENT_XML = """\
<botcomponent schemaname="{schema_name}">
  <componenttype>9</componenttype>
  <description>{description}</description>
  <iscustomizable>0</iscustomizable>
  <name>{display_name}</name>
  <parentbotid>
    <schemaname>{orchestrator_schema}</schemaname>
  </parentbotid>
  <statecode>0</statecode>
  <statuscode>1</statuscode>
</botcomponent>"""

INVOKE_CONNECTED_AGENT_DATA = """\
kind: TaskDialog
modelDisplayName: {display_name}
modelDescription: |-
{description_indented}{inputs_block}
action:
  kind: InvokeConnectedAgentTaskAction{input_type_block}
  botSchemaName: {child_schema}
  historyType:
    kind: ConversationHistory"""


def _copilot_type(json_type):
    """Map a JSON-schema parameter type (from agent.py metadata.parameters) to a
    Copilot Studio connected-agent input type. Copilot Studio inputs are
    String / Number / Boolean; object & array params are passed as JSON strings."""
    t = (json_type or "string").lower()
    if t in ("integer", "number"):
        return "Number"
    if t == "boolean":
        return "Boolean"
    return "String"


def _param_prop_names(params):
    """The sanitized, uniquified property name for each param entry, in order —
    the ONE name allocator every hop shares (the orchestrator's connected-agent
    inputs, the child's flow tool, the flow trigger schema), so the same param
    list yields the same names everywhere by construction. Two source params
    can sanitize to the SAME name ("user id" / "user-id" -> "userid");
    uniquify instead of silently dropping one — a dropped input is invisible
    data loss for LLM-distilled agents."""
    names, seen = [], set()
    for entry in params or []:
        pn = entry[0] if isinstance(entry, (list, tuple)) and entry else entry
        name = re.sub(r"[^A-Za-z0-9_]", "", str(pn)) or "input"
        if name in seen:
            base, i = name, 2
            while name in seen:
                name, i = f"{base}{i}", i + 1
        seen.add(name)
        names.append(name)
    return names


def _connected_inputs_yaml(params):
    """The orchestrator-side typed inputs for a connected agent, from the source
    agent.py's perform() params. Per the Copilot Studio connected-agent schema:
    `inputs` (AutomaticTaskInput list) sits at the TaskDialog root and `inputType`
    sits INSIDE the action block. These populate the connected agent's Inputs
    panel and let the orchestrator pass the params when it delegates. Returns
    (inputs_block, input_type_block) — both '' when there are no params."""
    params = params or []
    if not params:
        return "", ""
    inlines, props = [], []
    names = _param_prop_names(params)  # the ONE shared allocator (see _param_prop_names)
    for idx, entry in enumerate(params):
        pdesc = (str(entry[1]) if isinstance(entry, (list, tuple)) and len(entry) > 1
                 and entry[1] else "")
        required = bool(entry[2]) if isinstance(entry, (list, tuple)) and len(entry) > 2 else False
        ptype = entry[3] if isinstance(entry, (list, tuple)) and len(entry) > 3 else "string"
        name = names[idx]
        # REQUIRED params are model-filled from the delegated task (AutomaticTaskInput);
        # OPTIONAL params get a FIXED default value (ManualTaskInput) so the ORCHESTRATOR
        # does NOT prompt the user for them when delegating — the connected sub-agent
        # runs immediately (empty query returns all/top records). The empty-string Power
        # Fx literal is written as "" — the verified-working shape from a real export.
        jt = str(ptype).lower()
        if required:
            inlines.append("  - kind: AutomaticTaskInput\n    propertyName: " + name
                           + ("\n    description: " + _yaml_dq(pdesc[:200]) if pdesc else ""))
        else:
            default = entry[4] if isinstance(entry, (list, tuple)) and len(entry) > 4 else None
            inlines.append("  - kind: ManualTaskInput\n    propertyName: " + name
                           + "\n    value: " + _manual_value_token(default, jt))
        props.append("      " + name + ":\n"
                     "        displayName: " + name + "\n"
                     + ("        description: " + _yaml_dq(pdesc[:200]) + "\n" if pdesc else "")
                     + "        isRequired: true\n"
                     "        type: " + _copilot_type(ptype))
    return ("\ninputs:\n" + "\n".join(inlines),
            "\n  inputType:\n    properties:\n" + "\n".join(props))

INVOKE_CONNECTED_AGENT_DEPENDENCIES = '[{{"type":"bot","schemaName":"{child_schema}"}}]'

SYSTEM_TOPICS = {
    "ConversationStart": {
        "display_name": "Conversation Start",
        "description": "This system topic triggers when the agent receives an Activity indicating the beginning of a new conversation. If you do not want the agent to initiate the conversation, disable this topic.",
        "data": """\
kind: AdaptiveDialog
beginDialog:
  kind: OnConversationStart
  id: main
  actions:
    - kind: SendActivity
      id: sendMessage_M0LuhV
      activity:
        text:
          - Hello, I'm {{System.Bot.Name}}. How can I help?
        speak:
          - Hello and thank you for calling {{System.Bot.Name}}. Please note that some responses are generated by AI and may require verification for accuracy. How may I help you today?"""
    },
    "EndofConversation": {
        "display_name": "End of Conversation",
        "description": "This system topic is only triggered by a redirect action,\nand guides the user through rating their conversation with the agent.",
        "data": """\
kind: AdaptiveDialog
startBehavior: CancelOtherTopics
beginDialog:
  kind: OnSystemRedirect
  id: main
  actions:
    - kind: Question
      id: 41d42054-d4cb-4e90-b922-2b16b37fe379
      conversationOutcome: ResolvedImplied
      alwaysPrompt: true
      variable: init:Topic.SurveyResponse
      prompt: Did that answer your question?
      entity: BooleanPrebuiltEntity

    - kind: ConditionGroup
      id: condition-0
      conditions:
        - id: condition-0-item-0
          condition: =Topic.SurveyResponse = true
          actions:
            - kind: CSATQuestion
              id: csat_1
              conversationOutcome: ResolvedConfirmed

            - kind: SendActivity
              id: sendMessage_8r29O0
              activity: Thanks for your feedback.

            - kind: Question
              id: question_1
              alwaysPrompt: true
              variable: init:Topic.Continue
              prompt: Can I help with anything else?
              entity: BooleanPrebuiltEntity

            - kind: ConditionGroup
              id: condition-1
              conditions:
                - id: condition-1-item-0
                  condition: =Topic.Continue = true
                  actions:
                    - kind: SendActivity
                      id: sendMessage_4eOE6h
                      activity: Go ahead. I'm listening.

              elseActions:
                - kind: SendActivity
                  id: yHBz55
                  activity: Ok, goodbye.

                - kind: EndConversation
                  id: jh1GMT

      elseActions:
        - kind: Question
          id: PM68ot
          alwaysPrompt: true
          variable: init:Topic.TryAgain
          prompt: Sorry I wasn't able to help better. Would you like to try again?
          entity: BooleanPrebuiltEntity

        - kind: ConditionGroup
          id: KNxYBf
          conditions:
            - id: DPveFP
              condition: =Topic.TryAgain = false
              actions:
                - kind: BeginDialog
                  id: cngqi4
                  dialog: {bot_schema}.topic.Escalate

          elseActions:
            - kind: SendActivity
              id: GrVHEW
              activity: Go ahead. I'm listening."""
    },
    "Escalate": {
        "display_name": "Escalate",
        "description": "This system topic is triggered when the user indicates they would like to speak to a representative.\nYou can configure how the agent will handle human hand-off scenarios in the agent settings..\nIf your agent does not handle escalations, this topic should be disabled.",
        "data": """\
kind: AdaptiveDialog
startBehavior: CancelOtherTopics
beginDialog:
  kind: OnEscalate
  id: main
  intent:
    displayName: Escalate
    includeInOnSelectIntent: false
    triggerQueries:
      - Talk to agent
      - Talk to a person
      - Talk to someone
      - Call back
      - Call customer service
      - Call me please
      - Call support
      - Call technical support
      - Can an agent call me
      - Can I call
      - Can I get in touch with someone else
      - Can I get real agent support
      - Can I get transferred to a person to call
      - Can I have a call in number Or can I be called
      - Can I have a representative call me
      - Can I schedule a call
      - Can I speak to a representative
      - Can I talk to a human
      - Can I talk to a human assistant
      - Can someone call me
      - Chat with a human
      - Chat with a representative
      - Chat with agent
      - Chat with someone please
      - Connect me to a live agent
      - Connect me to a person
      - Could some one contact me by phone
      - Customer agent
      - Customer representative
      - Customer service
      - I need a manager to contact me
      - I need customer service
      - I need help from a person
      - I need to speak with a live argent
      - I need to talk to a specialist please
      - I want to talk to customer service
      - I want to proceed with live support
      - I want to speak with a consultant
      - I want to speak with a live tech
      - I would like to speak with an associate
      - I would like to talk to a technician
      - Talk with tech support member

  actions:
    - kind: SendActivity
      id: sendMessage_s39DCt
      conversationOutcome: Escalated
      activity: |-
        Escalating to a representative is not currently configured for this agent, however this is where the agent could provide information about how to get in touch with someone another way.

        Is there anything else I can help you with?"""
    },
    "Fallback": {
        "display_name": "Fallback",
        "description": "This system topic triggers when the user's utterance does not match any existing topics.",
        "data": """\
kind: AdaptiveDialog
beginDialog:
  kind: OnUnknownIntent
  id: main
  actions:
    - kind: ConditionGroup
      id: conditionGroup_LktzXw
      conditions:
        - id: conditionItem_tlGIVo
          condition: =System.FallbackCount < 3
          actions:
            - kind: SendActivity
              id: sendMessage_QZreqo
              activity: I'm sorry, I'm not sure how to help with that. Can you try rephrasing?

      elseActions:
        - kind: BeginDialog
          id: 5aXj5M
          dialog: {bot_schema}.topic.Escalate"""
    },
    "Goodbye": {
        "display_name": "Goodbye",
        "description": "This topic triggers when the user says goodbye. By default, it does not end the conversation. If you would like to end the conversation when the user says goodbye, you can add an \"End of Conversation\" action to this topic, or redirect to the \"End of Conversation\" system topic.",
        "data": """\
kind: AdaptiveDialog
startBehavior: CancelOtherTopics
beginDialog:
  kind: OnRecognizedIntent
  id: main
  intent:
    displayName: Goodbye
    includeInOnSelectIntent: false
    triggerQueries:
      - Bye
      - Bye for now
      - Bye now
      - Good bye
      - No thank you. Goodbye.
      - See you later

  actions:
    - kind: Question
      id: question_zf2HhP
      variable: Topic.EndConversation
      prompt: Would you like to end our conversation?
      entity: BooleanPrebuiltEntity

    - kind: ConditionGroup
      id: condition_DGc1Wy
      conditions:
        - id: condition_DGc1Wy-item-0
          condition: =Topic.EndConversation = true
          actions:
            - kind: BeginDialog
              id: dn94DC
              dialog: {bot_schema}.topic.EndofConversation

        - id: condition_DGc1Wy-item-1
          condition: =Topic.EndConversation = false
          actions:
            - kind: SendActivity
              id: sendMessage_LdLhmf
              activity: Go ahead. I'm listening."""
    },
    "Greeting": {
        "display_name": "Greeting",
        "description": "This topic is triggered when the user greets the agent.",
        "data": """\
kind: AdaptiveDialog
beginDialog:
  kind: OnRecognizedIntent
  id: main
  intent:
    displayName: Greeting
    includeInOnSelectIntent: false
    triggerQueries:
      - Good afternoon
      - Good morning
      - Hello
      - Hey
      - Hi

  actions:
    - kind: SendActivity
      id: sendMessage_abmysR
      activity:
        text:
          - Hello, how can I help you today?
        speak:
          - Hello, <break strength="medium" /> how can I help?

    - kind: CancelAllDialogs
      id: cancelAllDialogs_01At22"""
    },
    "MultipleTopicsMatched": {
        "display_name": "Multiple Topics Matched",
        "description": "This system topic triggers when the agent matches multiple Topics with the incoming message and needs to clarify which one should be triggered.",
        "data": """\
kind: AdaptiveDialog
beginDialog:
  kind: OnSelectIntent
  id: main
  triggerBehavior: Always
  actions:
    - kind: SetVariable
      id: setVariable_M6434i
      variable: init:Topic.IntentOptions
      value: =System.Recognizer.IntentOptions

    - kind: SetTextVariable
      id: setTextVariable_0
      variable: Topic.NoneOfTheseDisplayName
      value: None of these

    - kind: EditTable
      id: sendMessage_g5Ls09
      changeType: Add
      itemsVariable: Topic.IntentOptions
      value: "={{ DisplayName: Topic.NoneOfTheseDisplayName, TopicId: \\"NoTopic\\", TriggerId: \\"NoTrigger\\", Score: 1.0 }}"

    - kind: Question
      id: question_zf2HhP
      interruptionPolicy:
        allowInterruption: false

      alwaysPrompt: true
      variable: System.Recognizer.SelectedIntent
      prompt: "To clarify, did you mean:"
      entity:
        kind: DynamicClosedListEntity
        items: =Topic.IntentOptions

    - kind: ConditionGroup
      id: conditionGroup_60PuXb
      conditions:
        - id: conditionItem_rs7GgM
          condition: =System.Recognizer.SelectedIntent.TopicId = "NoTopic"
          actions:
            - kind: ReplaceDialog
              id: YZXRDb
              dialog: {bot_schema}.topic.Fallback"""
    },
    "OnError": {
        "display_name": "On Error",
        "description": "This system topic triggers when the agent encounters an error. When using the test chat pane, the full error description is displayed.",
        "data": """\
kind: AdaptiveDialog
startBehavior: UseLatestPublishedContentAndCancelOtherTopics
beginDialog:
  kind: OnError
  id: main
  actions:
    - kind: SetVariable
      id: setVariable_timestamp
      variable: init:Topic.CurrentTime
      value: =Text(Now(), DateTimeFormat.UTC)

    - kind: ConditionGroup
      id: condition_1
      conditions:
        - id: bL4wmY
          condition: =System.Conversation.InTestMode = true
          actions:
            - kind: SendActivity
              id: sendMessage_XJBYMo
              activity: |-
                Error Message: {{System.Error.Message}}
                Error Code: {{System.Error.Code}}
                Conversation Id: {{System.Conversation.Id}}
                Time (UTC): {{Topic.CurrentTime}}

      elseActions:
        - kind: SendActivity
          id: sendMessage_dZ0gaF
          activity:
            text:
              - |-
                An error has occurred.
                Error code: {{System.Error.Code}}
                Conversation Id: {{System.Conversation.Id}}
                Time (UTC): {{Topic.CurrentTime}}.
            speak:
              - An error has occurred, please try again.

    - kind: LogCustomTelemetryEvent
      id: 9KwEAn
      eventName: OnErrorLog
      properties: "={{ErrorMessage: System.Error.Message, ErrorCode: System.Error.Code, TimeUTC: Topic.CurrentTime, ConversationId: System.Conversation.Id}}"

    - kind: CancelAllDialogs
      id: NW7NyY"""
    },
    "ResetConversation": {
        "display_name": "Reset Conversation",
        "description": None,
        "data": """\
kind: AdaptiveDialog
startBehavior: UseLatestPublishedContentAndCancelOtherTopics
beginDialog:
  kind: OnSystemRedirect
  id: main
  actions:
    - kind: SendActivity
      id: sendMessage_OPsT1O
      activity: What can I help you with?

    - kind: ClearAllVariables
      id: clearAllVariables_73bTFR
      variables: ConversationScopedVariables

    - kind: CancelAllDialogs
      id: cancelAllDialogs_12Gt21"""
    },
    "Search": {
        "display_name": "Conversational boosting",
        "description": "Create generative answers from knowledge sources.",
        "data": """\
kind: AdaptiveDialog
beginDialog:
  kind: OnUnknownIntent
  id: main
  priority: -1
  actions:
    - kind: SearchAndSummarizeContent
      id: search-content
      variable: Topic.Answer
      userInput: =System.Activity.Text

    - kind: ConditionGroup
      id: has-answer-conditions
      conditions:
        - id: has-answer
          condition: =!IsBlank(Topic.Answer)
          actions:
            - kind: EndDialog
              id: end-topic
              clearTopicQueue: true"""
    },
    "Signin": {
        "display_name": "Sign in ",
        "description": "This system topic triggers when the agent needs to sign in the user or require the user to sign in",
        "data": """\
kind: AdaptiveDialog
beginDialog:
  kind: OnSignIn
  id: main
  actions:
    - kind: ConditionGroup
      id: conditionGroup_ypjGKL
      conditions:
        - id: conditionItem_7XYIIR
          condition: =System.SignInReason = SignInReason.SignInRequired
          actions:
            - kind: SendActivity
              id: sendMessage_1jHUNO
              activity: Hello! To be able to help you, I'll need you to sign in.

    - kind: OAuthInput
      id: gOjhZA
      title: Login
      text: To continue, please login"""
    },
    "StartOver": {
        "display_name": "Start Over",
        "description": None,
        "data": """\
kind: AdaptiveDialog
beginDialog:
  kind: OnRecognizedIntent
  id: main
  intent:
    displayName: Start Over
    includeInOnSelectIntent: false
    triggerQueries:
      - let's begin again
      - start over
      - start again
      - restart

  actions:
    - kind: Question
      id: question_zguoVV
      alwaysPrompt: false
      variable: init:Topic.Confirm
      prompt: Are you sure you want to restart the conversation?
      entity: BooleanPrebuiltEntity

    - kind: ConditionGroup
      id: conditionGroup_lvx2zV
      conditions:
        - id: conditionItem_sVQtHa
          condition: =Topic.Confirm = true
          actions:
            - kind: BeginDialog
              id: 0YKYsy
              dialog: {bot_schema}.topic.ResetConversation

      elseActions:
        - kind: SendActivity
          id: sendMessage_lk2CyQ
          activity: Ok. Let's carry on."""
    },
    "ThankYou": {
        "display_name": "Thank you",
        "description": "This topic triggers when the user says thank you.",
        "data": """\
kind: AdaptiveDialog
beginDialog:
  kind: OnRecognizedIntent
  id: main
  intent:
    displayName: Thank you
    includeInOnSelectIntent: false
    triggerQueries:
      - thanks
      - thank you
      - thanks so much
      - ty

  actions:
    - kind: SendActivity
      id: sendMessage_9iz6v7
      activity: You're welcome."""
    },
}


# ============================================================================
# Packager: orchestrator + connected sub-agents, with the 42-char name cap,
# 100-char schema cap, and optional channels (default off = headless-publishable)
# ============================================================================

MAX_SCHEMA = 100


_CONNECTED_INFIX = ".InvokeConnectedAgentTaskAction."   # 32 chars (incl. both dots)


_MIN_ACTION_BUDGET = 26   # always leave at least this many chars for the action suffix


MAX_BOT_NAME = 42


def _cap_bot_name(name: str, preserve_suffix: Optional[str] = None) -> str:
    """Truncate a bot display name to the 42-char limit, keeping a trailing word
    like 'Orchestrator' intact when present."""
    name = (name or "").strip()
    if len(name) <= MAX_BOT_NAME:
        return name
    if preserve_suffix and name.endswith(preserve_suffix):
        budget = MAX_BOT_NAME - len(preserve_suffix) - 1
        head = name[: -len(preserve_suffix)].rstrip()[:budget].rstrip()
        return f"{head} {preserve_suffix}"
    return name[:MAX_BOT_NAME].rstrip()


def _sanitize_schema(name: str) -> str:
    """Lowercase alphanumeric fragment for a bot schema name."""
    return re.sub(r"[^a-zA-Z0-9]", "", name or "").lower()


def _pascal(name: str) -> str:
    """PascalCase alphanumeric fragment for a connected-action schema name."""
    parts = re.split(r"[^a-zA-Z0-9]+", name or "")
    return "".join(p[:1].upper() + p[1:] for p in parts if p)


def _xml_escape(text: str) -> str:
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# C0 controls other than \t \n \r are outside the XML 1.0 Char production, and
# YAML rejects them even inside quoted scalars — a single such byte in any part
# makes the whole solution zip unimportable. Spec strings are LLM/transcript/
# PDF-derived, where \x0c (page break) and friends genuinely occur.
_XML_INVALID_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _ctrl_clean(text: str) -> str:
    """Scrub XML/YAML-invalid control characters: \x0b/\x0c arrive as page/line
    whitespace in pasted text, so they become a space; the rest are dropped."""
    return _XML_INVALID_CTRL.sub(
        lambda m: " " if m.group() in "\x0b\x0c" else "", text)


def _ctrl_clean_tree(value):
    """_ctrl_clean every string in a nested structure (CapIR dicts, params,
    records), leaving non-strings untouched."""
    if isinstance(value, str):
        return _ctrl_clean(value)
    if isinstance(value, dict):
        return {_ctrl_clean_tree(k): _ctrl_clean_tree(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_ctrl_clean_tree(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_ctrl_clean_tree(v) for v in value)
    return value


def _indent(text: str, spaces: int = 2) -> str:
    pad = " " * spaces
    return "\n".join(f"{pad}{line}" for line in (text or "").split("\n"))


def _yaml_display_safe(text: str) -> str:
    """A display-name YAML scalar: whitespace collapsed to one line, then
    double-quoted (via _yaml_dq) so YAML syntax in the name — a ' #' comment,
    a leading '[', a colon — can neither truncate the value nor break the
    document. Bare emission silently turned 'Scenario #2 Handler' into
    'Scenario' at parse time."""
    return _yaml_dq(re.sub(r"\s+", " ", (text or "")).strip())


# ============================================================================
# CapIR -> deterministic capability topic (the 1:1 conversion)
#
# A converted agent.py compiles its perform() to a CapIR (t2p-capir/1.0). When a
# sub-agent carries that CapIR, the packager emits a REAL Copilot Studio topic
# that runs the SAME steps perform() runs: OnRecognizedIntent (the agent's real
# triggers) -> Question (the user's real input) -> SetVariable Table() of the
# SEEDED records -> Filter by the real query -> branch -> SendActivity, plus a
# document render for artifact-producing capabilities. The control flow is real;
# only the DATA is mocked. Flipping the in-topic Table() to a Dataverse /
# SharePoint connector (binding.connector) is the one-line move to live data, and
# the same filter/respond/document logic runs unchanged. This is the opposite of
# an actions:[]+modelDescription "gamed" topic.
# ============================================================================

def _yaml_dq(text) -> str:
    """A YAML double-quoted scalar: robust for Power Fx expressions and message
    text (escapes backslash/quote, encodes newlines)."""
    s = (str(text).replace("\\", "\\\\").replace('"', '\\"')
         .replace("\n", "\\n").replace("\t", "\\t").replace("\r", ""))
    return '"' + s + '"'


def _pfx_str(value) -> str:
    """A Power Fx double-quoted string literal (internal quotes doubled)."""
    return '"' + str(value).replace('"', '""') + '"'


def _starter_title(text, limit: int = 38) -> str:
    """A conversation-starter title clipped to <= ``limit`` chars on a WORD
    boundary — never mid-word (which shipped clips like "Restock Request Cr" and
    "Shift Handoff Brie"). Whitespace is collapsed first so the boundary is
    clean; if the very first word alone already exceeds the budget it is
    hard-clipped (the only case where a whole word cannot fit)."""
    s = " ".join(str(text).split())
    if len(s) <= limit:
        return s
    cut = s[:limit]
    sp = cut.rfind(" ")
    return cut[:sp].rstrip() if sp > 0 else cut


def _pfx_safe_text(text) -> str:
    """Strip literal braces from message text so Copilot Studio does not parse
    them as variable bindings (unparseable {...} fails publish). Template tokens
    like {Topic.X} are added AFTER this, so they survive."""
    return str(text).replace("{", "(").replace("}", ")")


def _capir_topic_fields(records):
    """Stable union of record field names (the Table()/filter columns) when the
    binding omits an explicit field list (recovered / recompiled CapIRs)."""
    fields = []
    for r in records or []:
        if isinstance(r, dict):
            for k in r.keys():
                if k not in fields:
                    fields.append(k)
    return fields


_MONEY_SYMBOLS = "$€£¥₹"
_MONEY_CODES = ("USD", "EUR", "GBP", "JPY", "INR")
_MONEY_CODE_RE = re.compile(
    r"^(?:%s)\s+|\s+(?:%s)$" % ("|".join(_MONEY_CODES), "|".join(_MONEY_CODES)), re.I)


def _money_float(value, allow_code=True):
    """Parse a possibly money-formatted value to a float, or None.

    LLM-distilled business records carry money-formatted numeric strings —
    "$12,340", "USD 9,500", "9,500" — that plain float() rejects, so a threshold
    capability ("flag runs over $12,000") would otherwise ship without its numeric
    input and WHERE comparison. This strips currency symbols ($ € £ ¥ ₹), thousands
    commas, and spaces; with allow_code=True (the default) it also strips a leading
    or trailing whitespace-separated 3-letter currency code (USD/EUR/GBP/JPY/INR,
    case-insensitive). Plain numbers pass straight through. Out of scope:
    "9.500,00"-style European decimals.

    allow_code=False strips ONLY the symbol/comma/space set — exactly what the
    generated flow's runtime WDL replace()-chain can do (it cannot strip alphabetic
    codes). _numeric_metric_field uses it as the runtime-safety gate: a code-
    prefixed value is parseable by the broad form yet is NOT chosen as the runtime
    metric, keeping the flow's float() guaranteed-safe (the SIMPLEST SAFE RULE)."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None
    s = value.strip()
    if allow_code:
        s = _MONEY_CODE_RE.sub("", s)
    for ch in _MONEY_SYMBOLS:
        s = s.replace(ch, "")
    s = s.replace(",", "").replace(" ", "")
    if not s:
        return None
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def _numeric_metric_field(records, fields, hint=None):
    """Pick the field numeric-threshold queries compare against (e.g. "assets
    above a 30% failure probability" -> a real `Value(field) >= 0.30`). A field
    qualifies only if it parses as a number in EVERY record (so Power Fx Value()
    never errors). Values may be money-formatted ("$12,340", "9,500") — see
    _money_float — but a field is chosen as the metric only when every value is
    also convertible by the flow's runtime WDL (which strips currency symbols,
    commas, and spaces, but NOT 3-letter currency codes: the SIMPLEST SAFE RULE,
    so runtime float() never sees something it cannot parse). Prefers probability/
    score-like names and 0..1-ranged fields; honors an explicit binding
    `metric_field` hint WHEN it too passes this same validation."""
    if not records:
        return None
    numeric, ratio = [], []
    for f in fields:
        vals, ok = [], True
        for r in records:
            if not isinstance(r, dict) or f not in r:
                ok = False; break
            raw = r.get(f)
            mv = _money_float(raw)                       # money-aware numeric parse
            # ...only usable when the flow's WDL can convert it too (allow_code=
            # False mirrors the runtime replace-chain: symbols/commas/spaces, not
            # 3-letter codes) -> a code-prefixed value disqualifies the field.
            if mv is None or _money_float(raw, allow_code=False) is None:
                ok = False; break
            vals.append(mv)
        if ok and vals:
            numeric.append(f)
            if all(0.0 <= v <= 1.0 for v in vals):
                ratio.append(f)
    # honor an explicit hint ONLY if it passes the same every-record-parses-as-
    # float validation as auto-detection; otherwise ignore it and fall through
    # (a hint naming a non-numeric column would ship float('open') into WDL).
    if hint and hint in numeric:
        return hint
    pool = ratio or numeric
    if not pool:
        return None
    for pat in (r"p_?fail|prob|likeli|risk", r"score|rate|ratio|pct|percent|conf"):
        for f in pool:
            if re.search(pat, f, re.I):
                return f
    return pool[0]


# Numeric-threshold intent: a capability whose text PROMISES a cutoff ("flag runs
# over $12,000", "escalate scores above 30%") needs a numeric column to compare
# against. When the ONLY records are SYNTHESIZED stand-ins (no real data invented a
# numeric field), the generic id/label/status shape carries nothing numeric, so
# _numeric_metric_field finds no metric and the flow silently ships WITHOUT its
# number-typed input and WITHOUT the WHERE threshold comparison — the promised
# thresholding vanishes. _synthesize_records uses these to add an "amount" column
# in exactly that case (real records are never touched — see _resolve_capir).
_THRESHOLD_INTENT_RE = re.compile(
    r"(?:over|above|exceed(?:s|ing)?|at or above|more than|greater than|threshold)"
    r"\s*\$?\s*([\d][\d,]*(?:\.\d+)?)", re.I)


def _threshold_cutoff(*texts):
    """If any capability text (description / response / triggers) expresses a
    numeric-threshold intent, return the mentioned cutoff as a float; else None.
    Drives synthetic-record fabrication so a threshold-promising capability's
    stand-in data always carries a numeric metric field (see _synthesize_records)."""
    for t in texts:
        chunks = t if isinstance(t, (list, tuple)) else [t]
        for chunk in chunks:
            m = _THRESHOLD_INTENT_RE.search(str(chunk or ""))
            if m:
                return _money_float(m.group(1))
    return None


# A fixed, deterministic (NO RNG) multiplier set that straddles the cutoff, so the
# synthesized amounts include values both below and above it — a threshold that
# excludes nothing (or everything) would be meaningless. e.g. cutoff 12000 ->
# 8400.0, 11950.0, 12750.0, 15200.0, 10200.0, ... (always FLOATS).
_AMOUNT_MULTIPLIERS = (0.70, 0.9958333, 1.0625, 1.2666667, 0.85, 1.15, 0.80, 1.35)


def _amount_spread(cutoff, n):
    """n believable, deterministic FLOAT amounts spread around `cutoff`."""
    c = float(cutoff)
    return [round(c * _AMOUNT_MULTIPLIERS[i % len(_AMOUNT_MULTIPLIERS)], 2)
            for i in range(n)]


# Date-window intent: a capability whose text PROMISES a DATE WINDOW ("anything
# expiring within 30 days", "due in the next two weeks", "overdue invoices")
# must filter its records down to the rows whose date falls INSIDE that window —
# not everything, not nothing. This is the date-typed sibling of the numeric
# threshold above: the SAME detect-here / import-into-T2P / emit-in-the-flow-WHERE
# shape (see _threshold_cutoff). One shared detector, never a second copy: the
# T2P record expander straddles the boundary at generation time, the packaged
# flow's WHERE compares each row's ISO date against addDays(utcNow(), N).
# Overdue is represented as a NEGATIVE window (default magnitude below), so a
# single signed int rides the binding as `date_window_days`.
_OVERDUE_WINDOW_DAYS = 30           # straddle magnitude for a bare "overdue"
_DATE_WINDOW_UNIT_DAYS = {"day": 1, "week": 7, "month": 30}
# small number-words so "the next two weeks" resolves to 14 (digits handled too)
_DATE_WINDOW_NUM_WORDS = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12}
_DATE_WINDOW_NUM = (r"(\d{1,4}|a|an|one|two|three|four|five|six|seven|eight|"
                    r"nine|ten|eleven|twelve)")
# forward window: "expiring within 30 days", "due in the next two weeks",
# "inside 7 days", "under 14 days" — a within/next/inside/under prefix (also the
# "due in"/"in the next" phrasings) then N day|week|months.
_DATE_WINDOW_RE = re.compile(
    r"\b(?:within|next|inside|under|due\s+in|due\s+within|in\s+the\s+next)\s+"
    r"(?:the\s+)?" + _DATE_WINDOW_NUM + r"[\s-]+(day|week|month)s?\b", re.I)
# rule/line phrasing: "30-day window", "14 day rule", "30-day line".
_DATE_WINDOW_NDAY_RE = re.compile(
    r"\b" + _DATE_WINDOW_NUM + r"[\s-]+(day|week|month)s?\b[\s-]*"
    r"(?:window|line|rule)\b", re.I)
# overdue / past-due: the date is already in the past (no forward N needed).
_DATE_OVERDUE_RE = re.compile(r"\b(?:overdue|past[\s-]+due)\b", re.I)
# an ISO yyyy-mm-dd date value (lexicographic == chronological, so string
# comparison in the flow's WDL WHERE is correct).
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _date_window_num(tok):
    """Digits or a small number-word -> int; else None."""
    tok = str(tok).strip().lower()
    if tok.isdigit():
        return int(tok)
    return _DATE_WINDOW_NUM_WORDS.get(tok)


def _date_window_intent(*texts):
    """If any capability text (name/description/response/triggers) expresses a
    DATE-WINDOW intent, return the window as a SIGNED int number of days:

      * a POSITIVE N for a forward window — "anything expiring within 30 days"
        -> 30, "due in the next two weeks" -> 14, "14-day window" -> 14;
      * a NEGATIVE default (-_OVERDUE_WINDOW_DAYS) for an overdue / past-due
        window — "overdue invoices" -> already past (sign encodes direction);

    else None. An explicit forward N is preferred over a bare "overdue" (scanned
    in that order). Mirrors _threshold_cutoff: one shared detector both the T2P
    record expander and the packaged-flow WHERE read, so a date-window capability
    filters a real date-bounded subset instead of everything/nothing. Numeric-
    threshold text ("over $12,000") carries no day/week/month unit and yields
    None — no cross-talk with _threshold_cutoff."""
    chunks = []
    for t in texts:
        chunks.extend(t if isinstance(t, (list, tuple)) else [t])
    for chunk in chunks:
        s = str(chunk or "")
        for rx in (_DATE_WINDOW_RE, _DATE_WINDOW_NDAY_RE):
            m = rx.search(s)
            if m:
                n = _date_window_num(m.group(1))
                if n:
                    return n * _DATE_WINDOW_UNIT_DAYS[m.group(2).lower()]
    for chunk in chunks:
        if _DATE_OVERDUE_RE.search(str(chunk or "")):
            return -_OVERDUE_WINDOW_DAYS
    return None


def _date_metric_field(records, fields, hint=None):
    """Pick the DATE field a date-window query filters on (e.g. an
    "expiring within 30 days" capability -> a real comparison on
    expiration_date). A field qualifies only when every non-empty value is an
    ISO yyyy-mm-dd date, so the flow's WDL can compare it as a string against a
    formatDateTime(addDays(utcNow(), N)) cutoff (lexicographic == chronological).
    Honors an explicit binding `date_field` hint WHEN it too passes this same
    validation; otherwise prefers an expiry/due/date-named field. Mirrors
    _numeric_metric_field (the numeric sibling)."""
    if not records:
        return None
    valid = []
    for f in fields:
        ok, any_val = True, False
        for r in records:
            if not isinstance(r, dict):
                continue
            v = r.get(f)
            if v is None or v == "":
                continue
            any_val = True
            if not (isinstance(v, str) and _ISO_DATE_RE.match(v)):
                ok = False
                break
        if ok and any_val:
            valid.append(f)
    if hint and hint in valid:
        return hint
    if not valid:
        return None
    for pat in (r"expir", r"due", r"(?:^|_)date", r"end|close|renew|ship"):
        for f in valid:
            if re.search(pat, f, re.I):
                return f
    return valid[0]


# The load-bearing perform() constants (t2p-capir/1.0 CAPIR_CONSTS). The topic
# reads these off the CapIR when present so it mirrors the agent.py's numbers.
_CAPIR_TOPIC_CONSTS = {
    "example_take": 2, "fallback_take": 2, "pdf_records": 3,
    "pdf_prepared": "Prepared for {customer}",
    "pdf_footer": "Synthetic demo data - no customer data was needed.",
}


def capir_topic_action_name(capir: dict) -> str:
    """The custom-topic schema suffix for a capability: Handle<Pascal(key)>."""
    key = (capir or {}).get("key") or "capability"
    return "Handle" + (_pascal(key) or "Capability")


def capir_topic_data_yaml(display_name: str, capir: dict) -> str:
    """Render a capability's CapIR into a REAL deterministic Copilot Studio topic
    'data' YAML that goes INSIDE the sub-agent: OnRecognizedIntent triggers ->
    Question (slot) -> SetVariable Table() of the SEEDED records -> Filter by the
    real query -> ConditionGroup on the match count -> SendActivity, plus (for an
    artifact capability) a SetVariable that renders the document from the matched
    (or fallback) records exactly like perform()'s artifact step. The synthetic
    records live IN the topic and the control flow runs deterministically; only
    the DATA is mocked. Structural 1:1 with the generated agent.py's perform()."""
    capir = capir or {}
    consts = dict(_CAPIR_TOPIC_CONSTS)
    consts.update(capir.get("consts") or {})
    binding = capir.get("binding") or {}
    fields = [f for f in (binding.get("fields") or _capir_topic_fields(binding.get("records")))
              if isinstance(f, str) and f.isidentifier()]
    table = binding.get("table") or "records"
    records = binding.get("records") or []
    customer = str(capir.get("customer") or "the customer")
    response = _pfx_safe_text(capir.get("response") or f"Here is how I handle {display_name}.")
    # triggers + grounding facts + the artifact doc come straight from the steps
    triggers, facts, doc = [], [], None
    for step in capir.get("steps") or []:
        op = step.get("op")
        if op == "trigger_match":
            triggers = step.get("queries") or []
        elif op == "knowledge_lookup":
            facts = step.get("facts") or []
        elif op == "artifact":
            doc = step.get("doc")
    prompt = None
    for slot in capir.get("slots") or []:
        prompt = slot.get("prompt"); break
    prompt = prompt or f"What would you like help with for {display_name}?"

    # Power Fx: a real Table() of the seeded records, a real query Filter, a real
    # count, then a real branch -- the exact perform() path.
    recs = []
    for r in records:
        if isinstance(r, dict):
            cells = ", ".join("%s: %s" % (f, _pfx_str(r.get(f, ""))) for f in fields)
            recs.append("{" + cells + "}")
    table_pfx = "=Table(" + ", ".join(recs) + ")" if recs else "=Blank()"
    conds = " || ".join("(Lower(ThisRecord.%s) in Lower(Topic.Query))" % f for f in fields)
    text_clause = "(%s)" % (conds or "false")

    # numeric-threshold support: a query like "assets above a 30% failure
    # probability" sets Topic.Threshold (number, %-aware) + Topic.Direction
    # (ge/le) and the Filter does a REAL Value()-comparison on the metric field,
    # not just text containment. Falls back to text match when no number is asked.
    metric_field = _numeric_metric_field(records, fields, (binding.get("metric_field")))
    threshold_actions, filter_inner = "", text_clause
    if metric_field:
        num_re = r"\d+\.?\d*"
        thr_pfx = ('=If(IsMatch(Topic.Query, "\\d"), '
                   'Value(First(MatchAll(Topic.Query, "' + num_re + '")).FullMatch) '
                   '/ If(IsMatch(Topic.Query, "%"), 100, 1), Blank())')
        dir_pfx = ('=If(IsMatch(Lower(Topic.Query), "above|over|greater|more than|exceed|at least|higher|>"), "ge", '
                   'If(IsMatch(Lower(Topic.Query), "below|under|less|fewer|within|at most|lower|<"), "le", "ge"))')
        threshold_actions = (
            "    - kind: SetVariable\n"
            "      id: setThreshold\n"
            "      variable: Topic.Threshold\n"
            "      value: " + _yaml_dq(thr_pfx) + "\n"
            "    - kind: SetVariable\n"
            "      id: setDirection\n"
            "      variable: Topic.Direction\n"
            "      value: " + _yaml_dq(dir_pfx) + "\n")
        num_clause = ('(!IsBlank(Topic.Threshold) && If(Topic.Direction = "le", '
                      'Value(ThisRecord.' + metric_field + ') <= Topic.Threshold, '
                      'Value(ThisRecord.' + metric_field + ') >= Topic.Threshold))')
        filter_inner = "(" + text_clause + " || " + num_clause + ")"
    filter_pfx = "=Filter(Topic.Records, !IsBlank(Topic.Query) && " + filter_inner + ")"

    grounding = "\n".join("- " + _pfx_safe_text(f) for f in facts)
    ground_block = ("\n\nGrounded in what you told us:\n" + grounding) if grounding else ""

    # artifact (op==artifact): render the document from the matched-or-fallback
    # records, exactly like perform()'s artifact step (hits[:pdf_records] with a
    # data[:fallback_take] fallback). Materializing the real downloadable file is
    # the live-data flip -- a Create-file / Convert-to-PDF flow over these records.
    doc_actions, doc_block = "", ""
    if doc and fields:
        cells_pfx = ' & " | " & '.join('"%s: " & Text(ThisRecord.%s)' % (f, f) for f in fields)
        source = ("If(Topic.MatchCount > 0, Topic.Matches, FirstN(Topic.Records, %d))"
                  % consts["fallback_take"])
        document_pfx = ("=Concat(FirstN(%s, %d), %s & Char(10))"
                        % (source, consts["pdf_records"], cells_pfx))
        doc_actions = (
            "    - kind: SetVariable\n"
            "      id: setDocument\n"
            "      variable: Topic.Document\n"
            "      value: " + _yaml_dq(document_pfx) + "\n")
        prepared = _pfx_safe_text(consts["pdf_prepared"].replace("{customer}", customer))
        footer = _pfx_safe_text(consts["pdf_footer"])
        safe_doc = _pfx_safe_text(str(doc))
        doc_block = ("\n\n[" + safe_doc + "] " + prepared + ":\n"
                     + "{Topic.Document}\n" + footer
                     + "\n(In production, a Create-file / Convert-to-PDF flow over these "
                       "records delivers the real " + safe_doc + ".)")

    hit_msg = (response + ground_block
               + "\n\nI found {Topic.MatchCount} matching record(s) in the "
               + table + " data (synthetic demo data - no customer data needed)."
               + doc_block)
    miss_msg = (response + ground_block
                + "\n\nNo matching record in the " + table
                + " data; here are reference examples to ground the answer."
                + doc_block)
    trig = "\n".join("      - " + _yaml_dq(t) for t in triggers) or ("      - " + _yaml_dq(display_name))

    # intake: ask for the value to filter on. We intentionally do NOT read an
    # orchestrator-passed `Global.<param>` here. A connected agent can only
    # reference a global it has DECLARED as external-settable, and the solution
    # package format gives no reliable way to emit that declaration — referencing
    # an undeclared Global makes Copilot Studio's topic checker throw a
    # PowerFxError ("Identifier not recognized"), which blocks publish. The
    # orchestrator still DECLARES + PASSES the typed inputs (see the connected
    # action's inputType); the agent's generative layer receives them, and this
    # deterministic topic captures the value it filters on via the Question.
    intake_actions = (
        "    - kind: Question\n"
        "      id: question_query\n"
        "      variable: Topic.Query\n"
        "      prompt: " + _yaml_dq(prompt) + "\n"
        "      entity: StringPrebuiltEntity\n")

    return (
        "kind: AdaptiveDialog\n"
        "beginDialog:\n"
        "  kind: OnRecognizedIntent\n"
        "  id: main\n"
        "  intent:\n"
        "    displayName: " + _yaml_dq(display_name) + "\n"
        "    includeInOnSelectIntent: false\n"
        "    triggerQueries:\n" + trig + "\n"
        "  actions:\n"
        + intake_actions +
        "    - kind: SetVariable\n"
        "      id: setRecords\n"
        "      variable: Topic.Records\n"
        "      value: " + _yaml_dq(table_pfx) + "\n"
        + threshold_actions +
        "    - kind: SetVariable\n"
        "      id: setMatches\n"
        "      variable: Topic.Matches\n"
        "      value: " + _yaml_dq(filter_pfx) + "\n"
        "    - kind: SetVariable\n"
        "      id: setCount\n"
        "      variable: Topic.MatchCount\n"
        "      value: " + _yaml_dq("=CountRows(Topic.Matches)") + "\n"
        + doc_actions +
        "    - kind: ConditionGroup\n"
        "      id: hasMatches\n"
        "      conditions:\n"
        "        - id: hasMatches_hit\n"
        "          condition: " + _yaml_dq("=Topic.MatchCount > 0") + "\n"
        "          actions:\n"
        "            - kind: SendActivity\n"
        "              id: replyHit\n"
        "              activity: " + _yaml_dq(hit_msg) + "\n"
        "      elseActions:\n"
        "        - kind: SendActivity\n"
        "          id: replyMiss\n"
        "          activity: " + _yaml_dq(miss_msg) + "\n"
    )


# ============================================================================
# CapIR -> deterministic AGENT FLOW (topics -> workflows, the 1:1 conversion)
#
# Copilot Studio is retiring classic per-capability topics in favor of flows
# ("workflows" in the Copilot Studio UI). Each sub-agent's CapIR therefore
# compiles to a REAL solution-packaged Power Automate flow — the Copilot
# Studio-COMPATIBLE kind (Category 5 modern flow whose trigger is
# "When an agent calls the flow", Request kind: Skills — NOT an HTTP/scheduled
# flow, which an agent cannot call) — that runs the SAME steps perform() runs:
#
#   "When an agent calls the flow"      (Request trigger, kind: Skills)
#       text   : user_query — the value to filter on (was the topic's Question)
#       number : threshold  — optional, when the records carry a numeric metric
#   -> Get_records_STATIC_DATA          (Compose: the SEEDED synthetic records)
#   -> Filter_matching_records          (Query over the records, the real filter)
#   -> Select_result                    (matches, else perform()'s fallback examples)
#   -> "Respond to the agent"           (Response, kind: Skills)
#       message / matches_json / match_count [/ document_text]
#
# The control flow is real; only the DATA is mocked. Going live is a 1:1 swap:
# replace the single Get_records_STATIC_DATA Compose with the real connector
# action (Dataverse "List rows", SQL, an IoT/SCADA API, ...) returning the same
# array shape — every downstream step reads outputs('Get_records_STATIC_DATA'),
# so the filter/respond logic runs unchanged. connectionReferences stays {}
# until then, so the solution imports with NO connection dependency, and the
# flow ships activated (StateCode 1) so it runs immediately after import.
# ============================================================================

_FLOW_SCHEMA_VERSION = "1.0.0.0"
_FLOW_STATIC_DATA_ACTION = "Get_records_STATIC_DATA"
_FLOW_LIVE_DATA_ACTION = "Get_records_LIVE"
_FLOW_LIVE_WRITE_ACTION = "Create_record_LIVE"
_WORKFLOW_ROOT_COMPONENT = '      <RootComponent type="29" id="{{{workflow_id}}}" behavior="0" />'

# One <Workflow> element per deterministic capability flow (customizations.xml),
# field-for-field the shape Dataverse exports for a Copilot-callable cloud flow.
WORKFLOW_ELEMENT_XML = """\
    <Workflow WorkflowId="{{{workflow_id}}}" Name="{name}" Description="{description}">
      <JsonFileName>/Workflows/{json_file_name}</JsonFileName>
      <Type>1</Type>
      <Subprocess>0</Subprocess>
      <Category>5</Category>
      <Mode>0</Mode>
      <Scope>4</Scope>
      <OnDemand>0</OnDemand>
      <TriggerOnCreate>0</TriggerOnCreate>
      <TriggerOnDelete>0</TriggerOnDelete>
      <AsyncAutodelete>0</AsyncAutodelete>
      <SyncWorkflowLogOnFailure>0</SyncWorkflowLogOnFailure>
      <StateCode>{state_code}</StateCode>
      <StatusCode>{status_code}</StatusCode>
      <RunAs>1</RunAs>
      <IsTransacted>1</IsTransacted>
      <IntroducedVersion>{version}</IntroducedVersion>
      <IsCustomizable>1</IsCustomizable>
      <BusinessProcessType>0</BusinessProcessType>
      <IsCustomProcessingStepAllowedForOtherPublishers>1</IsCustomProcessingStepAllowedForOtherPublishers>
      <ModernFlowType>{modern_flow_type}</ModernFlowType>
      <PrimaryEntity>none</PrimaryEntity>
      <LocalizedNames>
        <LocalizedName languagecode="1033" description="{name}" />
      </LocalizedNames>
      <Descriptions>
        <Description languagecode="1033" description="{description}" />
      </Descriptions>
    </Workflow>"""


def _la_str(s) -> str:
    """A Logic Apps expression string literal (single quotes doubled)."""
    return "'" + str(s).replace("'", "''") + "'"


def _wdl_literal(s) -> str:
    """A literal string VALUE placed in a workflow definition (action inputs /
    trigger schema). WDL parses any string starting with '@' as an expression
    and '@{...}' anywhere as interpolation, so escape both ('@@' / '@@{')."""
    s = str(s).replace("@{", "@@{")
    if s.startswith("@") and not s.startswith("@@"):
        s = "@" + s
    return s


def _wdl_record_value(v):
    """Map one static-demo record value for the flow's Compose. String values
    still get WDL @/@{ escaping (an expression-injection concern that only
    applies to strings); JSON-native scalars (bool/int/float/None) pass through
    unchanged so the emitted flow json carries true/null/0.7 -- never the Python
    spellings "True"/"None" or a stringified "0.7"; nested dict/list values are
    embedded json-faithfully, recursing so inner strings keep their @ escaping."""
    if isinstance(v, str):
        return _wdl_literal(v)
    if v is None or isinstance(v, bool) or isinstance(v, (int, float)):
        return v
    if isinstance(v, dict):
        return {str(k): _wdl_record_value(vv) for k, vv in v.items()}
    if isinstance(v, list):
        return [_wdl_record_value(vv) for vv in v]
    return _wdl_literal(v)


def _la_field(f) -> str:
    """item()?['<field>'] accessor, null-safe: heterogeneous records may omit a
    field, and WDL string(null)/toLower(null) throw, so coalesce to ''."""
    return "coalesce(item()?[" + _la_str(f) + "], '')"


def _wdl_strip_money(expr: str) -> str:
    """Wrap a WDL field expression in a replace() chain that strips currency
    symbols, thousands commas, and spaces so float() gets a plain number (WDL has
    no regex, so one nested replace() per character). Runtime forms handled:
    "$12,340" / "9,500" / "12 340" — NOT a 3-letter currency code ("USD 9,500"),
    which _numeric_metric_field's runtime-safety gate already keeps out of here."""
    for ch in list(_MONEY_SYMBOLS) + [",", " "]:
        expr = "replace(" + expr + ", '" + ch + "', '')"
    return expr


# ============================================================================
# Live-connector catalog: the 1st-party (OOTB) connectors the LIVE twin can wire
# a capability's data step to. operationId / parameters / result_path are the
# real connector contracts (Dataverse ListRecords verified against a genuine
# Power Platform export). REPLACE_ parameter values are deliberate placeholders
# the maker sets after binding the connection — the flow imports fine with them.
# ============================================================================
LIVE_CONNECTOR_CATALOG = {
    "dataverse": {
        "api": "shared_commondataserviceforapps",
        "display": "Microsoft Dataverse",
        "operation": "ListRecords",
        "operation_label": "List rows",
        # "accounts" (the standard table's plural entity-set name) exists in
        # every Dataverse org, and the same-environment Dataverse connector
        # activates WITHOUT a pre-bound connection — so this flow imports,
        # activates, and runs real data out of the box (live-verified); the
        # maker repoints entityName at their table when ready.
        "parameters": {"entityName": "accounts", "$top": 100},
        "result_path": ["body", "value"],
        "impersonation": True,
        "setup_hint": ("ships RUNNABLE against the standard 'accounts' table - "
                       "change entityName to your table's plural entity-set name"),
    },
    "sharepoint": {
        "api": "shared_sharepointonline",
        "display": "SharePoint",
        "operation": "GetItems",
        "operation_label": "Get items",
        "parameters": {"dataset": "https://REPLACE.sharepoint.com/sites/REPLACE",
                       "table": "REPLACE_WITH_list_name"},
        "result_path": ["body", "value"],
    },
    "salesforce": {
        "api": "shared_salesforce",
        "display": "Salesforce",
        "operation": "GetItems",
        "operation_label": "Get records",
        "parameters": {"table": "REPLACE_WITH_object_api_name"},
        "result_path": ["body", "value"],
    },
    "sql": {
        "api": "shared_sql",
        "display": "SQL Server",
        "operation": "GetItems",
        "operation_label": "Get rows",
        "parameters": {"table": "REPLACE_WITH_table_name"},
        "result_path": ["body", "value"],
    },
    "servicenow": {
        "api": "shared_service-now",
        "display": "ServiceNow",
        "operation": "GetRecords",
        "operation_label": "List records",
        "parameters": {"tableType": "REPLACE_WITH_table_name"},
        "result_path": ["body", "result"],
    },
    "vivaengage": {
        # Viva Engage (Yammer) 1st-party connector — the SAME action the original
        # VivaEngageQueryAgent Copilot Studio solution used. Reads real group posts;
        # needs a Viva Engage connection (OAuth) bound to the flow's connection ref.
        "api": "shared_yammer",
        "display": "Viva Engage",
        "operation": "GetMessagesInGroupV3",
        "operation_label": "Get messages in a group (V3)",
        "parameters": {"group_id": 256680165376},
        "result_path": ["body", "messages"],
        "setup_hint": ("reads real Viva Engage group messages via GetMessagesInGroupV3 - "
                       "bind a Viva Engage connection and set group_id to your group"),
    },
}

# First-party Work IQ MCP servers, attachable as TOOLS on a bot (the modern
# "skills" surface, shapes verbatim from a live cliagent template): dialog
# kind McpTool, authMode Invoker (runs as the signed-in user, SSO-backed), a
# bot-scoped connection reference. Attached on the LIVE twin when an agent's
# source clearly does that kind of work (mail/people/M365 content).
MCP_TOOL_CATALOG = (
    {"key": "WorkIQMail", "display": "Work IQ Mail (Preview)",
     "api": "shared_a365outlookmailmcp", "operation": "mcp_MailTools",
     "keywords": ("email", "e-mail", " mail", "notif", "outreach",
                  "correspond", "escalate to", "alert the")},
    {"key": "WorkIQUser", "display": "Work IQ User (Preview)",
     "api": "shared_a365memcp", "operation": "mcp_MeServer",
     "keywords": ("employee", "hr case", "hr special", "people lookup",
                  "person lookup", "profile", "org chart", "manager of")},
    {"key": "WorkIQCopilot", "display": "Work IQ Copilot (Preview)",
     "api": "shared_a365copilotchatmcp", "operation": "mcp_m365copilot",
     "keywords": ("microsoft 365", "m365", "teams message", "meeting notes",
                  "sharepoint search", "onedrive")},
)

MCP_TOOL_DATA_YAML = """\
kind: McpTool
authMode: Invoker
connectionReference: {conn_ref_logical}
connectorId: /providers/Microsoft.PowerApps/apis/{api}
operationId: {operation}"""


def match_mcp_tools(text: str) -> list:
    """The Work IQ MCP tools whose keywords appear in an agent's own
    description/name — evidence-based, no per-use-case rules."""
    low = " " + (text or "").lower()
    return [t for t in MCP_TOOL_CATALOG if any(k in low for k in t["keywords"])]


# keyword -> catalog key, scanned over the capability's system/table hints.
# Each entry's keywords are TWO-TIER: most NAME a specific product/technology,
# but a few are GENERIC storage words ('database', 'warehouse') that could
# describe ANY system. _GENERIC_KEYWORDS flags those per connector so the
# explicit-binding scan prefers a NAMED product and only falls back to a generic
# word when no product is named (see pick_live_connector step 1). Any new entry
# that adds a generic keyword must list it here too, so future entries stay honest.
_CONNECTOR_KEYWORDS = (
    ("dataverse", ("dataverse", "dynamics", "d365", "power apps", "powerapps", "crm")),
    ("sharepoint", ("sharepoint", "spo", "site list", "document library")),
    ("salesforce", ("salesforce", "sfdc")),
    ("sql", ("sql", "database", "warehouse", "synapse", "azure db")),
    ("servicenow", ("servicenow", "service now", "snow ticket")),
    ("vivaengage", ("viva engage", "vivaengage", "yammer", "viva ")),
)
_GENERIC_KEYWORDS = {  # tier-2: generic storage words per connector (subset of the
    "sql": ("database", "warehouse"),  # entry's keywords above), never product-naming
}

_STATIC_API_HOST = "raw.githubusercontent.com"
_STATIC_API_COMMIT = "6d025c4bf55c396cf41328e65800b64c68cc9e06"
_STATIC_API_BASE_PATH = (
    "/kody-w/rapp-static-apis/" + _STATIC_API_COMMIT + "/industry-templates"
)
_STATIC_HTTP_BASE = (
    "https://cdn.jsdelivr.net/gh/kody-w/rapp-static-apis@"
    + _STATIC_API_COMMIT + "/industry-templates"
)
_STATIC_CATALOG_PATH = (
    Path(__file__).resolve().parents[1]
    / "hardening" / "aibast_library" / "static_api_catalog.json"
)
_STATIC_CATALOG_CACHE: Optional[dict] = None


def normalize_static_transport(static_connectors: bool, value: Any = None) -> Optional[str]:
    """Validate the static runtime transport at every public entry point."""
    raw = str(value or "").strip().casefold()
    if not static_connectors:
        if raw:
            raise ValueError("static_transport is valid only when static_connectors=true")
        return None
    if not raw:
        return "http"
    if raw not in ("http", "connector"):
        raise ValueError("static_transport must be 'http' or 'connector'")
    return raw


def _static_endpoint_url(live: dict) -> str:
    path = str(live.get("endpoint_path") or "").lstrip("/")
    if path.startswith("industry-templates/"):
        path = path[len("industry-templates/"):]
    if live.get("static_transport") == "http":
        return str(live.get("static_http_base") or _STATIC_HTTP_BASE).rstrip(
            "/") + "/" + path
    return "https://%s%s/%s" % (
        live.get("static_host"),
        str(live.get("static_base_path") or "").rstrip("/"),
        path,
    )


def _static_http(live: Optional[dict]) -> bool:
    return bool(
        live
        and live.get("kind") == "static"
        and live.get("static_transport") == "http"
    )


def _static_norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").casefold())


def _load_static_api_catalog() -> dict:
    global _STATIC_CATALOG_CACHE
    if _STATIC_CATALOG_CACHE is None:
        with _STATIC_CATALOG_PATH.open(encoding="utf-8") as fh:
            _STATIC_CATALOG_CACHE = json.load(fh)
    return _STATIC_CATALOG_CACHE


def _static_product(catalog: dict, adapter_id: str) -> Optional[dict]:
    return next(
        (item for item in catalog.get("products") or [] if item.get("id") == adapter_id),
        None,
    )


def _static_resource_score(resource: dict, schema: dict, hints: str, fields: set) -> int:
    resource_id = _static_norm(resource.get("id"))
    schema_fields = {
        _static_norm(item.get("name"))
        for item in (schema.get("fields") or [])
        if isinstance(item, dict)
    }
    score = 8 * len(fields & schema_fields)
    if resource_id and resource_id in hints:
        score += 12
    for token in re.findall(r"[a-z0-9]+", str(resource.get("id") or "").casefold()):
        if len(token) > 2 and token in hints:
            score += 3
    return score


def resolve_static_connector(
    capir: dict,
    capability_name: str = "",
    description: str = "",
    catalog_agent_id: str = "",
) -> tuple:
    """Resolve a capability to a public adapter without switching products."""
    catalog = _load_static_api_catalog()
    binding = (capir or {}).get("binding") or {}
    cap_hint = _static_norm(
        capability_name or (capir or {}).get("key") or (capir or {}).get("name")
    )
    agent = next(
        (item for item in catalog.get("agents") or []
         if str(item.get("agent_id") or "").casefold()
         == str(catalog_agent_id or "").strip().casefold()),
        None,
    )
    selected_route = None
    route_score = 0.0
    if agent and cap_hint:
        for route in agent.get("capability_routes") or []:
            route_hint = _static_norm(route.get("capability"))
            if not route_hint:
                continue
            score = (
                1.0
                if route_hint == cap_hint
                else SequenceMatcher(None, cap_hint, route_hint).ratio()
            )
            if cap_hint in route_hint or route_hint in cap_hint:
                score = max(score, 0.86)
            if score > route_score:
                selected_route, route_score = route, score
        if route_score < 0.58:
            selected_route = None

    resolution = "catalog_agent_route" if selected_route else "alias_resource_score"
    catalog_write_intent = (
        bool(selected_route.get("write_intent")) if selected_route else None
    )
    if selected_route:
        adapter_ids = [selected_route.get("adapter_id")]
        resource_id = selected_route.get("resource_id")
        endpoints = dict(selected_route.get("endpoints") or {})
        resolved_cap_code = _static_norm(
            selected_route.get("capability") or "template-default"
        )
    else:
        system = str(
            binding.get("system")
            or binding.get("source_system")
            or binding.get("connector")
            or ""
        ).strip()
        binding_write = bool(binding.get("write")) or str(
            binding.get("operation") or "").lower() in (
                "create", "add", "store", "write", "insert", "upsert", "save"
            )
        alias_index = catalog.get("alias_index") or {}
        adapter_ids = list(alias_index.get(_static_norm(system)) or [])
        if not system:
            alias_hints = _static_norm(
                " ".join([
                    capability_name,
                    description,
                    str(binding.get("table") or ""),
                ])
            )
            matches = [
                (len(alias), alias, product_ids)
                for alias, product_ids in alias_index.items()
                if len(alias) >= 4 and alias in alias_hints
            ]
            if matches:
                longest = max(item[0] for item in matches)
                adapter_ids = list(dict.fromkeys(
                    product_id
                    for length, _alias, product_ids in matches
                    if length == longest
                    for product_id in product_ids
                ))
        if not adapter_ids:
            return None, (
                "Static connector unresolved for capability '%s': product alias '%s' "
                "is not in static_api_catalog.json; retained existing live connector behavior."
                % (capability_name or (capir or {}).get("key") or "unknown",
                   system or "(none)")
            )
        hints = " ".join(
            str(value or "").casefold()
            for value in (
                capability_name,
                description,
                binding.get("table"),
                binding.get("resource"),
                binding.get("fields"),
            )
        )
        cap_fields = {_static_norm(item) for item in binding.get("fields") or []}
        choices = []
        for adapter_id in adapter_ids:
            product = _static_product(catalog, adapter_id)
            if not product:
                continue
            for resource in product.get("resources") or []:
                schema_id = str(resource.get("item_schema_ref") or "").rsplit("/", 1)[-1]
                schema = (catalog.get("resource_schemas") or {}).get(schema_id) or {}
                choices.append(
                    (_static_resource_score(resource, schema, hints, cap_fields),
                     adapter_id, resource)
                )
        if not choices:
            return None, (
                "Static connector unresolved for capability '%s': catalog product '%s' "
                "has no usable resources; retained existing live connector behavior."
                % (capability_name or "unknown", ", ".join(adapter_ids))
            )
        _score, adapter_id, resource = max(choices, key=lambda item: item[0])
        adapter_ids = [adapter_id]
        resource_id = resource.get("id")
        receipt = {}
        resolved_cap_code = cap_hint or "template-default"
        if binding_write:
            receipt_candidates = []
            for catalog_agent in catalog.get("agents") or []:
                for route in catalog_agent.get("capability_routes") or []:
                    candidate = (
                        (route.get("endpoints") or {}).get("write_simulation") or {}
                    )
                    if (
                        route.get("adapter_id") != adapter_id
                        or route.get("resource_id") != resource_id
                        or not candidate.get("path")
                    ):
                        continue
                    route_cap = _static_norm(route.get("capability"))
                    score = (
                        1.0 if route_cap == cap_hint
                        else SequenceMatcher(None, cap_hint, route_cap).ratio()
                    )
                    receipt_candidates.append((score, route_cap, candidate))
            if not receipt_candidates:
                return None, (
                    "Static connector unresolved for write capability '%s': adapter/resource "
                    "'%s/%s' has no matching deterministic receipt endpoint; retained "
                    "existing live connector behavior."
                    % (capability_name or "unknown", adapter_id, resource_id)
                )
            _receipt_score, resolved_cap_code, receipt = max(
                receipt_candidates, key=lambda item: (item[0], item[1])
            )
        endpoints = {
            "collection": {"method": "GET", "path": resource.get("collection_path")},
            "record": {
                "method": "GET",
                "path_template": resource.get("record_path_template"),
            },
            "write_simulation": {
                **receipt,
                "method": "GET",
            } if receipt else {},
        }

    adapter_id = adapter_ids[0]
    product = _static_product(catalog, adapter_id)
    if not product:
        return None, (
            "Static connector unresolved for capability '%s': adapter '%s' is absent; "
            "retained existing live connector behavior."
            % (capability_name or "unknown", adapter_id)
        )
    resource = next(
        (item for item in product.get("resources") or []
         if item.get("id") == resource_id),
        None,
    )
    if not resource:
        return None, (
            "Static connector unresolved for capability '%s': resource '%s/%s' is absent; "
            "retained existing live connector behavior."
            % (capability_name or "unknown", adapter_id, resource_id)
        )
    schema_id = str(resource.get("item_schema_ref") or "").rsplit("/", 1)[-1]
    item_schema = dict((catalog.get("resource_schemas") or {}).get(schema_id) or {})
    cap_code = resolved_cap_code
    return {
        "kind": "static",
        "key": "static",
        "system": product.get("display_name") or adapter_id,
        "display": "RAPP Static " + str(product.get("display_name") or adapter_id),
        "adapter_id": adapter_id,
        "resource_id": resource_id,
        "capability_code": cap_code,
        "catalog_agent_id": catalog_agent_id or None,
        "resolution": resolution,
        "route_match_score": round(route_score, 3) if selected_route else None,
        "catalog_write_intent": catalog_write_intent,
        "endpoints": endpoints,
        "item_schema": item_schema,
        "static_host": _STATIC_API_HOST,
        "static_base_path": _STATIC_API_BASE_PATH,
        "static_http_base": _STATIC_HTTP_BASE,
        "public_commit": _STATIC_API_COMMIT,
        "connection_binding_required": True,
        "connectionless_http_fallback": True,
        "migration": (
            "Replace the static endpoint/custom connector binding with the real "
            "product API while preserving this resource field schema."
        ),
    }, None


def _encode_connector_name(schema_name: str) -> str:
    """Power Platform's connector-name encoding ('_' -> '-5f', ' ' -> '-20'),
    per the import-verified custom-connector export shape."""
    return str(schema_name).replace("_", "-5f").replace(" ", "-20")


# Custom-connector NAMES are minted from the distilled source_system, which is
# arbitrary maker/LLM/transcript text ("SAP Analytics Cloud (SAC)", "Épic+Willow
# 2.0!", ...). Power Platform's LIVE-twin import REJECTS any connector name that
# is not alphanumeric/'-'/'_' starting alphanumeric ("Connector name must be
# alphanumeric, '-', or '_' and start with alphanumeric") — the parentheses in
# "(SAC)" made a real import fail at 27%. Every minted NAME goes through this ONE
# sanitizer so it ALWAYS matches ^[A-Za-z0-9][A-Za-z0-9_-]*$. DISPLAY names (what
# makers see) are NEVER passed through here — they keep the pretty original.
_CONNECTOR_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


def _sanitize_connector_name(raw: str, fallback: str = "connector", maxlen: int = 64) -> str:
    """Force ANY string into a platform-legal custom-connector NAME
    (^[A-Za-z0-9][A-Za-z0-9_-]*$). Keeps [A-Za-z0-9_-]; every run of other chars
    (spaces, punctuation, parentheses, non-ASCII) collapses to a single '_' —
    the separator this codebase already uses in schema/logical names; leading
    non-alphanumerics are stripped so the name starts alphanumeric; repeated
    separators collapse; trailing separators are trimmed; lowercased to match the
    existing prefix_bodyapi convention; empty -> `fallback`; capped at `maxlen`
    (no connector-name limit is documented, so a conservative 64 — well under the
    100-char schema cap the schemaName it feeds must also respect)."""
    s = re.sub(r"[^A-Za-z0-9_-]+", "_", str(raw or ""))   # illegal runs -> one '_'
    s = re.sub(r"[_-]{2,}", "_", s)                        # collapse repeat separators
    s = re.sub(r"^[^A-Za-z0-9]+", "", s)                   # must START alphanumeric
    s = re.sub(r"[_-]+$", "", s)                           # ...and not end on a separator
    s = s.lower()[:maxlen]
    s = re.sub(r"[_-]+$", "", s)                           # re-trim if the cap split a run
    return s or fallback


def pick_live_connector(capir: dict, system_hint: str = "", description: str = "") -> dict:
    """Resolve a capability's data source to its LIVE wiring: an OOTB 1st-party
    connector from the catalog when the named system has one, else a CUSTOM
    connector scaffold (kind='custom') the customer points at their API. The
    demo twin uses the same resolution for its README instructions.

    `description` is scanned for connector keywords too — so an agent DISTILLED from
    a document (which names its data source in prose, e.g. "the SQL warehouse" or
    "from Salesforce", but carries no explicit binding.system) still maps to the
    right connector instead of silently defaulting to Dataverse."""
    binding = (capir or {}).get("binding") or {}
    system = str(system_hint or binding.get("system") or "").strip()
    # EXPLICIT binding (system/connector/table) is authoritative; the free-text
    # description is only a FALLBACK for distilled agents that name their source in
    # prose. Kept separate so a stray keyword in the description can never override
    # an explicit binding.system.
    explicit_hints = " ".join([system, str(binding.get("connector") or ""),
                               str(binding.get("table") or "")]).lower()
    desc_hints = str(description or "").lower()
    # WRITE agents (e.g. ManageMemory) PERSIST a row instead of reading one: a
    # Dataverse CreateRecord ("Add a new row") whose item is mapped from the
    # agent's inputs. binding.write / binding.operation signals it.
    write = bool(binding.get("write")) or str(binding.get("operation") or "").lower() in (
        "create", "add", "store", "write", "insert", "upsert", "save")
    if write:
        # A write to a NAMED non-Dataverse system -> a CUSTOM connector (uniform: we do
        # not fit each 1st-party create shape, even when an OOTB connector exists). One
        # custom connector per system serves both the read agent and the write agent; the
        # maker binds it once. Dataverse / Dynamics / unnamed writes keep native CreateRecord.
        if system and not any(w in system.lower() for w in ("dataverse", "dynamics")):
            receipt_field = (binding.get("id_column")
                             or next(iter(binding.get("fields") or []), "id"))
            return {"kind": "custom", "key": "custom", "system": system,
                    "display": (system[:26] + " API"), "write": True,
                    "operation": "CreateRecord", "operation_label": "Create record",
                    "parameters": {}, "result_path": ["body"],
                    "columns": dict(binding.get("columns") or {}),
                    "id_column": receipt_field}
        table = str(binding.get("table") or "").strip() or "REPLACE_WITH_table_name"
        # Dataverse primary key = <singular logical name>id; derive it from the
        # entity-set (plural) name so record_id resolves on ANY table, not just the
        # memory table. rapp_fieldnotes -> rapp_fieldnoteid, rapp_memories -> rapp_memoryid.
        # '-es' plurals ('-ses/-xes/-zes/-ches/-shes') strip 'es' so rapp_addresses
        # -> rapp_addressid (not rapp_addresseid); plain '-s' and '-ies' rules stay.
        sing = (table[:-3] + "y" if table.endswith("ies")
                else table[:-2] if table.lower().endswith(("ses", "xes", "zes", "ches", "shes"))
                else table[:-1] if table.endswith("s") and not table.endswith("ss")
                else table)
        # primary NAME column: a custom table's is <prefix>_name; a standard table
        # (no publisher prefix) is "name". rapp_fieldnotes->rapp_name, contoso_x->contoso_name.
        name_col = binding.get("name_column") or (
            (table.split("_", 1)[0] + "_name") if "_" in table else "name")
        return {"kind": "ootb", "key": "dataverse", "system": system or "Microsoft Dataverse",
                "write": True, "api": "shared_commondataserviceforapps",
                "display": "Microsoft Dataverse", "operation": "CreateRecord",
                "operation_label": "Add a new row", "parameters": {"entityName": table},
                "result_path": ["body"], "columns": dict(binding.get("columns") or {}),
                "name_column": name_col,
                "id_column": binding.get("id_column") or (sing + "id")}

    def _ootb(key):
        d = {"kind": "ootb", "key": key,
             "system": system or LIVE_CONNECTOR_CATALOG[key]["display"],
             **LIVE_CONNECTOR_CATALOG[key]}
        tbl = str(binding.get("table") or "").strip()
        if tbl and key == "dataverse":
            d["parameters"] = {**dict(d.get("parameters") or {}), "entityName": tbl}
        return d

    # 1) explicit binding wins, and it is TWO-TIER: a specific product keyword
    #    (tier 1) beats a generic storage word (tier 2). So an explicit ServiceNow /
    #    Viva Engage binding whose table is e.g. "incident_database" resolves to the
    #    NAMED product, not SQL Server; a generic word only wins when the binding
    #    named no product at all (e.g. "customer database" -> SQL Server as before).
    for key, words in _CONNECTOR_KEYWORDS:
        generic = _GENERIC_KEYWORDS.get(key, ())
        if any(w in explicit_hints for w in words if w not in generic):
            return _ootb(key)
    for key, words in _CONNECTOR_KEYWORDS:
        if any(w in explicit_hints for w in _GENERIC_KEYWORDS.get(key, ())):
            return _ootb(key)
    # 2) an explicit named system with no 1st-party connector -> custom scaffold.
    if system:
        return {"kind": "custom", "key": "custom", "system": system,
                "display": system[:26] + " API", "operation": "GetRecords",
                "operation_label": "Get records", "parameters": {},
                "result_path": ["body"]}
    # 3) fallback: a distilled agent names its source only in the description.
    for key, words in _CONNECTOR_KEYWORDS:
        if any(w in desc_hints for w in words):
            return _ootb(key)
    # 4) no hint at all: Dataverse is the platform-endorsed default system of record.
    return {"kind": "ootb", "key": "dataverse", "system": "your system of record",
            **LIVE_CONNECTOR_CATALOG["dataverse"]}


_FLOW_TYPE_MAP = {  # agent.py JSON-schema param type -> trigger schema type + hint
    "number": ("number", "NUMBER"), "integer": ("number", "NUMBER"),
    "boolean": ("boolean", "BOOLEAN"),
}


def flow_trigger_inputs(params, display_name: str, metric: str):
    """The flow trigger's input schema, mirroring the source agent.py's perform()
    params 1:1 (same names, same descriptions) so the SAME contract is visible at
    every hop: agent.py -> orchestrator's connected-agent inputs -> the child's
    flow tool -> this trigger. Returns (props, required, query_prop, thr_prop,
    mirrored) where mirrored is [(name, description)] for the tool wiring."""
    props, required, mirrored = {}, [], []
    query_prop = thr_prop = None
    names = _param_prop_names(params)  # the ONE shared allocator (see _param_prop_names)
    for idx, entry in enumerate(params or []):
        if not isinstance(entry, (list, tuple)) or not entry:
            continue
        # the same sanitized+uniquified name _connected_inputs_yaml assigns this
        # entry, so every hop matches by construction. idx advances for EVERY
        # entry (even skipped non-tuple ones) to stay aligned with the allocator.
        name = names[idx]
        desc = str(entry[1] if len(entry) > 1 and entry[1] else
                   f"The {name} input, exactly as the source agent.py declares it.")
        req = bool(entry[2]) if len(entry) > 2 else False
        jtype = str(entry[3] if len(entry) > 3 and entry[3] else "string").lower()
        ptype, hint = _FLOW_TYPE_MAP.get(jtype, ("string", "TEXT"))
        if jtype in ("array", "object"):
            desc = (desc + " (JSON-encoded " + jtype + ")")[:200]
        props[name] = {"title": name, "type": ptype, "x-ms-dynamically-added": True,
                       "x-ms-content-hint": hint,
                       "description": _wdl_literal(desc[:200])}
        mirrored.append((name, desc[:200]))
        if req:
            required.append(name)
        if ptype == "string" and query_prop is None:
            query_prop = name
        if ptype == "number" and thr_prop is None:
            thr_prop = name
    # Compiler-added props get UNIQUE names too: a source param that sanitized to
    # the literal base ("text"/"number") already occupies props, so BUMP the
    # compiler name (text -> text2, number -> number2) instead of silently
    # OVERWRITING that mirrored source param and dropping it from the contract.
    def _alloc(base):
        name, i = base, 2
        while name in props:
            name, i = f"{base}{i}", i + 1
        return name
    if query_prop is None:
        # No string param recovered from the agent.py: add the free-text query
        # the deterministic filter runs on (flagged as compiler-added).
        qname = _alloc("text")
        props[qname] = {"title": "user_query", "type": "string",
                        "x-ms-dynamically-added": True, "x-ms-content-hint": "TEXT",
                        "description": _wdl_literal(
                            f"Compiler-added free-text query to filter the {display_name} "
                            "records on (the source agent.py declared no string param).")}
        query_prop = qname
        # Intentionally NOT marked required: the sub-agent calls the flow with an
        # empty query by default (returns all/top records) and its generative model
        # grounds the answer — rather than prompting the user for a filter value.
    if metric and thr_prop is None:
        nname = _alloc("number")
        props[nname] = {"title": "threshold", "type": "number",
                        "x-ms-dynamically-added": True, "x-ms-content-hint": "NUMBER",
                        "description": ("Compiler-added optional numeric threshold: pass it when "
                                        f"the user asks for records at or above a value of {metric} "
                                        "(e.g. 0.3 for 30%). Pass 0 when not asked.")}
        thr_prop = nname
    return props, required, query_prop, thr_prop, mirrored


def _readme_compose_steps(display_name: str, live: dict, fields, table: str,
                          is_live: bool, twin_display: str) -> list:
    """The literal, in-editor swap instructions: every step a maker follows to
    point this capability at real data, right next to the actions they edit."""
    conn = live or {}
    sys_name = conn.get("system") or "your system of record"
    field_list = ", ".join(fields) if fields else "(fields are free-form)"
    if is_live and conn.get("kind") == "static":
        transport = conn.get("static_transport") or "connector"
        schema_fields = ", ".join(
            item.get("name") for item in (conn.get("item_schema") or {}).get("fields") or []
            if isinstance(item, dict) and item.get("name")
        ) or field_list
        fallback_shape = (
            "map body.receipt and body.receipt.idempotency_key into the existing "
            "simulated-action response; do not use body.value"
            if conn.get("write") else
            "keep body.value as the downstream array"
        )
        steps = [
            "THIS IS A PUBLIC STATIC DEMO FLOW using active transport '%s': it calls "
            "%s. It contains no PII and never calls or mutates %s."
            % (transport, conn.get("full_endpoint_url"), sys_name),
        ]
        if transport == "http":
            steps += [
                "ZERO-BIND RUNTIME - the active built-in HTTP GET action has no "
                "connection reference or $connections parameter, so this flow can "
                "import and activate without connection binding. Built-in HTTP may "
                "still require a premium license and tenant DLP/policy allowance.",
                "PACKAGED MIGRATION CONTRACT - the typed custom connector '%s' is "
                "included in this solution but is not used at runtime. To switch, "
                "replace the HTTP action with its operation, create/bind a no-auth "
                "connection reference, and preserve %s."
                % (conn.get("packaged_connector"), fallback_shape),
            ]
        else:
            steps += [
                "CONNECTION BINDING REQUIRED - Power Platform requires a connection "
                "object and connection-reference binding even when this packaged custom "
                "connector declares no authentication. Create/select that no-auth "
                "connection, bind the solution reference, then turn the draft flow on.",
                "OPTIONAL ZERO-BIND SWITCH - replace only the OpenApiConnection action "
                "with a built-in HTTP GET using the same URL; %s. Built-in HTTP may "
                "require a premium license and tenant DLP/policy allowance."
                % fallback_shape,
            ]
        steps += [
            "CUSTOMER MIGRATION - replace the static endpoint/custom connector binding "
            "with the real %s API. Preserve the same field schema so the filter and "
            "agent contract stay unchanged: %s." % (sys_name, schema_fields),
            "STATIC QUALIFIER - reads are public static demo context. Receipt GETs set "
            "action_status=simulated and include receipt/idempotency evidence; they "
            "never prove an external mutation.",
        ]
        if twin_display:
            steps.append(
                "OFFLINE FALLBACK: '%s' embeds synthetic Compose data and requires "
                "no connector or connection." % twin_display
            )
        return steps
    if is_live:
        suggested = (f"{conn.get('display')} - '{conn.get('operation_label')}' "
                     f"(operationId {conn.get('operation')})")
        setup = conn.get("setup_hint") or ("set every REPLACE_ placeholder "
                                           "(table/entity/site) to your real names")
        steps = [
            f"THIS IS THE LIVE FLOW: the 'Get_records_LIVE' step below calls {sys_name} "
            f"via {suggested}. Nothing is synthetic once its connection is bound.",
            "STEP 1 - Bind the connection: open Solutions > this solution > Connection "
            "references, select the reference this flow uses, and pick (or create) a "
            "connection with credentials for " + sys_name + ".",
            "STEP 2 - Point it at your data: open 'Get_records_LIVE' - it " + setup + ".",
            f"STEP 3 - Map your columns: 'Filter_matching_records' and the response expect "
            f"these record fields: {field_list}. If your column names differ, add a Select "
            "action after 'Get_records_LIVE' that renames yours to these.",
            "STEP 4 - Save, then turn the flow ON (it ships off until its connection is "
            "bound). Test from the agent - the response schema is unchanged.",
        ]
        if conn.get("kind") == "custom":
            steps.insert(2, "STEP 1b - This system has no first-party connector, so the "
                            f"solution ships a CUSTOM CONNECTOR scaffold ('{conn.get('display')}'). "
                            "Open Custom connectors > edit it > set Host to your API endpoint. Its "
                            "GET /records must return a JSON array shaped like the fields in STEP 3.")
        if twin_display:
            steps.append(f"FALLBACK: blocked on credentials? The companion solution "
                         f"'{twin_display}' is this same prototype running on synthetic data - "
                         "zero connections needed.")
    else:
        suggested = (f"{conn.get('display')} - '{conn.get('operation_label')}'"
                     if conn.get("kind") == "ootb" else
                     f"a custom connector for {sys_name} (no first-party connector exists)")
        steps = [
            f"THIS FLOW RUNS ON SYNTHETIC DATA: the 'Get_records_STATIC_DATA' Compose below "
            f"holds stand-in {table} records. Swapping that ONE step for your real data "
            "source makes this flow fully live - every other step stays unchanged.",
            f"STEP 1 - Add the real data step: click + below this card and add {suggested}, "
            f"pointed at your {table} data in {sys_name}.",
            "STEP 2 - Rewire the filter: open 'Filter_matching_records' and set its From to "
            "the new step's output array (for Dataverse/SharePoint that is the 'value' list).",
            f"STEP 3 - Keep these exact record fields: {field_list}. If your column names "
            "differ, add a Select action that renames yours to these.",
            "STEP 4 - Delete 'Get_records_STATIC_DATA' and Save. 'Respond_to_the_agent' "
            "returns the same schema either way, so the agent needs no changes.",
        ]
        if twin_display:
            steps.append(f"SHORTCUT: the companion solution '{twin_display}' ships this same "
                         f"flow ALREADY WIRED to {suggested.split(' - ')[0]} - bind its "
                         "connection reference and turn it on instead of editing this one.")
    return steps


def _readme_card(steps: list, description: str) -> dict:
    """A no-op Compose that IS documentation: a parallel root holding numbered
    guidance right in the designer. Nothing consumes its outputs — deleting it
    changes nothing at runtime."""
    return {
        "runAfter": {},
        "type": "Compose",
        "inputs": [_wdl_literal(s) for s in steps],
        "description": description[:250],
    }


def readme_cards(display_name, conn, fields, table, is_live, twin_display,
                 provenance, mirrored, query_prop, thr_prop, metric, records,
                 data_action, doc, example_take, fallback_take) -> dict:
    """The flow's in-editor self-documentation: three numbered cards a maker
    reads top-to-bottom to fully understand the flow's 1:1 fidelity with its
    source agent.py — what it is and who calls it, how to wire real data, and
    exactly how the matching/fallback logic works."""
    prov = provenance or {}
    agent_file = str(prov.get("agent_file") or "the source agent") + ".py"
    param_bits = []
    for name, _d in mirrored:
        role = (" (the query the filter runs on)" if name == query_prop else
                " (the numeric threshold)" if name == thr_prop else "")
        param_bits.append(name + role)
    if query_prop and all(query_prop != n for n, _ in mirrored):
        param_bits.append(query_prop + " (compiler-added free-text query)")
    if thr_prop and all(thr_prop != n for n, _ in mirrored):
        param_bits.append(thr_prop + " (compiler-added threshold)")
    about = [
        f"WHAT THIS FLOW IS: the deterministic twin of {agent_file} "
        f"('{display_name}'). It runs the SAME steps as that agent's perform(): "
        "load records -> filter by the query -> respond"
        + (" -> build the document lines" if doc else "") + ". "
        + str(prov.get("description") or "")[:300],
        "WHO CALLS IT: the '" + display_name + "' agent invokes this flow as its "
        "tool, and the orchestrator passes the agent the same inputs — the SAME "
        "parameter names travel agent.py -> orchestrator -> agent tool -> this "
        "trigger, so a dropped value is visible at whichever hop lost it.",
        "INPUTS (mirrored 1:1 from the agent.py): " + ("; ".join(param_bits) or "none") + ".",
        "OUTPUTS: message (the answer sentence), matches_json (the matched records, "
        "for the agent to reason over), match_count, received_inputs (echo of exactly "
        "what this flow received - open a run and read it to debug a handoff)"
        + (", document_text (the artifact's lines)" if doc else "") + ".",
        f"STEP BY STEP: '{data_action}' provides the {table} records -> "
        "'Filter_matching_records' applies the query -> 'Select_result' keeps the "
        f"top {example_take} matches (else {fallback_take} reference examples - the "
        "agent.py fallback) -> 'Respond_to_the_agent' returns the outputs above.",
    ]
    sample = ""
    if records:
        try:
            sample = json.dumps(records[0])[:220]
        except Exception:  # noqa: BLE001
            sample = str(records[0])[:220]
    matching = [
        "FILTER LOGIC (ported clause-for-clause from perform()): a record matches "
        "when the query text appears anywhere in the record's JSON, OR when any "
        "record field's value appears inside the query.",
    ]
    if metric and thr_prop:
        matching.append(
            f"NUMERIC THRESHOLD: when '{thr_prop}' > 0, records with "
            f"{metric} >= threshold ALSO match. 0 means 'no threshold asked' and "
            "never matches everything.")
    matching += [
        f"FALLBACK: when nothing matches, the response carries {fallback_take} "
        "reference example records instead, so the agent always answers from "
        "grounded data - exactly perform()'s behavior.",
        "RECORD FIELDS: " + (", ".join(fields) if fields else "(free-form)") + ".",
    ]
    if sample:
        matching.append("SAMPLE RECORD: " + sample)
    return {
        "README_1_About_this_flow": _readme_card(
            about, "START HERE - what this flow is, who calls it, and the exact "
                   "input/output contract it shares with the source agent.py."),
        "README_2_Connect_your_real_data": _readme_card(
            _readme_compose_steps(display_name, conn, fields, table, is_live, twin_display),
            "HOW TO CONNECT REAL DATA - numbered steps. Does nothing at runtime; "
            "safe to delete."),
        "README_3_How_matching_works": _readme_card(
            matching, "The deterministic matching/fallback semantics, 1:1 with the "
                      "agent.py perform() - read before changing the filter."),
    }


def _static_pascal(value: str) -> str:
    return "".join(part.capitalize() for part in re.findall(r"[A-Za-z0-9]+", value))


def _static_swagger_operations(live: dict) -> list:
    adapter = live["adapter_id"]
    resource = live["resource_id"]
    cap_code = live["capability_code"]
    item = {
        key: value
        for key, value in (live.get("item_schema") or {}).items()
        if key in {"type", "additionalProperties", "required", "properties"}
    }
    item.setdefault("type", "object")
    item.setdefault("properties", {})
    stem = _static_pascal(adapter)
    resource_stem = _static_pascal(resource)
    endpoints = live.get("endpoints") or {}
    collection = endpoints.get("collection") or {}
    record = endpoints.get("record") or {}
    receipt = endpoints.get("write_simulation") or {}
    receipt_props = {
        "receipt_id": {"type": "string"},
        "operation": {"type": "string"},
        "resource_id": {"type": "string"},
        "accepted": {"type": "boolean"},
        "simulated": {"type": "boolean", "enum": [True]},
        "status": {
            "type": "string",
            "enum": ["accepted", "rejected", "validation_failed"],
        },
        "processed_at": {"type": "string", "format": "date-time"},
        "idempotency_key": {"type": "string"},
    }
    operations = []
    if collection.get("path"):
        operations.append({
            "kind": "collection",
            "path": collection["path"],
            "operation_id": "Get%s%sCollection" % (stem, resource_stem),
            "summary": "List static " + resource,
            "description": "Returns a deterministic no-PII collection.",
            "response_description": "Deterministic no-PII collection",
            "response_schema": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "schema", "generated", "adapter_id", "resource_id", "count", "value"
                ],
                "properties": {
                    "schema": {"type": "string"},
                    "generated": {"type": "string", "format": "date-time"},
                    "adapter_id": {"type": "string", "enum": [adapter]},
                    "resource_id": {"type": "string", "enum": [resource]},
                    "count": {"type": "integer", "format": "int32"},
                    "value": {"type": "array", "items": item},
                },
            },
        })
    if record.get("path_template"):
        operations.append({
            "kind": "record",
            "path": record["path_template"],
            "operation_id": "Get%s%sRecord" % (stem, resource_stem),
            "summary": "Get one static " + resource + " record",
            "description": "Returns one deterministic no-PII record.",
            "parameters": [{
                "name": "record_id", "in": "path", "required": True, "type": "string"
            }],
            "response_description": "Deterministic no-PII record",
            "response_schema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["schema", "generated", "adapter_id", "resource_id", "record"],
                "properties": {
                    "schema": {"type": "string"},
                    "generated": {"type": "string", "format": "date-time"},
                    "adapter_id": {"type": "string", "enum": [adapter]},
                    "resource_id": {"type": "string", "enum": [resource]},
                    "record": item,
                },
            },
        })
    if receipt.get("path"):
        operations.append({
            "kind": "receipt",
            "path": receipt["path"],
            "operation_id": "Simulate%s%s" % (stem, _static_pascal(cap_code)),
            "summary": "Get a deterministic write-simulation receipt; no mutation",
            "description": "Static receipt preview; no external system is mutated.",
            "response_description": "Static simulated-write receipt",
            "response_schema": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "schema", "generated", "adapter_id", "capability_code",
                    "route_count", "write_intent_count", "receipt",
                ],
                "properties": {
                    "schema": {"type": "string"},
                    "generated": {"type": "string", "format": "date-time"},
                    "adapter_id": {"type": "string", "enum": [adapter]},
                    "capability_code": {"type": "string", "enum": [cap_code]},
                    "route_count": {"type": "integer", "format": "int32"},
                    "write_intent_count": {"type": "integer", "format": "int32"},
                    "receipt": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": list(receipt_props),
                        "properties": receipt_props,
                    },
                },
            },
        })
    return operations


def _custom_connector_swagger(cc: dict) -> str:
    """The custom-connector OpenAPI definition. MUST be Swagger 2.0 (OpenAPI 3
    fails import). The typed 200 response mirrors the capability's record
    fields, so the maker sees exactly the shape their API must return and the
    designer surfaces the fields as named outputs."""
    if cc.get("static"):
        paths = {}
        for operation in cc.get("operations") or []:
            path = str(operation["path"])
            prefix = "industry-templates"
            if path.startswith(prefix):
                path = path[len(prefix):]
            path = "/" + path.lstrip("/")
            paths.setdefault(path, {})["get"] = {
                "operationId": operation["operation_id"],
                "summary": operation["summary"],
                "description": operation["description"],
                "parameters": operation.get("parameters") or [],
                "responses": {
                    "200": {
                        "description": operation["response_description"],
                        "schema": operation["response_schema"],
                    },
                    **(
                        {"404": {"description": "Unknown deterministic record ID"}}
                        if operation.get("kind") == "record" else {}
                    ),
                },
                "x-ms-visibility": (
                    "advanced" if operation.get("kind") == "receipt" else "important"
                ),
            }
        return json.dumps({
            "swagger": "2.0",
            "info": {
                "title": cc["display"],
                "description": (
                    "Unauthenticated no-PII static GET adapter. Write operations "
                    "return deterministic receipts and never mutate an external product."
                ),
                "version": "1.0.0",
            },
            "host": _STATIC_API_HOST,
            "basePath": _STATIC_API_BASE_PATH,
            "schemes": ["https"],
            "consumes": [],
            "produces": ["application/json"],
            "paths": paths,
            "definitions": {},
            "parameters": {},
            "responses": {},
            "tags": [],
        })

    props = {}
    sample = (cc.get("records") or [{}])
    sample = sample[0] if sample and isinstance(sample[0], dict) else {}
    for f in cc.get("fields") or []:
        v = sample.get(f)
        t = ("number" if isinstance(v, (int, float)) and not isinstance(v, bool)
             else "boolean" if isinstance(v, bool) else "string")
        props[f] = {"type": t, "description": f}
    post_props = dict(props)
    for name, schema in (cc.get("write_inputs") or {}).items():
        post_props[name] = {
            "type": (schema or {}).get("type", "string"),
            "description": (schema or {}).get("description") or name,
        }
    return json.dumps({
        "swagger": "2.0",
        "info": {"title": cc["display"], "description": cc["description"][:250],
                 "version": "1.0"},
        "host": "replace-with-your-host.example.com",
        "basePath": "/", "schemes": ["https"],
        "consumes": [], "produces": ["application/json"],
        "paths": {"/records": {
            "get": {
                "summary": "Get records",
                "description": ("Returns this capability's records from "
                                + str(cc.get("system") or "your system")
                                + " as a JSON array (the field shape below)."),
                "operationId": "GetRecords",
                "parameters": [{"name": "query", "in": "query", "required": False,
                                "type": "string",
                                "description": "Optional server-side filter."}],
                "responses": {"200": {"description": "The record array",
                                      "schema": {"type": "array",
                                                 "items": {"type": "object",
                                                           "properties": props}}},
                              "default": {"description": "default"}}},
            "post": {
                "summary": "Create record",
                "description": ("Creates a record in "
                                + str(cc.get("system") or "your system")
                                + " from the posted JSON body (the field shape below)."),
                "operationId": "CreateRecord",
                "parameters": [{"name": "body", "in": "body", "required": True,
                                "schema": {"type": "object", "properties": post_props}}],
                "responses": {"200": {"description": "The created record",
                                      "schema": {"type": "object", "properties": props}},
                              "default": {"description": "default"}}}}},
        "definitions": {}, "parameters": {}, "responses": {}, "tags": []})


def capir_flow_name(display_name: str) -> str:
    """The flow's display name in Power Automate / Copilot Studio."""
    return ("Run " + str(display_name or "Capability"))[:96]


def capir_flow_guid(solution_unique_name: str, child_schema: str) -> str:
    """Deterministic WorkflowId — same solution + sub-agent always yields the
    same GUID, so a re-import UPDATES the flow instead of duplicating it."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL,
                          f"t2p-flow://{solution_unique_name}/{child_schema}"))


def flow_json_file_name(name: str, workflow_id: str) -> str:
    """/Workflows/<Name>-<GUID>.json, matching the exporter's convention."""
    base = re.sub(r"[^A-Za-z0-9]", "", str(name)) or "Flow"
    return f"{base[:60]}-{workflow_id.upper()}.json"


def _capir_flow_features(capir: dict):
    """The shared CapIR reads used by both the flow and its tool wiring:
    (records, fields, metric_field, facts, doc, consts, table, response)."""
    capir = capir or {}
    consts = dict(_CAPIR_TOPIC_CONSTS)
    consts.update(capir.get("consts") or {})
    binding = capir.get("binding") or {}
    fields = [f for f in (binding.get("fields") or _capir_topic_fields(binding.get("records")))
              if isinstance(f, str) and f.isidentifier()]
    records = []
    for r in binding.get("records") or []:
        if isinstance(r, dict):
            records.append({k: _wdl_record_value(v) for k, v in r.items()
                            if isinstance(k, str) and k.isidentifier()})
    facts, doc = [], None
    for step in capir.get("steps") or []:
        if step.get("op") == "knowledge_lookup":
            facts = [str(f) for f in (step.get("facts") or [])]
        elif step.get("op") == "artifact":
            doc = step.get("doc")
    table = str(binding.get("table") or "records")
    response = str(capir.get("response") or "")
    metric = _numeric_metric_field(records, fields, binding.get("metric_field"))
    return records, fields, metric, facts, doc, consts, table, response


def capir_flow_definition(display_name: str, capir: dict, params=None,
                          live: Optional[dict] = None,
                          twin_display: str = "",
                          provenance: Optional[dict] = None) -> dict:
    """Compile a capability's CapIR into the flow clientdata JSON (the
    /Workflows/*.json part): the agent-compatible Skills trigger whose inputs
    MIRROR the source agent.py's perform() params (same names + descriptions at
    every hop, for traceability), the data step, perform()'s filter -> fallback
    -> respond steps, and an in-editor README Compose with the literal
    swap-to-real-data instructions.

    live=None  -> DEMO twin: synthetic records in a static Compose (no
                  connections; imports + activates anywhere).
    live=dict  -> LIVE twin: the data step calls the resolved source. Static
                  transport=http uses a built-in connectionless HTTP action;
                  all other live sources use OpenApiConnection."""
    records, fields, metric, facts, doc, consts, table, response = _capir_flow_features(capir)
    prompt = None
    for slot in (capir or {}).get("slots") or []:
        prompt = slot.get("prompt"); break
    prompt = prompt or f"A keyword, id, or value to filter the {display_name} records on."
    response = response or f"Here is how I handle {display_name}."
    example_take = int(consts.get("example_take") or 2)
    fallback_take = int(consts.get("fallback_take") or 2)
    pdf_records = int(consts.get("pdf_records") or 3)

    # ---- trigger: "When an agent calls the flow" (Request, kind: Skills) ----
    # Inputs mirror the agent.py params 1:1 (falling back to the legacy free-
    # text 'text' input when none were recovered) — see flow_trigger_inputs.
    trig_props, required, query_prop, thr_prop, mirrored = flow_trigger_inputs(
        params, display_name, metric)
    # the compiler-added free-text query carries the capability's slot prompt as
    # its input description — key on the RETURNED query_prop (which may have been
    # uniquified to text2/… to avoid clobbering a mirrored source param), never
    # the literal "text". A source param that already occupies query_prop is in
    # `mirrored`, so it keeps its own description.
    if query_prop and query_prop not in {n for n, _ in mirrored}:
        trig_props[query_prop]["description"] = _wdl_literal(str(prompt)[:200])

    # DEMO twin of a WRITE agent (no live connector to persist to): acknowledge the
    # write coherently, instead of falling through to the read/synthetic-records flow
    # (a "log/save" agent listing records back at the user is confusing).
    _wbind = (capir or {}).get("binding") or {}
    if not live and (bool(_wbind.get("write")) or str(_wbind.get("operation") or "").lower()
                     in ("create", "add", "store", "write", "insert", "upsert", "save")):
        write_and_generate = bool(_wbind.get("generative"))
        ack = {}
        ack_after = {}
        if write_and_generate:
            ack["Prepare_deliverable_context"] = {
                "runAfter": {}, "type": "Compose",
                "inputs": "@string(triggerBody())",
                "description": ("The complete drafted content/context the agent supplied "
                                "for this simulated outbound action.")[:250]}
            ack_after = {"Prepare_deliverable_context": ["Succeeded"]}
        ack.update({"Acknowledge_demo_write": {"runAfter": ack_after, "type": "Compose",
                   "inputs": ("SIMULATED ACTION ONLY - no external system changed. "
                              "The demo received the proposed write/action. Preserve this "
                              "qualifier in the user-facing answer and do not claim delivery "
                              "or persistence. Do not invent a next action, owner, assignment, "
                              "or follow-up unless it is explicitly present in received_inputs.")},
               "Respond_to_the_agent": {"runAfter": {"Acknowledge_demo_write": ["Succeeded"]},
                   "type": "Response", "kind": "Skills",
                   "inputs": {"statusCode": 200,
                       "body": {"message": "@outputs('Acknowledge_demo_write')",
                                "action_status": "simulated",
                                "receipt": "demo-simulated",
                                "compose_required": write_and_generate,
                                "deliverable_context": (
                                    "@outputs('Prepare_deliverable_context')"
                                    if write_and_generate else ""),
                                "data_provenance": "synthetic_demo",
                                "received_inputs": "@string(triggerBody())"},
                       "schema": {"type": "object", "properties": {
                           "message": {"title": "message", "type": "string", "x-ms-dynamically-added": True},
                           "action_status": {"title": "action_status", "type": "string", "x-ms-dynamically-added": True},
                           "receipt": {"title": "receipt", "type": "string", "x-ms-dynamically-added": True},
                           "compose_required": {"title": "compose_required", "type": "boolean", "x-ms-dynamically-added": True},
                           "deliverable_context": {"title": "deliverable_context", "type": "string", "x-ms-dynamically-added": True},
                           "data_provenance": {"title": "data_provenance", "type": "string", "x-ms-dynamically-added": True},
                           "received_inputs": {"title": "received_inputs", "type": "string", "x-ms-dynamically-added": True}}}}}})
        return {"properties": {"connectionReferences": {},
            "definition": {"$schema": "https://schema.management.azure.com/providers/"
                           "Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
                "contentVersion": "1.0.0.0",
                "parameters": {"$authentication": {"defaultValue": {}, "type": "SecureObject"}},
                "triggers": {"manual": {"type": "Request", "kind": "Skills",
                    "inputs": {"schema": {"type": "object", "properties": trig_props, "required": required}}}},
                "actions": ack, "outputs": {}},
            "templateName": None}, "schemaVersion": _FLOW_SCHEMA_VERSION}

    # WRITE flow (e.g. ManageMemory): map the agent's inputs onto a row and CREATE
    # it, then respond — the Dataverse write archetype. No filter/records shape;
    # ContextMemory then READS the same table so memory is shared across agents.
    if live and live.get("write"):
        if live.get("kind") == "static":
            write_and_generate = bool(_wbind.get("generative"))
            actions = {
                "README_2_Static_write_binding_and_fallback": _readme_card(
                    _readme_compose_steps(
                        display_name, live, fields, table, True, twin_display
                    ),
                    "PUBLIC STATIC WRITE SIMULATION - binding, HTTP fallback, "
                    "receipt mapping, and customer migration instructions.",
                )
            }
            run_after = {}
            if write_and_generate:
                actions["Prepare_deliverable_context"] = {
                    "runAfter": {},
                    "type": "Compose",
                    "inputs": "@string(triggerBody())",
                    "description": (
                        "Composed content retained while the public adapter returns "
                        "a deterministic simulation receipt."
                    ),
                }
                run_after = {"Prepare_deliverable_context": ["Succeeded"]}
            actions[_FLOW_LIVE_WRITE_ACTION] = {
                "runAfter": run_after,
                "type": "Http" if _static_http(live) else "OpenApiConnection",
                "inputs": (
                    {
                        "method": "GET",
                        "uri": live["full_endpoint_url"],
                        "headers": {
                            "Accept": "application/json",
                            "User-Agent": "RAPP-Static-Industry/1.0",
                        },
                    }
                    if _static_http(live)
                    else {
                        "host": {
                            "apiId": live["apiId"],
                            "connectionName": live["api"],
                            "operationId": live["operation"],
                        },
                        "parameters": {},
                    }
                ),
                "description": (
                    "STATIC SIMULATION GET - returns a deterministic receipt; "
                    "no external system is mutated."
                ),
            }
            receipt_expr = (
                "@string(outputs('%s')?['body']?['receipt'])"
                % _FLOW_LIVE_WRITE_ACTION
            )
            idempotency_expr = (
                "@string(outputs('%s')?['body']?['receipt']?['idempotency_key'])"
                % _FLOW_LIVE_WRITE_ACTION
            )
            action_status_expr = (
                "@if(equals(outputs('%s')?['body']?['receipt']?['simulated'], "
                "true), 'simulated', 'unverified')" % _FLOW_LIVE_WRITE_ACTION
            )
            actions["Respond_to_the_agent"] = {
                "runAfter": {_FLOW_LIVE_WRITE_ACTION: ["Succeeded"]},
                "type": "Response",
                "kind": "Skills",
                "inputs": {
                    "statusCode": 200,
                    "body": {
                        "message": (
                            "SIMULATED ACTION ONLY - the public static adapter returned "
                            "a deterministic receipt; no external system changed."
                        ),
                        "action_status": action_status_expr,
                        "receipt": receipt_expr,
                        "idempotency_key": idempotency_expr,
                        "compose_required": write_and_generate,
                        "deliverable_context": (
                            "@outputs('Prepare_deliverable_context')"
                            if write_and_generate else ""
                        ),
                        "data_provenance": "public_static_demo",
                        "received_inputs": "@string(triggerBody())",
                    },
                    "schema": {
                        "type": "object",
                        "properties": {
                            "message": {"title": "message", "type": "string",
                                        "x-ms-dynamically-added": True},
                            "action_status": {"title": "action_status", "type": "string",
                                              "x-ms-dynamically-added": True},
                            "receipt": {"title": "receipt", "type": "string",
                                        "x-ms-dynamically-added": True},
                            "idempotency_key": {"title": "idempotency_key", "type": "string",
                                                "x-ms-dynamically-added": True},
                            "compose_required": {"title": "compose_required", "type": "boolean",
                                                 "x-ms-dynamically-added": True},
                            "deliverable_context": {
                                "title": "deliverable_context", "type": "string",
                                "x-ms-dynamically-added": True,
                            },
                            "data_provenance": {"title": "data_provenance", "type": "string",
                                                "x-ms-dynamically-added": True},
                            "received_inputs": {"title": "received_inputs", "type": "string",
                                                "x-ms-dynamically-added": True},
                        },
                    },
                },
            }
            conn_refs = {}
            if not _static_http(live):
                conn_refs[live["api"]] = {
                    "runtimeSource": "embedded",
                    "connection": {
                        "connectionReferenceLogicalName": live["conn_ref_logical"]
                    },
                    "api": {"name": live["api"]},
                }
            definition_params = {
                "$authentication": {
                    "defaultValue": {}, "type": "SecureObject"
                },
            }
            if conn_refs:
                definition_params["$connections"] = {
                    "defaultValue": {}, "type": "Object"
                }
            return {
                "properties": {
                    "connectionReferences": conn_refs,
                    "definition": {
                        "$schema": "https://schema.management.azure.com/providers/"
                                   "Microsoft.Logic/schemas/2016-06-01/"
                                   "workflowdefinition.json#",
                        "contentVersion": "1.0.0.0",
                        "parameters": definition_params,
                        "triggers": {
                            "manual": {
                                "type": "Request",
                                "kind": "Skills",
                                "inputs": {
                                    "schema": {
                                        "type": "object",
                                        "properties": trig_props,
                                        "required": required,
                                    }
                                },
                            }
                        },
                        "actions": actions,
                        "outputs": {},
                    },
                    "templateName": None,
                },
                "schemaVersion": _FLOW_SCHEMA_VERSION,
            }
        cols = live.get("columns") or {}
        entity = (live.get("parameters") or {}).get("entityName") or "REPLACE_WITH_table_name"
        name_col = live.get("name_column") or "rapp_name"
        id_col = live.get("id_column") or "id"
        item = {}
        for pname in trig_props:
            col = cols.get(pname) or ("rapp_" + re.sub(r"[^a-z0-9]", "", pname.lower()))
            item["item/" + col] = "@triggerBody()?['" + pname + "']"
        # primary name column: a short title from the MOST MEANINGFUL text input
        # (prefer content/text/message/body over type/tag fields), so every row is
        # human-readable in Dataverse.
        name_src = next((p for p in trig_props if p.lower() in
                         ("content", "text", "message", "body", "memory", "note", "summary")), None) \
            or next((p for p in trig_props if (trig_props[p] or {}).get("type") == "string"), None)
        if name_src:
            # fallback title when the input is empty: the capability name, not the
            # memory-agent's old 'Memory' default (which leaked into every write).
            name_fallback = (display_name or "Record").replace("'", "''")
            item["item/" + name_col] = (
                "@if(greater(length(coalesce(triggerBody()?['" + name_src + "'], '')), 80), "
                "concat(substring(triggerBody()?['" + name_src + "'], 0, 80), '...'), "
                "coalesce(triggerBody()?['" + name_src + "'], '" + name_fallback + "'))")
        # custom connector -> POST body (field-per-input); Dataverse -> entityName + item/<col>
        if live.get("kind") == "custom":
            write_params = {"body/" + re.sub(r"[^A-Za-z0-9_]", "", p): "@triggerBody()?['" + p + "']"
                            for p in trig_props}
            write_target = str(live.get("system") or live.get("display") or "the system")
        else:
            write_params = {"entityName": entity, **item}
            write_target = str(entity)
        write_and_generate = bool(_wbind.get("generative"))
        create_step = {
            "runAfter": ({"Prepare_deliverable_context": ["Succeeded"]}
                         if write_and_generate else {}),
            "type": "OpenApiConnection",
            "inputs": {
                "host": {"apiId": live["apiId"], "connectionName": live["api"],
                         "operationId": live.get("operation") or "CreateRecord"},
                "parameters": write_params,
                **({} if live.get("kind") in ("custom", "static")
                   else {"authentication": "@parameters('$authentication')"}),
            },
            "description": ("LIVE write - creates a record in " + write_target + " via "
                            + str(live.get("display") or "Dataverse")
                            + ". Bind the connection reference, then turn the flow on.")[:250],
        }
        record_id_expr = ("string(coalesce(outputs('"
                          + _FLOW_LIVE_WRITE_ACTION + "')?['body']?['"
                          + id_col + "'], ''))")
        write_actions = {}
        if write_and_generate:
            write_actions["Prepare_deliverable_context"] = {
                "runAfter": {}, "type": "Compose",
                "inputs": "@string(triggerBody())",
                "description": ("The drafted content/context supplied to the outbound "
                                "write action.")[:250]}
        write_actions.update({
            _FLOW_LIVE_WRITE_ACTION: create_step,
            "Respond_to_the_agent": {
                "runAfter": {_FLOW_LIVE_WRITE_ACTION: ["Succeeded"]},
                "type": "Response", "kind": "Skills",
                "inputs": {"statusCode": 200,
                           "body": {
                                    "message": ("@if(greater(length(" + record_id_expr
                                                + "), 0), concat('Saved to "
                                                + write_target.replace("'", "''")
                                                + ". Receipt: ', " + record_id_expr
                                                + "), 'Write action returned without a "
                                                "record receipt; verify it in the target "
                                                "system before claiming success.')"),
                                    "action_status": ("@if(greater(length("
                                                      + record_id_expr
                                                      + "), 0), 'succeeded', 'unverified')"),
                                    "receipt": "@" + record_id_expr,
                                    "compose_required": write_and_generate,
                                    "deliverable_context": (
                                        "@outputs('Prepare_deliverable_context')"
                                        if write_and_generate else ""),
                                    "data_provenance": "live_connector",
                                    "received_inputs": "@string(triggerBody())"},
                           "schema": {"type": "object", "properties": {
                               "message": {"title": "message", "type": "string", "x-ms-dynamically-added": True},
                               "action_status": {"title": "action_status", "type": "string", "x-ms-dynamically-added": True},
                               "receipt": {"title": "receipt", "type": "string", "x-ms-dynamically-added": True},
                               "compose_required": {"title": "compose_required", "type": "boolean", "x-ms-dynamically-added": True},
                               "deliverable_context": {"title": "deliverable_context", "type": "string", "x-ms-dynamically-added": True},
                               "data_provenance": {"title": "data_provenance", "type": "string", "x-ms-dynamically-added": True},
                               "received_inputs": {"title": "received_inputs", "type": "string", "x-ms-dynamically-added": True}}}},
            },
        })
        conn_refs = {live["api"]: {"runtimeSource": "embedded",
                     "connection": {"connectionReferenceLogicalName": live["conn_ref_logical"]},
                     "api": {"name": live["api"]}}}
        return {
            "properties": {
                "connectionReferences": conn_refs,
                "definition": {
                    "$schema": "https://schema.management.azure.com/providers/"
                               "Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
                    "contentVersion": "1.0.0.0",
                    "parameters": {"$authentication": {"defaultValue": {}, "type": "SecureObject"},
                                   "$connections": {"defaultValue": {}, "type": "Object"}},
                    "triggers": {"manual": {"type": "Request", "kind": "Skills",
                                 "inputs": {"schema": {"type": "object",
                                            "properties": trig_props, "required": required}}}},
                    "actions": write_actions,
                    "outputs": {},
                },
                "templateName": None,
            },
            "schemaVersion": _FLOW_SCHEMA_VERSION,
        }

    # ---- the real filter, ported clause-for-clause from the topic/perform() ----
    q = f"toLower(coalesce(triggerBody()?['{query_prop}'], ''))"
    binding = (capir or {}).get("binding") or {}
    key_field = str(binding.get("key_field") or "id")
    exact_key_required = bool(binding.get("exact_key_required")) and key_field in fields
    if exact_key_required:
        # Match the generated Python interpreter: split on whitespace, remove
        # identifier punctuation from each token and key, then use exact array
        # membership. CH-31 cannot match CH-3109, and CH-3109? still matches.
        query_norm = q
        key_norm = f"toLower(string({_la_field(key_field)}))"
        for punct in (
                "-", "_", ".", ",", ":", ";", "(", ")", "?", "!", "/", "#", "@",
                "+", "$", "%", "^", "&", "*", "=", "[", "]", "{", "}", "<", ">",
                "~", "`", "'", '"'):
            query_norm = "replace(" + query_norm + ", " + _la_str(punct) + ", '')"
            key_norm = "replace(" + key_norm + ", " + _la_str(punct) + ", '')"
        for encoded_ws in ("%0A", "%0D", "%09"):
            decoded = "decodeUriComponent(" + _la_str(encoded_ws) + ")"
            query_norm = "replace(" + query_norm + ", " + decoded + ", ' ')"
            key_norm = "replace(" + key_norm + ", " + decoded + ", ' ')"
        # Pipe-delimited contiguous token sequences preserve boundaries while
        # supporting identifiers with spaces: |ch31| cannot match |ch3109|,
        # while |po20260091|revb| matches the same two-token sequence in a query.
        for _ in range(3):
            query_norm = "replace(" + query_norm + ", '  ', ' ')"
            key_norm = "replace(" + key_norm + ", '  ', ' ')"
        query_seq = ("concat('|', join(split(trim(" + query_norm
                     + "), ' '), '|'), '|')")
        key_seq = ("concat('|', join(split(trim(" + key_norm
                   + "), ' '), '|'), '|')")
        where = f"contains({query_seq}, {key_seq})"
    else:
        clauses = [f"contains(toLower(string(item())), {q})"]
        for f in fields:
            clauses.append(f"contains({q}, toLower(string({_la_field(f)})))")
        where = "or(" + ", ".join(clauses) + ")" if len(clauses) > 1 else clauses[0]
    if metric and thr_prop:
        # absent or 0 = "no threshold asked" (the tool tells the model to pass
        # 0 when the user gave no number), so 0 must never match everything
        thr = f"coalesce(triggerBody()?['{thr_prop}'], 0)"
        field_expr = _la_field(metric)
        # money-formatted metric values ("$12,340", "9,500") aren't float()-
        # parseable as-is: when any record carries a currency symbol or thousands
        # comma, strip the [$ € £ ¥ ₹ , space] set before float(). Detection has
        # already guaranteed every value is convertible by exactly this set (no
        # 3-letter currency code reaches here), so the conversion is safe; plain-
        # number fields keep the original expression untouched.
        metric_vals = [r.get(metric) for r in records
                       if isinstance(r, dict) and metric in r]
        if any(isinstance(v, str) and any(c in v for c in _MONEY_SYMBOLS + ",")
               for v in metric_vals):
            field_expr = _wdl_strip_money(field_expr)
        # _la_field coalesces a missing field to '' — map '' to '0' so float()
        # can never throw on a record that lacks the metric.
        metric_num = ("float(if(equals(" + field_expr + ", ''), '0', "
                      + field_expr + "))")
        where = ("or(" + where + ", and(greater(" + thr + ", 0), "
                 "greaterOrEquals(" + metric_num + ", " + thr + ")))")

    # DATE-WINDOW branch (datewin): a capability whose text promised a window
    # ("expiring within 30 days", "overdue") carries a SIGNED day count on the
    # binding (date_window_days: forward>0, overdue<0) plus the ISO date field it
    # compares. ISO yyyy-mm-dd strings compare lexicographically == chronologically,
    # so the WHERE compares each row's date (string) against
    # formatDateTime(addDays(utcNow(), N), 'yyyy-MM-dd'). Forward: inside the
    # window is today <= date <= cutoff (already-expired rows excluded). Overdue:
    # date strictly before today (a non-empty guard drops missing-date rows, which
    # _la_field coalesces to '' and would otherwise sort before every date). The
    # date_field is re-validated against the records (every value ISO) so a bad
    # hand-authored hint can never emit a broken comparison; composed alongside
    # the text/threshold branches (a user may pass a drug name AND ask expiry).
    _dbind = (capir or {}).get("binding") or {}
    _dwin = _dbind.get("date_window_days")
    try:
        _dwin = int(_dwin) if _dwin not in (None, "", 0) else None
    except (TypeError, ValueError):
        _dwin = None
    _dfield = _date_metric_field(records, fields, _dbind.get("date_field")) if _dwin else None
    if _dwin and _dfield:
        date_expr = _la_field(_dfield)
        today_expr = "formatDateTime(utcNow(), 'yyyy-MM-dd')"
        if _dwin > 0:
            cutoff_expr = ("formatDateTime(addDays(utcNow(), " + str(int(_dwin))
                           + "), 'yyyy-MM-dd')")
            date_clause = ("and(lessOrEquals(" + date_expr + ", " + cutoff_expr + "), "
                           "greaterOrEquals(" + date_expr + ", " + today_expr + "))")
        else:
            date_clause = ("and(greater(" + date_expr + ", ''), "
                           "less(" + date_expr + ", " + today_expr + "))")
        where = "or(" + where + ", " + date_clause + ")"

    data_tag = (
        " (public static demo data from the %s adapter; not an official source)."
        % str((live or {}).get("adapter_id"))
        if live and live.get("kind") == "static"
        else (" (live data from " + str((live or {}).get("system") or "your system")
              + ")." if live else
              " data (synthetic demo data - no customer data needed).")
    )
    hit_prefix = _pfx_safe_text(response) + " I found "
    hit_suffix = " matching record(s) in the " + table + data_tag
    if exact_key_required:
        miss_msg = (_pfx_safe_text(response) + " No record matched the requested "
                    + key_field + ". Do not substitute another record. If the user "
                    "supplied an identifier, report it as not found; otherwise ask "
                    "for the required " + key_field + ".")
    else:
        miss_msg = (_pfx_safe_text(response) + " (No row exactly matched that query in the demo "
                    "data.) Tell the user no exact row matched, then label any rows in "
                    "matches_json as synthetic examples rather than results.")
    if facts:
        grounding = " Grounding: " + " | ".join(_pfx_safe_text(f) for f in facts[:4])
        hit_suffix += grounding
        miss_msg += grounding
    # GENERATIVE capability (draft/summarize/translate): the rows are CONTEXT to write from,
    # not the answer. Tell the agent to compose the content directly and NOT enumerate rows,
    # so a "draft a reply" tool doesn't dump sample records at the user.
    if bool(((capir or {}).get("binding") or {}).get("generative")):
        # SHOW DON'T TELL (tag "docfirst", Kody 2026-07-06): the flow RETURNS a
        # pre-composed deliverable draft built from the demo records, so the
        # agent PRESENTS an actual document with actual figures — never "it has
        # been prepared and recorded". The draft is packaging-time deterministic;
        # the agent adapts its wording to the user's specific ask.
        draft = ""
        if records and not live and not exact_key_required:
            lines = ["DELIVERABLE DRAFT - " + _pfx_safe_text(display_name) + ":"]
            for r in records[:6]:
                bits = "; ".join("%s: %s" % (_pfx_safe_text(str(k)), _pfx_safe_text(str(v)))
                                 for k, v in list(r.items())[:6])
                lines.append("* " + bits)
            lines.append("(Draft grounded in the synthetic demo dataset.)")
            draft = " ".join(lines)[:1200]
        provenance_rule = (
            "The rows came from a public static demo adapter, not the external product. "
            "The FIRST sentence must label them static demo context; never claim an "
            "external mutation or official source. "
            if live and live.get("kind") == "static" else
            "The rows came from a live connector. Do not label them synthetic. Cite a source "
            "only when the live rows explicitly include a source URL or document reference. "
            if live else
            "Synthetic demo data is not an official source: your FIRST sentence MUST label it "
            "synthetic demo context, and you must never cite it or emit citation markers. ")
        gen_note = (_pfx_safe_text(response) + " This capability GENERATES written content: "
                    "COMPOSE the requested deliverable NOW and OUTPUT IT IN FULL in your reply, "
                    "using ONLY facts explicitly present in the draft, rows, and received inputs. "
                    "Never invent actions, owners, causes, delivery states, timestamps, or SLAs. "
                    "If a requested detail is absent, say it is unavailable. "
                    + provenance_rule + "Do not turn a "
                    "status into an action, plan, assignment, or owner. Never use assigned, planned, "
                    "or confirmed unless that exact fact appears in the inputs. Never reply that it "
                    "'has been prepared/recorded' - SHOW the document itself, with its figures. "
                    "Do not enumerate raw rows; weave their values into the deliverable. "
                    + draft)
        hit_prefix = gen_note + " ("
        hit_suffix = " context row(s) available.)"
        if not exact_key_required:
            miss_msg = gen_note
    n_matches = "length(body('Filter_matching_records'))"
    message_expr = ("@if(greater(" + n_matches + ", 0), "
                    "concat(" + _la_str(hit_prefix) + ", string(" + n_matches + "), "
                    + _la_str(hit_suffix) + "), " + _la_str(miss_msg) + ")")

    # ---- the data step: static Compose (demo) or the real connector (live).
    # Downstream steps read data_expr, so the two twins differ ONLY here.
    if live:
        data_action = _FLOW_LIVE_DATA_ACTION
        path = "".join("?[%s]" % _la_str(p) for p in (live.get("result_path") or ["body"]))
        data_expr = "coalesce(outputs('%s')%s, json('[]'))" % (data_action, path)
        data_step = {
            "runAfter": {},
            "type": "Http" if _static_http(live) else "OpenApiConnection",
            "inputs": (
                {
                    "method": "GET",
                    "uri": live["full_endpoint_url"],
                    "headers": {
                        "Accept": "application/json",
                        "User-Agent": "RAPP-Static-Industry/1.0",
                    },
                }
                if _static_http(live)
                else {
                    "host": {"apiId": live["apiId"],
                             "connectionName": live["api"],
                             "operationId": live["operation"]},
                    "parameters": dict(live.get("parameters") or {}),
                    # OOTB 1st-party connectors take the platform $authentication
                    # param; custom connectors reject it on save.
                    **({} if live.get("kind") in ("custom", "static")
                       else {"authentication": "@parameters('$authentication')"}),
                }
            ),
            # NOTE: the flow service caps action descriptions at 256 chars
            "description": (((
                             "PUBLIC STATIC DEMO GET - "
                             if live.get("kind") == "static" else "LIVE data step - "
                             ) + str(live.get("display") or "connector")
                             + " '" + str(live.get("operation_label") or live.get("operation"))
                             + "'. It " + str(live.get("setup_hint") or (
                                 "returns deterministic no-PII data and never mutates "
                                 "an external product" if live.get("kind") == "static"
                                 else "needs its REPLACE_ parameters set to your real "
                                      "table/site names"))
                             + "; see the README step for the walkthrough.")[:250]),
        }
    else:
        data_action = _FLOW_STATIC_DATA_ACTION
        data_expr = "outputs('%s')" % data_action
        data_step = {
            "runAfter": {},
            "type": "Compose",
            "inputs": records,
            # NOTE: the flow service caps action descriptions at 256 chars
            "description": ("SYNTHETIC stand-in data from the generated agent.py. To go "
                            "live, replace ONLY this action with the real connector "
                            "(Dataverse List rows / SQL / your API) returning the same "
                            "array shape - downstream steps read this action's outputs."),
        }

    actions = {
        **readme_cards(display_name,
                       live if live else pick_live_connector(
                           capir,
                           description=str((provenance or {}).get("description") or "")),
                       fields, table, bool(live), twin_display, provenance,
                       mirrored, query_prop, thr_prop, metric,
                       [r for r in ((capir or {}).get("binding") or {}).get("records") or []
                        if isinstance(r, dict)],
                       data_action, doc, example_take, fallback_take),
        data_action: data_step,
        "Filter_matching_records": {
            "runAfter": {data_action: ["Succeeded"]},
            "type": "Query",
            "inputs": {"from": "@" + data_expr,
                       "where": "@" + where},
        },
        "Select_result": {
            "runAfter": {"Filter_matching_records": ["Succeeded"]},
            "type": "Compose",
            "inputs": ("@if(greater(" + n_matches + ", 0), "
                       "take(body('Filter_matching_records'), " + str(example_take) + "), "
                       + ("json('[]')" if exact_key_required
                          else "take(" + data_expr + ", " + str(fallback_take) + ")")
                       + ")"),
            "description": ("Exact-key match only; no record substitution."
                            if exact_key_required else
                            "The matched records, else labeled synthetic examples."),
        },
    }
    resp_body = {"message": message_expr,
                 "matches_json": "@string(outputs('Select_result'))",
                 "match_count": "@" + n_matches,
                 "required_identifier": key_field if exact_key_required else "",
                 "data_provenance": (
                     "public_static_demo"
                     if live and live.get("kind") == "static"
                     else "live_connector" if live else "synthetic_demo"
                 ),
                 # traceability: echo the exact inputs this flow RECEIVED, so a
                 # dropped/renamed param is visible at this hop (run history +
                 # the calling agent both see it).
                 "received_inputs": "@string(triggerBody())"}
    resp_props = {
        "message": {"title": "message", "type": "string", "x-ms-dynamically-added": True},
        "matches_json": {"title": "matches_json", "type": "string", "x-ms-dynamically-added": True},
        "match_count": {"title": "match_count", "type": "number", "x-ms-dynamically-added": True},
        "required_identifier": {"title": "required_identifier", "type": "string",
                                "x-ms-dynamically-added": True},
        "data_provenance": {"title": "data_provenance", "type": "string",
                            "x-ms-dynamically-added": True},
        "received_inputs": {"title": "received_inputs", "type": "string",
                            "x-ms-dynamically-added": True},
    }
    respond_after = "Select_result"
    if doc and fields:
        # build "f1: v1 | f2: v2 | ..." per record (fields are known statically)
        parts = []
        for i, f in enumerate(fields):
            if i:
                parts.append("' | '")
            parts.append(_la_str(f + ": "))
            parts.append("string(" + _la_field(f) + ")")
        line = "concat(" + ", ".join(parts) + ")"
        actions["Select_document_lines"] = {
            "runAfter": {"Select_result": ["Succeeded"]},
            "type": "Select",
            "inputs": {"from": "@take(outputs('Select_result'), " + str(pdf_records) + ")",
                       "select": "@" + line},
            "description": f"The lines of the {doc} document, from the selected records."[:250],
        }
        # a REAL newline (json.dumps encodes it; WDL literals have no backslash
        # escapes, so '\\n' would join with the two-character text backslash+n)
        resp_body["document_text"] = "@join(body('Select_document_lines'), '\n')"
        resp_props["document_text"] = {"title": "document_text", "type": "string",
                                       "x-ms-dynamically-added": True}
        respond_after = "Select_document_lines"
    actions["Respond_to_the_agent"] = {
        "runAfter": {respond_after: ["Succeeded"]},
        "type": "Response",
        "kind": "Skills",
        "inputs": {"statusCode": 200, "body": resp_body,
                   "schema": {"type": "object", "properties": resp_props}},
    }

    # live twin: bind the data action to its connection reference (key must
    # exactly equal host.connectionName), and declare $connections — the shape
    # real connector-bearing exports use. Demo twin stays connector-free.
    conn_refs = {}
    definition_params = {
        "$authentication": {"defaultValue": {}, "type": "SecureObject"},
    }
    if live and not _static_http(live):
        ref = {"runtimeSource": "embedded",
               "connection": {"connectionReferenceLogicalName": live["conn_ref_logical"]},
               "api": {"name": live["api"]}}
        if live.get("impersonation"):
            ref["impersonation"] = {}
        conn_refs[live["api"]] = ref
        definition_params["$connections"] = {"defaultValue": {}, "type": "Object"}

    return {
        "properties": {
            "connectionReferences": conn_refs,
            "definition": {
                "$schema": "https://schema.management.azure.com/providers/"
                           "Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
                "contentVersion": "1.0.0.0",
                "parameters": definition_params,
                "triggers": {
                    "manual": {
                        "type": "Request",
                        "kind": "Skills",
                        "inputs": {"schema": {"type": "object",
                                              "properties": trig_props,
                                              "required": required}},
                    },
                },
                "actions": actions,
                "outputs": {},
            },
            "templateName": None,
        },
        "schemaVersion": _FLOW_SCHEMA_VERSION,
    }


def capir_flow_tool_yaml(display_name: str, description: str, flow_guid: str,
                         capir: dict, params=None, live: Optional[dict] = None) -> str:
    """The sub-agent's TOOL wiring for its deterministic flow: a TaskDialog
    whose action is InvokeFlowTaskAction — the generative-orchestration tool
    shape, verbatim per real exports (AutomaticTaskInput descriptions guide the
    model's slot filling; input/output property names bind to the flow's
    trigger/response schema keys; outputMode All returns every output).

    The tool's inputs are built by the SAME flow_trigger_inputs used for the
    flow's trigger schema, so this hop passes exactly the params the agent.py
    declares — names and descriptions match at every hop by construction."""
    records, fields, metric, _facts, doc, _consts, table, _response = _capir_flow_features(capir)
    prompt = None
    for slot in (capir or {}).get("slots") or []:
        prompt = slot.get("prompt"); break
    desc = (description or f"Deterministic handler for {display_name}.")
    binding = (capir or {}).get("binding") or {}
    is_write = bool(binding.get("write")) or bool((live or {}).get("write")) or str(
        binding.get("operation") or "").lower() in (
            "create", "add", "store", "write", "insert", "upsert", "save")
    write_and_generate = bool(is_write and binding.get("generative"))
    data_tag = ((" records (live " + str((live or {}).get("system") or "connector")
                 + " data)") if live else " records (synthetic demo data)")
    if is_write:
        desc += (" Performs the packaged action and returns message / action_status / "
                 "receipt / compose_required / deliverable_context / data_provenance / "
                 "received_inputs. A simulated status means no external system changed.")
        if live and live.get("kind") == "static":
            desc += " The public static GET also returns idempotency_key evidence."
    else:
        desc += (" Runs the packaged flow over the " + table + data_tag
                 + " and returns message / matches_json / match_count / "
                 "required_identifier / data_provenance / received_inputs"
                 + (" / document_text" if doc and fields else "") + ".")
    trig_props, req, query_prop, thr_prop, mirrored = flow_trigger_inputs(
        params, display_name, metric)

    _tool_defaults = {re.sub(r"[^A-Za-z0-9_]", "", str(p[0])):
                      (p[4] if isinstance(p, (list, tuple)) and len(p) > 4 else None)
                      for p in (params or []) if isinstance(p, (list, tuple)) and p}

    def _input_yaml(name, pdesc, force_automatic=False):
        # REQUIRED inputs stay model-filled (AutomaticTaskInput). OPTIONAL inputs get
        # the agent.py's OWN fallback default as a fixed value (ManualTaskInput), so the
        # sub-agent calls the flow immediately with the same defaults perform() uses
        # instead of prompting. Mirrors the ManualTaskInput+value shape of real exports.
        if name in req or force_automatic:
            return ("  - kind: AutomaticTaskInput\n"
                    "    propertyName: " + name + "\n"
                    "    description: " + _yaml_dq(pdesc) + "\n")
        t = (trig_props.get(name) or {}).get("type", "string")
        return ("  - kind: ManualTaskInput\n"
                "    propertyName: " + name + "\n"
                "    value: " + _manual_value_token(_tool_defaults.get(name), t) + "\n")

    inputs = "inputs:\n"
    emitted = set()
    for name, pdesc in mirrored:
        inputs += _input_yaml(
            name, pdesc,
            # Generate-and-send actions need every textual field (recipient,
            # subject, body, message, etc.) model-filled. Fixing only the first
            # string/query param silently left the actual body empty.
            force_automatic=bool(
                write_and_generate
                and (trig_props.get(name) or {}).get("type") == "string"))
        emitted.add(name)
    if query_prop not in emitted:
        inputs += _input_yaml(
            query_prop,
            prompt or f"The keyword, id, or value to filter the {display_name} records on.",
            # A draft-and-send capability must let the model pass its composed
            # content; a fixed empty ManualTaskInput makes the action unusable.
            force_automatic=write_and_generate)
    if thr_prop and thr_prop not in emitted:   # compiler-added threshold (optional -> fixed 0)
        inputs += _input_yaml(thr_prop, "numeric threshold")
    outputs = "outputs:\n  - propertyName: message\n"
    if is_write:
        outputs += (
            "  - propertyName: action_status\n"
            "  - propertyName: receipt\n"
        )
        if live and live.get("kind") == "static":
            outputs += "  - propertyName: idempotency_key\n"
        outputs += (
            "  - propertyName: compose_required\n"
            "  - propertyName: deliverable_context\n"
            "  - propertyName: data_provenance\n"
            "  - propertyName: received_inputs\n"
        )
    else:
        outputs += (
            "  - propertyName: matches_json\n"
            "  - propertyName: match_count\n"
            "  - propertyName: required_identifier\n"
            "  - propertyName: data_provenance\n"
            "  - propertyName: received_inputs\n")
    if not is_write and doc and fields:
        outputs += "  - propertyName: document_text\n"
    return ("kind: TaskDialog\n"
            "modelDisplayName: " + _yaml_display_safe(capir_flow_name(display_name)) + "\n"
            "modelDescription: |-\n"
            + _indent(desc.strip(), 2) + "\n"
            + inputs
            + outputs +
            "action:\n"
            "  kind: InvokeFlowTaskAction\n"
            "  flowId: " + str(flow_guid) + "\n"
            "outputMode: All")


@dataclass
class SubAgentSpec:
    """One connected sub-agent (one agent.py promoted to its own bot)."""
    agent_name: str           # e.g. "loanoriginationassistant"
    display_name: str         # e.g. "Loan Origination Assistant"
    description: str          # routing description the orchestrator selects on
    instructions: str         # the sub-agent's gpt.default instruction blob
    # The capability's compiled CapIR (t2p-capir/1.0), records already injected.
    # When present, the packager emits a REAL deterministic topic INSIDE this
    # sub-agent that runs the same steps as the converted agent.py's perform(),
    # instead of leaving the behavior to the gpt.default instruction blob. The
    # instructions remain as the persona/router fallback.
    capir: Optional[dict] = None
    # The source agent.py's perform() params [(name, description, required), ...],
    # declared as typed INPUTS on the orchestrator's connected-agent action so the
    # Copilot Studio orchestrator passes them when it delegates (the agent's
    # "Inputs" panel) — the contract, structurally, not just in the description.
    params: Optional[list] = None
    # A handwritten agent.py's perform() source. When present, the sub-agent's
    # instructions gain a CODE INTERPRETER recipe: reproduce this computation in
    # Copilot Studio's Python sandbox over the records the deterministic flow
    # returns — the flow stays the untouched deterministic data layer; the code
    # interpreter mirrors the agent.py's real math (scores, rankings, documents).
    compute_source: Optional[str] = None
    # DEMO-twin reference material (tag "refmat"): a short, LLM-authored (with a
    # deterministic fallback) domain briefing grounded in THIS capability's own
    # shipped records, so the demo child bot can answer "why/what does this mean"
    # questions about the SAME synthetic entries its flow returns. The packager
    # embeds it as a trailing gpt.default section ONLY on the DEMO twin (a bot
    # written with name_suffix set); the LIVE twin and the orchestrator never
    # carry it. Empty by default — opt-in data the pipeline supplies, never
    # fabricated for an authored/verbatim sub-agent at the packager layer.
    reference_material: str = ""


@dataclass
class ConnectedSolutionSpec:
    """A single solution bundling an orchestrator + N connected sub-agents."""
    solution_unique_name: str
    solution_display_name: str
    orchestrator_display_name: str
    subagents: List[SubAgentSpec]
    orchestrator_instructions: str = ""   # synthesized if empty
    publisher_prefix: str = "rapp"
    publisher_unique_name: str = "DefaultPublisher"
    publisher_display_name: str = "Default Publisher"
    solution_version: str = "1.0.0.0"
    managed: bool = False
    orchestrator_schema_suffix: str = "orchestrator"
    # When True the orchestrator auto-publishes on import. Leave False so the
    # import itself never depends on the (slower, fail-prone) publish step.
    orchestrator_publish_on_import: bool = False
    # When True the orchestrator declares MsTeams + M365 Copilot channels. This
    # requires a maker-portal publish (headless `pac copilot publish` 409s on the
    # channel registration). Default False = fully headlessly publishable.
    orchestrator_channels: bool = False
    # How a sub-agent's CapIR becomes deterministic behavior:
    #   "flow"  (default) — a solution-packaged agent flow ("workflow" in the
    #           Copilot Studio UI: Skills trigger + Respond to the agent) wired
    #           to the sub-agent as a TOOL. Forward-looking: topics are being
    #           deprecated in favor of flows.
    #   "topic" — the legacy deterministic OnRecognizedIntent topic.
    capability_mode: str = "flow"
    # Topology of the emitted solution:
    #   "hierarchical" (default) — orchestrator + one connected GENERATIVE child
    #           bot per agent (each child owns its capability flow tool). This is
    #           the Copilot Studio "connected agents" feature — a SECOND reasoning
    #           layer per agent that can re-plan, prompt the user, and re-synthesize.
    #   "flat" — ONE generative orchestrator with every agent's capability flow
    #           attached DIRECTLY as an InvokeFlowTaskAction tool; no child bots.
    #           This matches the brainstem's execution model EXACTLY: a single
    #           reasoning layer (soul.md loop) calling deterministic flow tools
    #           (perform() functions) that always run to completion and never pause
    #           to prompt. One-size-fits-all — every agent is the same shape.
    topology: str = "hierarchical"
    # workflow.modernflowtype: 1 = Copilot Studio agent flow (what the Copilot
    # Studio UI calls a "flow"/"workflow", billed to Copilot Studio capacity —
    # the default), 0 = classic Power Automate cloud flow. Both use the same
    # agent-callable Skills trigger; only billing/surfacing differ.
    flow_type: int = 1
    # LIVE twin: each capability flow's data step is a REAL connector action
    # (OOTB 1st-party from LIVE_CONNECTOR_CATALOG, or a packaged custom-
    # connector scaffold for systems without one) through a connection
    # reference. Flows ship DRAFT (activation needs the customer to bind
    # connections — expected, that IS the hook-into-your-data step).
    live_connectors: bool = False
    # Public no-PII adapter mode. False leaves all existing connector selection
    # and package output unchanged.
    static_connectors: bool = False
    # Static adapter runtime: built-in connectionless HTTP (default) or the
    # packaged no-auth custom connector (requires manual connection binding).
    static_transport: Optional[str] = None
    catalog_agent_id: str = ""
    # The companion solution's display name, cross-referenced in every flow's
    # README Compose ("the live twin is ..." / "the demo fallback is ...").
    twin_display_name: str = ""
    # Display-name suffix for this solution's bots + flows (" (Demo)") so the
    # two twins are tellable apart in the Copilot Studio agent list.
    name_suffix: str = ""


class ConnectedSolutionPackager:
    """Assembles a multi-bot connected-agent solution zip from a spec."""

    def __init__(self, spec: ConnectedSolutionSpec):
        self.spec = spec
        spec.static_transport = normalize_static_transport(
            bool(getattr(spec, "static_connectors", False)),
            getattr(spec, "static_transport", None),
        )
        # topology='flat' has no child-bot path, so the legacy deterministic TOPIC
        # writer (which lives only on that path) never runs and _flow_ids stays
        # empty in topic mode: the solution would ship ZERO deterministic
        # capabilities while its orchestrator still advertises them. Fail loudly —
        # this __init__ is the single source of truth every caller funnels through.
        if (getattr(spec, "topology", "hierarchical") == "flat"
                and getattr(spec, "capability_mode", "flow") == "topic"):
            raise ValueError("topology='flat' does not support capability_mode='topic'; "
                             "use capability_mode='flow'")
        # Scrub XML/YAML-invalid control characters from every string that can
        # reach an emitted part, once, at the single entry point every caller
        # funnels through (mutating the spec, like publisher_prefix below).
        for k, v in vars(spec).items():
            if k != "subagents":
                setattr(spec, k, _ctrl_clean_tree(v))
        for sub in spec.subagents:
            for k, v in vars(sub).items():
                setattr(sub, k, _ctrl_clean_tree(v))
        # publisher_prefix is the one untamed length input feeding the schema caps
        # below; bound it to Dataverse's 8-char prefix limit so no schema exceeds
        # MAX_SCHEMA for ANY direct caller (perform() already caps it). Mutate the
        # spec too so the CustomizationPrefix stays consistent with the schemas.
        spec.publisher_prefix = spec.publisher_prefix[:8]
        prefix = spec.publisher_prefix

        # Connected-agent components are named
        #   {orch_schema}.InvokeConnectedAgentTaskAction.{Action}
        # and the full schema name must stay within Dataverse's 100-char limit.
        # Cap the orchestrator schema (reserving room for the action suffix) so a
        # long stack name can never push a component name over the limit.
        suffix = spec.orchestrator_schema_suffix
        base = re.sub(r"stack$", "", _sanitize_schema(spec.solution_unique_name)) or "agents"
        orch = f"{prefix}_{base}{suffix}"
        max_orch = MAX_SCHEMA - len(_CONNECTED_INFIX) - _MIN_ACTION_BUDGET   # 42
        if len(orch) > max_orch:
            keep = max(4, max_orch - len(prefix) - 1 - len(suffix))
            orch = f"{prefix}_{base[:keep]}{suffix}"
        self.orch_schema = orch
        # Whatever room is left after the (capped) orchestrator schema + infix.
        self._action_budget = MAX_SCHEMA - len(_CONNECTED_INFIX) - len(self.orch_schema)

        # Assign a unique schema name + connected-action name to each sub-agent.
        self._children = []  # list of (SubAgentSpec, child_schema, action_name)
        seen_schemas = {self.orch_schema}
        seen_actions = set()
        # Children need room for a ".topic.<Name>" suffix within MAX_SCHEMA. The
        # orchestrator schema is capped above; children were NOT, so a long
        # solution + capability name overflowed the Dataverse 100-char limit.
        child_base_max = max(4, MAX_SCHEMA - 35 - len(prefix) - 1)
        # A twin solution (name_suffix set, e.g. " (Demo)") must mint DISTINCT
        # child schemas — the agent_name alone is shared with its twin, and a
        # colliding schema would make the second import overwrite the first
        # twin's bots. The sanitized suffix salts every child schema.
        salt = _sanitize_schema(getattr(spec, "name_suffix", "") or "")
        for sub in spec.subagents:
            base = (_sanitize_schema(sub.agent_name) or "agent")[:child_base_max]
            if salt:
                base = base[: max(4, child_base_max - len(salt))] + salt
            child_schema = f"{prefix}_{base}"
            n = 2
            while child_schema in seen_schemas:
                child_schema = f"{prefix}_{base}{n}"
                n += 1
            seen_schemas.add(child_schema)

            pascal = _pascal(sub.display_name or sub.agent_name) or "Agent"
            action = pascal[: self._action_budget]
            n = 2
            while action in seen_actions:
                tag = str(n)
                action = pascal[: max(1, self._action_budget - len(tag))] + tag
                n += 1
            seen_actions.add(action)

            self._children.append((sub, child_schema, action))

        # Deterministic WorkflowId per capability flow (capability_mode="flow"):
        # keyed by child schema so re-imports update instead of duplicate.
        self._flow_ids = {}
        # (tool botcomponent schemaname, workflow id) pairs collected while the
        # bots are written — declared in Assets/botcomponent_workflowset.xml.
        self._flow_tool_links: List[tuple] = []
        if getattr(spec, "capability_mode", "flow") != "topic":
            for sub, child_schema, _action in self._children:
                if sub.capir:
                    self._flow_ids[child_schema] = capir_flow_guid(
                        spec.solution_unique_name, child_schema)

        # LIVE twin: resolve every capability's data source ONCE, solution-wide.
        # One connection reference per distinct connector api (real exports share
        # them across flows); one custom-connector scaffold per distinct system
        # that has no 1st-party connector.
        self._live_by_child: Dict[str, dict] = {}   # child_schema -> live wiring
        self._conn_refs: Dict[str, dict] = {}       # api key -> conn ref info
        self._custom_connectors: Dict[str, dict] = {}  # connector name -> info
        self._static_warnings: List[str] = []
        if getattr(spec, "live_connectors", False) and self._flow_ids:
            sol = spec.solution_unique_name
            for sub, child_schema, _action in self._children:
                if child_schema not in self._flow_ids:
                    continue
                live = None
                if getattr(spec, "static_connectors", False):
                    live, warning = resolve_static_connector(
                        sub.capir,
                        capability_name=sub.display_name or sub.agent_name,
                        description=getattr(sub, "description", "") or "",
                        catalog_agent_id=getattr(spec, "catalog_agent_id", "") or "",
                    )
                    if warning:
                        self._static_warnings.append(warning)
                if live is None:
                    live = pick_live_connector(
                        sub.capir,
                        description=getattr(sub, "description", "") or "",
                    )
                if live["kind"] == "static":
                    binding = (sub.capir or {}).get("binding") or {}
                    if live.get("catalog_write_intent") is not None:
                        binding = {
                            **binding,
                            "write": bool(live.get("catalog_write_intent")),
                        }
                        if live.get("catalog_write_intent") is False:
                            binding.pop("operation", None)
                        sub.capir = {**(sub.capir or {}), "binding": binding}
                    is_write = bool(binding.get("write")) or str(
                        binding.get("operation") or ""
                    ).lower() in (
                        "create", "add", "store", "write", "insert", "upsert", "save"
                    )
                    adapter = live["adapter_id"]
                    norm = "static:" + adapter
                    cc = self._custom_connectors.get(norm)
                    if cc is None:
                        frag = _sanitize_connector_name(adapter, fallback="staticapi")[:24]
                        conn_name = _sanitize_connector_name(
                            f"{prefix}_static_{frag}", fallback="staticconnector"
                        )
                        guid = str(uuid.uuid5(
                            uuid.NAMESPACE_URL, f"t2p-static-connector://{sol}/{adapter}"
                        ))
                        api_hash = hashlib.sha1(
                            f"{prefix}|{sol}|static|{adapter}".encode()
                        ).hexdigest()[:16]
                        api_name = (
                            "shared_" + conn_name.replace("_", "-5f") + "-5f" + api_hash
                        )
                        cc = self._custom_connectors.setdefault(norm, {
                            "static": True,
                            "guid": guid,
                            "api_name": api_name,
                            "conn_name": conn_name,
                            "display": live["display"][:30],
                            "description": (
                                "Public no-PII static adapter for %s. All actions are GET; "
                                "receipt actions simulate writes and never mutate an external product."
                                % live["system"]
                            ),
                            "system": live["system"],
                            "adapter_id": adapter,
                            "operations": [],
                        })
                    existing = {
                        (item["path"], item["operation_id"])
                        for item in cc["operations"]
                    }
                    for operation in _static_swagger_operations(live):
                        marker = (operation["path"], operation["operation_id"])
                        if marker not in existing:
                            cc["operations"].append(operation)
                            existing.add(marker)
                    operations = _static_swagger_operations(live)
                    selected_kind = "receipt" if is_write else "collection"
                    selected = next(item for item in operations if item["kind"] == selected_kind)
                    live.update(
                        write=is_write,
                        apiId="/providers/Microsoft.PowerApps/apis/" + cc["api_name"],
                        api=cc["api_name"],
                        operation=selected["operation_id"],
                        operation_label=selected["summary"],
                        endpoint_path=selected["path"],
                        result_path=["body"] if is_write else ["body", "value"],
                        connector_guid=cc["guid"],
                        connector_name=cc["conn_name"],
                        receipt_path=["body", "receipt"],
                        static_transport=spec.static_transport,
                        packaged_connector=cc["conn_name"],
                    )
                    live["full_endpoint_url"] = _static_endpoint_url(live)
                    live["connection_binding_required"] = (
                        spec.static_transport == "connector"
                    )
                    ref_key = cc["api_name"]
                    connector_id = "/providers/Microsoft.PowerApps/apis/" + cc["api_name"]
                    custom_guid = cc["guid"]
                    ref_display = cc["display"] + " " + sol
                elif live["kind"] == "custom":
                    # Deterministic custom-connector identity keyed on the EXACT
                    # system name (normalized: casefolded, whitespace-collapsed).
                    # The SAME system shares ONE connector on purpose; two DIFFERENT
                    # systems must NOT merge — even when their sanitized fragments
                    # share the first 24 chars, or both sanitize to nothing (unicode-
                    # only names). So we register by the normalized system and, when a
                    # new system's visible fragment collides with an already-registered
                    # different one, re-mint the fragment with a deterministic hash of
                    # the normalized system (sha1 -> no randomness, stable re-imports).
                    # SEMANTIC key (tag "connunify", observed live 2026-07-06):
                    # the distiller may spell ONE system two ways across
                    # capabilities — "SAP Analytics Cloud (SAC)" and "SAP
                    # Analytics Cloud" — and two spellings minted two connector
                    # identities; the import then died with connector 'Does Not
                    # Exist' on the second. Normalize away parenthesized
                    # acronyms/punctuation so one real system = ONE connector;
                    # genuinely different systems still key apart.
                    norm = " ".join(re.sub(
                        r"[^a-z0-9]+", " ",
                        re.sub(r"\([^)]*\)", " ", str(live["system"]).casefold())).split())
                    cc = self._custom_connectors.get(norm)
                    _records, cfields, cmetric, *_rest = _capir_flow_features(sub.capir)
                    ctrig_props, _creq, _cq, _ct, _cm = flow_trigger_inputs(
                        sub.params, sub.display_name, cmetric)
                    if cc is None:
                        # NAME minted from the (messy) source system -> forced
                        # through the ONE sanitizer so it ALWAYS satisfies
                        # ^[A-Za-z0-9][A-Za-z0-9_-]*$ (the LIVE-twin import rule the
                        # parentheses in "(SAC)" otherwise trip). frag caps at 24 so
                        # the assembled {prefix}_<frag>api stays short; the whole
                        # name is re-sanitized to collapse any prefix/suffix seam.
                        frag = _sanitize_connector_name(
                            live["system"], fallback="customapi")[:24]
                        conn_name = _sanitize_connector_name(
                            f"{prefix}_{frag}api", fallback="connector")
                        if conn_name in {c["conn_name"] for c in self._custom_connectors.values()}:
                            # two DIFFERENT systems collided on the visible fragment
                            # -> re-mint with a deterministic sha1 of the normalized
                            # system (stable re-imports, no randomness), still sanitized.
                            frag = _sanitize_connector_name(
                                live["system"], fallback="customapi")[:18] + hashlib.sha1(
                                norm.encode("utf-8")).hexdigest()[:6]
                            conn_name = _sanitize_connector_name(
                                f"{prefix}_{frag}api", fallback="connector")
                        guid = str(uuid.uuid5(uuid.NAMESPACE_URL,
                                              f"t2p-connector://{sol}/{conn_name}"))
                        api_hash = hashlib.sha1(
                            f"{prefix}|{sol}|{conn_name}".encode()).hexdigest()[:16]
                        # Power Platform's runtime api id: shared_ + name('_'->'-5f') + -5f<hash>
                        api_name = "shared_" + conn_name.replace("_", "-5f") + "-5f" + api_hash
                        cc = self._custom_connectors.setdefault(norm, {
                            "guid": guid, "api_name": api_name, "conn_name": conn_name,
                            "display": live["display"][:30],
                            "description": (f"Custom connector scaffold for {live['system']} - set "
                                            "Host to your API endpoint; GET /records returns the record "
                                            "array reads expect, POST /records creates a record for writes."),
                            "system": live["system"], "fields": list(cfields or []),
                            "records": [r for r in ((sub.capir or {}).get("binding") or {}).get("records") or []][:1],
                            "write_inputs": {},
                        })
                    if live.get("write"):
                        cc.setdefault("write_inputs", {}).update(
                            {name: dict(schema or {}) for name, schema in ctrig_props.items()})
                    conn_name = cc["conn_name"]
                    api_name = cc["api_name"]
                    live.update(apiId="/providers/Microsoft.PowerApps/apis/" + api_name,
                                api=api_name,
                                operation=("CreateRecord" if live.get("write") else "GetRecords"),
                                connector_guid=cc["guid"], connector_name=conn_name)
                    ref_key = api_name
                    connector_id = "/providers/Microsoft.PowerApps/apis/" + api_name
                    custom_guid = cc["guid"]
                    ref_display = cc["display"] + " " + sol
                else:
                    live.update(apiId="/providers/Microsoft.PowerApps/apis/" + live["api"])
                    ref_key = live["api"]
                    connector_id = "/providers/Microsoft.PowerApps/apis/" + live["api"]
                    custom_guid = None
                    ref_display = live["display"] + " " + sol
                if not _static_http(live):
                    ref = self._conn_refs.setdefault(ref_key, {
                        "logical": "%s_%s_%s" % (
                            prefix, re.sub(r"[^a-z0-9]", "", ref_key.lower())[:38],
                            hashlib.sha1(f"{sol}|{ref_key}".encode()).hexdigest()[:5]),
                        "connector_id": connector_id, "display": ref_display[:100],
                        "custom_guid": custom_guid,
                    })
                    live["conn_ref_logical"] = ref["logical"]
                else:
                    live["conn_ref_logical"] = None
                self._live_by_child[child_schema] = live

        # LIVE twin: Work IQ MCP tools ("skills") for sub-agents whose own
        # description evidences that work (mail/people/M365). Planned here
        # because their connection references land in customizations.xml,
        # which package() writes before the bots. Shapes per the cliagent
        # template: <bot>.tool.<Name>_<salt> component + <bot>.cr.<api>.<hash>
        # bot-scoped connection reference + the M:N set entry.
        self._mcp_by_child: Dict[str, list] = {}
        self._mcp_conn_refs: List[dict] = []
        self._conn_ref_links: List[tuple] = []   # (component schema, ref logical)
        # FLAT topology has no child bots, so per-sub-agent MCP "skill" tools have
        # nowhere to attach — emitting their conn-ref links would leave the
        # connection-reference set pointing at a .tool. component that is never
        # written (import fails with an unresolved reference). Skip them in flat.
        if getattr(spec, "live_connectors", False) and getattr(spec, "topology", "hierarchical") != "flat":
            for sub, child_schema, _action in self._children:
                hits = match_mcp_tools(" ".join(
                    [sub.display_name or "", sub.description or "", sub.agent_name or ""]))
                tools = []
                for t in hits:
                    salt = hashlib.sha1(
                        f"{child_schema}|{t['api']}".encode()).hexdigest()[:3]
                    comp_schema = f"{child_schema}.tool.{t['key']}_{salt}"[:100]
                    ref_logical = "%s.cr.%s.%s" % (
                        child_schema, t["api"],
                        hashlib.sha1(f"{spec.solution_unique_name}|{child_schema}|{t['api']}"
                                     .encode()).hexdigest())
                    tools.append({**t, "component_schema": comp_schema,
                                  "conn_ref_logical": ref_logical})
                    self._mcp_conn_refs.append({
                        "logical": ref_logical,
                        "connector_id": "/providers/Microsoft.PowerApps/apis/" + t["api"],
                        "display": ref_logical, "custom_guid": None})
                    self._conn_ref_links.append((comp_schema, ref_logical))
                if tools:
                    self._mcp_by_child[child_schema] = tools

    # -- public ----------------------------------------------------------

    def package(self, output_path: Optional[Path] = None) -> bytes:
        buf = io.BytesIO()
        overrides: List[str] = []  # /data parts for [Content_Types].xml

        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1. Deterministic capability flows ("workflows"): one Copilot
            #    Studio-callable flow per sub-agent CapIR, packaged as real
            #    Workflow components (declared in customizations.xml +
            #    RootComponents, definition under /Workflows). Zero connection
            #    references — the static-data Compose stands in for the live
            #    connector, so import has no connection dependency.
            workflow_elements, root_components = [], []
            live_mode = bool(getattr(self.spec, "live_connectors", False))
            suffix = getattr(self.spec, "name_suffix", "") or ""
            twin = getattr(self.spec, "twin_display_name", "") or ""
            for sub, child_schema, _action in self._children:
                flow_id = self._flow_ids.get(child_schema)
                if not flow_id:
                    continue
                live = self._live_by_child.get(child_schema)
                name = capir_flow_name(sub.display_name + suffix)
                if live:
                    if _static_http(live):
                        desc = (
                            f"Deterministic {sub.display_name} capability - active "
                            "transport http calls the pinned public static endpoint with "
                            "zero connection binding. The packaged typed connector is the "
                            "migration contract for switching to a connector or real API."
                        )
                    else:
                        desc = (f"Deterministic {sub.display_name} capability - runs the same "
                                "steps as the generated agent.py over LIVE "
                                + str(live.get("system") or "connector") + " data. Bind the "
                                "connection reference, set the REPLACE_ parameters, then "
                                "turn the flow on.")
                else:
                    desc = (f"Deterministic {sub.display_name} capability - runs the same "
                            "steps as the generated agent.py over seeded synthetic data. "
                            "Swap the Get_records_STATIC_DATA Compose for the real "
                            "connector to go live.")
                fname = flow_json_file_name(name, flow_id)
                zf.writestr(
                    "Workflows/" + fname,
                    json.dumps(capir_flow_definition(
                        sub.display_name, sub.capir,
                        params=getattr(sub, "params", None),
                        live=live, twin_display=twin,
                        provenance={"agent_file": sub.agent_name,
                                    "description": sub.description}),
                               ensure_ascii=False, indent=2),
                )
                workflow_elements.append(WORKFLOW_ELEMENT_XML.format(
                    workflow_id=flow_id, name=_xml_escape(name),
                    description=_xml_escape(desc), json_file_name=fname,
                    version=self.spec.solution_version,
                    # Connectionless static HTTP and demo flows can activate on
                    # import; connector-backed live flows remain Draft.
                    state_code=0 if live and not _static_http(live) else 1,
                    status_code=1 if live and not _static_http(live) else 2,
                    modern_flow_type=int(getattr(self.spec, "flow_type", 1))))
                root_components.append(_WORKFLOW_ROOT_COMPONENT.format(workflow_id=flow_id))

            # 1b. LIVE twin artifacts: connection references (customizations) +
            #     custom-connector scaffolds (Connector/ files, type-372 roots).
            #     Flow-level refs AND the bot-scoped Work IQ MCP tool refs.
            conn_ref_xml, connectors_xml = "", ""
            all_refs = list(self._conn_refs.values()) + self._mcp_conn_refs
            if all_refs:
                conn_ref_xml = "\n".join(CONNECTION_REFERENCE_XML.format(
                    logical_name=ref["logical"],
                    display_name=_xml_escape(ref["display"]),
                    connector_id=ref["connector_id"],
                    custom_connector_element=(
                        CUSTOM_CONNECTOR_ID_ELEMENT.format(connector_guid=ref["custom_guid"])
                        if ref.get("custom_guid") else ""),
                ) for ref in all_refs)
            if self._custom_connectors:
                elements = []
                # keyed on the normalized system now, so read the visible connector
                # name from the entry (cc["conn_name"]), not the dict key.
                for cc in self._custom_connectors.values():
                    conn_name = cc["conn_name"]
                    elements.append(CONNECTOR_ELEMENT_XML.format(
                        connector_guid=cc["guid"],
                        description=_xml_escape(cc["description"]),
                        display_name=_xml_escape(cc["display"]),
                        encoded_name=conn_name))
                    zf.writestr(f"Connector/{conn_name}_openapidefinition.json",
                                _custom_connector_swagger(cc))
                    zf.writestr(f"Connector/{conn_name}_connectionparameters.json", "{}")
                    zf.writestr(f"Connector/{conn_name}_policytemplateinstances.json", "[]")
                    zf.writestr(f"Connector/{conn_name}_iconblob.Png",
                                base64.b64decode(DEFAULT_ICON_BASE64))
                    root_components.append(_CONNECTOR_ROOT_COMPONENT.format(
                        connector_guid=cc["guid"], encoded_name=conn_name))
                connectors_xml = ("\n  <Connectors>\n" + "\n".join(elements)
                                  + "\n  </Connectors>")
                overrides.append('<Default Extension="Png" ContentType="application/octet-stream" />')

            # 2. solution + customizations (workflow declarations included)
            zf.writestr("solution.xml", self._solution_xml(root_components))
            zf.writestr(
                "customizations.xml",
                CUSTOMIZATIONS_XML_NATIVE.format(
                    connectors=connectors_xml,
                    connection_references=conn_ref_xml,
                    workflows=("\n" + "\n".join(workflow_elements) + "\n  ")
                              if workflow_elements else "",
                ),
            )

            # 3. Orchestrator bot (router) — instructions list the sub-agents
            self._write_bot(
                zf,
                bot_schema=self.orch_schema,
                display_name=self.spec.orchestrator_display_name,
                instructions=self._orchestrator_instructions(),
                overrides=overrides,
                is_orchestrator=True,
                name_suffix=suffix,
            )

            if getattr(self.spec, "topology", "hierarchical") == "flat":
                # FLAT (brainstem-faithful): NO child bots, NO connected-agent layer.
                # Every agent's deterministic capability flow is attached DIRECTLY to
                # the single orchestrator as an InvokeFlowTaskAction tool — one
                # reasoning layer calling deterministic tools that never prompt,
                # exactly like the brainstem soul loop calling perform() functions.
                for sub, child_schema, _action in self._children:
                    fg = self._flow_ids.get(child_schema)
                    if fg:
                        self._write_flow_tool(
                            zf, self.orch_schema, sub.display_name, sub.capir, fg,
                            getattr(sub, "params", None),
                            self._live_by_child.get(child_schema), overrides)
            else:
                # 4. Connected-agent delegation components (under the orchestrator)
                for sub, child_schema, action in self._children:
                    self._write_connected_action(
                        zf, sub, child_schema, action, overrides
                    )

                # 5. Each sub-agent as its own connectable bot — carrying its REAL
                #    deterministic capability (1:1 with its agent.py) when a CapIR
                #    is present: the flow TOOL wiring (default) or the legacy topic.
                for sub, child_schema, _action in self._children:
                    self._write_bot(
                        zf,
                        bot_schema=child_schema,
                        display_name=sub.display_name,
                        instructions=sub.instructions,
                        overrides=overrides,
                        capir=sub.capir,
                        flow_guid=self._flow_ids.get(child_schema),
                        compute_source=getattr(sub, "compute_source", None),
                        params=getattr(sub, "params", None),
                        live=self._live_by_child.get(child_schema),
                        name_suffix=suffix,
                        description=sub.description or "",
                        reference_material=getattr(sub, "reference_material", "") or "",
                    )

            # 6. The botcomponent <-> connection reference M:N set: links each
            #    Work IQ MCP tool component to its bot-scoped reference (empty
            #    for the demo twin — its flows ship connector-less).
            set_entries = "\n".join(
                ('  <botcomponent_connectionreference botcomponentid.schemaname="%s" '
                 'connectionreferenceid.connectionreferencelogicalname="%s">\n'
                 "    <iscustomizable>1</iscustomizable>\n"
                 "  </botcomponent_connectionreference>") % (cs, rl)
                for cs, rl in self._conn_ref_links)
            zf.writestr(
                "Assets/botcomponent_connectionreferenceset.xml",
                CONN_REF_SET_XML.format(entries=set_entries),
            )

            # 7. The tool <-> flow associations, so each capability flow is a
            #    declared dependency of the TaskDialog that invokes it.
            if self._flow_tool_links:
                zf.writestr(
                    "Assets/botcomponent_workflowset.xml",
                    WORKFLOW_SET_XML.format(entries="\n".join(
                        WORKFLOW_SET_ENTRY_XML.format(component_schema=cs, workflow_id=wf)
                        for cs, wf in self._flow_tool_links)),
                )

            # 8. [Content_Types].xml — every extensionless /data part listed
            zf.writestr(
                "[Content_Types].xml",
                CONTENT_TYPES_XML_NATIVE.format(overrides="".join(overrides)),
            )

        data = buf.getvalue()
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(data)
        return data

    @property
    def bot_schemas(self) -> List[str]:
        # Flat topology emits ONLY the orchestrator bot (no child bots), so the
        # deploy/publish path must not try to publish children that never shipped.
        if getattr(self.spec, "topology", "hierarchical") == "flat":
            return [self.orch_schema]
        return [self.orch_schema] + [c[1] for c in self._children]

    @property
    def workflow_ids(self) -> Dict[str, str]:
        """child bot schema -> deterministic capability flow WorkflowId."""
        return dict(self._flow_ids)

    # -- bot writers -----------------------------------------------------

    def _write_bot(
        self,
        zf: zipfile.ZipFile,
        bot_schema: str,
        display_name: str,
        instructions: str,
        overrides: List[str],
        is_orchestrator: bool = False,
        capir: Optional[dict] = None,
        flow_guid: Optional[str] = None,
        compute_source: Optional[str] = None,
        params: Optional[list] = None,
        live: Optional[dict] = None,
        name_suffix: str = "",
        description: str = "",
        reference_material: str = "",
    ) -> None:
        """Write a complete bot: bot.xml, configuration.json, gpt.default, system
        topics, and (for a sub-agent carrying a CapIR) the REAL deterministic
        capability that runs the same steps as the converted agent.py — wired as
        a flow TOOL (flow_guid set, the default) or as the legacy topic. When the
        source agent.py carries real computation (compute_source), the sub-agent
        also gets a CODE INTERPRETER recipe so that math runs faithfully in
        Copilot Studio's Python sandbox — layered ON TOP of the deterministic
        flow, never replacing it."""
        # Copilot Studio caps the bot name at 42 chars; keep "Orchestrator" (and
        # the twin's " (Demo)" tag) intact so the twins stay tellable apart.
        if name_suffix:
            display_name = display_name + name_suffix
        preserve = ("Orchestrator" + name_suffix).strip() if is_orchestrator \
            else (name_suffix.strip() or None)
        display_name = _cap_bot_name(
            display_name, preserve_suffix=preserve
        )
        # bot.xml + configuration.json
        zf.writestr(
            f"bots/{bot_schema}/bot.xml",
            BOT_XML.format(
                bot_schema=bot_schema,
                bot_display_name=_xml_escape(display_name),
                icon_base64=DEFAULT_ICON_BASE64,
                # Demo twins are the autonomous test profile: no end-user
                # authentication, so their built-in web/mobile Direct Line
                # channel can run after publish. Live/customer twins retain
                # Integrated authentication.
                authentication_mode=0 if name_suffix else 2,
                authentication_trigger=0 if name_suffix else 1,
            ),
        )
        gpt_schema = f"{bot_schema}.gpt.default"
        if is_orchestrator:
            # The connected-agent root needs the channels + isLightweightBot config
            # or its post-publish provisioning fails with a 409 ExternalServiceException.
            poi = '\n  "publishOnImport": true,' if self.spec.orchestrator_publish_on_import else ""
            channels = ORCHESTRATOR_CHANNELS_BLOCK if self.spec.orchestrator_channels else ""
            config_json = ORCHESTRATOR_CONFIGURATION_JSON.format(
                gpt_schema=gpt_schema, publish_on_import_line=poi, channels_block=channels
            )
        else:
            config_json = BOT_CONFIGURATION_JSON_NATIVE.format(gpt_schema=gpt_schema)
        zf.writestr(f"bots/{bot_schema}/configuration.json", config_json)

        # gpt.default component (instructions). Its description column is the
        # agent's Details description in Copilot Studio — describe the USE
        # CASE, never ship "None provided".
        gpt_folder = f"botcomponents/{gpt_schema}"
        if is_orchestrator:
            subs_line = ", ".join(s.display_name for s, _c, _a in self._children[:8])
            bot_desc = (f"Orchestrates the {self.spec.solution_display_name} use case: "
                        f"routes each request to the right connected agent "
                        f"({subs_line}).")[:950]
        else:
            bot_desc = (description or "").strip()[:950]
        desc_el = (f"\n  <description>{_xml_escape(bot_desc)}</description>"
                   if bot_desc else "")
        zf.writestr(
            f"{gpt_folder}/botcomponent.xml",
            GPT_BOTCOMPONENT_XML.format(
                schema_name=gpt_schema,
                description_element=desc_el,
                display_name=_xml_escape(display_name),
                bot_schema=bot_schema,
            ),
        )
        instr = instructions or f"You are {display_name}. Help the user with their request."
        if capir and flow_guid and not is_orchestrator:
            cap_binding = (capir or {}).get("binding") or {}
            write_and_generate = bool(cap_binding.get("write")
                                      and cap_binding.get("generative"))
            tool_rule = (
                "First compose the complete requested content using only the user's facts, "
                "then call the flow and pass that complete draft in its free-text input. "
                "After the tool returns, show the draft in full together with action_status "
                "and the receipt or simulation qualifier."
                if write_and_generate else
                "Call the flow tool RIGHT AWAY. Pass the user's query when they gave one, "
                "otherwise pass an EMPTY STRING; pass 0 for the numeric threshold unless the "
                "user explicitly gave one.")
            instr += (f"\n\n# Deterministic capability tool\n"
                      f"For any request about {display_name}, use the "
                      f"'{capir_flow_name(display_name)}' flow tool. " + tool_rule +
                      " Ground your answer in the tool outputs. Preserve every demo/simulation "
                      "qualifier verbatim. Use only facts explicitly present in the tool outputs; "
                      "never invent actions, owners, causes, delivery states, timestamps, SLAs, "
                      "or citations. When data_provenance is synthetic_demo, the first sentence "
                      "must say it is synthetic demo context and not an official source. When "
                      "data_provenance is public_static_demo, the first sentence must say it is "
                      "public static demo context, not the external product or an official source. "
                      "Claim an external action succeeded only when action_status "
                      "is succeeded and receipt is non-empty.")
        if True:
            # Generic file production — EVERY bot, any format, no special-casing:
            # the Copilot Studio code interpreter carries document libraries, so
            # "save it as a word document" must yield a real .docx, not a
            # Markdown apology. The ORCHESTRATOR is included deliberately: in the
            # flat topology it is the single answering agent, and gating this to
            # sub-agents shipped an orchestrator that offered .md with an apology
            # until the user taught it about its own code interpreter (observed
            # live, EstimatesBriefs 2026-07-06).
            instr += (
                "\n\n# Files & documents (code interpreter)\n"
                "When the user asks for a document, report, template, "
                "spreadsheet, presentation, chart, or any downloadable file — "
                "in any format they name — produce the REAL file with your "
                "Python code interpreter and return it as a file. The sandbox "
                "includes document libraries (python-docx, openpyxl, "
                "python-pptx, reportlab, pandas, matplotlib and more): use the "
                "one matching the requested format. Never refuse a supported "
                "format and never substitute plain text or Markdown for the "
                "actual file the user asked for. When the user does NOT name a "
                "format, default by content type: business documents (briefs, "
                "reports, letters, memos, summaries) -> .docx via python-docx; "
                "tabular data -> .xlsx via openpyxl; presentations -> .pptx via "
                "python-pptx; charts -> .png via matplotlib. Produce .md or .txt "
                "ONLY when the user explicitly asks for that format. Build the "
                "content from this agent's own data — the deterministic tool "
                "outputs (message / matches_json / document_text) and what the "
                "user provides. The sandbox has no network access.")
        if compute_source and not is_orchestrator:
            snippet = compute_source
            if len(snippet) > 3200:
                snippet = snippet[:3200].rsplit("\n", 1)[0] + "\n# ... (truncated)"
            instr += (
                "\n\n# Computation (code interpreter)\n"
                "This agent's source computation is reproduced below. When the user "
                "asks for COMPUTED results (scores, rankings, projections, plans, "
                "generated documents) rather than a raw record lookup, use your "
                "Python code interpreter to reproduce this logic faithfully — do "
                "not invent your own formulas. Get the input records from the "
                "deterministic flow tool's matches_json output (or from data the "
                "user supplies), run the computation, and present the results. "
                "The code interpreter sandbox has NO network access: never attempt "
                "external calls; work only with the records and inputs you have.\n"
                "```python\n" + snippet + "\n```")
        # DEMO twin only (tag "refmat"): a trailing, clearly-labeled reference
        # section grounded in THIS capability's own synthetic records, so the demo
        # child bot can answer domain "why/what does this mean" questions about the
        # SAME entries its flow returns. Rendered ONLY when name_suffix is set (the
        # " (Demo)" twin) and this is a sub-agent — the LIVE twin's instructions
        # stay byte-for-byte unchanged and the orchestrator stays lean. Truncate
        # the reference (never the base instructions) so total instr stays <= 8000.
        if name_suffix and reference_material and not is_orchestrator:
            header = (
                "\n\n# Reference material (synthetic demo domain)\n"
                "This material is invented demo context, not an official or external source. "
                "Never cite it, emit citation markers, or present it as authoritative.\n"
            )
            ref = str(reference_material).replace("{", "(").replace("}", ")")
            room = 8000 - len(instr) - len(header)
            if room > 0:
                if len(ref) > room:
                    ref = ref[:room]
                    nl = ref.rfind("\n")
                    if nl > 0:
                        ref = ref[:nl]
                if ref.strip():
                    instr += header + ref
        # Conversation starters (suggested prompts): the capability's own
        # trigger phrases for a sub-agent; one per connected agent for the
        # orchestrator — so the Test pane teaches the use case immediately.
        starters = []
        if is_orchestrator:
            for s, _c, _a in self._children[:6]:
                trig = ((s.capir or {}).get("expect") or [None])[0] or \
                    f"Help me with {s.display_name.lower()}"
                starters.append((_starter_title(s.display_name), str(trig)[:150]))
        else:
            for trig in ((capir or {}).get("expect") or [])[:3]:
                starters.append((_starter_title(str(trig)).title(), str(trig)[:150]))
            if not starters:
                prompt = None
                for slot in (capir or {}).get("slots") or []:
                    prompt = slot.get("prompt"); break
                starters.append((_starter_title(f"Try {display_name}"),
                                 str(prompt or f"Show me how you handle "
                                     f"{display_name.lower()}.")[:150]))
        starters_yaml = ""
        if starters:
            starters_yaml = "conversationStarters:\n" + "".join(
                "  - kind: ConversationStarter\n"
                "    title: " + _yaml_dq(t) + "\n"
                "    text: " + _yaml_dq(x) + "\n" for t, x in starters)
        zf.writestr(
            f"{gpt_folder}/data",
            GPT_DATA_YAML.format(
                display_name=_yaml_display_safe(display_name),
                instructions_indented=_indent(instr.strip(), 2),
                conversation_starters=starters_yaml,
            ),
        )
        overrides.append(CONTENT_TYPE_OVERRIDE.format(part_name=f"{gpt_folder}/data"))

        # Work IQ MCP tools ("skills") planned for this bot on the LIVE twin:
        # a .tool. component per matched server, Invoker-auth (runs as the
        # signed-in user; SSO — no secret to configure).
        for t in self._mcp_by_child.get(bot_schema, []):
            folder = f"botcomponents/{t['component_schema']}"
            zf.writestr(
                f"{folder}/botcomponent.xml",
                BOTCOMPONENT_XML.format(
                    schema_name=t["component_schema"],
                    component_type=9,
                    display_name=_xml_escape(t["display"]),
                    bot_schema=bot_schema,
                    description_element=("\n  <description>%s</description>" % _xml_escape(
                        "MCP skill - %s: attached because this agent's source does this "
                        "kind of work. Runs as the signed-in user (SSO)." % t["display"])),
                ),
            )
            zf.writestr(f"{folder}/data", MCP_TOOL_DATA_YAML.format(
                conn_ref_logical=t["conn_ref_logical"], api=t["api"],
                operation=t["operation"]))
            overrides.append(CONTENT_TYPE_OVERRIDE.format(part_name=f"{folder}/data"))

        # system topics (one set per bot)
        for topic_key, topic_data in SYSTEM_TOPICS.items():
            schema_name = f"{bot_schema}.topic.{topic_key}"
            folder = f"botcomponents/{schema_name}"
            zf.writestr(
                f"{folder}/botcomponent.xml",
                self._topic_botcomponent_xml(bot_schema, topic_key, topic_data),
            )
            zf.writestr(
                f"{folder}/data",
                topic_data["data"].format(bot_schema=bot_schema),
            )
            overrides.append(CONTENT_TYPE_OVERRIDE.format(part_name=f"{folder}/data"))

        # custom per-capability behavior: the REAL deterministic logic, INSIDE
        # this sub-agent (1:1 with the converted agent.py's CapIR steps). The
        # orchestrator stays a pure router and never carries one.
        if capir and not is_orchestrator:
            if flow_guid:
                # The packaged capability flow attached to THIS bot as a TOOL (a
                # TaskDialog invoking the flow). Topology-agnostic: _write_flow_tool
                # parents it to a child bot (hierarchical) OR the orchestrator (flat).
                self._write_flow_tool(zf, bot_schema, display_name, capir, flow_guid,
                                      params, live, overrides)
            else:
                desc = (f"Deterministic handler for {display_name} "
                        "(seeded records + the real user query, 1:1 with the agent.py).")
                action = capir_topic_action_name(capir)
                # keep "{bot_schema}.topic.{action}" within the 100-char schema limit
                action = action[: max(4, MAX_SCHEMA - len(bot_schema) - len(".topic."))]
                schema_name = f"{bot_schema}.topic.{action}"
                folder = f"botcomponents/{schema_name}"
                zf.writestr(
                    f"{folder}/botcomponent.xml",
                    self._topic_botcomponent_xml(
                        bot_schema, action,
                        {"display_name": display_name,
                         "description": desc}),
                )
                zf.writestr(f"{folder}/data", capir_topic_data_yaml(display_name, capir))
                overrides.append(CONTENT_TYPE_OVERRIDE.format(part_name=f"{folder}/data"))

    def _write_flow_tool(self, zf, parent_schema, display_name, capir, flow_guid,
                         params, live, overrides):
        """Attach a capability flow to `parent_schema` as an InvokeFlowTaskAction
        TOOL (componenttype-9 TaskDialog). Topology-agnostic — `parent_schema` is a
        connected child bot (hierarchical) OR the orchestrator itself (flat). The
        flow is deterministic and always runs to completion (it never prompts), so
        parenting it straight onto the orchestrator reproduces the brainstem's
        one-LLM-plus-deterministic-tools execution model."""
        desc = (f"Deterministic handler for {display_name} "
                "(seeded records + the real user query, 1:1 with the agent.py).")
        action = "Run" + (_pascal((capir or {}).get("key") or display_name) or "Capability")
        budget = max(4, MAX_SCHEMA - len(parent_schema) - len(".component."))
        # CapIR keys are LLM-chosen and DO collide (two agents both keyed
        # "lookup"). In flat topology every tool shares the orchestrator as
        # parent, so a repeat name would write duplicate zip parts (OPC-
        # forbidden) and link one component to two flows in the workflowset,
        # silently shadowing a capability. Numeric suffix within the schema
        # budget, mirroring __init__'s child/action dedup.
        taken = {s for s, _ in self._flow_tool_links}
        schema_name = f"{parent_schema}.component.{action[:budget]}"
        n = 2
        while schema_name in taken:
            trimmed = action[: max(4, budget - len(str(n)))] + str(n)
            schema_name = f"{parent_schema}.component.{trimmed}"
            n += 1
        folder = f"botcomponents/{schema_name}"
        zf.writestr(
            f"{folder}/botcomponent.xml",
            BOTCOMPONENT_XML.format(
                schema_name=schema_name,
                component_type=9,
                display_name=_xml_escape(capir_flow_name(display_name)),
                bot_schema=parent_schema,
                description_element=f"\n  <description>{_xml_escape(desc)}</description>",
            ),
        )
        zf.writestr(f"{folder}/data",
                    capir_flow_tool_yaml(display_name, desc, flow_guid, capir,
                                         params=params, live=live))
        overrides.append(CONTENT_TYPE_OVERRIDE.format(part_name=f"{folder}/data"))
        self._flow_tool_links.append((schema_name, flow_guid))

    def _write_connected_action(
        self,
        zf: zipfile.ZipFile,
        sub: SubAgentSpec,
        child_schema: str,
        action: str,
        overrides: List[str],
    ) -> None:
        """Write the orchestrator's delegation component for one sub-agent."""
        schema_name = f"{self.orch_schema}.InvokeConnectedAgentTaskAction.{action}"
        folder = f"botcomponents/{schema_name}"
        description = sub.description or f"Delegate to {sub.display_name}."

        zf.writestr(
            f"{folder}/botcomponent.xml",
            INVOKE_CONNECTED_AGENT_BOTCOMPONENT_XML.format(
                schema_name=schema_name,
                description=_xml_escape(description),
                display_name=_xml_escape(sub.display_name),
                orchestrator_schema=self.orch_schema,
            ),
        )
        zf.writestr(
            f"{folder}/dependencies.json",
            INVOKE_CONNECTED_AGENT_DEPENDENCIES.format(child_schema=child_schema),
        )
        inputs_block, input_type_block = _connected_inputs_yaml(getattr(sub, "params", None))
        zf.writestr(
            f"{folder}/data",
            INVOKE_CONNECTED_AGENT_DATA.format(
                display_name=_yaml_display_safe(sub.display_name),
                description_indented=_indent(description.strip(), 2),
                child_schema=child_schema,
                inputs_block=inputs_block,
                input_type_block=input_type_block,
            ),
        )
        overrides.append(CONTENT_TYPE_OVERRIDE.format(part_name=f"{folder}/data"))

    # -- xml helpers -----------------------------------------------------

    def _topic_botcomponent_xml(self, bot_schema, topic_key, topic_data) -> str:
        schema_name = f"{bot_schema}.topic.{topic_key}"
        desc = topic_data.get("description")
        desc_element = ""
        if desc:
            desc_element = f"\n  <description>{_xml_escape(desc)}</description>"
        return BOTCOMPONENT_XML.format(
            schema_name=schema_name,
            component_type=9,
            display_name=_xml_escape(topic_data["display_name"]),
            bot_schema=bot_schema,
            description_element=desc_element,
        )

    def _solution_xml(self, root_components: Optional[List[str]] = None) -> str:
        rc = ""
        if root_components:
            rc = "\n" + "\n".join(root_components) + "\n    "
        return SOLUTION_XML_NATIVE.format(
            solution_unique_name=_xml_escape(self.spec.solution_unique_name),
            solution_display_name=_xml_escape(self.spec.solution_display_name),
            publisher_unique_name=_xml_escape(self.spec.publisher_unique_name),
            publisher_display_name=_xml_escape(self.spec.publisher_display_name),
            publisher_prefix=self.spec.publisher_prefix,
            solution_version=self.spec.solution_version,
            managed_flag="1" if self.spec.managed else "0",
            root_components=rc,
        )

    # -- orchestrator instructions --------------------------------------

    def _orchestrator_instructions(self) -> str:
        flat = getattr(self.spec, "topology", "hierarchical") == "flat"
        base = (self.spec.orchestrator_instructions or "").strip()
        if flat:
            # Brainstem-faithful: ONE reasoning layer + deterministic flow tools.
            # The orchestrator both selects tool args AND writes the final answer,
            # exactly like the soul.md loop calling perform() functions. Every
            # capability is a flow tool it calls directly — no sub-agent to delegate
            # to, so nothing can pause to re-prompt the user.
            lines = [base] if base else [
                f"You are {self.spec.orchestrator_display_name} for the "
                f"{self.spec.solution_display_name}. Answer the user directly using your "
                "deterministic flow tools — you are the single reasoning layer that both "
                "calls the tools and writes the final answer."
            ]
            lines += ["", "# Flow tools you call directly (one per capability)"]
            has_read = False
            has_write = False
            has_write_generate = False
            for sub, _schema, _action in self._children:
                one_line = re.sub(r"\s+", " ", (sub.description or sub.display_name)).strip()
                binding = (sub.capir or {}).get("binding") or {}
                write = bool(binding.get("write"))
                write_generate = bool(write and binding.get("generative"))
                has_read = has_read or not write
                has_write = has_write or write
                has_write_generate = has_write_generate or write_generate
                contract = (
                    "generate+write: compose the complete content first, pass every "
                    "text/action input, then use action_status / receipt / "
                    "deliverable_context / data_provenance"
                    if write_generate else
                    "write: use message / action_status / receipt / data_provenance"
                    if write else
                    "read: use message / matches_json / match_count / "
                    "required_identifier / data_provenance")
                lines.append(
                    f"- {capir_flow_name(sub.display_name)} ({sub.display_name}): "
                    f"{one_line} [{contract}]")
            lines += [
                "",
                "# Rules",
                "- For any request that matches a tool, call that tool and obey the output contract listed above.",
                "- A request may need several tools; call them across turns until it is fully answered.",
            ]
            if has_read:
                lines += [
                    "- For read tools, pass the user's query when given, otherwise an empty string; pass 0 for a numeric threshold unless the user supplied one.",
                    "- Ground read answers in message / matches_json / match_count / required_identifier / data_provenance.",
                ]
            if has_write:
                lines += [
                    "- For write tools, pass every user-provided action field. Preserve simulation qualifiers and report action_status plus receipt; never claim external success without action_status succeeded and a non-empty receipt.",
                ]
            if has_write_generate:
                lines += [
                    "- For generate+write tools, first compose the complete requested content from user facts, fill every text input with that draft and its addressing details, then call the tool. Show the same draft in full with action_status, receipt, deliverable_context, and data_provenance.",
                ]
            return "\n".join(lines)
        if base:
            return base
        lines = [
            f"You are {self.spec.orchestrator_display_name}, the orchestrator for the "
            f"{self.spec.solution_display_name} workflow. You route each user request to the "
            "right connected sub-agent and never answer specialized questions yourself.",
            "",
            "Connected sub-agents you can delegate to:",
        ]
        for sub, _schema, _action in self._children:
            one_line = re.sub(r"\s+", " ", (sub.description or sub.display_name)).strip()
            lines.append(f"- {sub.display_name}: {one_line}")
        lines += [
            "",
            "Routing rules:",
            "- Read the user's request, pick the single best-matching sub-agent from the list, and delegate to it.",
            "- Pass each sub-agent only the inputs it needs; do not paraphrase or pre-answer its work.",
            "- If the request spans several sub-agents, handle one sub-agent per turn and confirm before moving on.",
            "- If no sub-agent fits, say so and ask a clarifying question rather than inventing an answer.",
        ]
        return "\n".join(lines)


def generate_connected_solution(
    spec: ConnectedSolutionSpec,
    output_path: Optional[Path] = None,
) -> bytes:
    """Build a connected (multi-bot) solution zip from a ConnectedSolutionSpec."""
    return ConnectedSolutionPackager(spec).package(output_path=output_path)


# ============================================================================
# Build sub-agents from an agent stack (agents/*.py + metadata.json) and validate
# ============================================================================

def _humanize(name: str) -> str:
    name = re.sub(r"_stacks$", "", name or "")
    name = name.replace("_", " ").replace("-", " ").strip()
    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    return " ".join(w[:1].upper() + w[1:] for w in name.split())


def _humanize_class(name: str) -> str:
    name = re.sub(r"Agent$", "", name or "")
    name = re.sub(r"_agent$", "", name)
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)
    name = name.replace("_", " ").strip()
    return " ".join(w[:1].upper() + w[1:] for w in name.split())


def _safe_literal(node):
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


# Class-body literals a converted agent.py embeds. CAPIR is the compiled CapIR
# (perform()'s spec); SYNTHETIC_DATA holds the seeded records (the build keeps
# them OUT of the CapIR binding, so we re-inject them); the rest let us recompile
# a CapIR when one was not embedded.
_RECOVERED_ATTRS = {"CAPIR", "SYNTHETIC_DATA", "KNOWLEDGE", "RESPONSE",
                    "DOC_NAME", "CUSTOMER", "TRIGGERS"}


def _module_const_map(tree):
    """Module-level `NAME = <literal>` (or annotated `NAME: type = <literal>`)
    constants (e.g. DEFAULT_GROUP_ID = "256680165376") so a param default that
    references one resolves to its value."""
    consts = {}
    for node in tree.body:
        # plain `NAME = <literal>` (single Name target) OR annotated
        # `NAME: type = <literal>` (ast.AnnAssign) — both are module constants.
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)):
            target, value = node.targets[0], node.value
        elif (isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
                and node.value is not None):
            target, value = node.target, node.value
        else:
            continue
        v = _safe_literal(value)
        if v is not None:
            consts[target.id] = v
    return consts


def _extract_param_defaults(func_node, consts, names):
    """Mimic the agent.py's OWN fallback resolution: the value perform() uses when
    the caller omits an optional param — from `kwargs.get("p", DEFAULT)` or the
    `kwargs.get("p") or os.environ.get(...) or DEFAULT` idiom (module constants
    resolved). So the connected agent ships the SAME default the code falls back
    to, and never prompts."""
    defaults = {}
    if func_node is None:
        return defaults

    def _resolve(n):
        if isinstance(n, ast.Constant):
            return n.value
        if isinstance(n, ast.Name):
            return consts.get(n.id)
        return _safe_literal(n)

    def _is_kwargs_get(n):
        return (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "get" and isinstance(n.func.value, ast.Name)
                and n.func.value.id == "kwargs" and n.args
                and isinstance(n.args[0], ast.Constant) and n.args[0].value in names)

    for node in ast.walk(func_node):
        if _is_kwargs_get(node) and len(node.args) > 1:          # kwargs.get("p", <default>)
            v = _resolve(node.args[1])
            if v is not None:
                defaults.setdefault(node.args[0].value, v)
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
            vals = node.values
            for i, val in enumerate(vals):
                if _is_kwargs_get(val):
                    p = val.args[0].value
                    for cand in vals[i + 1:]:                    # ... or ENV or DEFAULT
                        if isinstance(cand, (ast.Constant, ast.Name)):
                            rv = _resolve(cand)
                            if rv not in (None, ""):
                                defaults.setdefault(p, rv)
                                break
    return defaults


def _manual_value_token(default, jtype):
    """Power Fx literal for a ManualTaskInput `value:`, YAML-double-quoted. Uses the
    agent.py's own default when known; else empty/0/false by type."""
    jt = str(jtype).lower()
    if isinstance(default, bool):
        return "true" if default else "false"
    if isinstance(default, (int, float)):
        return str(default)
    if default is None:
        if jt in ("number", "integer"):
            return "0"
        if jt == "boolean":
            return "false"
        return json.dumps('""')                                 # empty Power Fx string ""
    return json.dumps('"' + str(default).replace('"', '""') + '"')  # quoted Power Fx string


def _parse_basic_agent(py_path: Path):
    """AST-extract (display_name, agent_name, description, module_doc, params,
    recovered) from a BasicAgent .py — `recovered` carries any embedded CapIR /
    seeded records used to build the deterministic capability topic."""
    src = py_path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    module_doc = (ast.get_docstring(tree) or "").strip()

    cls = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and any(
            isinstance(b, ast.Name) and b.id == "BasicAgent" for b in node.bases
        ):
            cls = node
            break
    if cls is None:
        return None

    self_name = None
    description = ""
    params = []  # (name, description, required)
    recovered = {}  # class-level CAPIR / SYNTHETIC_DATA / ... for deterministic topics
    for sub in ast.walk(cls):
        # Annotated attributes (`SYNTHETIC_DATA: list = [...]`, `self.name: str =
        # "X"`, `self.metadata: dict = {...}`) are ast.AnnAssign, not ast.Assign —
        # handle both. AnnAssign has ONE target and an optional value (a bare
        # annotation `x: int` has value=None, which we skip like an empty Assign).
        if isinstance(sub, ast.Assign):
            targets, value = sub.targets, sub.value
        elif isinstance(sub, ast.AnnAssign) and sub.value is not None:
            targets, value = [sub.target], sub.value
        else:
            continue
        for tgt in targets:
            # class-body literals the build stage embeds (CAPIR = {...},
            # SYNTHETIC_DATA = [...], KNOWLEDGE / RESPONSE / DOC_NAME / CUSTOMER / TRIGGERS)
            if isinstance(tgt, ast.Name) and tgt.id in _RECOVERED_ATTRS:
                val = _safe_literal(value)
                if val is not None:
                    recovered[tgt.id] = val
                continue
            if not (isinstance(tgt, ast.Attribute) and isinstance(tgt.value, ast.Name)
                    and tgt.value.id == "self"):
                continue
            if tgt.attr == "name" and isinstance(value, ast.Constant) and isinstance(value.value, str):
                self_name = value.value
            elif tgt.attr == "metadata" and isinstance(value, ast.Dict):
                # Walk the dict node key-by-key: the metadata literal contains a
                # non-literal value ("name": self.name), so literal_eval on the
                # whole dict fails — pull the literal keys we care about directly.
                for k, v in zip(value.keys, value.values):
                    key = k.value if isinstance(k, ast.Constant) else None
                    if key == "description":
                        dv = _safe_literal(v)
                        if isinstance(dv, str):
                            description = dv.strip()
                    elif key == "parameters":
                        pv = _safe_literal(v)
                        if isinstance(pv, dict):
                            # LLM-plausible schema mistakes must not crash the run:
                            # "properties" may arrive as a LIST of param objects
                            # (each carrying its own "name") instead of a
                            # name->schema map, and "required" may arrive as a bare
                            # bool instead of a list of names.
                            props = pv.get("properties")
                            if isinstance(props, list):
                                props = {p.get("name"): p for p in props
                                         if isinstance(p, dict) and p.get("name")}
                            elif not isinstance(props, dict):
                                props = {}
                            req_raw = pv.get("required")
                            req = set(req_raw) if isinstance(req_raw, (list, tuple, set)) else set()
                            for pn, pinfo in props.items():
                                pdesc = (pinfo.get("description") if isinstance(pinfo, dict) else "") or pn
                                ptype = (pinfo.get("type") if isinstance(pinfo, dict) else None) or "string"
                                is_req = pn in req
                                # A free-text SEARCH/QUERY input is treated as OPTIONAL even when the
                                # agent marks it required — so a "query agent" (e.g. Viva Engage) returns
                                # ALL records and its generative model answers from them, instead of
                                # PROMPTING for a query. The user can still ask a specific question (the
                                # sub-agent grounds its answer on the returned records); they just aren't
                                # forced to supply one. Genuine data inputs (content, id, name) stay required.
                                if is_req and str(pn).lower() in ("query", "question", "search", "keyword", "q"):
                                    is_req = False
                                params.append((pn, pdesc, is_req, ptype))

    stem_name = re.sub(r"_agent$", "", py_path.stem)
    agent_name = stem_name
    display = _humanize_class(self_name or stem_name)
    if not description:
        # First paragraph of the module docstring.
        description = re.sub(r"\s+", " ", module_doc.split("\n\n")[0]).strip()
    # Statically infer the SHAPE of the data this agent works with (the dict keys
    # its perform()/helpers read & write) so we can synthesize matching static
    # stand-in records — no execution, no domain rules.
    # Attach each param's agent.py fallback default (mimics perform()'s own
    # resolution) as a 5th tuple element, so connected-agent inputs ship the REAL
    # default (e.g. group_id -> DEFAULT_GROUP_ID) instead of an empty "".
    _consts = _module_const_map(tree)
    _perform = next((n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                     and n.name == "perform"), None)
    _pdef = _extract_param_defaults(_perform, _consts, {p[0] for p in params})
    params = [(p[0], p[1], p[2], p[3], _pdef.get(p[0])) for p in params]
    recovered["INFERRED_FIELDS"] = _infer_record_fields(tree, exclude=[p[0] for p in params])
    # The perform() SOURCE, for the sub-agent's code-interpreter recipe: a
    # handwritten agent's real computation (scoring, ranking, projections) can
    # then be reproduced faithfully in Copilot Studio's Python sandbox over the
    # records the deterministic flow returns.
    for sub in cls.body:
        if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)) and sub.name == "perform":
            seg = ast.get_source_segment(src, sub)
            if seg:
                recovered["PERFORM_SOURCE"] = seg
            break
    return display, agent_name, description, module_doc, params, recovered


def _stack_subagent_instructions(display, description, module_doc, params) -> str:
    """The sub-agent's brain: self-documents the agent.py end-to-end — its purpose
    and its FULL input contract (what the orchestrator passes to delegate). Generic
    for ANY agent.py; no domain assumptions."""
    lines = [f"You are the {display} agent.", "", "# Purpose"]
    lines.append(module_doc.strip() if module_doc else (description or f"Handle {display} requests."))
    lines += ["", "# Inputs the orchestrator passes you"]
    if params:
        for pn, pdesc, required, *rest in params:
            tag = "required" if required else "optional"
            ptype = rest[0] if rest else "string"
            clean = re.sub(r"\s+", " ", pdesc).strip()
            lines.append(f"- {pn} ({tag}, {ptype}): {clean}")
    else:
        lines.append("- No structured inputs are required; use the user's request directly.")
    lines += ["", "# How you answer",
              "- Run your deterministic capability topic and ground every answer in its seeded records.",
              "- Treat tool outputs as the complete fact boundary. Use only facts explicitly present "
              "in message, matches_json, document_text, received_inputs, and receipt fields; if a "
              "requested fact is absent, say it is unavailable.",
              "- Never invent actions, owners, causes, delivery states, timestamps, SLAs, or citations.",
              "- Claim an external action succeeded only when action_status is succeeded and a receipt "
              "is non-empty. When action_status is simulated, say clearly that no external system changed.",
              "- That seeded data is SYNTHETIC stand-in data for your real source system, so you load "
              "and run end-to-end with no live connection. Swapping the topic's Table() for the live "
              "connector takes you to production with no change to the logic.",
              "- Stay in your lane: if the request belongs to another connected agent, say so and let "
              "the orchestrator route it."]
    return "\n".join(lines)


def _contract_description(description, params, limit=850):
    """The orchestrator-facing routing description: the agent's purpose PLUS its
    input contract, so the Copilot Studio agent knows what to pass when it
    delegates. Self-documenting, generic, length-capped for the component."""
    base = re.sub(r"\s+", " ", description or "").strip()
    if params:
        ins = "; ".join("%s (%s)" % (pn, "required" if req else "optional")
                        for pn, _pd, req, *_rest in params)
        base = (base + " Inputs to pass: " + ins + ".").strip()
    return base[:limit]


# t2p-capir/1.0 — the load-bearing perform() constants, mirrored so a recompiled
# CapIR carries the same numbers the agent.py uses.
_CAPIR_SCHEMA = "t2p-capir/1.0"
_RECOMPILE_CONSTS = {
    "word_min_len": 3, "example_take": 2, "fallback_take": 2, "pdf_records": 3,
    "pdf_prepared": "Prepared for {customer}",
    "pdf_footer": "Synthetic demo data - no customer data was needed.",
}


# Envelope / structural dict keys that are NOT data columns, so schema inference
# never mistakes the result wrapper for record fields.
_ENVELOPE_KEYS = {"status", "agent", "data", "parameters", "properties",
                  "required", "type", "name", "description", "items", "enum",
                  "error", "result", "results", "success", "ok", "count", "as_of_utc"}
# Objects whose `.get("x")` calls are NOT record reads (input kwargs, env, etc.).
_SKIP_GET_OBJS = {"kwargs", "self", "metadata", "os", "sys", "environ", "params", "config"}


def _flatten_record(r):
    """Flatten one record to top-level scalar fields (the Table()/filter columns):
    a nested dict is merged up one level; lists/dicts are json-encoded to strings."""
    if not isinstance(r, dict):
        return {}
    out = {}
    for k, v in r.items():
        if isinstance(v, dict):
            for kk, vv in v.items():
                out[str(kk)] = vv if not isinstance(vv, (list, dict)) else json.dumps(vv, ensure_ascii=False)
        elif isinstance(v, list):
            out[str(k)] = json.dumps(v, ensure_ascii=False)
        else:
            out[str(k)] = v
    return out


def _infer_record_fields(tree, exclude=None, max_fields=14):
    """Infer the SHAPE of the data an agent.py works with by statically scanning
    its code for the dict keys it reads/writes: `rec.get("field")`, `rec["field"]`
    and `{"field": ...}` literals. Excludes input-param names + envelope keys so
    only genuine data columns remain. 100% static — no execution, no domain rules."""
    exclude = set(exclude or []) | _ENVELOPE_KEYS
    keys = []

    def add(k):
        if (isinstance(k, str) and k and k.isidentifier()
                and k not in exclude and k not in keys):
            keys.append(k)

    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "get" and node.args):
            obj = node.func.value
            if isinstance(obj, ast.Name) and obj.id in _SKIP_GET_OBJS:
                continue
            a = node.args[0]
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                add(a.value)
        elif isinstance(node, ast.Subscript):
            sl = node.slice
            if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                add(sl.value)
        elif isinstance(node, ast.Dict):
            klits = [k.value for k in node.keys
                     if isinstance(k, ast.Constant) and isinstance(k.value, str)]
            if "status" in klits and "data" in klits:
                continue  # a result-envelope literal, not a data record
            for k in klits:
                add(k)
    return keys[:max_fields]


def _synthesize_value(field, i):
    """A clearly-synthetic, generic value for `field` on row i — typed by the field
    NAME's TOKENS only (token-matched, so "age" never fires inside "message"). No
    domain knowledge. Deterministic (index-based, no RNG)."""
    f = field.lower()
    toks = set(t for t in re.split(r"[^a-z0-9]+", f) if t)
    if toks & {"prob", "probability", "score", "rate", "ratio", "pct", "percent",
               "confidence", "likelihood", "fail", "risk"}:
        return round(0.15 + 0.7 * (((i - 1) % 5) / 4.0), 2)   # 0.15 .. 0.85
    if f.startswith(("is_", "has_")) or toks & {"enabled", "active", "flag", "bool"}:
        return (i % 2 == 0)
    if toks & {"date", "time", "utc", "timestamp", "datetime", "created", "updated"}:
        return "2026-01-%02dT00:00:00Z" % min(i, 28)
    if toks & {"id", "guid", "uuid", "code", "ref"}:
        return "%s-%04d" % ((re.sub(r"[^A-Za-z]", "", field).upper()[:4] or "REC"), i)
    if toks & {"count", "qty", "quantity", "amount", "price", "cost", "value", "age",
               "days", "years", "hours", "num", "number", "level", "index", "size",
               "total", "kv", "voltage", "pct"}:
        return i * 10
    return "synthetic %s %d" % (f.replace("_", " "), i)


def _synthesize_records(fields, n=5, threshold_cutoff=None):
    """Generate n self-documenting STATIC stand-in records over `fields` — the
    synthetic data that lets the topic load and run end-to-end with no live
    connection. Generic for any field set; swap the Table() for the live connector.

    THRESHOLD-INTENT RULE: when `threshold_cutoff` is given (the capability's text
    promised a numeric cutoff — see _threshold_cutoff) AND none of the synthesized
    fields is numeric, add an "amount" column spread believably around the cutoff.
    Without it _numeric_metric_field finds no metric and the flow ships without its
    number-typed input and WHERE comparison, silently dropping the thresholding."""
    fields = [f for f in (fields or []) if f] or ["id", "label", "detail"]
    recs = [{f: _synthesize_value(f, i) for f in fields} for i in range(1, n + 1)]
    if threshold_cutoff is not None and not _numeric_metric_field(recs, fields):
        for r, amt in zip(recs, _amount_spread(threshold_cutoff, len(recs))):
            r["amount"] = amt
    return recs


def _resolve_capir(recovered, display, agent_name, description, params, capir_mode):
    """Decide the CapIR a sub-agent's deterministic topic is built from — the
    topic that IS this agent.py's perform() running on STATIC stand-in data, so
    the Copilot Studio orchestrator gets the same result it would by chatting the
    brainstem and invoking the agent.py.

    Policy (capir_mode):
      off       -> never emit a topic (instructions-blob only)
      embedded  -> only when the agent.py embeds a CAPIR literal
      static    -> embedded, else recompile ONLY from real seeded data
                   (SYNTHETIC_DATA); do not synthesize a stand-in
      auto      -> (default) embedded, else recompile from SYNTHETIC_DATA, else
                   SYNTHESIZE static stand-in data from the agent's inferred data
                   shape. Maps EVERY agent.py to a self-documented topic."""
    mode = (capir_mode or "auto").lower()
    if mode in ("capture", "always", "run"):
        mode = "auto"
    if mode == "off":
        return None
    synth = recovered.get("SYNTHETIC_DATA") or []
    embedded = recovered.get("CAPIR") if isinstance(recovered.get("CAPIR"), dict) else {}
    if embedded.get("steps"):
        binding = dict(embedded.get("binding") or {})
        if not binding.get("records"):
            binding["records"] = synth
        if not binding.get("fields"):
            binding["fields"] = _capir_topic_fields(binding.get("records"))
        out = {**embedded, "binding": binding}
        out.setdefault("customer", recovered.get("CUSTOMER") or "the customer")
        return out
    if mode == "embedded":
        return None
    if mode == "static":
        result = (_recompile_capir_from_meta(recovered, display, agent_name, description,
                                             params, records=synth) if synth else None)
    else:
        # auto: always map — real seeded data if present, else a STATIC stand-in
        # synthesized from the agent's inferred data shape (its perform() field reads).
        records = synth
        if not records:
            fields = recovered.get("INFERRED_FIELDS") or [p[0] for p in (params or [])]
            # A threshold-promising capability with only synthesized stand-in data
            # needs a numeric column, or its number-input + WHERE threshold vanish.
            cutoff = _threshold_cutoff(description, recovered.get("RESPONSE"),
                                       recovered.get("TRIGGERS"))
            records = _synthesize_records(fields, threshold_cutoff=cutoff)
        result = _recompile_capir_from_meta(recovered, display, agent_name, description,
                                            params, records=records)
    # A PARTIAL declared CAPIR (binding hints only, no steps) still expresses intent —
    # write / system / table / columns. Overlay it on the recompiled CAPIR so an author
    # can declare the data source without hand-writing the whole spec.
    overlay = dict(embedded.get("binding") or {})
    if overlay and isinstance(result, dict):
        result["binding"] = {**(result.get("binding") or {}), **overlay}
    return result


def _recompile_capir_from_meta(recovered, display, agent_name, description, params, records=None):
    """Build a CapIR for an agent.py with no embedded CAPIR — mirrors T2P's
    _compile_capir shape from its records (real or synthesized), KNOWLEDGE,
    RESPONSE, DOC_NAME, TRIGGERS plus the parsed metadata. Same structure and
    perform()-parity constants as the generated path; only the source differs."""
    records = [_flatten_record(r) for r in (records if records is not None
               else (recovered.get("SYNTHETIC_DATA") or []))][:10]
    knowledge = list(recovered.get("KNOWLEDGE") or [])
    triggers = list(recovered.get("TRIGGERS") or [])
    if not triggers:
        triggers = [display] + ([re.sub(r"\s+", " ", description).strip()[:60]]
                                if description else [])
    response = recovered.get("RESPONSE") or description or f"Here is how I handle {display}."
    doc = recovered.get("DOC_NAME") or None
    key = re.sub(r"[^a-z0-9_]", "", (agent_name or display).lower().replace(" ", "_")) or "capability"
    fields = _capir_topic_fields(records)
    candidates = [f for f in fields
                  if f == "id" or f.endswith(("_id", "_number", "_code"))]
    key_blob = " ".join((display or "", description or "", response or "",
                         " ".join(str(t) for t in triggers))).lower()
    if candidates:
        def _key_score(field):
            stem = re.sub(r"_(?:id|number|code)$", "", field.lower())
            label = field.lower().replace("_", " ")
            suffix_rank = (2 if field.lower().endswith("_id")
                           else 1 if field.lower().endswith("_number") else 0)
            value_hit = any(
                str(r.get(field, "")).strip()
                and str(r.get(field, "")).strip().lower() in key_blob
                for r in records if isinstance(r, dict))
            return (6 if value_hit else 0,
                    4 if label in key_blob else 0,
                    2 if stem and stem.replace("_", " ") in key_blob else 0,
                    suffix_rank,
                    -candidates.index(field))
        key_field = max(candidates, key=_key_score)
    else:
        key_field = fields[0] if fields else "id"
    request_examples = " ".join(str(t) for t in triggers).lower()
    key_values = [
        str(r.get(key_field, "")).strip()
        for r in records if isinstance(r, dict)
        and str(r.get(key_field, "")).strip()]
    single_token_keys = not any(
        any(ch.isspace() for ch in value) for value in key_values)
    key_value_hit = any(value.lower() in request_examples for value in key_values)
    exact_key_required = bool(
        single_token_keys
        and
        (key_field == "id" or key_field.endswith(("_id", "_number", "_code")))
        and (key_value_hit or re.search(
            r"\b(?:specific|exact|given)\b[^.!?\n]{0,40}\b(?:id|number|code)\b"
            r"|\b(?:look\s*up|lookup|retrieve|find|check)\b[^.!?\n]{0,70}"
            r"\b(?:id|number|code)\b", key_blob, re.I)))
    prompt = f"What would you like to ask the {display} agent? (a keyword, id, or value to filter on)"
    binding = {
        "connector": "table",
        "table": "rec_" + key,
        "library": display + " Library",
        "fields": fields,
        "key_field": key_field,
        "exact_key_required": exact_key_required,
        "row_count": len(records),
        "records": records,
    }
    steps = [
        {"id": "trigger", "op": "trigger_match", "queries": triggers},
        {"id": "slot_query", "op": "slot_fill", "slot": "query"},
        {"id": "ground", "op": "knowledge_lookup", "facts": knowledge, "into": "Grounding"},
        {"id": "lookup", "op": "record_lookup", "source": "binding", "from": "query",
         "into": "Matches", "take": _RECOMPILE_CONSTS["example_take"],
         "fallback_take": _RECOMPILE_CONSTS["fallback_take"]},
        {"id": "respond", "op": "respond", "template_kind": "standard"},
    ]
    if doc:
        steps.append({"id": "artifact", "op": "artifact", "doc": doc,
                      "from": ["Grounding", "Matches"]})
    return {
        "schema": _CAPIR_SCHEMA,
        "key": key,
        "response": response,
        "customer": recovered.get("CUSTOMER") or "the customer",
        "binding": binding,
        "slots": [{"name": "query", "entity": "StringPrebuiltEntity",
                   "prompt": prompt, "required": True}],
        "consts": dict(_RECOMPILE_CONSTS),
        "steps": steps,
        "expect": list(triggers),
        "triggers_owned": True,
    }


def _subagents_from_stack(stack_dir: Path, capir_mode: str = "auto") -> List[SubAgentSpec]:
    agents_dir = stack_dir / "agents"
    if not agents_dir.is_dir():
        agents_dir = stack_dir
    subs: List[SubAgentSpec] = []
    for py in sorted(agents_dir.glob("*.py")):
        if py.name.startswith("_") or py.name == "basic_agent.py":
            continue
        # One malformed agent file must never kill the whole stack: isolate each
        # per-file parse so a bad schema drops that agent and keeps the rest.
        try:
            parsed = _parse_basic_agent(py)
            if not parsed:
                logger.warning("  - %s: no BasicAgent subclass, skipping", py.name)
                continue
            display, agent_name, description, module_doc, params, recovered = parsed
            capir = _resolve_capir(recovered, display, agent_name, description, params, capir_mode)
            # Code-interpreter recipe: only for HANDWRITTEN agents with a real,
            # non-trivial perform() (a T2P-generated agent embeds CAPIR and its
            # perform() is the generic interpreter the flow already mirrors 1:1).
            perform_src = recovered.get("PERFORM_SOURCE") or ""
            compute_source = None
            if recovered.get("CAPIR") is None and perform_src.count("\n") >= 10:
                compute_source = perform_src
            subs.append(SubAgentSpec(
                agent_name=agent_name,
                display_name=display,
                # description carries the input contract so the orchestrator knows what
                # to pass when it delegates (self-documented, like the agent.py).
                description=_contract_description(description, params) or f"Handle {display} requests.",
                instructions=_stack_subagent_instructions(display, description, module_doc, params),
                capir=capir,
                params=params,
                compute_source=compute_source,
            ))
            logger.info("  + %s%s%s", display, "  [deterministic flow]" if capir else "",
                        "  [code-interpreter recipe]" if compute_source else "")
        except Exception as exc:  # noqa: BLE001
            logger.warning("  - %s: failed to parse, skipping (%s)", py.name, exc)
            continue
    return subs


def _load_stack_metadata(stack_dir: Path) -> dict:
    mpath = stack_dir / "metadata.json"
    if mpath.is_file():
        try:
            return json.loads(mpath.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _author_demo_reference_material(subs: List[SubAgentSpec], display_name: str,
                                    meta: dict) -> None:
    """Populate each sub-agent's `reference_material` (tag "refmat") for the DEMO
    twin: ONE LLM call authors a short domain briefing per capability, GROUNDED in
    that capability's OWN shipped records (with a deterministic fallback + a
    verify-and-mend pass, both in T2P), so the demo child bots can answer
    "why/what does this mean" questions about the SAME synthetic entries their
    flows return. The pipeline generates this itself — never a manual upload. A
    no-op when the T2P authoring helper isn't importable or no sub ships records,
    and it NEVER raises, so packaging never depends on the network. Mutates
    `subs` in place; only the demo twin (name_suffix set) renders the result."""
    try:
        from agents.transcript2prototype_agent import author_reference_sections  # type: ignore
    except ImportError:
        try:
            from transcript2prototype_agent import author_reference_sections  # type: ignore
        except ImportError:
            return
    views, keyed, seen = [], [], set()
    for sub in subs:
        capir = getattr(sub, "capir", None) or {}
        binding = capir.get("binding") or {}
        recs = [r for r in (binding.get("records") or []) if isinstance(r, dict) and r]
        if not recs:
            continue
        base = str(capir.get("key") or sub.agent_name or sub.display_name or "cap")
        key, i = base, 2
        while key in seen:
            key = "%s_%d" % (base, i)
            i += 1
        seen.add(key)
        views.append({"key": key, "name": sub.display_name,
                      "description": sub.description,
                      "generative": bool(binding.get("generative")),
                      "write": bool(binding.get("write")),
                      "response": capir.get("response") or "",
                      "triggers": capir.get("expect") or [],
                      "synthetic_records": recs})
        keyed.append((sub, key))
    if not views:
        return
    company = (meta or {}).get("name") or display_name or "the customer"
    # The synchronous /pipeline route has a hard Azure gateway ceiling. The
    # deterministic fallback is already verified/mended against the shipped
    # rows and avoids a second authoring call after distillation. Makers can
    # opt the prose-enhancement call back in outside latency-sensitive paths.
    use_llm = os.environ.get("DEMO_REFERENCE_LLM", "").strip().lower() in (
        "1", "true", "yes", "on")
    sections = author_reference_sections(
        display_name, company, views, use_llm=use_llm) or {}
    for sub, key in keyed:
        sec = sections.get(key)
        if sec:
            sub.reference_material = sec


def _orchestrator_instructions_from_metadata(
        meta: dict, subs: List[SubAgentSpec], topology: str = "hierarchical") -> str:
    name = meta.get("name", "the agent stack")
    desc = meta.get("description", "")
    lines = [f"You are the orchestrator for {name}.", ""]
    if desc:
        lines += [desc, ""]
    flat = str(topology or "hierarchical").lower() == "flat"
    lines.append(
        "You answer directly by selecting and calling the right deterministic flow tool."
        if flat else
        "You route each user request to the right connected sub-agent and never do their specialized work yourself.")
    features = meta.get("features") or []
    if features:
        lines += ["", "End-to-end flow this stack supports, in order:"]
        lines += [f"- {f}" for f in features]
    lines += ["", ("Capabilities exposed as flow tools:"
                   if flat else "Connected sub-agents you can delegate to:")]
    for sub in subs:
        lines.append(f"- {sub.display_name}: {sub.description}")
    starters = meta.get("starters") or []
    if starters:
        lines += ["", "Example requests you should expect:"]
        lines += [f"- {s}" for s in starters]
    lines += [
        "",
        "Routing rules:",
        ("- Pick the single best-matching flow tool and call it; pass the inputs named in its description."
         if flat else
         "- Pick the single best-matching connected agent for the request and delegate to it; pass it the inputs named in its description."),
        ("- Each flow tool runs the generated agent.py capability's deterministic logic."
         if flat else
         "- Calling a connected agent gives you the SAME result you would get by chatting the source brainstem and letting it invoke that agent.py — each connected agent's topic runs the agent's deterministic logic on its seeded sample data."),
        ("- If a request spans several flow tools, call one at a time, show its result, then continue."
         if flat else
         "- If a request spans several connected agents, handle one per turn, show its result, then continue to the next."),
        "- If a required input is missing, ask for it. The seeded data is synthetic stand-in data; do not invent records beyond it.",
        "- Treat tool outputs as the complete fact boundary. Use only explicit tool facts; if a requested fact is absent, say it is unavailable.",
        "- Never invent actions, owners, causes, delivery states, timestamps, SLAs, or citations. Synthetic demo data is never an official source.",
        "- When data_provenance is synthetic_demo, the first sentence must explicitly say the answer uses synthetic demo context and is not an official source.",
        "- Do not turn status fields into actions, plans, assignments, or owners. If those fields are absent, say unavailable.",
        "- Preserve simulation/demo qualifiers. Claim an external action succeeded only when action_status is succeeded and receipt is non-empty.",
        "- For a capability that both generates content and performs an action, compose the complete content first, pass that draft to the flow tool, then show the same draft with its action status and receipt.",
        "- If no connected agent or flow tool fits, say the capability is not implemented; do not answer the specialized business request from general knowledge.",
    ]
    return "\n".join(lines)


def validate_connected_solution(zip_path: Path) -> bool:
    """Structural checks that the connected solution is import-shaped."""
    ok = True
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = set(zf.namelist())

        # OPC forbids duplicate part names; a set() view hides them, and the
        # importer can reject the package (or silently shadow one part — one
        # lost capability). Compare the raw namelist against its set view.
        namelist = zf.namelist()
        if len(namelist) != len(names):
            dupes = sorted({p for p in namelist if namelist.count(p) > 1})
            logger.error("  X %d duplicate part names (e.g. %s)", len(dupes), dupes[:3])
            ok = False

        for required in ("[Content_Types].xml", "solution.xml", "customizations.xml"):
            if required not in names:
                logger.error("  X missing %s", required)
                ok = False

        bots = sorted({n.split("/")[1] for n in names if n.startswith("bots/")})
        logger.info("  bots: %d (%s)", len(bots), ", ".join(bots))

        # Every connected-action must reference an existing child bot.
        actions = [n for n in names if ".InvokeConnectedAgentTaskAction." in n and n.endswith("/dependencies.json")]
        logger.info("  connected-agent actions: %d", len(actions))
        for dep in actions:
            child = json.loads(zf.read(dep).decode("utf-8"))[0]["schemaName"]
            if f"bots/{child}/bot.xml" not in names:
                logger.error("  X action %s -> missing child bot %s", dep, child)
                ok = False
            data_path = dep.rsplit("/", 1)[0] + "/data"
            if data_path in names:
                data_text = zf.read(data_path).decode("utf-8")
                if f"botSchemaName: {child}" not in data_text:
                    logger.error("  X %s data does not invoke %s", data_path, child)
                    ok = False

        # Deterministic capability flows: every declared Workflow must ship its
        # JSON (agent-callable Skills trigger + Respond), be a RootComponent,
        # and every flow TOOL must point at a declared WorkflowId.
        cust = zf.read("customizations.xml").decode("utf-8")
        sol = zf.read("solution.xml").decode("utf-8")
        declared = re.findall(
            r'<Workflow WorkflowId="\{([0-9a-fA-F-]+)\}"[^>]*>.*?<JsonFileName>/(Workflows/[^<]+)</JsonFileName>',
            cust, re.DOTALL)
        logger.info("  workflows: %d declared", len(declared))
        for wf_id, json_name in declared:
            if json_name not in names:
                logger.error("  X workflow %s missing %s", wf_id, json_name)
                ok = False
                continue
            try:
                d = json.loads(zf.read(json_name).decode("utf-8"))
                trig = d["properties"]["definition"]["triggers"]["manual"]
                if trig.get("kind") != "Skills" or trig.get("type") != "Request":
                    logger.error("  X %s trigger is not agent-callable (kind=%s)",
                                 json_name, trig.get("kind"))
                    ok = False
                conn_refs = d["properties"].get("connectionReferences") or {}
                acts = d["properties"]["definition"].get("actions") or {}
                api_actions = {k: a for k, a in acts.items()
                               if str(a.get("type")) == "OpenApiConnection"}
                if conn_refs:
                    # LIVE twin: every ref must be declared in customizations,
                    # every connector action must bind to a declared ref key,
                    # and $connections must be a definition parameter.
                    for key, ref in conn_refs.items():
                        logical = ((ref.get("connection") or {})
                                   .get("connectionReferenceLogicalName") or "")
                        if f'connectionreferencelogicalname="{logical}"' not in cust:
                            logger.error("  X %s ref %s not declared in customizations",
                                         json_name, logical)
                            ok = False
                    for ak, act in api_actions.items():
                        cn = ((act.get("inputs") or {}).get("host") or {}).get("connectionName")
                        if cn not in conn_refs:
                            logger.error("  X %s action %s connectionName %r has no ref",
                                         json_name, ak, cn)
                            ok = False
                    if "$connections" not in (d["properties"]["definition"]
                                              .get("parameters") or {}):
                        logger.error("  X %s has refs but no $connections parameter", json_name)
                        ok = False
                elif api_actions:
                    logger.error("  X %s has connector actions but no connection references",
                                 json_name)
                    ok = False
            except Exception as exc:  # noqa: BLE001
                logger.error("  X %s does not parse: %s", json_name, exc)
                ok = False
            if f'type="29" id="{{{wf_id.lower()}}}"' not in sol.lower():
                logger.error("  X workflow %s missing from RootComponents", wf_id)
                ok = False
        declared_ids = {wf_id.lower() for wf_id, _ in declared}
        flow_tools = []
        for n in names:
            if n.startswith("botcomponents/") and n.endswith("/data"):
                data_text = zf.read(n).decode("utf-8")
                if "kind: InvokeFlowTaskAction" in data_text:
                    flow_tools.append(n)
                    m = re.search(r"flowId:\s*([0-9a-fA-F-]+)", data_text)
                    if not m or m.group(1).lower() not in declared_ids:
                        logger.error("  X %s does not reference a declared workflow", n)
                        ok = False
        logger.info("  flow tools: %d", len(flow_tools))
        if declared and "Assets/botcomponent_workflowset.xml" in names:
            wfset = zf.read("Assets/botcomponent_workflowset.xml").decode("utf-8")
            for comp, wf in re.findall(
                    r'botcomponentid\.schemaname="([^"]+)" workflowid\.workflowid="([^"]+)"', wfset):
                if f"botcomponents/{comp}/data" not in names:
                    logger.error("  X workflowset references missing component %s", comp)
                    ok = False
                if wf.lower() not in declared_ids:
                    logger.error("  X workflowset references undeclared workflow %s", wf)
                    ok = False
        elif flow_tools:
            logger.error("  X flow tools present but Assets/botcomponent_workflowset.xml missing")
            ok = False

        # Every extensionless /data part must be declared in [Content_Types].xml.
        ct = zf.read("[Content_Types].xml").decode("utf-8")
        data_parts = [n for n in names if n.endswith("/data")]
        missing = [p for p in data_parts if f'PartName="/{p}"' not in ct]
        if missing:
            logger.error("  X %d /data parts missing from [Content_Types].xml (e.g. %s)",
                         len(missing), missing[0])
            ok = False
        else:
            logger.info("  content-types: all %d /data parts declared", len(data_parts))

        # Each bot needs gpt.default + the system-topic set.
        for bot in bots:
            if f"botcomponents/{bot}.gpt.default/data" not in names:
                logger.error("  X bot %s missing gpt.default", bot)
                ok = False

        # No botcomponent schema name may exceed the Dataverse 100-char limit.
        schemas = {n.split("/")[1] for n in names if n.startswith("botcomponents/")}
        longest = max(schemas, key=len) if schemas else ""
        if len(longest) > 100:
            logger.error("  X schema name too long (%d > 100): %s", len(longest), longest)
            ok = False
        else:
            logger.info("  schema lengths: max %d/100 (%s)", len(longest), longest)

        # Copilot Studio rejects bot display names longer than 42 chars.
        # (The limit applies to the DECODED value, so unescape before measuring.)
        worst_name, worst_len = "", 0
        for bot in bots:
            bx = zf.read(f"bots/{bot}/bot.xml").decode("utf-8")
            m = re.search(r"<name>(.*?)</name>", bx, re.DOTALL)
            nm = (m.group(1).strip() if m else "")
            for ent, ch in (("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&amp;", "&")):
                nm = nm.replace(ent, ch)
            if len(nm) > worst_len:
                worst_name, worst_len = nm, len(nm)
        if worst_len > 42:
            logger.error("  X bot name too long (%d > 42): %s", worst_len, worst_name)
            ok = False
        else:
            logger.info("  bot names: max %d/42 (%s)", worst_len, worst_name)
    return ok


# ===========================================================================
# Autonomous deploy to Microsoft Copilot Studio (Dataverse Web API, stdlib only)
#
# Self-contained so this one file, dropped into any brainstem, can BOTH package a
# connected-agents solution AND import + publish it into a real Copilot Studio
# environment — no pac CLI, no third-party packages. App-registration credentials
# come ONLY from env vars or a settings file, never from chat, and the secret is
# never echoed back. Same proven path as the T2P deploy agent: service-principal
# token -> ImportSolution -> PvaPublish (children first, orchestrator last).
# ===========================================================================

_DEPLOY_AUTH = "https://login.microsoftonline.com"


def _http(url, data=None, headers=None, method=None, timeout=300):
    """Minimal stdlib HTTP: dict data -> form-encoded (OAuth), else JSON bytes."""
    if isinstance(data, dict):
        data = urllib.parse.urlencode(data).encode()
    elif data is not None and not isinstance(data, (bytes, bytearray)):
        data = json.dumps(data).encode()
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, (json.loads(body) if body[:1] in ("{", "[") else body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, body
    except Exception as e:  # network / DNS / timeout
        return 0, str(e)


def _extract_dyn_creds(creds):
    """From a settings dict ({IsEncrypted,Values} or bare), a Values dict, or a
    JSON string -> {client_id, client_secret, tenant_id, resource} or None."""
    if isinstance(creds, str):
        try:
            creds = json.loads(creds)
        except Exception:
            return None
    if not isinstance(creds, dict):
        return None
    vals = creds.get("Values", creds)
    cid, sec = vals.get("DYNAMICS_365_CLIENT_ID"), vals.get("DYNAMICS_365_CLIENT_SECRET")
    ten, res = vals.get("DYNAMICS_365_TENANT_ID"), vals.get("DYNAMICS_365_RESOURCE")
    if not all([cid, sec, ten, res]):
        return None
    return {"client_id": cid, "client_secret": sec, "tenant_id": ten, "resource": str(res).rstrip("/")}


def _deploy_creds(kwargs):
    """Resolve app-registration creds for deploy — env / settings file ONLY, never
    from chat. Returns (creds_dict, source_label) or (None, reason).

    An explicitly supplied credentials_path is AUTHORITATIVE: ONLY that file is
    considered. If it is missing, unparseable, or lacks the required
    DYNAMICS_365_* keys, return (None, "<path> unusable: <reason>") so the deploy
    fails loudly naming the file instead of silently falling through to env /
    home / local creds (which could land the deploy in the WRONG environment).
    The fallback chain below runs ONLY when credentials_path was omitted."""
    explicit = kwargs.get("credentials_path")
    if explicit:
        path = os.path.expanduser(explicit)
        if not os.path.isfile(path):
            return None, "%s unusable: file not found" % path
        try:
            raw = json.load(open(path))
        except Exception as e:
            return None, "%s unusable: not valid JSON (%s)" % (path, str(e)[:120])
        c = _extract_dyn_creds(raw)
        if not c:
            return None, ("%s unusable: missing required DYNAMICS_365_CLIENT_ID / "
                          "CLIENT_SECRET / TENANT_ID / RESOURCE" % path)
        return c, path
    candidates = [
        os.environ.get("RAPP_DEPLOY_SETTINGS"),
        os.path.expanduser("~/.rapp_deploy_settings.json"),
        "local.settings.json",
    ]
    for cand in candidates:
        if cand and os.path.isfile(cand):
            try:
                c = _extract_dyn_creds(json.load(open(cand)))
                if c:
                    return c, cand
            except Exception:
                pass
    c = _extract_dyn_creds({"Values": dict(os.environ)})
    if c:
        return c, "process env"
    return None, None


def _sp_token(client_id, secret, tenant, resource):
    """Service-principal (client-credentials) token for the Dataverse env."""
    code, t = _http(f"{_DEPLOY_AUTH}/{tenant}/oauth2/v2.0/token",
                    data={"grant_type": "client_credentials", "client_id": client_id,
                          "client_secret": secret, "scope": resource.rstrip("/") + "/.default"},
                    headers={"Content-Type": "application/x-www-form-urlencoded"})
    if code != 200 or not isinstance(t, dict) or "access_token" not in t:
        raise RuntimeError("service-principal auth failed: " + str(t)[:200])
    return t["access_token"]


def _dataverse_action(resource, token, action, body=None, method="POST"):
    data = json.dumps(body).encode() if body is not None else None
    return _http(resource.rstrip("/") + "/api/data/v9.2/" + action, data=data, method=method,
                 headers={"Authorization": "Bearer " + token, "Content-Type": "application/json",
                          "Accept": "application/json", "OData-MaxVersion": "4.0",
                          "OData-Version": "4.0"})


def _import_solution(resource, token, zip_bytes):
    """ImportSolution (unmanaged, overwrite) then PublishAllXml."""
    code, r = _dataverse_action(resource, token, "ImportSolution", {
        "OverwriteUnmanagedCustomizations": True, "PublishWorkflows": True,
        "ImportJobId": str(uuid.uuid4()),
        "CustomizationFile": base64.b64encode(zip_bytes).decode()})
    if code not in (200, 204):
        raise RuntimeError("ImportSolution failed (%s): %s" % (code, str(r)[:400]))
    _dataverse_action(resource, token, "PublishAllXml")


def _activate_flows(resource, token, workflow_ids):
    """Activate imported capability flows (Draft -> Activated). ImportSolution's
    PublishWorkflows alone leaves hand-packaged flows in Draft, so each one is
    PATCHed explicitly; the flows ship connector-free, so activation has no
    connection prerequisites."""
    out = []
    for wf in workflow_ids or []:
        wf = str(wf).strip("{}")
        code, r = _http(
            resource + "/api/data/v9.2/workflows(" + wf + ")",
            data=json.dumps({"statecode": 1, "statuscode": 2}).encode(),
            headers={"Authorization": "Bearer " + token,
                     "Content-Type": "application/json",
                     "Accept": "application/json", "If-Match": "*"},
            method="PATCH")
        if code in (200, 204):
            out.append({"workflow_id": wf, "status": "activated"})
        else:
            err = str(r)[:300]
            # A LIVE-twin flow can't activate until the customer binds its
            # connection reference / sets its REPLACE_ parameters — that is
            # the expected hook-into-your-data step, not a deploy failure.
            low = err.lower()
            pending = ("connection" in low or "consent" in low
                       or "invalidopenapiflow" in low or "dynamicoperation" in low)
            out.append({"workflow_id": wf,
                        "status": "pending_connection" if pending else "activate_failed",
                        "error": err[:160]})
    return out


def _find_botid(resource, token, schema):
    qs = urllib.parse.urlencode({"$select": "botid,schemaname",
                                 "$filter": "schemaname eq '%s'" % schema,
                                 "$orderby": "createdon desc", "$top": "1"})
    code, r = _http(resource.rstrip("/") + "/api/data/v9.2/bots?" + qs,
                    headers={"Authorization": "Bearer " + token, "Accept": "application/json"})
    rows = (r.get("value") if isinstance(r, dict) else None) or []
    return rows[0]["botid"] if rows else None


def _publish_botid(botid, resource, token):
    """Publish ONE bot via the Dataverse PvaPublish Web API action. PURE HTTPS —
    no pac/CLI/subprocess — so this agent.py runs identically in a local brainstem
    AND inside an Azure-Function-hosted brainstem (no binary to ship)."""
    code, r = _dataverse_action(resource, token,
                                "bots(%s)/Microsoft.Dynamics.CRM.PvaPublish" % botid, {})
    if code in (200, 204):
        return {"bot_id": botid, "status": "publish_requested", "via": "PvaPublish"}
    return {"bot_id": botid, "status": "publish_failed", "via": "PvaPublish", "error": str(r)[:160]}


def _publish_connected(bot_schemas, resource, token):
    """Publish every bot — CHILDREN first, ORCHESTRATOR last (a connected-agent
    root cannot publish until its invoked sub-agents are published)."""
    if not bot_schemas:
        return []
    orch = bot_schemas[0]
    order = list(bot_schemas[1:]) + [orch]
    out = []
    for schema in order:
        botid = _find_botid(resource, token, schema)
        if not botid:
            out.append({"schema": schema, "status": "not_found"})
            continue
        out.append({"schema": schema, **_publish_botid(botid, resource, token)})
    return out


def _run_deploy(zip_bytes, bot_schemas, orch_display, kwargs, workflow_ids=None):
    """Import + activate the capability flows + (optionally) publish the
    connected solution into Copilot Studio. Returns a result dict with a human
    `summary`; never includes the secret."""
    creds, src = _deploy_creds(kwargs)
    if creds and kwargs.get("environment_url"):
        creds = {**creds, "resource": str(kwargs["environment_url"]).rstrip("/")}
    if not creds:
        return {"status": "creds_missing",
                "summary": "NOT deployed — no app-registration credentials found.",
                "how_to": ("Set env DYNAMICS_365_CLIENT_ID / DYNAMICS_365_CLIENT_SECRET / "
                           "DYNAMICS_365_TENANT_ID / DYNAMICS_365_RESOURCE, or pass "
                           "credentials_path=<local.settings.json>, or place "
                           "~/.rapp_deploy_settings.json. Secrets never travel through chat.")}
    publish = bool(kwargs.get("publish", True))
    try:
        token = _sp_token(creds["client_id"], creds["client_secret"],
                          creds["tenant_id"], creds["resource"])
    except Exception as e:
        return {"status": "auth_failed", "summary": "NOT deployed — service-principal auth failed.",
                "error": str(e)[:300], "creds_source": src, "environment": creds["resource"]}
    try:
        _import_solution(creds["resource"], token, zip_bytes)
    except Exception as e:
        return {"status": "import_failed", "summary": "Import FAILED.", "error": str(e)[:400],
                "environment": creds["resource"], "creds_source": src}
    activated = _activate_flows(creds["resource"], token, workflow_ids)
    nact = sum(1 for a in activated if a.get("status") == "activated")
    npend = sum(1 for a in activated if a.get("status") == "pending_connection")
    published = _publish_connected(bot_schemas, creds["resource"], token) if publish else []
    npub = sum(1 for p in published if p.get("status") in ("published", "publish_requested"))
    # Only a GENUINE failure downgrades the deploy. A flow that ACTIVATED or is
    # PENDING_CONNECTION (the expected live-twin bind-your-data step — Draft by
    # design) is a success; only 'activate_failed' is a real failure. A bot that
    # PUBLISHED (published/publish_requested) is a success; 'publish_failed' or
    # 'not_found' is a real failure.
    errors = []
    for a in activated:
        if a.get("status") == "activate_failed":
            errors.append("flow %s activate_failed: %s"
                          % (a.get("workflow_id"), str(a.get("error", ""))[:120]))
    for p in published:
        if p.get("status") in ("publish_failed", "not_found"):
            errors.append("bot %s %s%s"
                          % (p.get("schema"), p.get("status"),
                             (": " + str(p.get("error"))[:120]) if p.get("error") else ""))
    summary = ("Imported into " + creds["resource"] + ", "
               + (("activated %d/%d flows, " % (nact, len(activated))) if activated else "")
               + (("%d flow(s) pending connection binding (bind under Solutions > "
                   "Connection references, then turn them on), " % npend) if npend else "")
               + (("published %d/%d bots. " % (npub, len(published))) if publish else "skipped publish. ")
               + "Open Copilot Studio, select that environment, open '"
               + orch_display[:42] + "' and use the Test pane.")
    # 'deployed' ONLY when every step succeeded; otherwise flag it loudly
    # ('deployed_with_errors' + the failing entries) so perform() downgrades the
    # overall result to "partial" instead of falsely reporting success.
    status = "deployed" if not errors else "deployed_with_errors"
    if errors:
        summary += (" %d step(s) FAILED — " % len(errors)) + "; ".join(errors)
    return {"status": status, "summary": summary, "environment": creds["resource"],
            "orchestrator": orch_display[:42], "publish_enabled": publish,
            "flows_activated": activated, "published": published, "creds_source": src,
            "errors": errors, "test_in_studio": "https://copilotstudio.microsoft.com"}


# ---------------------------------------------------------------------------
# RAPP agent wrapper
# ---------------------------------------------------------------------------

class ConnectedSolutionAgent(BasicAgent):
    """Generate a connected-agent (orchestrator + sub-agents) Copilot Studio solution."""

    def __init__(self):
        self.name = "ConnectedSolutionAgent"
        self.metadata = {
            "name": self.name,
            "description": (
                "Turn an agent stack (a folder of BasicAgent *.py files + optional "
                "metadata.json) or an explicit list of sub-agents into ONE import-ready "
                "Microsoft Copilot Studio connected-agent solution: an orchestrator plus "
                "one connected sub-agent per agent, wired with InvokeConnectedAgentTaskAction. "
                "When an agent.py carries its compiled CapIR (t2p-capir/1.0) — or one can be "
                "recompiled from its seeded data — each sub-agent ALSO gets a REAL "
                "deterministic capability topic that runs the same steps as the agent.py's "
                "perform() (trigger -> the user's real query -> filter the seeded records -> "
                "branch -> respond, plus the document for artifact capabilities); only the "
                "data is mocked, so flipping the in-topic Table() to a live Dataverse / "
                "SharePoint connector is the one-line move to production. No code deploy. Bot "
                "names are auto-capped to 42 chars and orchestrator channels default off so it "
                "imports and publishes fully headlessly."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "stack_dir": {
                        "type": "string",
                        "description": "Path to an agent stack folder. Each BasicAgent *.py under it "
                                       "(or its agents/ subfolder) becomes one connected sub-agent; "
                                       "metadata.json (name/description/features/starters) shapes the orchestrator.",
                    },
                    "subagents": {
                        "type": "array",
                        "description": "Alternative to stack_dir: explicit sub-agents, each an object with "
                                       "agent_name, display_name, description, instructions.",
                    },
                    "solution_name": {
                        "type": "string",
                        "description": "Solution unique name (alphanumeric). Defaults from metadata.json id / stack folder name.",
                    },
                    "solution_display_name": {"type": "string", "description": "Solution friendly name."},
                    "orchestrator_name": {
                        "type": "string",
                        "description": "Orchestrator display name (auto-capped to 42 chars, 'Orchestrator' kept).",
                    },
                    "orchestrator_channels": {
                        "type": "boolean",
                        "description": "Declare MsTeams + M365 Copilot channels on the orchestrator. Default false "
                                       "(headlessly publishable). True requires a maker-portal publish.",
                    },
                    "static_connectors": {
                        "type": "boolean",
                        "description": (
                            "Resolve LIVE twin operations to pinned public no-PII "
                            "static adapters. Default false."
                        ),
                    },
                    "static_transport": {
                        "type": "string",
                        "enum": ["http", "connector"],
                        "description": (
                            "Runtime transport for static_connectors: 'http' (default, "
                            "built-in connectionless HTTP GET) or 'connector' (packaged "
                            "no-auth custom connector requiring manual binding). Valid "
                            "only when static_connectors=true."
                        ),
                    },
                    "catalog_agent_id": {
                        "type": "string",
                        "description": (
                            "Optional canonical <industry>/<slug> route used to resolve "
                            "static adapter resources."
                        ),
                    },
                    "capir_mode": {
                        "type": "string",
                        "description": "How to build the deterministic per-capability topic inside each "
                                       "sub-agent (the topic that runs the agent.py's perform() logic on STATIC "
                                       "synthetic stand-in data): 'auto' (default) uses an embedded CapIR, else "
                                       "real seeded data, else SYNTHESIZES static stand-in records from the "
                                       "agent's inferred data shape — so EVERY agent.py maps to a self-documented "
                                       "topic; 'static' uses only real seeded data (no synthetic stand-in); "
                                       "'embedded' uses only an embedded CapIR; 'off' emits instructions-only "
                                       "sub-agents. Synthetic data is the swap-for-live seam (Table() -> connector).",
                    },
                    "version": {"type": "string", "description": "Solution version, e.g. 1.0.0.0."},
                    "output_path": {
                        "type": "string",
                        "description": "Where to write the .zip. Defaults to <SolutionName>_connected_solution.zip.",
                    },
                    "deploy": {
                        "type": "boolean",
                        "description": "When true, AUTONOMOUSLY import the solution into your Microsoft Copilot "
                                       "Studio (Dataverse) environment and publish every bot (sub-agents first, "
                                       "orchestrator last) — no pac CLI needed, stdlib only. App-registration "
                                       "credentials are read ONLY from env vars (DYNAMICS_365_CLIENT_ID / "
                                       "DYNAMICS_365_CLIENT_SECRET / DYNAMICS_365_TENANT_ID / DYNAMICS_365_RESOURCE) "
                                       "or a settings file — NEVER from chat. Default false (package only).",
                    },
                    "publish": {
                        "type": "boolean",
                        "description": "When deploy=true, also publish the bots after import (default true). "
                                       "false imports without publishing.",
                    },
                    "credentials_path": {
                        "type": "string",
                        "description": "Path to a local.settings.json-style file holding DYNAMICS_365_CLIENT_ID / "
                                       "DYNAMICS_365_CLIENT_SECRET / DYNAMICS_365_TENANT_ID / DYNAMICS_365_RESOURCE "
                                       "(under a top-level 'Values' object or at the root). Used only for deploy; "
                                       "the secret is never echoed back. If omitted, env vars / "
                                       "~/.rapp_deploy_settings.json / ./local.settings.json are tried.",
                    },
                    "environment_url": {
                        "type": "string",
                        "description": "Optional override for the target Dataverse environment URL (e.g. "
                                       "https://yourorg.crm.dynamics.com). Defaults to DYNAMICS_365_RESOURCE from the creds.",
                    },
                    "publisher_prefix": {
                        "type": "string",
                        "description": "Customization prefix for the bot schema names (2-8 lowercase alphanumerics, "
                                       "default 'rapp'). Use a FRESH prefix to mint brand-new, isolated bots + a "
                                       "distinct solution instead of updating ones that already exist.",
                    },
                    "publisher_name": {
                        "type": "string",
                        "description": "Solution publisher unique name (default 'DefaultPublisher'). Pair a fresh "
                                       "publisher_name with a fresh publisher_prefix to create a brand-new publisher.",
                    },
                    "publisher_display": {
                        "type": "string",
                        "description": "Solution publisher friendly name (default 'Default Publisher').",
                    },
                },
                "required": [],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs):
        static_enabled = bool(kwargs.get("static_connectors", False))
        try:
            static_transport = normalize_static_transport(
                static_enabled, kwargs.get("static_transport")
            )
        except ValueError as exc:
            return {"status": "error", "agent": self.name, "message": str(exc)}
        stack_dir = kwargs.get("stack_dir")
        subagents_in = kwargs.get("subagents")
        if not stack_dir and not subagents_in:
            return {
                "status": "needs_input",
                "agent": self.name,
                "message": "Provide 'stack_dir' (a folder of BasicAgent *.py + optional metadata.json) "
                           "or 'subagents' (a list of {agent_name, display_name, description, instructions}).",
            }

        meta: Dict[str, Any] = {}
        if stack_dir:
            sd = Path(stack_dir)
            if not sd.exists():
                return {"status": "error", "agent": self.name, "message": f"stack_dir not found: {sd}"}
            subs = _subagents_from_stack(sd, capir_mode=str(kwargs.get("capir_mode") or "auto"))
            meta = _load_stack_metadata(sd)
            fallback = _humanize(sd.name)
        else:
            subs = []
            for s in subagents_in:
                dn = s.get("display_name") or s.get("agent_name") or "Agent"
                subs.append(SubAgentSpec(
                    agent_name=s.get("agent_name") or dn,
                    display_name=dn,
                    description=(s.get("description") or "").strip() or f"Handle {dn} requests.",
                    instructions=s.get("instructions") or "",
                    capir=s.get("capir") if isinstance(s.get("capir"), dict) else None,
                ))
            fallback = kwargs.get("solution_name") or "Connected Agents"

        if not subs:
            return {"status": "error", "agent": self.name, "message": "No sub-agents found to bundle."}

        short = re.sub(r"\b(Agent\s+Stack|Agent|Stack)\b", "", meta.get("name", "")).strip()
        unique = re.sub(r"[^A-Za-z0-9]", "",
                        kwargs.get("solution_name") or meta.get("id", "") or fallback.replace(" ", ""))
        display = kwargs.get("solution_display_name") or meta.get("name") or f"{fallback} Agents"
        orch_name = kwargs.get("orchestrator_name") or f"{short or fallback} Orchestrator"
        topology = str(kwargs.get("topology") or "hierarchical")
        orch_instructions = (
            _orchestrator_instructions_from_metadata(meta, subs, topology=topology)
            if meta else "")

        common = dict(
            orchestrator_display_name=orch_name,
            subagents=subs,
            orchestrator_instructions=orch_instructions,
            orchestrator_channels=bool(kwargs.get("orchestrator_channels", False)),
            capability_mode=str(kwargs.get("capability_mode") or "flow"),
            topology=topology,
            solution_version=kwargs.get("version", "1.0.0.0"),
            # publisher controls — a fresh publisher_prefix mints brand-new bot
            # schema names (an isolated, clearly-distinct solution), instead of
            # updating bots that already exist under the default 'rapp' prefix.
            publisher_prefix=re.sub(r"[^a-z0-9]", "", str(kwargs.get("publisher_prefix") or "rapp").lower())[:8] or "rapp",
            publisher_unique_name=kwargs.get("publisher_name") or "DefaultPublisher",
            publisher_display_name=kwargs.get("publisher_display") or "Default Publisher",
        )
        unique = unique or "ConnectedAgents"
        # twins=True (the pipeline default): emit BOTH the LIVE prototype
        # (real connector actions through connection references — the primary,
        # keeps the base name) and its DEMO twin (synthetic data, activates
        # with zero connections — the fallback, "<name>Demo").
        twins = bool(kwargs.get("twins"))
        # DEMO twin (tag "refmat"): the pipeline authors grounded reference
        # material per capability and embeds it in the demo child bots. Populate
        # it on the SHARED sub specs before packaging so ONLY the demo twin
        # (name_suffix set) renders it; the live packaging below ignores it.
        if twins:
            try:
                _author_demo_reference_material(subs, display, meta)
            except Exception as exc:  # noqa: BLE001 - never block packaging on this
                logger.warning("  - reference material authoring skipped (%s)", exc)
        spec = ConnectedSolutionSpec(
            solution_unique_name=unique,
            solution_display_name=display,
            live_connectors=twins,
            static_connectors=static_enabled,
            static_transport=static_transport,
            catalog_agent_id=str(kwargs.get("catalog_agent_id") or ""),
            twin_display_name=(display + " (Demo)") if twins else "",
            **common,
        )
        # topology/capability_mode conflicts (e.g. flat+topic) raise ValueError in
        # the packager __init__ — surface that as a clean error result, no traceback.
        try:
            packager = ConnectedSolutionPackager(spec)
        except ValueError as e:
            return {"status": "error", "agent": self.name, "message": str(e)}
        out = Path(kwargs.get("output_path") or f"{spec.solution_unique_name}_connected_solution.zip")
        data = packager.package(output_path=out)
        ok = validate_connected_solution(out)

        demo_packager, demo_out, demo_ok, demo_data = None, None, True, None
        if twins:
            demo_spec = ConnectedSolutionSpec(
                solution_unique_name=unique + "Demo",
                solution_display_name=display + " (Demo)",
                # In static mode the test twin exercises the SAME pinned public
                # API over zero-bind HTTP, while keeping anonymous Direct Line
                # auth via name_suffix. Non-static runs retain embedded Compose.
                live_connectors=static_enabled,
                static_connectors=static_enabled,
                static_transport=static_transport,
                catalog_agent_id=str(kwargs.get("catalog_agent_id") or ""),
                twin_display_name=display,
                name_suffix=" (Demo)",
                **common,
            )
            demo_packager = ConnectedSolutionPackager(demo_spec)
            demo_out = out.with_name(out.stem + "_demo" + out.suffix)
            demo_data = demo_packager.package(output_path=demo_out)
            demo_ok = validate_connected_solution(demo_out)

        # autonomous deploy: import into Copilot Studio + publish the bots
        # (children first, orchestrator last). Creds come ONLY from env / a
        # settings file — never from chat. Twins import sequentially (Dataverse
        # runs one solution import per org at a time).
        deploy_result = _run_deploy(data, list(packager.bot_schemas), display, kwargs,
                                    workflow_ids=list(packager.workflow_ids.values())) \
            if kwargs.get("deploy") else None
        demo_deploy_result = None
        if kwargs.get("deploy") and demo_packager is not None:
            demo_deploy_result = _run_deploy(
                demo_data, list(demo_packager.bot_schemas), display + " (Demo)", kwargs,
                workflow_ids=list(demo_packager.workflow_ids.values()))

        deterministic = [s.display_name for s in subs if getattr(s, "capir", None)]
        n_flows = len(packager.workflow_ids)
        how = (f"{n_flows} with a deterministic capability flow (agent-callable workflow)"
               if n_flows else f"{len(deterministic)} with a deterministic capability topic")
        msg = (f"Generated '{out.name}' — {len(packager.bot_schemas)} bots "
               f"(1 orchestrator + {len(subs)} connected sub-agents, {how}), "
               f"{round(len(data)/1024,1)} KB. Validation: {'pass' if ok else 'fail'}.")
        if twins:
            demo_source = (
                "the same pinned public static API with zero connection binding"
                if static_enabled and static_transport == "http" else
                "public static connectors that require no-auth connection binding"
                if static_enabled else
                "synthetic data with zero connections"
            )
            msg += (f" Demo twin '{demo_out.name}' ({round(len(demo_data)/1024,1)} KB, "
                    f"validation: {'pass' if demo_ok else 'fail'}) runs the same flows "
                    f"on {demo_source}.")
        if kwargs.get("static_connectors"):
            if static_transport == "http":
                msg += (
                    " Static mode uses connectionless built-in HTTP GET against pinned "
                    "public no-PII endpoints; no connection binding is required. Typed "
                    "custom connectors remain packaged as the migration contract."
                )
            else:
                msg += (
                    " Static connector transport uses public no-PII GET adapters; "
                    "simulated write receipts never mutate external products. A no-auth "
                    "custom-connector connection must still be created and bound."
                )
            if packager._static_warnings:
                msg += " %d capability mapping warning(s) retained legacy wiring." % len(
                    packager._static_warnings
                )
        if deploy_result:
            msg += " " + deploy_result.get("summary", "")
        if demo_deploy_result:
            msg += " Demo twin: " + demo_deploy_result.get("summary", "")

        data_block = {
            "solution_path": str(out),
            "size_kb": round(len(data) / 1024, 1),
            "orchestrator_schema": packager.orch_schema,
            "sub_agents": [s.display_name for s in subs],
            # capir_topics stays as the count of deterministic capabilities for
            # callers (function_app) that read it; agent_flows is the new detail.
            "capir_topics": len(deterministic),
            "agent_flows": n_flows,
            "workflow_ids": packager.workflow_ids,
            "deterministic_topics": deterministic,
            "validation": "pass" if ok else "fail",
            # LIVE-twin wiring detail: which connector each capability's data
            # step calls, and the connection references the customer binds.
            "live_connectors": {cs: {"system": lv.get("system"), "kind": lv.get("kind"),
                                     "connector": lv.get("display"),
                                     "operation": lv.get("operation"),
                                     "connection_reference": lv.get("conn_ref_logical"),
                                     **({
                                         "transport": lv.get("static_transport"),
                                         "static_adapter": lv.get("adapter_id"),
                                         "static_resource": lv.get("resource_id"),
                                         "static_endpoint": lv.get("endpoint_path"),
                                         "full_pinned_endpoint_url":
                                             lv.get("full_endpoint_url"),
                                         "static_host": lv.get("static_host"),
                                         "static_base_path": lv.get("static_base_path"),
                                         "packaged_connector":
                                             lv.get("packaged_connector"),
                                         "catalog_resolution": lv.get("resolution"),
                                         "catalog_agent_id": lv.get("catalog_agent_id"),
                                         "connection_binding_required":
                                             lv.get("connection_binding_required"),
                                         "connectionless_http_fallback":
                                             lv.get("connectionless_http_fallback"),
                                         "migration": lv.get("migration"),
                                     } if kwargs.get("static_connectors") else {})}
                                for cs, lv in packager._live_by_child.items()},
        }
        if kwargs.get("static_connectors"):
            data_block.update({
                "static_connectors": True,
                "static_transport": static_transport,
                "static_connector_warnings": list(packager._static_warnings),
                "static_platform_limitation": (
                    "Built-in HTTP can be subject to premium licensing and tenant DLP/"
                    "policy. Connector transport requires a connection object/reference "
                    "binding even when custom-connector authentication is disabled."
                ),
            })
        if twins:
            data_block.update({
                "demo_solution_path": str(demo_out),
                "demo_size_kb": round(len(demo_data) / 1024, 1),
                "demo_orchestrator_schema": demo_packager.orch_schema,
                "demo_workflow_ids": demo_packager.workflow_ids,
                "demo_validation": "pass" if demo_ok else "fail",
            })
        status = "success" if (ok and demo_ok) else "error"
        if deploy_result:
            data_block["deploy"] = deploy_result
            if deploy_result.get("status") not in ("deployed",):
                status = "partial"
        if demo_deploy_result:
            data_block["demo_deploy"] = demo_deploy_result
            if demo_deploy_result.get("status") not in ("deployed",):
                status = "partial"
        if deploy_result is None and demo_deploy_result is None:
            data_block["deploy_hint"] = ("Pass deploy=true to import + publish into your Copilot Studio "
                                         "environment automatically (creds from env DYNAMICS_365_CLIENT_ID/"
                                         "SECRET/TENANT_ID/RESOURCE or a settings file via credentials_path).")
            data_block["m365_exposure"] = ("Set orchestrator_channels=true and publish the orchestrator "
                                           "in the maker portal for M365/Teams exposure.")
        return {"status": status, "agent": self.name, "message": msg, "data": data_block}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    target = sys.argv[1] if len(sys.argv) > 1 else None
    if not target:
        print("usage: python connected_solution_agent.py <stack_dir> [output.zip]")
        sys.exit(1)
    out_path = sys.argv[2] if len(sys.argv) > 2 else None
    result = ConnectedSolutionAgent().perform(stack_dir=target, output_path=out_path)
    print(json.dumps(result, indent=2))
