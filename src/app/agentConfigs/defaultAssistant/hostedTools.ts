import { tool } from '@openai/agents/realtime';

const RESPONSES_MODEL = 'gpt-4.1';

async function callResponses(body: unknown) {
  try {
    const response = await fetch('/api/responses', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ ...(body as object), parallel_tool_calls: false }),
    });

    if (!response.ok) {
      console.warn('Server returned an error:', response);
      return { error: 'tool_call_failed' };
    }

    return await response.json();
  } catch (error) {
    console.warn('Failed to call /api/responses:', error);
    return { error: 'tool_call_failed' };
  }
}

function extractOutputText(response: any): string {
  if (typeof response?.output_text === 'string' && response.output_text.trim()) {
    return response.output_text.trim();
  }

  const outputItems: any[] = Array.isArray(response?.output) ? response.output : [];
  const messages = outputItems.filter((item) => item.type === 'message');

  return messages
    .map((msg: any) => {
      const content = Array.isArray(msg.content) ? msg.content : [];
      return content
        .filter((item: any) => item.type === 'output_text')
        .map((item: any) => item.text)
        .join('');
    })
    .join('\n')
    .trim();
}

export const webSearch = tool({
  name: 'webSearch',
  description:
    'Search the web for recent or factual information and return a concise summary with sources.',
  parameters: {
    type: 'object',
    properties: {
      query: {
        type: 'string',
        description: 'Search query to run on the web.',
      },
    },
    required: ['query'],
    additionalProperties: false,
  },
  execute: async (input) => {
    const { query } = input as { query: string };

    const response = await callResponses({
      model: RESPONSES_MODEL,
      input: `Use web search to answer this query accurately and concisely. Include key source URLs in plain text.\n\nQuery: ${query}`,
      tools: [{ type: 'web_search' }],
    });

    if ((response as any)?.error) {
      return { error: 'web_search_failed' };
    }

    const text = extractOutputText(response);
    return { result: text || 'No search result available.' };
  },
});

export const codeInterpreter = tool({
  name: 'codeInterpreter',
  description:
    'Run calculations, data analysis, or code tasks via hosted code interpreter and return the result.',
  parameters: {
    type: 'object',
    properties: {
      task: {
        type: 'string',
        description: 'Computation or coding task to execute.',
      },
    },
    required: ['task'],
    additionalProperties: false,
  },
  execute: async (input) => {
    const { task } = input as { task: string };

    const response = await callResponses({
      model: RESPONSES_MODEL,
      input: `Use code interpreter when helpful to solve this task. Return a concise final answer.\n\nTask: ${task}`,
      tools: [
        {
          type: 'code_interpreter',
          container: { type: 'auto' },
        },
      ],
    });

    if ((response as any)?.error) {
      return { error: 'code_interpreter_failed' };
    }

    const text = extractOutputText(response);
    return { result: text || 'No code interpreter result available.' };
  },
});

export const fileSearch = tool({
  name: 'fileSearch',
  description:
    'Search configured project documents using hosted file search. Returns an error when not configured.',
  parameters: {
    type: 'object',
    properties: {
      query: {
        type: 'string',
        description: 'Document search query.',
      },
    },
    required: ['query'],
    additionalProperties: false,
  },
  execute: async (input) => {
    const { query } = input as { query: string };
    const vectorStoreId = process.env.NEXT_PUBLIC_OPENAI_VECTOR_STORE_ID;

    if (!vectorStoreId) {
      return {
        error: 'file_search_not_configured',
        message:
          'File search is not configured. Set NEXT_PUBLIC_OPENAI_VECTOR_STORE_ID to enable it.',
      };
    }

    const response = await callResponses({
      model: RESPONSES_MODEL,
      input: `Use file search to answer this query with concise, grounded detail.\n\nQuery: ${query}`,
      tools: [
        {
          type: 'file_search',
          vector_store_ids: [vectorStoreId],
        },
      ],
    });

    if ((response as any)?.error) {
      return { error: 'file_search_failed' };
    }

    const text = extractOutputText(response);
    return { result: text || 'No file search result available.' };
  },
});
