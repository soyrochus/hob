export interface AvatarConfig {
  baseImage: string;
  overlayImages?: {
    level1: string;
    level2: string;
    level3: string;
    level4: string;
  };
  altText?: string;
}

export const defaultOverlays = {
  level1: "/avatars/overlays/overlay-1.png",
  level2: "/avatars/overlays/overlay-2.png",
  level3: "/avatars/overlays/overlay-3.png",
  level4: "/avatars/overlays/overlay-4.png",
};

export const defaultBaseImage = "/avatars/default-avatar.svg";

export const avatarConfigs: Record<string, AvatarConfig> = {
  chatAgent: {
    //baseImage: "/avatars/chat-agent.svg",
    baseImage: "/avatars/hob-small.png",
    altText: "Chat agent avatar",
  },
};
