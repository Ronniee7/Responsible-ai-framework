# Responsible AI Framework

## LLM provider framework

The backend now exposes a provider-agnostic LLM abstraction under the llm package.

### How it works
- The chat flow uses the factory to obtain a provider instance.
- Provider selection is controlled by the LLM_PROVIDER environment variable.
- Supported providers are gemini, openai, and ollama.

### Configuration
Set the provider and the corresponding credentials in the backend environment or in .env:
- LLM_PROVIDER=openai
- OPENAI_API_KEY=...
- GEMINI_API_KEY=...
- OLLAMA_HOST=http://localhost:11434
- OLLAMA_MODEL=llama3
- OPENAI_MODEL=gpt-4.1
- GEMINI_MODEL=gemini-2.5-flash

### Adding a new provider
1. Create a new provider class implementing the LLMProvider interface in Backend/llm/providers/.
2. Register it in Backend/llm/factory.py.
3. Select it with LLM_PROVIDER=<provider-name>.
