import Image from "next/image";
import {
  AvatarConfig,
  defaultBaseImage,
  defaultOverlayImages,
} from "@/app/agentConfigs/avatarConfig";
import { useAvatarAudioLevel } from "@/app/hooks/useAvatarAudioLevel";

interface AvatarProps {
  config: AvatarConfig;
  audioElement?: HTMLAudioElement | null;
}

function Avatar({ config, audioElement }: AvatarProps) {
  const baseImage = config.baseImage || defaultBaseImage;
  const altText = config.altText || "Agent avatar";
  const level = useAvatarAudioLevel(audioElement);
  const overlayImages = {
    ...defaultOverlayImages,
    ...config.overlayImages,
  };
  const overlayPath =
    level > 0 ? overlayImages[`level${level}` as keyof typeof overlayImages] : null;

  return (
    <div
      className="w-1/2 rounded-xl bg-white flex items-center justify-center overflow-hidden"
      data-audio-level={level}
    >
      <div className="relative w-4/5 max-w-[420px] aspect-square">
        <Image
          src={baseImage}
          alt={altText}
          fill
          className="object-contain z-0"
          sizes="(max-width: 1024px) 45vw, 30vw"
          priority
        />
        {overlayPath ? (
          <Image
            src={overlayPath}
            alt={`${altText} overlay`}
            fill
            className="object-contain pointer-events-none z-10"
            sizes="(max-width: 1024px) 45vw, 30vw"
            priority
          />
        ) : null}
      </div>
    </div>
  );
}

export default Avatar;
