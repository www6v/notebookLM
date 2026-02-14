<template>
  <router-view />
</template>

<script setup lang="ts">
</script>

<style>
:root {
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
