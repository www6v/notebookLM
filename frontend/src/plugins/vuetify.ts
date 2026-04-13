import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { aliases, mdi } from 'vuetify/iconsets/mdi'

/**
 * Material Design theme: primary actions use black fills; surfaces unchanged.
 */
const lightTheme = {
  dark: false,
  colors: {
    primary: '#000000',
    'primary-darken-1': '#333333',
    secondary: '#5f6368',
    'surface-bright': '#ffffff',
    'surface-light': '#f8f9fa',
    'surface-variant': '#f1f3f4',
    background: '#f8f9fa',
    error: '#d93025',
    info: '#4285f4',
    success: '#1e8e3e',
    warning: '#f9ab00',
  },
}

const darkTheme = {
  dark: true,
  colors: {
    primary: '#000000',
    'primary-darken-1': '#333333',
    secondary: '#9aa0a6',
    'surface-bright': '#2d2d2d',
    'surface-light': '#1f1f1f',
    'surface-variant': '#3d3d3d',
    background: '#1f1f1f',
    error: '#f28b82',
    info: '#8ab4f8',
    success: '#81c995',
    warning: '#fdd663',
  },
}

export default createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'light',
    themes: {
      light: lightTheme,
      dark: darkTheme,
    },
  },
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: {
      mdi,
    },
  },
  defaults: {
    VBtn: {
      style: 'text-transform: none;',
    },
    VCard: {
      elevation: 0,
      rounded: 'lg',
    },
    VTextField: {
      variant: 'outlined',
      density: 'comfortable',
      hideDetails: 'auto',
    },
    VSelect: {
      variant: 'outlined',
      density: 'comfortable',
      hideDetails: 'auto',
    },
  },
})
