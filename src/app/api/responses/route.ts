import { NextRequest, NextResponse } from 'next/server';
import OpenAI, { AzureOpenAI } from 'openai';
import { resolveProvider } from '@/app/lib/resolveProvider';

type ResponsesClient = OpenAI | AzureOpenAI;

function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

function buildClient(): ResponsesClient {
  const provider = resolveProvider();

  if (provider === 'azure') {
    return new AzureOpenAI({
      endpoint: requireEnv('AZURE_OPENAI_ENDPOINT'),
      apiKey: requireEnv('AZURE_OPENAI_API_KEY'),
      apiVersion: requireEnv('AZURE_OPENAI_API_VERSION'),
    });
  }

  return new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
}

// Proxy endpoint for the OpenAI Responses API
export async function POST(req: NextRequest) {
  const body = await req.json();
  const provider = resolveProvider();

  if (provider === 'azure' && body.model) {
    body.model = requireEnv('AZURE_OPENAI_RESPONSES_DEPLOYMENT');
  }

  const openai = buildClient();

  if (body.text?.format?.type === 'json_schema') {
    return await structuredResponse(openai, body);
  } else {
    return await textResponse(openai, body);
  }
}

async function structuredResponse(openai: ResponsesClient, body: any) {
  try {
    const response = await openai.responses.parse({
      ...(body as any),
      stream: false,
    });

    return NextResponse.json(response);
  } catch (err: any) {
    console.error('responses proxy error', err);
    return NextResponse.json({ error: 'failed' }, { status: 500 }); 
  }
}

async function textResponse(openai: ResponsesClient, body: any) {
  try {
    const response = await openai.responses.create({
      ...(body as any),
      stream: false,
    });

    return NextResponse.json(response);
  } catch (err: any) {
    console.error('responses proxy error', err);
    return NextResponse.json({ error: 'failed' }, { status: 500 });
  }
}
  
