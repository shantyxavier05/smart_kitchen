import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext'

function UserMenu() {
  const [isOpen, setIsOpen] = useState(false)
  const { user, logout } = useAuth()
  const menuRef = useRef(null)

  // Get first letter of username for avatar
  const getInitial = () => {
    if (user?.username) {
      return user.username.charAt(0).toUpperCase()
    }
    return 'U'
  }

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  const handleLogout = () => {
    logout()
    setIsOpen(false)
    window.location.hash = 'home'
  }

  const handleProfileClick = () => {
    setIsOpen(false)
    window.location.hash = 'profile'
  }

  return (
    <div className="user-menu-container" ref={menuRef}>
      <button 
        className="user-menu-avatar" 
        onClick={() => setIsOpen(!isOpen)}
        aria-label="User menu"
      >
        {getInitial()}
      </button>

      {isOpen && (
        <div className="user-menu-dropdown">
          <div className="user-menu-header">
            <div className="user-menu-avatar-large">
              {getInitial()}
            </div>
            <div className="user-menu-info">
              <p className="user-menu-name">{user?.username || 'User'}</p>
              <p className="user-menu-email">{user?.email || ''}</p>
            </div>
          </div>
          
          <div className="user-menu-divider"></div>
          
          <button className="user-menu-item" onClick={handleProfileClick}>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
            <span>View Profile</span>
          </button>
          
          <button className="user-menu-item" onClick={handleLogout}>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
            <span>Logout</span>
          </button>
        </div>
      )}
    </div>
  )
}

export default UserMenu

