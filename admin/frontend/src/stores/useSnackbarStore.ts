import { defineStore } from 'pinia'
import { ref } from 'vue'

export type SnackbarColor = 'success' | 'error' | 'warning' | 'info' | 'primary'

export const useSnackbarStore = defineStore('snackbar', () => {
  const visible = ref(false)
  const message = ref('')
  const color = ref<SnackbarColor>('primary')
  const timeout = ref(3000)

  function show(options: {
    message: string
    color?: SnackbarColor
    timeout?: number
  }) {
    message.value = options.message
    color.value = options.color ?? 'primary'
    timeout.value = options.timeout ?? 3000
    visible.value = true
  }

  function success(msg: string, t = 3000) {
    show({ message: msg, color: 'success', timeout: t })
  }

  function error(msg: string, t = 3000) {
    show({ message: msg, color: 'error', timeout: t })
  }

  function warning(msg: string, t = 3000) {
    show({ message: msg, color: 'warning', timeout: t })
  }

  function info(msg: string, t = 3000) {
    show({ message: msg, color: 'info', timeout: t })
  }

  function close() {
    visible.value = false
  }

  return {
    visible,
    message,
    color,
    timeout,
    show,
    success,
    error,
    warning,
    info,
    close,
  }
})
