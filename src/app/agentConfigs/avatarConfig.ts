export interface AvatarConfig {
  baseImage: string;
  overlayImages?: Partial<AvatarOverlayImages>;
  altText?: string;
}

export interface AvatarOverlayImages {
  level1: string;
  level2: string;
  level3: string;
  level4: string;
}

export const defaultOverlayImages: AvatarOverlayImages = {
  level1: "/avatars/overlays/overlay-1.png",
  level2: "/avatars/overlays/overlay-2.png",
  level3: "/avatars/overlays/overlay-3.png",
  level4: "/avatars/overlays/overlay-4.png",
};

export const defaultBaseImage = "/avatars/default-avatar.svg";

export const avatarConfigs: Record<string, AvatarConfig> = {
  chatAgent: {
    baseImage: "/avatars/Hob-small.png",
    altText: "Chat agent avatar",
  },
  greeter: {
    baseImage: "/avatars/Hob-small.png",
    altText: "Greeter agent avatar",
  },
  haikuWriter: {
    baseImage: "/avatars/Hob-small.png",
    altText: "Haiku writer agent avatar",
  },
  authentication: {
    baseImage: "/avatars/Hob-small.png",
    altText: "Authentication agent avatar",
  },
  salesAgent: {
    baseImage: "/avatars/Hob-small.png",
    altText: "Sales agent avatar",
  },
  returns: {
    baseImage: "/avatars/Hob-small.png",
    altText: "Returns agent avatar",
  },
  simulatedHuman: {
    baseImage: "/avatars/Hob-small.png",
    altText: "Simulated human agent avatar",
  },
};
