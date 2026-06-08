# ─────────────────────────────────────────────
# AI BRAIN — Universal AI Provider
# Supports: OpenAI, Groq, Gemini
# Switch provider by changing .env only
# Never need to touch this file again
# ─────────────────────────────────────────────

from config.config_manager import config


# ─────────────────────────────────────────────
# AI BRAIN CLASS
# ─────────────────────────────────────────────
class AIBrain:

    # ─── Model map per provider ───────────────
    MODELS = {
        "openai": "gpt-4o-mini",
        "groq":   "llama-3.1-8b-instant",
        "gemini": "gemini-2.0-flash",
    }

    def __init__(self):
        self.conversation_history = []
        self.client  = None
        self.provider = config.ai_provider
        self.model    = self.MODELS.get(self.provider, "gpt-4o-mini")
        self._setup_client()

    # ─────────────────────────────────────────
    # SETUP CLIENT
    # Automatically picks correct SDK
    # ─────────────────────────────────────────
    def _setup_client(self):
        """Initialize correct AI client from .env provider setting."""
        self.provider = config.ai_provider
        self.model    = self.MODELS.get(self.provider, "gpt-4o-mini")
        api_key       = config.active_api_key

        if not api_key:
            print(f"[AI] ⚠️ No API key found for provider: {self.provider}")
            return

        try:
            if self.provider == "openai":
                self._setup_openai(api_key)

            elif self.provider == "groq":
                self._setup_groq(api_key)

            elif self.provider == "gemini":
                self._setup_gemini(api_key)

            else:
                print(f"[AI] ⚠️ Unknown provider: {self.provider}")
                print("[AI] Valid options: openai | groq | gemini")

        except Exception as e:
            print(f"[AI ERROR] Setup failed: {e}")

    # ─── OpenAI Setup ─────────────────────────
    def _setup_openai(self, api_key: str):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        print(f"[AI] ✅ OpenAI ({self.model}) ready")

    # ─── Groq Setup ───────────────────────────
    def _setup_groq(self, api_key: str):
        from groq import Groq
        self.client = Groq(api_key=api_key)
        print(f"[AI] ✅ Groq ({self.model}) ready")

    # ─── Gemini Setup ─────────────────────────
    def _setup_gemini(self, api_key: str):
        from google import genai
        self.client = genai.Client(api_key=api_key)
        print(f"[AI] ✅ Gemini ({self.model}) ready")

    # ─────────────────────────────────────────
    # BUILD SYSTEM PROMPT
    # ─────────────────────────────────────────
    def _build_system_prompt(self, language: str) -> str:
        """Build dynamic system prompt from dashboard settings."""

        robot_name       = config.get("robot", "name", default="Alexa")
        robot_identity   = config.get("identity", "robot_identity", default="")
        enterprise_intro = config.get("identity", "enterprise_introduction", default="")
        additional_info  = config.get("identity", "additional_information", default="")
        conv_styles      = config.get("robot", "conversation_style", default=["Friendly"])
        style_str        = ", ".join(conv_styles)

        # ─── Identity ─────────────────────────
        identity_section = robot_identity if robot_identity else (
            f"You are {robot_name}, an intelligent greeting robot assistant. "
            f"You help visitors, answer questions, and provide information."
        )

        # ─── Force name usage ─────────────────
        # Ensures AI always uses admin-configured name
        # regardless of what's in identity text
        identity_section = (
            f"YOUR NAME IS {robot_name}. "
            f"Always refer to yourself as {robot_name}. "
            f"Never use any other name.\n\n"
            + identity_section
        )

        # ─── Enterprise ───────────────────────
        enterprise_section = ""
        if enterprise_intro:
            enterprise_section = (
                f"\n\nAbout the organization:\n{enterprise_intro}"
            )
        if additional_info:
            enterprise_section += f"\n\nAdditional info:\n{additional_info}"

        # ─── Language ─────────────────────────
        if language == "ar":
            lang_instruction = (
                "\n\nIMPORTANT: Respond in Arabic ONLY. "
                "Use natural Gulf Arabic. Max 2-3 sentences."
            )
        else:
            lang_instruction = (
                "\n\nIMPORTANT: Respond in English ONLY. "
                "Max 2-3 sentences."
            )

        # ─── Style ────────────────────────────
        style_instruction = (
            f"\n\nStyle: {style_str}. "
            "Be warm and professional. "
            "No markdown, no bullet points. "
            "You are a physical robot — keep it short and clear."
        )

        return (
            identity_section
            + enterprise_section
            + lang_instruction
            + style_instruction
        )

    # ─────────────────────────────────────────
    # MAIN CHAT METHOD
    # Routes to correct provider automatically
    # ─────────────────────────────────────────
    def chat(self, user_text: str, language: str = "en") -> str:
        """
        Send message and get AI response.
        Automatically uses provider set in .env
        """
        if not self.client:
            if language == "ar":
                return "عذراً، لا يمكنني الاتصال بالذكاء الاصطناعي الآن."
            return "Sorry, I'm having trouble connecting right now."

        try:
            system_prompt = self._build_system_prompt(language)

            # ─── Add to history ───────────────
            self.conversation_history.append({
                "role": "user",
                "content": user_text
            })

            # ─── Trim history ─────────────────
            max_history = config.get("ai", "context_memory", default=10)
            if len(self.conversation_history) > max_history:
                self.conversation_history = (
                    self.conversation_history[-max_history:]
                )

            # ─── Route to correct provider ────
            if self.provider == "gemini":
                response_text = self._chat_gemini(system_prompt)
            else:
                # OpenAI and Groq use same SDK format
                response_text = self._chat_openai_format(system_prompt)

            # ─── Save to history ──────────────
            self.conversation_history.append({
                "role": "assistant",
                "content": response_text
            })

            print(f"[AI] ({self.provider}/{language}): {response_text[:80]}...")
            return response_text

        except Exception as e:
            print(f"[AI ERROR] {e}")
            if language == "ar":
                return "عذراً، حدث خطأ ما. هل يمكنك إعادة السؤال؟"
            return "Sorry, something went wrong. Could you please repeat that?"

    # ─────────────────────────────────────────
    # STREAMING CHAT — yields text chunks live
    # ─────────────────────────────────────────
    def chat_stream(self, user_text: str, language: str = "en"):
        """
        Generator yielding text chunks as the AI streams them.
        Conversation history is updated when the stream is exhausted.
        """
        if not self.client:
            yield (
                "عذراً، لا يمكنني الاتصال." if language == "ar"
                else "Sorry, I'm having trouble connecting right now."
            )
            return

        try:
            system_prompt = self._build_system_prompt(language)

            self.conversation_history.append(
                {"role": "user", "content": user_text}
            )
            max_history = config.get("ai", "context_memory", default=10)
            if len(self.conversation_history) > max_history:
                self.conversation_history = (
                    self.conversation_history[-max_history:]
                )

            full_response = ""

            if self.provider == "gemini":
                for chunk in self._stream_gemini(system_prompt):
                    full_response += chunk
                    yield chunk
            else:
                for chunk in self._stream_openai_format(system_prompt):
                    full_response += chunk
                    yield chunk

            full_response = full_response.strip()
            self.conversation_history.append(
                {"role": "assistant", "content": full_response}
            )
            print(f"[AI STREAM] ({self.provider}/{language}): {full_response[:80]}...")

        except Exception as e:
            print(f"[AI STREAM ERROR] {e}")
            yield (
                "عذراً، حدث خطأ ما." if language == "ar"
                else "Sorry, something went wrong."
            )

    # ─────────────────────────────────────────
    # OPENAI / GROQ FORMAT (same SDK structure)
    # ─────────────────────────────────────────
    def _chat_openai_format(self, system_prompt: str) -> str:
        """Handles both OpenAI and Groq — identical API format."""
        messages = [
            {"role": "system", "content": system_prompt}
        ] + self.conversation_history

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=config.get("ai", "temperature", default=0.7),
            max_tokens=config.get("ai", "max_tokens", default=300),
        )
        return response.choices[0].message.content.strip()

    def _stream_openai_format(self, system_prompt: str):
        """Streaming variant for OpenAI and Groq."""
        messages = [
            {"role": "system", "content": system_prompt}
        ] + self.conversation_history

        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=config.get("ai", "temperature", default=0.7),
            max_tokens=config.get("ai", "max_tokens", default=300),
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    # ─────────────────────────────────────────
    # GEMINI FORMAT
    # ─────────────────────────────────────────
    def _chat_gemini(self, system_prompt: str) -> str:
        """Handles Gemini — different SDK format."""
        from google.genai import types

        contents = [
            types.Content(
                role="user" if m["role"] == "user" else "model",
                parts=[types.Part(text=m["content"])]
            )
            for m in self.conversation_history
        ]

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=config.get("ai", "temperature", default=0.7),
                max_output_tokens=config.get("ai", "max_tokens", default=300),
            )
        )
        return response.text.strip()

    def _stream_gemini(self, system_prompt: str):
        """Streaming variant for Gemini."""
        from google.genai import types

        contents = [
            types.Content(
                role="user" if m["role"] == "user" else "model",
                parts=[types.Part(text=m["content"])]
            )
            for m in self.conversation_history
        ]

        for chunk in self.client.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=config.get("ai", "temperature", default=0.7),
                max_output_tokens=config.get("ai", "max_tokens", default=300),
            ),
        ):
            if chunk.text:
                yield chunk.text

    # ─── Reset Conversation ───────────────────
    def reset_conversation(self):
        """Clear history for new visitor."""
        self.conversation_history = []
        print("[AI] Conversation reset.")

    # ─── Reload Config ────────────────────────
    def reload_config(self):
        """Reload after dashboard saves changes."""
        print("[AI] Config reloaded.")


# ─── Singleton Instance ───────────────────────
ai_brain = AIBrain()
