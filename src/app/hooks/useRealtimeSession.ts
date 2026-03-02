import { useCallback, useRef, useState, useEffect } from 'react';
import {
  RealtimeSession,
  RealtimeAgent,
  OpenAIRealtimeWebRTC,
} from '@openai/agents/realtime';

import { applyCodecPreferences } from '../lib/codecUtils';
import { useEvent } from '../contexts/EventContext';
import { useHandleSessionHistory } from './useHandleSessionHistory';
import { SessionStatus } from '../types';

export interface RealtimeSessionCallbacks {
  onConnectionChange?: (status: SessionStatus) => void;
  onAgentHandoff?: (agentName: string) => void;
}

export interface ConnectOptions {
  getEphemeralKey: () => Promise<{ key: string; realtimeUrl?: string }>;
  initialAgents: RealtimeAgent[];
  audioElement?: HTMLAudioElement;
  extraContext?: Record<string, any>;
  outputGuardrails?: any[];
}

export function useRealtimeSession(callbacks: RealtimeSessionCallbacks = {}) {
  const realtimeModel = 'gpt-realtime-2025-08-28';
  const openAiWebRtcUrl = `https://api.openai.com/v1/realtime?model=${encodeURIComponent(
    realtimeModel,
  )}`;
  const sessionRef = useRef<RealtimeSession | null>(null);
  const [status, setStatus] = useState<
    SessionStatus
  >('DISCONNECTED');
  const { logClientEvent } = useEvent();

  const updateStatus = useCallback(
    (s: SessionStatus) => {
      setStatus(s);
      callbacks.onConnectionChange?.(s);
      logClientEvent({}, s);
    },
    [callbacks],
  );

  const { logServerEvent } = useEvent();

  const historyHandlers = useHandleSessionHistory().current;

  const normalizeWebRtcUrl = (url: string) => {
    const normalized = new URL(url);
    if (normalized.protocol === "ws:") normalized.protocol = "http:";
    if (normalized.protocol === "wss:") normalized.protocol = "https:";
    return normalized.toString();
  };

  const normalizeLegacyMessageItem = (item: any) => {
    if (!item || item.type !== "message") return item;
    const role = item.role;
    const content = Array.isArray(item.content)
      ? item.content.map((c: any) => {
          if (!c || typeof c !== "object") return c;
          if (c.type !== "audio") return c;
          return {
            ...c,
            type: role === "assistant" ? "output_audio" : "input_audio",
          };
        })
      : [];

    return {
      itemId: item.itemId ?? item.id,
      previousItemId: item.previousItemId ?? item.previous_item_id,
      type: item.type,
      role,
      status: item.status,
      content,
    };
  };

  const buildLegacyFunctionTools = (agent: RealtimeAgent) => {
    const rawTools = ((agent as any)?.tools ?? []) as any[];
    return rawTools
      .map((tool) => {
        if (!tool || typeof tool !== "object") return null;
        const type = tool.type ?? "function";
        if (type !== "function") return null;
        if (!tool.name) return null;
        return {
          type: "function",
          name: tool.name,
          description: tool.description,
          parameters: tool.parameters,
        };
      })
      .filter(Boolean);
  };

  function handleTransportEvent(event: any) {
    // Handle additional server events that aren't managed by the session
    switch (event.type) {
      case "conversation.item.created": {
        const normalizedItem = normalizeLegacyMessageItem(event.item);
        if (normalizedItem?.type === "message") {
          historyHandlers.handleHistoryAdded(normalizedItem);
        }
        break;
      }
      case "response.output_item.added": {
        const normalizedItem = normalizeLegacyMessageItem(event.item);
        if (normalizedItem?.type === "message") {
          historyHandlers.handleHistoryAdded(normalizedItem);
        }
        if (event.item?.type === "function_call") {
          const tool = { name: event.item.name };
          const details = { toolCall: { arguments: event.item.arguments } };
          historyHandlers.handleAgentToolStart(undefined, undefined, tool, details);
        }
        break;
      }
      case "response.output_item.done": {
        const normalizedItem = normalizeLegacyMessageItem(event.item);
        if (normalizedItem?.type === "message") {
          historyHandlers.handleHistoryUpdated([normalizedItem]);
        }
        if (event.item?.type === "function_call") {
          const tool = { name: event.item.name };
          const details = { toolCall: { arguments: event.item.arguments } };
          historyHandlers.handleAgentToolStart(undefined, undefined, tool, details);
          historyHandlers.handleAgentToolEnd(
            undefined,
            undefined,
            tool,
            event.item.output,
            details,
          );
        }
        break;
      }
      case "conversation.item.input_audio_transcription.completed": {
        historyHandlers.handleTranscriptionCompleted(event);
        break;
      }
      case "response.output_audio_transcript.done":
      case "response.audio_transcript.done": {
        historyHandlers.handleTranscriptionCompleted(event);
        break;
      }
      case "response.output_audio_transcript.delta":
      case "response.audio_transcript.delta": {
        historyHandlers.handleTranscriptionDelta(event);
        break;
      }
      case "response.content_part.done": {
        const transcript = event.part?.transcript;
        if (event.item_id && transcript) {
          historyHandlers.handleTranscriptionCompleted({
            item_id: event.item_id,
            transcript,
          });
        }
        break;
      }
      default: {
        logServerEvent(event);
        break;
      } 
    }
  }

  const codecParamRef = useRef<string>(
    (typeof window !== 'undefined'
      ? (new URLSearchParams(window.location.search).get('codec') ?? 'opus')
      : 'opus')
      .toLowerCase(),
  );

  // Wrapper to pass current codec param.
  // This lets you use the codec selector in the UI to force narrow-band (8 kHz) codecs to
  // simulate how the voice agent sounds over a PSTN/SIP phone call.
  const applyCodec = useCallback(
    (pc: RTCPeerConnection) => applyCodecPreferences(pc, codecParamRef.current),
    [],
  );

  const handleAgentHandoff = (_context: any, _fromAgent: any, toAgent: any) => {
    const agentName = toAgent?.name;
    if (agentName) {
      callbacks.onAgentHandoff?.(agentName);
    }
  };

  useEffect(() => {
    if (sessionRef.current) {
      // Log server errors
      sessionRef.current.on("error", (...args: any[]) => {
        logServerEvent({
          type: "error",
          message: args[0],
        });
      });

      // history events
      sessionRef.current.on("agent_handoff", handleAgentHandoff);
      sessionRef.current.on("agent_tool_start", historyHandlers.handleAgentToolStart);
      sessionRef.current.on("agent_tool_end", historyHandlers.handleAgentToolEnd);
      sessionRef.current.on("history_updated", historyHandlers.handleHistoryUpdated);
      sessionRef.current.on("history_added", historyHandlers.handleHistoryAdded);
      sessionRef.current.on("guardrail_tripped", historyHandlers.handleGuardrailTripped);

      // additional transport events
      sessionRef.current.on("transport_event", handleTransportEvent);
    }
  }, [sessionRef.current]);

  const connect = useCallback(
    async ({
      getEphemeralKey,
      initialAgents,
      audioElement,
      extraContext,
      outputGuardrails,
    }: ConnectOptions) => {
      if (sessionRef.current) return; // already connected

      updateStatus('CONNECTING');

      const { key, realtimeUrl } = await getEphemeralKey();
      const rootAgent = initialAgents[0];

      sessionRef.current = new RealtimeSession(rootAgent, {
        transport: new OpenAIRealtimeWebRTC({
          audioElement,
          // For OpenAI provider, use the WebRTC SDP endpoint directly.
          // Azure can still override this by passing `connect({ url })`.
          baseUrl: openAiWebRtcUrl,
          // Set preferred codec before offer creation
          changePeerConnection: async (pc: RTCPeerConnection) => {
            applyCodec(pc);
            return pc;
          },
        }),
        model: realtimeModel,
        config: {
          inputAudioTranscription: {
            model: 'gpt-4o-mini-transcribe',
          },
        },
        outputGuardrails: outputGuardrails ?? [],
        context: extraContext ?? {},
      });

      await sessionRef.current.connect(
        realtimeUrl
          ? { apiKey: key, url: normalizeWebRtcUrl(realtimeUrl) }
          : { apiKey: key }
      );

      // Legacy protocol compatibility: ensure instructions/tools/transcription are
      // explicitly applied even when session.update behavior differs across model versions.
      try {
        const legacyFunctionTools = buildLegacyFunctionTools(rootAgent);
        sessionRef.current.transport.sendEvent({
          type: "session.update",
          session: {
            modalities: ["audio", "text"],
            instructions: (rootAgent as any)?.instructions,
            tool_choice: "auto",
            tools: legacyFunctionTools,
            input_audio_transcription: {
              model: "gpt-4o-mini-transcribe",
            },
            turn_detection: {
              type: "server_vad",
              create_response: true,
              interrupt_response: true,
            },
          },
        } as any);
      } catch (error) {
        logServerEvent({
          type: "legacy_session_update_error",
          error,
        });
      }

      updateStatus('CONNECTED');
    },
    [callbacks, updateStatus],
  );

  const disconnect = useCallback(() => {
    sessionRef.current?.close();
    sessionRef.current = null;
    updateStatus('DISCONNECTED');
  }, [updateStatus]);

  const assertconnected = () => {
    if (!sessionRef.current) throw new Error('RealtimeSession not connected');
  };

  /* ----------------------- message helpers ------------------------- */

  const interrupt = useCallback(() => {
    sessionRef.current?.interrupt();
  }, []);
  
  const sendUserText = useCallback((text: string) => {
    assertconnected();
    sessionRef.current!.sendMessage(text);
  }, []);

  const sendEvent = useCallback((ev: any) => {
    sessionRef.current?.transport.sendEvent(ev);
  }, []);

  const mute = useCallback((m: boolean) => {
    sessionRef.current?.mute(m);
  }, []);

  const pushToTalkStart = useCallback(() => {
    if (!sessionRef.current) return;
    sessionRef.current.transport.sendEvent({ type: 'input_audio_buffer.clear' } as any);
  }, []);

  const pushToTalkStop = useCallback(() => {
    if (!sessionRef.current) return;
    sessionRef.current.transport.sendEvent({ type: 'input_audio_buffer.commit' } as any);
    sessionRef.current.transport.sendEvent({ type: 'response.create' } as any);
  }, []);

  return {
    status,
    connect,
    disconnect,
    sendUserText,
    sendEvent,
    mute,
    pushToTalkStart,
    pushToTalkStop,
    interrupt,
  } as const;
}
