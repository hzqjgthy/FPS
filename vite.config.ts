import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('three/examples/jsm/')) {
            return 'three-extras';
          }

          if (id.includes('node_modules/three')) {
            return 'three-core';
          }

          return undefined;
        },
      },
    },
  },
});
