export type LLMProvider = "openai" | "azure";

export function resolveProvider(): LLMProvider {
  const explicitProvider = process.env.LLM_PROVIDER;

  if (explicitProvider === "openai" || explicitProvider === "azure") {
    return explicitProvider;
  }

  if (explicitProvider) {
    throw new Error(
      `Invalid LLM_PROVIDER "${explicitProvider}". Must be "openai" or "azure".`
    );
  }

  if (process.env.OPENAI_API_KEY) {
    return "openai";
  }

  if (process.env.AZURE_OPENAI_ENDPOINT) {
    return "azure";
  }

  throw new Error(
    "No LLM provider configured. Set LLM_PROVIDER, OPENAI_API_KEY, or AZURE_OPENAI_ENDPOINT."
  );
}
