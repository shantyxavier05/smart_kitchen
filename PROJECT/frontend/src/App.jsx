import { useState, useEffect } from 'react'
import { AuthProvider } from './context/AuthContext'
import Landing from './components/Landing'
import Login from './components/Login'
import Signup from './components/Signup'
import MealPlanner from './components/MealPlanner'
import Inventory from './components/Inventory'
import ShoppingList from './components/ShoppingList'
import UserProfile from './components/UserProfile'
import ProtectedRoute from './components/ProtectedRoute'
import './App.css'

function AppContent() {
  const [currentPage, setCurrentPage] = useState('home')

  useEffect(() => {
    // Simple routing based on URL hash
    const handleHashChange = () => {
      const hash = window.location.hash.slice(1) || 'home'
      setCurrentPage(hash)
    }

    handleHashChange()
    window.addEventListener('hashchange', handleHashChange)

    return () => window.removeEventListener('hashchange', handleHashChange)
  }, [])

  // Override link clicks for navigation
  useEffect(() => {
    const handleClick = (e) => {
      const link = e.target.closest('a')
      if (link && link.getAttribute('href')?.startsWith('/') || link?.getAttribute('href')?.startsWith('#')) {
        e.preventDefault()
        const path = link.getAttribute('href').slice(1) || 'home'
        window.location.hash = path
      }
    }

    document.addEventListener('click', handleClick)
    return () => document.removeEventListener('click', handleClick)
  }, [])

  // Render the appropriate page based on route
  const renderPage = () => {
    switch (currentPage) {
      case 'login':
        return <Login />
      case 'signup':
        return <Signup />
      case 'meal-planner':
        return (
          <ProtectedRoute>
            <MealPlanner />
          </ProtectedRoute>
        )
      case 'inventory':
        return (
          <ProtectedRoute>
            <Inventory />
          </ProtectedRoute>
        )
      case 'shopping-list':
        return (
          <ProtectedRoute>
            <ShoppingList />
          </ProtectedRoute>
        )
      case 'profile':
        return (
          <ProtectedRoute>
            <UserProfile />
          </ProtectedRoute>
        )
      case 'home':
      default:
        return <Landing />
    }
  }

  return <>{renderPage()}</>
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App

