"use client";

import { useRef } from "react";
import { useTranscript } from "@/app/contexts/TranscriptContext";
import { useEvent } from "@/app/contexts/EventContext";

export function useHandleSessionHistory() {
  const {
    transcriptItems,
    addTranscriptBreadcrumb,
    addTranscriptMessage,
    updateTranscriptMessage,
    updateTranscriptItem,
  } = useTranscript();

  const { logServerEvent } = useEvent();

  /* ----------------------- helpers ------------------------- */

  const extractMessageText = (content: any[] = []): string => {
    if (!Array.isArray(content)) return "";

    return content
      .map((c) => {
        if (!c || typeof c !== "object") return "";
        if (c.type === "input_text") return c.text ?? "";
        if (c.type === "output_text") return c.text ?? "";
        if (c.type === "input_audio") return c.transcript ?? "";
        if (c.type === "output_audio") return c.transcript ?? "";
        if (c.type === "audio") return c.transcript ?? c.text ?? "";
        return "";
      })
      .filter(Boolean)
      .join("\n");
  };

  const maybeParseJson = (val: any) => {
    if (typeof val === 'string') {
      try {
        return JSON.parse(val);
      } catch {
        console.warn('Failed to parse JSON:', val);
        return val;
      }
    }
    return val;
  };

  const extractGuardrailOutputInfo = (error: any) => {
    return error?.result?.output?.outputInfo;
  };

  const sketchilyDetectGuardrailMessage = (text: string) => {
    return text.match(/Failure Details: (\{.*?\})/)?.[1];
  };

  /* ----------------------- event handlers ------------------------- */

  function handleAgentToolStart(_context: any, _agent: any, tool: any, details: any) {
    const functionName = tool?.name ?? "";
    const functionArgs = maybeParseJson(details?.toolCall?.arguments);
    addTranscriptBreadcrumb(
      `function call: ${functionName}`,
      functionArgs
    );    
  }
  function handleAgentToolEnd(_context: any, _agent: any, tool: any, result: any, _details: any) {
    addTranscriptBreadcrumb(
      `function call result: ${tool?.name ?? ""}`,
      maybeParseJson(result)
    );
  }

  function handleHistoryAdded(item: any) {
    console.log("[handleHistoryAdded] ", item);
    if (!item || item.type !== 'message') return;

    const { itemId, role, content = [] } = item;
    if (itemId && role) {
      const isUser = role === "user";
      let text = extractMessageText(content);

      if (isUser && !text) {
        text = "[Transcribing...]";
      }

      // If the guardrail has been tripped, this message is a message that gets sent to the 
      // assistant to correct it, so we add it as a breadcrumb instead of a message.
      const guardrailMessage = sketchilyDetectGuardrailMessage(text);
      if (guardrailMessage) {
        const failureDetails = JSON.parse(guardrailMessage);
        addTranscriptBreadcrumb('Output Guardrail Active', { details: failureDetails });
      } else {
        addTranscriptMessage(itemId, role, text);
      }
    }
  }

  function handleHistoryUpdated(history: any[]) {
    console.log("[handleHistoryUpdated] ", history);
    history.forEach((item: any) => {
      if (!item || item.type !== 'message') return;

      const { itemId, content = [] } = item;
      const existingMessage = transcriptItems.find(
        (transcriptItem) => transcriptItem.itemId === itemId && transcriptItem.type === "MESSAGE"
      );
      if (!existingMessage) return;
      if (existingMessage.status === "DONE") return;

      const text = extractMessageText(content);

      if (text && text !== existingMessage.title) {
        updateTranscriptMessage(itemId, text, false);
      }
    });
  }

  function handleTranscriptionDelta(item: any) {
    const itemId = item.item_id;
    const deltaText = item.delta || "";
    if (itemId) {
      const transcriptItem = transcriptItems.find((i) => i.itemId === itemId);
      if (!transcriptItem) {
        addTranscriptMessage(itemId, "user", "[Transcribing...]");
      }
      updateTranscriptMessage(itemId, deltaText, true);
    }
  }

  function handleTranscriptionCompleted(item: any) {
    // History updates don't reliably end in a completed item, 
    // so we need to handle finishing up when the transcription is completed.
    const itemId = item.item_id;
    const finalTranscript =
        !item.transcript || item.transcript === "\n"
        ? "[inaudible]"
        : item.transcript;
    if (itemId) {
      const existing = transcriptItems.find((i) => i.itemId === itemId);
      if (!existing) {
        addTranscriptMessage(itemId, "user", finalTranscript);
      }
      updateTranscriptMessage(itemId, finalTranscript, false);
      // Use the ref to get the latest transcriptItems
      const transcriptItem = transcriptItems.find((i) => i.itemId === itemId);
      updateTranscriptItem(itemId, { status: 'DONE' });

      // If guardrailResult still pending, mark PASS.
      if (transcriptItem?.guardrailResult?.status === 'IN_PROGRESS') {
        updateTranscriptItem(itemId, {
          guardrailResult: {
            status: 'DONE',
            category: 'NONE',
            rationale: '',
          },
        });
      }
    }
  }

  function handleGuardrailTripped(_context: any, _agent: any, error: any, details: any) {
    console.log("[guardrail tripped]", _context, _agent, error, details);
    const moderation = extractGuardrailOutputInfo(error);
    logServerEvent({ type: 'guardrail_tripped', payload: moderation });

    const itemId = details?.itemId;
    if (!itemId || !moderation || typeof moderation !== "object") {
      return;
    }

    const category = moderation.moderationCategory ?? 'NONE';
    const rationale = moderation.moderationRationale ?? '';
    const offendingText: string | undefined = moderation?.testText;

    updateTranscriptItem(itemId, {
      guardrailResult: {
        status: 'DONE',
        category,
        rationale,
        testText: offendingText,
      },
    });
  }

  const handlersRef = useRef({
    handleAgentToolStart,
    handleAgentToolEnd,
    handleHistoryUpdated,
    handleHistoryAdded,
    handleTranscriptionDelta,
    handleTranscriptionCompleted,
    handleGuardrailTripped,
  });

  return handlersRef;
}
