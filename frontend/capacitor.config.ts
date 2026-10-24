import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "app.nextpost",
  appName: "NextPost",
  webDir: "dist",
  ios: {
    preferredContentMode: "mobile",
  },
  plugins: {
    CapacitorHttp: {
      enabled: true,
    },
  },
};

export default config;
