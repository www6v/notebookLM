<template>
  <router-view />
</template>

<script setup lang="ts">
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
