import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useConfirmStore = defineStore('confirm', () => {
  const visible = ref(false)
  const title = ref('')
  const text = ref('')
  const confirmText = ref('确定')
  const cancelText = ref('取消')
  const resolveRef = ref<((value: boolean) => void) | null>(null)

  function confirm(options: {
    title: string
    text?: string
    confirmButtonText?: string
    cancelButtonText?: string
  }): Promise<boolean> {
    title.value = options.title
    text.value = options.text ?? ''
    confirmText.value = options.confirmButtonText ?? '确定'
    cancelText.value = options.cancelButtonText ?? '取消'
    visible.value = true
    return new Promise((resolve) => {
      resolveRef.value = resolve
    })
  }

  function onConfirm() {
    resolveRef.value?.(true)
    resolveRef.value = null
    visible.value = false
  }

  function onCancel() {
    resolveRef.value?.(false)
    resolveRef.value = null
    visible.value = false
  }

  return {
    visible,
    title,
    text,
    confirmText,
    cancelText,
    confirm,
    onConfirm,
    onCancel,
  }
})
