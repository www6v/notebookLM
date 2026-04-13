<template>
  <v-app :theme="themeStore.theme">
    <router-view />

    <v-snackbar
      v-model="snackbar.visible"
      :color="snackbar.color"
      :timeout="snackbar.timeout"
      location="bottom"
      @update:model-value="(v) => !v && snackbar.close()"
    >
      {{ snackbar.message }}
    </v-snackbar>

    <v-dialog
      v-model="confirm.visible"
      max-width="400"
      persistent
    >
      <v-card>
        <v-card-title>{{ confirm.title }}</v-card-title>
        <v-card-text v-if="confirm.text">{{ confirm.text }}</v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            variant="text"
            @click="confirm.onCancel()"
          >
            {{ confirm.cancelText }}
          </v-btn>
          <v-btn
            color="primary"
            variant="text"
            @click="confirm.onConfirm()"
          >
            {{ confirm.confirmText }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-app>
</template>

<script setup lang="ts">
import { useThemeStore } from '@/stores/useThemeStore'
import { useSnackbarStore } from '@/stores/useSnackbarStore'
import { useConfirmStore } from '@/stores/useConfirmStore'

const themeStore = useThemeStore()
const snackbar = useSnackbarStore()
const confirm = useConfirmStore()
</script>

<style>
:root,
.theme-light {
  --primary-color: #4285f4;
  --primary-hover: #3367d6;
  --bg-color: #f8f9fa;
  --surface-color: #ffffff;
  --text-primary: #202124;
  --text-secondary: #5f6368;
  --border-color: #dadce0;
  --shadow-sm: 0 1px 2px 0 rgba(60, 64, 67, 0.3), 0 1px 3px 1px rgba(60, 64, 67, 0.15);
  --shadow-md: 0 1px 3px 0 rgba(60, 64, 67, 0.3), 0 4px 8px 3px rgba(60, 64, 67, 0.15);
  --radius: 8px;
  --radius-lg: 16px;
  --home-bg: #f8f9fa;
  --home-surface: #ffffff;
  --home-border: #dadce0;
  --home-text: #202124;
  --home-text-secondary: #5f6368;
  --home-primary: #4285f4;
  /* 首页操作栏红框风格：分段按钮与主按钮 */
  --action-bar-inactive-bg: #f1f3f4;
  --action-bar-active-bg: #e8eaed;
  --action-bar-hover-bg: #e8eaed;
  --action-bar-border: #dadce0;
  --action-bar-primary-bg: #202124;
  --action-bar-primary-text: #ffffff;
  --list-header-bg: #f8f9fa;
  --list-row-hover-bg: rgba(60, 64, 67, 0.06);
}

.theme-dark {
  --primary-color: #8ab4f8;
  --primary-hover: #aecbfa;
  --bg-color: #1f1f1f;
  --surface-color: #2d2d2d;
  --text-primary: #e8e8e8;
  --text-secondary: #9aa0a6;
  --border-color: #3d3d3d;
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3), 0 1px 3px 1px rgba(0, 0, 0, 0.2);
  --shadow-md: 0 1px 3px 0 rgba(0, 0, 0, 0.3), 0 4px 8px 3px rgba(0, 0, 0, 0.2);
  --home-bg: #1f1f1f;
  --home-surface: #2d2d2d;
  --home-border: #3d3d3d;
  --home-text: #e8e8e8;
  --home-text-secondary: #9aa0a6;
  --home-primary: #8ab4f8;
  --action-bar-inactive-bg: #3d3d3d;
  --action-bar-active-bg: #5d5d5d;
  --action-bar-hover-bg: #4d4d4d;
  --action-bar-border: #3d3d3d;
  --action-bar-primary-bg: #202124;
  --action-bar-primary-text: #ffffff;
  --list-header-bg: #2d2d2d;
  --list-row-hover-bg: rgba(255, 255, 255, 0.04);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Google Sans', 'Segoe UI', Roboto, -apple-system, BlinkMacSystemFont, sans-serif;
  background-color: var(--bg-color);
  color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
}

a {
  color: var(--primary-color);
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}
</style>
