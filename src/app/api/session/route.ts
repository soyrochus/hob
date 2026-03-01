import { NextResponse } from "next/server";
import { resolveProvider } from "@/app/lib/resolveProvider";

function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

function buildAzureRealtimeUrl(endpoint: string, deployment: string): string {
  const realtimeUrl = new URL(endpoint);
  realtimeUrl.protocol = realtimeUrl.protocol === "http:" ? "ws:" : "wss:";
  realtimeUrl.pathname = "/openai/v1/realtime";
  realtimeUrl.search = new URLSearchParams({ model: deployment }).toString();
  return realtimeUrl.toString();
}

export async function GET() {
  try {
    const provider = resolveProvider();
    const isAzure = provider === "azure";

    const openAiSessionUrl = "https://api.openai.com/v1/realtime/sessions";
    const openAiModel = "gpt-4o-realtime-preview-2025-06-03";

    const azureEndpoint = isAzure ? requireEnv("AZURE_OPENAI_ENDPOINT") : "";
    const azureApiVersion = isAzure
      ? requireEnv("AZURE_OPENAI_API_VERSION")
      : "";
    const azureApiKey = isAzure ? requireEnv("AZURE_OPENAI_API_KEY") : "";
    const azureRealtimeDeployment = isAzure
      ? requireEnv("AZURE_OPENAI_REALTIME_DEPLOYMENT")
      : "";

    const url = isAzure
      ? `${azureEndpoint.replace(
          /\/+$/,
          ""
        )}/openai/realtime/sessions?api-version=${encodeURIComponent(
          azureApiVersion
        )}`
      : openAiSessionUrl;

    const headers: Record<string, string> = isAzure
      ? {
          "api-key": azureApiKey,
          "Content-Type": "application/json",
        }
      : {
          Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
          "Content-Type": "application/json",
        };

    const response = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify({
        model: isAzure ? azureRealtimeDeployment : openAiModel,
      }),
    });

    const data = await response.json();
    const responseBody = isAzure
      ? {
          ...data,
          realtimeUrl: buildAzureRealtimeUrl(
            azureEndpoint,
            azureRealtimeDeployment
          ),
        }
      : data;

    return NextResponse.json(responseBody, { status: response.status });
  } catch (error) {
    console.error("Error in /session:", error);
    return NextResponse.json(
      { error: "Internal Server Error" },
      { status: 500 }
    );
  }
}
