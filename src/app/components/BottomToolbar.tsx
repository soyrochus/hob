import React from "react";
import { SessionStatus } from "@/app/types";

interface BottomToolbarProps {
  sessionStatus: SessionStatus;
  onToggleConnection: () => void;
  isPTTActive: boolean;
  setIsPTTActive: (val: boolean) => void;
  isPTTUserSpeaking: boolean;
  handleTalkButtonDown: () => void;
  handleTalkButtonUp: () => void;
  isEventsPaneExpanded: boolean;
  setIsEventsPaneExpanded: (val: boolean) => void;
  isAudioPlaybackEnabled: boolean;
  setIsAudioPlaybackEnabled: (val: boolean) => void;
  isDebugMode: boolean;
  setIsDebugMode: (val: boolean) => void;
  codec: string;
  onCodecChange: (newCodec: string) => void;
}

function BottomToolbar({
  sessionStatus,
  onToggleConnection,
  isPTTActive,
  setIsPTTActive,
  isPTTUserSpeaking,
  handleTalkButtonDown,
  handleTalkButtonUp,
  isEventsPaneExpanded,
  setIsEventsPaneExpanded,
  isAudioPlaybackEnabled,
  setIsAudioPlaybackEnabled,
  isDebugMode,
  setIsDebugMode,
  codec,
  onCodecChange,
}: BottomToolbarProps) {
  const isConnected = sessionStatus === "CONNECTED";
  const isConnecting = sessionStatus === "CONNECTING";

  const handleCodecChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newCodec = e.target.value;
    onCodecChange(newCodec);
  };

  function getConnectionButtonLabel() {
    if (isConnected) return "Disconnect";
    if (isConnecting) return "Connecting...";
    return "Connect";
  }

  function getConnectionButtonClasses() {
    const baseClasses = "text-white text-base p-2 w-36 rounded-md h-full";
    const cursorClass = isConnecting ? "cursor-not-allowed" : "cursor-pointer";

    if (isConnected) {
      // Connected -> label "Disconnect" -> red
      return `bg-red-600 hover:bg-red-700 ${cursorClass} ${baseClasses}`;
    }
    // Disconnected or connecting -> label is either "Connect" or "Connecting" -> black
    return `bg-black hover:bg-gray-900 ${cursorClass} ${baseClasses}`;
  }

  return (
    <div className="p-4 flex flex-row items-center gap-x-8">
      <div
        className={`flex flex-row items-center gap-x-8 ${
          !isDebugMode ? "invisible" : ""
        }`}
      >
        <button
          onClick={onToggleConnection}
          className={getConnectionButtonClasses()}
          disabled={isConnecting}
        >
          {getConnectionButtonLabel()}
        </button>

        <div className="flex flex-row items-center gap-2">
          <input
            id="push-to-talk"
            type="checkbox"
            checked={isPTTActive}
            onChange={(e) => setIsPTTActive(e.target.checked)}
            disabled={!isConnected}
            className="w-4 h-4"
          />
          <label
            htmlFor="push-to-talk"
            className="flex items-center cursor-pointer"
          >
            Push to talk
          </label>
          <button
            onMouseDown={handleTalkButtonDown}
            onMouseUp={handleTalkButtonUp}
            onTouchStart={handleTalkButtonDown}
            onTouchEnd={handleTalkButtonUp}
            disabled={!isPTTActive}
            className={
              (isPTTUserSpeaking ? "bg-gray-300" : "bg-gray-200") +
              " py-1 px-4 cursor-pointer rounded-md" +
              (!isPTTActive ? " bg-gray-100 text-gray-400" : "")
            }
          >
            Talk
          </button>
        </div>

        <div className="flex flex-row items-center gap-1">
          <input
            id="audio-playback"
            type="checkbox"
            checked={isAudioPlaybackEnabled}
            onChange={(e) => setIsAudioPlaybackEnabled(e.target.checked)}
            disabled={!isConnected}
            className="w-4 h-4"
          />
          <label
            htmlFor="audio-playback"
            className="flex items-center cursor-pointer"
          >
            Audio playback
          </label>
        </div>

        <div className="flex flex-row items-center gap-2">
          <input
            id="logs"
            type="checkbox"
            checked={isEventsPaneExpanded}
            onChange={(e) => setIsEventsPaneExpanded(e.target.checked)}
            className="w-4 h-4"
          />
          <label htmlFor="logs" className="flex items-center cursor-pointer">
            Logs
          </label>
        </div>

        <div className="flex flex-row items-center gap-2">
          <div>Codec:</div>
          {/*
            Codec selector – Lets you force the WebRTC track to use 8 kHz
            PCMU/PCMA so you can preview how the agent will sound
            (and how ASR/VAD will perform) when accessed via a
            phone network.  Selecting a codec reloads the page with ?codec=...
            which our App-level logic picks up and applies via a WebRTC monkey
            patch (see codecPatch.ts).
          */}
          <select
            id="codec-select"
            value={codec}
            onChange={handleCodecChange}
            className="border border-gray-300 rounded-md px-2 py-1 focus:outline-none cursor-pointer"
          >
            <option value="opus">Opus (48 kHz)</option>
            <option value="pcmu">PCMU (8 kHz)</option>
            <option value="pcma">PCMA (8 kHz)</option>
          </select>
        </div>
      </div>

      <div className="flex flex-row items-center gap-2 ml-auto">
        <label htmlFor="debug-mode" className="text-sm text-gray-600 cursor-pointer">
          Debug
        </label>
        <label htmlFor="debug-mode" className="relative inline-flex cursor-pointer items-center">
          <input
            id="debug-mode"
            type="checkbox"
            role="switch"
            checked={isDebugMode}
            onChange={(e) => setIsDebugMode(e.target.checked)}
            className="sr-only peer"
          />
          <span className="h-6 w-11 rounded-full bg-gray-300 transition-colors peer-checked:bg-gray-800" />
          <span className="absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform peer-checked:translate-x-5" />
        </label>
      </div>
    </div>
  );
}

export default BottomToolbar;
