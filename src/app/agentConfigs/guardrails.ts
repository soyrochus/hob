import { zodTextFormat } from 'openai/helpers/zod';
import { GuardrailOutputZod, GuardrailOutput } from '@/app/types';

export type GuardrailProfile = 'company' | 'general';

interface GuardrailClassifierOptions {
  companyName?: string;
  profile?: GuardrailProfile;
}

// Validator that calls the /api/responses endpoint to
// validates the realtime output according to moderation policies. 
// This will prevent the realtime model from responding in undesired ways
// By sending it a corrective message and having it redirect the conversation.
export async function runGuardrailClassifier(
  message: string,
  options: GuardrailClassifierOptions = {},
): Promise<GuardrailOutput> {
  const companyName = options.companyName ?? 'newTelco';
  const profile = options.profile ?? 'company';
  const policyText =
    profile === 'general'
      ? `
      System Guardrail: Contextual Safety Policy

      You are allowed to retrieve, analyze, and summarize web content that references violence, war, crime, political conflict, terrorism, or other sensitive topics when the context is informational, historical, academic, journalistic, or analytical.

      Do not block content solely because it contains references to violence or conflict.

      Allowed Content
      – Historical accounts of wars, revolutions, terrorism, or crime
      – Current geopolitical conflicts and military reporting
      – Academic or legal analysis of violent events
      – News summaries of attacks or casualties (non-graphic)
      – Critical discussion of extremist groups (non-propagandistic)
      – Clinical or educational discussion of sexuality (non-explicit)

      Disallowed Content
      1. Graphic or extreme violence
      – Detailed gore, mutilation, torture, dismemberment
      – Sensory descriptions of physical suffering intended to shock or arouse
      2. Instruction or facilitation of harm
      – How-to guidance for harming, killing, building weapons, or evading law enforcement
      – Tactical or operational advice that meaningfully enables violence
      3. Glorification or endorsement of violence
      – Praise, romanticization, or propaganda supporting violent acts
      4. Explicit sexual content
      – Pornographic descriptions
      – Fetishized sexual content
      – Any sexual content involving minors
      5. Graphic sexual violence

      Decision Rule
      - If violence appears in a neutral, analytical, educational, or journalistic context, classify as NONE.
      - If content is graphic, operational, exploitative, pornographic, or meaningfully enables harm, classify as VIOLENCE or OFFENSIVE.
      - If uncertain, prefer a high-level non-graphic allowance and classify as NONE.
      - Do not use keyword blocking. Evaluate context, intent, and severity.

      Classification examples:
      - "The article analyzes the risk of regional war escalation in 2026." -> NONE
      - "News report covering casualties from an attack without graphic detail." -> NONE
      - "Step-by-step instructions to make a bomb." -> VIOLENCE
      - "Graphic description of dismemberment." -> VIOLENCE
      - "Hateful slurs targeting a protected group." -> OFFENSIVE
      `
      : `
      Company Safety Policy
      - Keep responses safe and brand-appropriate.
      - Flag insulting, hateful, threatening, or explicit harm content.
      - Flag competitor disparagement as off-brand for this company context.
      `;

  const outputClasses =
    profile === 'general'
      ? `
      - OFFENSIVE: Hate speech, discriminatory insults/harassment, or explicit sexual content (including any sexual content involving minors).
      - VIOLENCE: Graphic/extreme violence, instruction/facilitation of harm, glorification/endorsement of violence, or graphic sexual violence.
      - NONE: Content is acceptable in context, including non-graphic informational, historical, academic, journalistic, or analytical discussion of conflict/violence.
      `
      : `
      - OFFENSIVE: Content that includes hate speech, discriminatory language, insults, slurs, or harassment.
      - OFF_BRAND: Content that discusses competitors in a disparaging way.
      - VIOLENCE: Content that includes explicit threats, incitement of harm, or graphic descriptions of physical injury or violence.
      - NONE: If no other classes are appropriate and the message is fine.
      `;

  const messages = [
    {
      role: 'user',
      content: `You are an expert at classifying text according to moderation policies. Consider the provided message, analyze potential classes from output_classes, and output the best classification. Output json, following the provided schema. Keep your analysis and reasoning short and to the point, maximum 2 sentences.

      <info>
      - Company name: ${companyName}
      - Profile: ${profile}
      </info>

      <policy>
      ${policyText}
      </policy>

      <message>
      ${message}
      </message>

      <output_classes>
      ${outputClasses}
      </output_classes>
      `,
    },
  ];

  const response = await fetch('/api/responses', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'gpt-4o-mini',
      input: messages,
      text: {
        format: zodTextFormat(GuardrailOutputZod, 'output_format'),
      },
    }),
  });

  if (!response.ok) {
    console.warn('Server returned an error:', response);
    return Promise.reject('Error with runGuardrailClassifier.');
  }

  const data = await response.json();

  try {
    const output = GuardrailOutputZod.parse(data.output_parsed);
    return {
      ...output,
      testText: message,
    };
  } catch (error) {
    console.error('Error parsing the message content as GuardrailOutput:', error);
    return Promise.reject('Failed to parse guardrail output.');
  }
}

export interface RealtimeOutputGuardrailResult {
  tripwireTriggered: boolean;
  outputInfo: any;
}

export interface RealtimeOutputGuardrailArgs {
  agentOutput: string;
  agent?: any;
  context?: any;
}

function isTripwireTriggered(category: string, profile: GuardrailProfile) {
  if (category === 'OFFENSIVE' || category === 'VIOLENCE') {
    return true;
  }
  if (profile === 'company' && category === 'OFF_BRAND') {
    return true;
  }
  return false;
}

// Creates a guardrail bound to a specific company name for output moderation purposes. 
export function createModerationGuardrail(
  companyName: string,
  profile: GuardrailProfile = 'company',
) {
  return {
    name: 'moderation_guardrail',

    async execute({ agentOutput }: RealtimeOutputGuardrailArgs): Promise<RealtimeOutputGuardrailResult> {
      try {
        const res = await runGuardrailClassifier(agentOutput, { companyName, profile });
        const triggered = isTripwireTriggered(res.moderationCategory, profile);
        return {
          tripwireTriggered: triggered,
          outputInfo: res,
        };
      } catch {
        return {
          tripwireTriggered: false,
          outputInfo: { error: 'guardrail_failed' },
        };
      }
    },
  } as const;
}
