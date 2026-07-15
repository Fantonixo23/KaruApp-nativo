import React, { useState, useEffect, createContext, useContext } from 'react'

const FullscreenContext = createContext()

export function FullscreenProvider({ children }) {
  const [isFullscreen, setIsFullscreen] = useState(() => {
    return localStorage.getItem('fullscreen') === 'true'
  })

  useEffect(() => {
    localStorage.setItem('fullscreen', String(isFullscreen))
    
    if (isFullscreen) {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(() => {})
      }
    } else {
      if (document.fullscreenElement) {
        document.exitFullscreen().catch(() => {})
      }
    }
  }, [isFullscreen])

  useEffect(() => {
    const handleChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }
    document.addEventListener('fullscreenchange', handleChange)
    return () => document.removeEventListener('fullscreenchange', handleChange)
  }, [])

  const toggle = () => setIsFullscreen(!isFullscreen)

  return (
    <FullscreenContext.Provider value={{ isFullscreen, toggle }}>
      {children}
    </FullscreenContext.Provider>
  )
}

export function useFullscreen() {
  return useContext(FullscreenContext)
}