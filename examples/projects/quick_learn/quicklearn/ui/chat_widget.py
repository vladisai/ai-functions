"""Floating chat widget for user <-> conversation agent interaction.

Collapsed: small button bottom-right.
Expanded: full-height panel on the right side, ~40% of viewport width.

Also provides a text-selection popup: select text on the page, click
"Ask about this", and the chat opens with the selected text quoted.
"""

from __future__ import annotations

from collections.abc import Callable

from nicegui import run, ui

from quicklearn.ui.math_markdown import math_markdown


def render_chat_widget(
    messages: list[dict[str, str]],
    on_send: Callable[[str], str] | None = None,
    on_open: Callable[[], None] | None = None,
) -> Callable[[str], None]:
    """Render a floating chat button that expands into a full-height side panel.

    on_send: callback that takes user message, returns assistant reply.
    on_open: called when the panel opens, e.g. to close a panel that would cover the text.

    Returns a function push_assistant_message(text) to programmatically add
    an assistant message to the chat (e.g. from quiz feedback).
    """
    chat_visible = {"value": False}
    sending = {"value": False}
    quoted_text = {"value": ""}

    with ui.page_sticky(position="bottom-right", x_offset=20, y_offset=20):
        toggle_btn = ui.button(icon="chat").props("fab color=dark")

    # Full-height side panel
    chat_panel = ui.element("div").classes(
        "fixed right-0 bg-white shadow-xl border-l border-gray-200 "
        "flex flex-col z-50"
    ).style("width: 36rem; top: var(--ql-header-h, 50px); height: calc(100vh - var(--ql-header-h, 50px));")
    chat_panel.set_visibility(False)

    with chat_panel:
        # Header
        with ui.row().classes(
            "w-full items-center justify-between p-3 border-b border-gray-200"
        ).style("flex-shrink: 0; z-index: 10;"):
            ui.label("Chat").classes("text-lg font-bold")
            close_btn = ui.button(icon="close").props("flat dense round color=dark")

        # Messages area
        scroll_area = ui.scroll_area().classes("flex-grow w-full p-4")
        scroll_area.style("position: relative;")
        ui.add_css("""
            /* While the chat is open, the text and its 200px margin notes center left of the panel */
            body.ql-chat-open .q-page-container { padding-right: calc(36rem + 200px) !important; }
            .chat-scroll .q-scrollarea__content {
                min-height: 100% !important;
                display: flex !important;
                flex-direction: column !important;
                justify-content: flex-end !important;
            }
        """)
        scroll_area.classes(add="chat-scroll")
        with scroll_area:
            messages_container = ui.column().classes("w-full gap-2")
            with messages_container:
                for msg in messages:
                    _render_message(msg)

        # Input area — quote banner + textarea + send button
        with ui.column().classes("w-full border-t border-gray-200 p-3 gap-2"):
            # Quote banner (hidden by default)
            quote_banner = ui.column().classes("w-full").style("display: none;")
            with quote_banner:
                with ui.row().classes(
                    "w-full items-start gap-2 p-2 rounded bg-gray-50 "
                    "border-l-4 border-amber-400"
                ):
                    quote_label = ui.label("").classes(
                        "text-xs text-gray-600 italic flex-grow line-clamp-3"
                    )
                    quote_close = ui.button(icon="close").props(
                        "flat dense round size=xs color=grey"
                    )

            with ui.row().classes("w-full gap-2 items-end"):
                msg_input = ui.textarea(placeholder="Ask a question...").classes(
                    "flex-grow"
                ).props("dense outlined autogrow rows=1 max-rows=5")
                send_btn = ui.button(icon="send").props("flat dense color=dark")

    # ── Helpers ──────────────────────────────────────────────────────

    def _set_quote(text: str) -> None:
        quoted_text["value"] = text
        if text:
            display = text if len(text) <= 300 else text[:300] + "..."
            quote_label.text = display
            quote_banner.style("display: flex;")
        else:
            quote_label.text = ""
            quote_banner.style("display: none;")

    def _clear_quote() -> None:
        _set_quote("")

    quote_close.on("click", _clear_quote)

    # ── Send handler ─────────────────────────────────────────────────

    async def handle_send(
        e=None,
        input_ref: ui.textarea = msg_input,
        container_ref: ui.column = messages_container,
        scroll_ref: ui.scroll_area = scroll_area,
        send_ref: ui.button = send_btn,
    ) -> None:
        # Allow Shift+Enter to insert newline (args=[shiftKey] from JS)
        if e and getattr(e, "args", None):
            shift = e.args[0] if isinstance(e.args, list) else e.args
            if shift:
                input_ref.set_value((input_ref.value or "") + "\n")
                return
        if sending["value"]:
            return
        text = input_ref.value
        if not text or not text.strip():
            return
        text = text.strip()

        # Build message with quote context if present
        full_message = text
        display_message = text
        if quoted_text["value"]:
            full_message = (
                f"Regarding this passage:\n> {quoted_text['value']}\n\n{text}"
            )
            display_message = full_message

        input_ref.set_value("")
        _clear_quote()
        sending["value"] = True
        send_ref.props("disabled")

        # Show user message immediately
        messages.append({"role": "user", "content": display_message})
        with container_ref:
            _render_message({"role": "user", "content": display_message})
        scroll_ref.scroll_to(percent=1.0)

        # Show typing indicator
        with container_ref:
            typing_indicator = _render_typing_indicator()
        scroll_ref.scroll_to(percent=1.0)

        # Run LLM call off the event loop. A failure still frees the input, then reaches the log.
        reply = None
        try:
            if on_send:
                reply = await run.io_bound(on_send, full_message)
        except Exception:
            reply = "Something went wrong answering this. The server log has the details."
            raise
        finally:
            typing_indicator.delete()
            if reply:
                with container_ref:
                    _render_message({"role": "assistant", "content": reply})
                scroll_ref.scroll_to(percent=1.0)
            sending["value"] = False
            send_ref.props(remove="disabled")

    # Enter sends, Shift+Enter inserts newline
    msg_input.on("keydown.enter.prevent", handle_send, ["shiftKey"])
    send_btn.on("click", handle_send)

    # ── Chat open / close ────────────────────────────────────────────

    def open_chat() -> None:
        if not chat_visible["value"]:
            chat_visible["value"] = True
            chat_panel.set_visibility(True)
            toggle_btn.set_visibility(False)
            scroll_area.scroll_to(percent=1.0)
            ui.run_javascript("localStorage.setItem('ql_chat_open', '1'); document.body.classList.add('ql-chat-open')")
            if on_open:
                on_open()

    def close_chat() -> None:
        chat_visible["value"] = False
        chat_panel.set_visibility(False)
        toggle_btn.set_visibility(True)
        ui.run_javascript("localStorage.setItem('ql_chat_open', '0'); document.body.classList.remove('ql-chat-open')")

    def toggle_chat() -> None:
        if chat_visible["value"]:
            close_chat()
        else:
            open_chat()

    toggle_btn.on("click", toggle_chat)
    close_btn.on("click", close_chat)

    # Restore chat panel state from localStorage on page load
    async def _restore_chat_state() -> None:
        try:
            result = await ui.run_javascript("localStorage.getItem('ql_chat_open')")
            if result == "1":
                open_chat()
        except TimeoutError:
            pass  # client not ready yet, default to closed

    ui.timer(0.5, _restore_chat_state, once=True)

    # ── Text selection popup ─────────────────────────────────────────
    # Strategy: JS stores selected text in window.__ql_selected. A hidden
    # NiceGUI button is clicked from JS; its async handler reads the text
    # back via ui.run_javascript (Python->JS->Python round-trip).

    sel_btn = ui.button("sel").style(
        "position:fixed; left:-9999px; top:-9999px; opacity:0; pointer-events:none;"
    )

    async def _on_sel_click() -> None:
        text = await ui.run_javascript("window.__ql_selected || ''")
        text = (text or "").strip()
        if not text:
            return
        _set_quote(text)
        open_chat()
        ui.timer(0.15, lambda: msg_input.run_method("focus"), once=True)

    sel_btn.on("click", _on_sel_click)
    # ── Push function for external callers (e.g. quiz feedback) ────
    def push_assistant_message(text: str) -> None:
        """Add an assistant message to the chat panel programmatically."""
        msg = {"role": "assistant", "content": text}
        messages.append(msg)
        with messages_container:
            _render_message(msg)
        scroll_area.scroll_to(percent=1.0)
        # Open chat if not already visible
        if not chat_visible["value"]:
            open_chat()

    sel_btn_id = sel_btn.id

    ui.run_javascript(f"""
    (function() {{
        window.__ql_selected = '';

        const popup = document.createElement('div');
        popup.textContent = String.fromCodePoint(0x1F4AC) + ' Ask about this';
        Object.assign(popup.style, {{
            display: 'none',
            position: 'fixed',
            zIndex: '10000',
            background: '#1a1a1a',
            color: 'white',
            fontSize: '12px',
            padding: '6px 12px',
            borderRadius: '999px',
            cursor: 'pointer',
            userSelect: 'none',
            boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
            whiteSpace: 'nowrap',
            alignItems: 'center',
            gap: '4px',
        }});
        popup.addEventListener('mouseenter', () => popup.style.background = '#333');
        popup.addEventListener('mouseleave', () => popup.style.background = '#1a1a1a');
        document.body.appendChild(popup);

        let selectedText = '';

        document.addEventListener('mouseup', function(e) {{
            if (e.target.closest('.z-50') || popup.contains(e.target)) return;
            setTimeout(function() {{
                const sel = window.getSelection();
                const text = sel ? sel.toString().trim() : '';
                if (text.length > 3) {{
                    selectedText = text;
                    const range = sel.getRangeAt(0);
                    const rect = range.getBoundingClientRect();
                    popup.style.display = 'flex';
                    popup.style.left = Math.max(8, rect.left + rect.width / 2 - 70) + 'px';
                    popup.style.top = Math.max(8, rect.top - 38) + 'px';
                }} else {{
                    popup.style.display = 'none';
                    selectedText = '';
                }}
            }}, 10);
        }});

        document.addEventListener('mousedown', function(e) {{
            if (!popup.contains(e.target)) {{
                popup.style.display = 'none';
            }}
        }});

        popup.addEventListener('click', function(e) {{
            e.preventDefault();
            e.stopPropagation();
            if (selectedText) {{
                window.__ql_selected = selectedText;
                // Programmatically click the hidden NiceGUI button
                const btn = document.getElementById('c{sel_btn_id}');
                if (btn) btn.click();
                window.getSelection().removeAllRanges();
                popup.style.display = 'none';
                selectedText = '';
            }}
        }});
    }})();
    """)

    return push_assistant_message


def _render_typing_indicator() -> ui.row:
    """Render an animated typing indicator (three bouncing dots)."""
    with ui.column().classes("w-full items-start") as container:
        with ui.row().classes("p-3 rounded-lg bg-gray-100 gap-1 items-center"):
            for i in range(3):
                ui.element("div").classes(
                    "w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                ).style(f"animation-delay: {i * 0.15}s;")
    return container


def _render_message(msg: dict[str, str]) -> None:
    is_user = msg["role"] == "user"
    align = "items-end" if is_user else "items-start"
    bg = "bg-gray-200" if is_user else "bg-gray-100"
    with ui.column().classes(f"w-full {align}"):
        math_markdown(msg["content"], classes=f"text-sm p-3 rounded-lg {bg} max-w-[85%]")
