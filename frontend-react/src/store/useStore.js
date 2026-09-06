import { create } from 'zustand'

const getInitialHiddenModules = () => {
  if (typeof window === 'undefined') return []
  const saved = localStorage.getItem('hiddenModules')
  if (saved) {
    try {
      return JSON.parse(saved)
    } catch {
      return []
    }
  }
  return []
}

const getInitialDarkMode = () => {
  if (typeof window === 'undefined') return false
  const saved = localStorage.getItem('darkMode')
  if (saved === null) {
    localStorage.setItem('darkMode', 'false')
    return false
  }
  return saved === 'true'
}

const getInitialLicense = () => {
  if (typeof window === 'undefined') return { estado: 'activa', dias_restantes: 999, mensaje: '', nombre: '' }
  const saved = localStorage.getItem('license')
  if (saved) {
    try {
      return JSON.parse(saved)
    } catch {
      return { estado: 'activa', dias_restantes: 999, mensaje: '', nombre: '' }
    }
  }
  return { estado: 'activa', dias_restantes: 999, mensaje: '', nombre: '' }
}

export const useStore = create((set, get) => ({
  darkMode: getInitialDarkMode(),
  hiddenModules: getInitialHiddenModules(),
  license: getInitialLicense(),
  isMobile: typeof window !== 'undefined' && (window.innerWidth < 768 || (window.matchMedia('(pointer: coarse)').matches && window.innerWidth < 1280)),

  setIsMobile: (val) => set({ isMobile: val }),

  toggleDarkMode: () => {
    const newMode = !get().darkMode
    localStorage.setItem('darkMode', newMode)
    set({ darkMode: newMode })
    if (newMode) {
      document.body.classList.add('dark')
    } else {
      document.body.classList.remove('dark')
    }
    window.dispatchEvent(new Event('darkModeChange'))
  },

  initDarkMode: () => {
    const saved = localStorage.getItem('darkMode') === 'true'
    set({ darkMode: saved })
    if (saved) {
      document.body.classList.add('dark')
    } else {
      document.body.classList.remove('dark')
    }
  },

  syncDarkMode: () => {
    const saved = localStorage.getItem('darkMode') === 'true'
    const current = get().darkMode
    if (saved !== current) {
      set({ darkMode: saved })
      if (saved) {
        document.body.classList.add('dark')
      } else {
        document.body.classList.remove('dark')
      }
    }
  },

  setLicense: (licenseData) => {
    localStorage.setItem('license', JSON.stringify(licenseData))
    set({ license: licenseData })
  },

  toggleHiddenModule: (modulo) => {
    const current = get().hiddenModules
    const next = current.includes(modulo)
      ? current.filter(m => m !== modulo)
      : [...current, modulo]
    localStorage.setItem('hiddenModules', JSON.stringify(next))
    set({ hiddenModules: next })
  },
}))

if (typeof window !== 'undefined') {
  window.addEventListener('storage', (e) => {
    if (e.key === 'darkMode') {
      useStore.getState().syncDarkMode()
    }
  })
  
  window.addEventListener('darkModeChange', () => {
    useStore.getState().syncDarkMode()
  })
  
  window.addEventListener('focus', () => {
    useStore.getState().syncDarkMode()
  })
}