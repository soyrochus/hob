"use client";

import { useEffect, useRef, useState } from "react";

export type AvatarAudioLevel = 0 | 1 | 2 | 3 | 4;

const FFT_SIZE = 512;
const UPDATE_EVERY_N_FRAMES = 2;
const SILENCE_THRESHOLD = 0.0012;
const LEVEL_1_THRESHOLD = 0.0035;
const LEVEL_2_THRESHOLD = 0.008;
const LEVEL_3_THRESHOLD = 0.018;
const SIGNAL_SMOOTHING_ALPHA = 0.45;
const NOISE_FLOOR_ALPHA = 0.04;
const NOISE_GATE_MULTIPLIER = 1.35;
const MIN_NOISE_GATE = 0.0006;
const ACTIVE_FRAMES_TO_RAISE = 1;

let sharedAudioContext: AudioContext | null = null;
const sourceNodeByElement = new WeakMap<
  HTMLMediaElement,
  MediaElementAudioSourceNode
>();
const sourceNodeByStream = new WeakMap<MediaStream, MediaStreamAudioSourceNode>();

function getAudioContext(): AudioContext {
  if (sharedAudioContext) {
    return sharedAudioContext;
  }
  const AudioContextCtor =
    window.AudioContext ||
    (window as typeof window & { webkitAudioContext?: typeof AudioContext })
      .webkitAudioContext;
  if (!AudioContextCtor) {
    throw new Error("Web Audio API is not supported in this browser.");
  }
  sharedAudioContext = new AudioContextCtor();
  return sharedAudioContext;
}

function getOrCreateSourceNode(
  audioElement: HTMLMediaElement,
  context: AudioContext
): MediaElementAudioSourceNode {
  const existing = sourceNodeByElement.get(audioElement);
  if (existing) {
    return existing;
  }
  const source = context.createMediaElementSource(audioElement);
  sourceNodeByElement.set(audioElement, source);
  return source;
}

function getOrCreateStreamSourceNode(
  stream: MediaStream,
  context: AudioContext
): MediaStreamAudioSourceNode {
  const existing = sourceNodeByStream.get(stream);
  if (existing) {
    return existing;
  }
  const source = context.createMediaStreamSource(stream);
  sourceNodeByStream.set(stream, source);
  return source;
}

function mapActivityToLevel(activity: number): AvatarAudioLevel {
  if (activity < SILENCE_THRESHOLD) return 0;
  if (activity < LEVEL_1_THRESHOLD) return 1;
  if (activity < LEVEL_2_THRESHOLD) return 2;
  if (activity < LEVEL_3_THRESHOLD) return 3;
  return 4;
}

