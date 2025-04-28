import aiohttp
import re
from telethon.tl.types import Message
from .. import loader, utils

__version__ = (1, 0, 1)

#        █████  ██████   ██████ ███████  ██████  ██████   ██████ 
#       ██   ██ ██   ██ ██      ██      ██      ██    ██ ██      
#       ███████ ██████  ██      █████   ██      ██    ██ ██      
#       ██   ██ ██      ██      ██      ██      ██    ██ ██      
#       ██   ██ ██       ██████ ███████  ██████  ██████   ██████

#              © Copyright 2025
#           https://t.me/apcecoc
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# meta developer: @apcecoc
# scope: hikka_only
# scope: hikka_min 1.2.10

@loader.tds
class GeminiRealtimeMod(loader.Module):
    """Interact with Google Gemini Realtime API"""

    strings = {
        "name": "GeminiRealtime",
        "processing": "🤖 <b>Processing your request...</b>",
        "error": "❌ <b>Error while processing your request: {error}</b>",
        "response": "🤖 <b>Gemini Response:</b>\n\n{response}",
        "no_input": "❌ <b>Please provide a message to send to the AI.</b>",
        "session_cleared": "✅ <b>Session cleared. A new chat has been started.</b>",
    }

    strings_ru = {
        "processing": "🤖 <b>Обрабатываю ваш запрос...</b>",
        "error": "❌ <b>Ошибка при обработке запроса: {error}</b>",
        "response": "🤖 <b>Ответ Gemini:</b>\n\n{response}",
        "no_input": "❌ <b>Пожалуйста, укажите сообщение для отправки AI.</b>",
        "session_cleared": "✅ <b>Сессия очищена. Новый чат начат.</b>",
        "_cls_doc": "Взаимодействие с Google Gemini Realtime API",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "session_id",
                None,
                lambda: "Session ID for continuing the conversation with Gemini API",
                validator=loader.validators.String(),
            ),
        )

    def _markdown_to_html(self, text: str) -> str:
        """
        Convert Markdown to HTML manually for Hikka compatibility.
        """
        parts = []
        last_pos = 0
        code_blocks = re.finditer(r"```(\w+)?\n([\s\S]*?)```", text)

        for match in code_blocks:
            start, end = match.span()
            if last_pos < start:
                parts.append(("text", text[last_pos:start]))
            language = match.group(1) or "plaintext"
            code = match.group(2).strip()
            parts.append(("code", language, code))
            last_pos = end

        if last_pos < len(text):
            parts.append(("text", text[last_pos:]))

        result = []
        for part in parts:
            if part[0] == "code":
                language, code = part[1], part[2]
                formatted_code = f"<pre><code class='{language}'>{utils.escape_html(code)}</code></pre>"
                result.append(formatted_code)
            else:
                text_part = part[1]
                # Обрабатываем ссылки в формате [название](ссылка)
                text_part = re.sub(
                    r'\[([^\]]+)\]\((https?://[^\s]+)\)',
                    r'<a href="\2">\1</a>',
                    text_part
                )
                # Обрабатываем остальные элементы Markdown
                text_part = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text_part)
                text_part = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text_part)
                text_part = re.sub(r"^# (.+)", r"<b>\1</b>", text_part, flags=re.MULTILINE)
                text_part = re.sub(r"^## (.+)", r"<b>\1</b>", text_part, flags=re.MULTILINE)
                text_part = re.sub(r"^### (.+)", r"<b>\1</b>", text_part, flags=re.MULTILINE)
                text_part = re.sub(r"`(.+?)`", r"<code>\1</code>", text_part)
                text_part = re.sub(r"^\s*\* (.+)", r"• \1", text_part, flags=re.MULTILINE)
                text_part = re.sub(r"^\s*(\d+)\.\s+(.+)", r"\1. \2", text_part, flags=re.MULTILINE)
                result.append(text_part)

        return "\n".join(result)

    @loader.command(ru_doc="Отправить запрос к Google Gemini Realtime API")
    async def gemini(self, message: Message):
        """Send a request to Google Gemini Realtime API"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("no_input"))
            return

        await utils.answer(message, self.strings("processing"))

        api_url = "https://api.paxsenix.biz.id/ai/gemini-realtime"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer YOUR_API_KEY",
        }
        params = {"text": args}
        
        if self.config["session_id"]:
            params["session_id"] = self.config["session_id"]

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if not data.get("ok", False):
                            await utils.answer(
                                message,
                                self.strings("error").format(error="API returned an error"),
                            )
                            return

                        response_message = data.get("message", "No response received.")

                        html_response = self._markdown_to_html(response_message)

                        new_session_id = data.get("session_id")
                        if new_session_id:
                            self.config["session_id"] = new_session_id

                        await utils.answer(
                            message,
                            self.strings("response").format(response=html_response),
                        )
                    elif resp.status == 400:
                        await utils.answer(
                            message,
                            self.strings("error").format(error="Bad request"),
                        )
                    elif resp.status == 500:
                        await utils.answer(
                            message,
                            self.strings("error").format(error="Server error"),
                        )
                    else:
                        await utils.answer(
                            message,
                            self.strings("error").format(error=f"HTTP {resp.status}"),
                        )
        except Exception as e:
            await utils.answer(
                message,
                self.strings("error").format(error=str(e)),
            )

    @loader.command(ru_doc="Очистить сессию и начать новый чат")
    async def clearid(self, message: Message):
        """Clear the session ID to start a new chat"""
        self.config["session_id"] = None
        await utils.answer(message, self.strings("session_cleared"))