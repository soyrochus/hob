import Image from "next/image";
import { AvatarConfig, defaultBaseImage } from "@/app/agentConfigs/avatarConfig";

interface AvatarProps {
  config: AvatarConfig;
}

function Avatar({ config }: AvatarProps) {
  const baseImage = config.baseImage || defaultBaseImage;
  const altText = config.altText || "Agent avatar";

  return (
    <div className="w-1/2 rounded-xl bg-white flex items-center justify-center overflow-hidden">
      <div className="relative w-4/5 max-w-[420px] aspect-square">
        <Image
          src={baseImage}
          alt={altText}
          fill
          className="object-contain"
          sizes="(max-width: 1024px) 45vw, 30vw"
          priority
        />
      </div>
    </div>
  );
}

export default Avatar;