export function useAvatarAudioLevel(
  audioElement: HTMLAudioElement | null | undefined
): AvatarAudioLevel {
  const [level, setLevel] = useState<AvatarAudioLevel>(0);
  const frameRef = useRef<number | null>(null);
  const frameCounterRef = useRef(0);
  const lastLevelRef = useRef<AvatarAudioLevel>(0);
  const smoothedActivityRef = useRef(0);
  const noiseFloorRef = useRef(0);
  const activeFrameCountRef = useRef(0);

  useEffect(() => {
    if (!audioElement || typeof window === "undefined") {
      setLevel(0);
      lastLevelRef.current = 0;
      return;
    }

    let audioContext: AudioContext;
    try {
      audioContext = getAudioContext();
    } catch {
      setLevel(0);
      return;
    }
    setLevel(0);
    lastLevelRef.current = 0;
    smoothedActivityRef.current = 0;
    noiseFloorRef.current = 0;
    activeFrameCountRef.current = 0;
    void audioContext.resume().catch(() => {
      // Browser autoplay policies can defer context activation.
    });

    const analyser = audioContext.createAnalyser();
    analyser.fftSize = FFT_SIZE;
    analyser.smoothingTimeConstant = 0.55;
    let source: MediaElementAudioSourceNode | MediaStreamAudioSourceNode | null =
      null;
    let sourceKind: "element" | "stream" | null = null;
    let connectedStream: MediaStream | null = null;

    const disconnectSource = () => {
      if (!source) return;

      try {
        source.disconnect(analyser);
      } catch {
        // No-op: source may already be disconnected.
      }

      if (sourceKind === "element") {
        try {
          (source as MediaElementAudioSourceNode).disconnect(
            audioContext.destination
          );
        } catch {
          // No-op: destination connection may already be disconnected.
        }
      }

      source = null;
      sourceKind = null;
      connectedStream = null;
    };

    const connectSource = () => {
      const srcObject = audioElement.srcObject;
      const stream =
        srcObject instanceof MediaStream && srcObject.getAudioTracks().length > 0
          ? srcObject
          : null;

      if (stream) {
        const streamSource = getOrCreateStreamSourceNode(stream, audioContext);
        if (source === streamSource) return;
        disconnectSource();
        streamSource.connect(analyser);
        source = streamSource;
        sourceKind = "stream";
        connectedStream = stream;
        return;
      }

      const elementSource = getOrCreateSourceNode(audioElement, audioContext);
      if (source === elementSource) return;
      disconnectSource();
      elementSource.connect(analyser);
      elementSource.connect(audioContext.destination);
      source = elementSource;
      sourceKind = "element";
      connectedStream = null;
    };

    connectSource();

    // Resume AudioContext on the first user gesture (e.g. the Connect button
    // click). This must happen before srcObject is set so the Web Audio graph
    // is already live when audio starts flowing. The earlier resume() above
    // will have been rejected because it ran before any user interaction.
    const resumeOnActivation = () => {
      void audioContext.resume().catch(() => {});
    };
    document.addEventListener("click", resumeOnActivation, { once: true });
    document.addEventListener("pointerdown", resumeOnActivation, { once: true });
    document.addEventListener("keydown", resumeOnActivation, { once: true });

    // Belt-and-suspenders: also resume when the element actually plays.
    const handlePlay = () => {
      void audioContext.resume().catch(() => {});
    };
    audioElement.addEventListener("play", handlePlay);

    const samples = new Uint8Array(analyser.fftSize);
    let unmounted = false;

    const tick = () => {
      if (unmounted) return;

      const srcObject = audioElement.srcObject;
      const currentStream = srcObject instanceof MediaStream ? srcObject : null;
      if (currentStream !== connectedStream) {
        connectSource();
      }

      frameCounterRef.current += 1;
      if (frameCounterRef.current % UPDATE_EVERY_N_FRAMES === 0) {
        analyser.getByteTimeDomainData(samples);
        let sumSquares = 0;
        let peak = 0;
        for (let i = 0; i < samples.length; i += 1) {
          const centered = (samples[i] - 128) / 128;
          const abs = Math.abs(centered);
          sumSquares += centered * centered;
          if (abs > peak) peak = abs;
        }

        const rms = Math.sqrt(sumSquares / samples.length);
        const activity = Math.max(rms, peak * 0.8);
        const smoothedActivity =
          smoothedActivityRef.current +
          (activity - smoothedActivityRef.current) * SIGNAL_SMOOTHING_ALPHA;
        smoothedActivityRef.current = smoothedActivity;

        const shouldAdaptNoiseFloor =
          lastLevelRef.current === 0 || smoothedActivity < LEVEL_1_THRESHOLD;
        if (shouldAdaptNoiseFloor) {
          noiseFloorRef.current =
            noiseFloorRef.current +
            (smoothedActivity - noiseFloorRef.current) * NOISE_FLOOR_ALPHA;
        }

        const noiseGate = Math.max(
          MIN_NOISE_GATE,
          noiseFloorRef.current * NOISE_GATE_MULTIPLIER
        );
        const gatedActivity = Math.max(0, smoothedActivity - noiseGate);
        const mappedLevel = mapActivityToLevel(gatedActivity);

        let nextLevel: AvatarAudioLevel = 0;
        if (mappedLevel > 0) {
          activeFrameCountRef.current += 1;
          if (
            lastLevelRef.current > 0 ||
            activeFrameCountRef.current >= ACTIVE_FRAMES_TO_RAISE
          ) {
            nextLevel = mappedLevel;
          }
        } else {
          activeFrameCountRef.current = 0;
        }

        if (nextLevel !== lastLevelRef.current) {
          lastLevelRef.current = nextLevel;
          setLevel(nextLevel);
        }
      }

      frameRef.current = window.requestAnimationFrame(tick);
    };

    frameRef.current = window.requestAnimationFrame(tick);

    return () => {
      unmounted = true;
      document.removeEventListener("click", resumeOnActivation);
      document.removeEventListener("pointerdown", resumeOnActivation);
      document.removeEventListener("keydown", resumeOnActivation);
      audioElement.removeEventListener("play", handlePlay);
      if (frameRef.current !== null) {
        window.cancelAnimationFrame(frameRef.current);
        frameRef.current = null;
      }
      frameCounterRef.current = 0;
      disconnectSource();
      analyser.disconnect();
      lastLevelRef.current = 0;
      smoothedActivityRef.current = 0;
      noiseFloorRef.current = 0;
      activeFrameCountRef.current = 0;
    };
  }, [audioElement]);

  return level;
}
