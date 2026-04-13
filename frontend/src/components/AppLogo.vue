<template>
  <div
    class="app-logo"
    :class="[`app-logo--${size}`]"
  >
    <svg
      class="app-logo__icon"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M12 18c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm0-4c-1.1 0-2.08.45-2.79 1.17l-1.42-1.42C8.84 12.7 10.33 12 12 12s3.16.7 4.21 1.75l-1.42 1.42C14.08 14.45 13.1 14 12 14zm0-4c-2.2 0-4.19.9-5.64 2.36l-1.42-1.42C6.68 9.21 9.22 8 12 8s5.32 1.21 7.06 2.94l-1.42 1.42C16.19 10.9 14.2 10 12 10zm0-4c-3.31 0-6.31 1.34-8.49 3.51L2.1 8.1C4.63 5.57 8.13 4 12 4s7.37 1.57 9.9 4.1l-1.41 1.41C18.31 7.34 15.31 6 12 6z"
        fill="currentColor"
      />
    </svg>
    <span class="app-logo__text">NoteWorks</span>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'AppLogo' })

withDefaults(defineProps<{
  size?: 'small' | 'medium' | 'large'
}>(), {
  size: 'medium',
})
</script>

<style scoped>
.app-logo {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  user-select: none;
}

.app-logo__icon {
  color: var(--home-text, #202124);
}

.app-logo__text {
  font-weight: 700;
  color: var(--home-text, #202124);
  line-height: 1;
}

.app-logo--small .app-logo__icon {
  width: 20px;
  height: 20px;
}

.app-logo--small .app-logo__text {
  font-size: 18px;
}

.app-logo--medium .app-logo__icon {
  width: 24px;
  height: 24px;
}

.app-logo--medium .app-logo__text {
  font-size: 22px;
}

.app-logo--large .app-logo__icon {
  width: 30px;
  height: 30px;
}

.app-logo--large .app-logo__text {
  font-size: 28px;
}
</style>
