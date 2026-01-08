import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'

function UserProfile() {
  const { user } = useAuth()
  
  // Allergies state
  const [allergies, setAllergies] = useState([])
  const [allergyInput, setAllergyInput] = useState('')
  const [loadingAllergies, setLoadingAllergies] = useState(false)
  const [savingAllergies, setSavingAllergies] = useState(false)
  
  
  // Fetch user profile data on component mount
  useEffect(() => {
    const fetchUserProfile = async () => {
      const token = localStorage.getItem('token')
      if (!token) return
      
      setLoadingAllergies(true)
      try {
        const response = await fetch('http://localhost:8000/api/user/profile', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        
        if (response.ok) {
          const data = await response.json()
          setAllergies(data.allergies || [])
        }
      } catch (err) {
        console.error('Error fetching user profile:', err)
      } finally {
        setLoadingAllergies(false)
      }
    }
    
    fetchUserProfile()
  }, [])

  // Allergy handlers
  const handleAddAllergy = (e) => {
    // Allow Enter key or button click
    if (e && e.preventDefault) {
      e.preventDefault()
    }
    
    const trimmedInput = allergyInput.trim()
    if (!trimmedInput) return
    
    // Case-insensitive duplicate check
    const inputLower = trimmedInput.toLowerCase()
    const isDuplicate = allergies.some(allergy => allergy.toLowerCase() === inputLower)
    
    if (isDuplicate) {
      alert(`"${trimmedInput}" is already in your allergies list.`)
      return
    }
    
    // Add the allergy (capitalize first letter of each word)
    const formattedAllergy = trimmedInput
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ')
    
    setAllergies([...allergies, formattedAllergy])
    setAllergyInput('')
  }

  const handleAddAllergyKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleAddAllergy(e)
    }
  }

  const handleRemoveAllergy = (allergyToRemove) => {
    setAllergies(allergies.filter(allergy => allergy !== allergyToRemove))
  }


  // Save handlers
  const handleSaveAllergies = async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      alert('You must be logged in to save allergies')
      return
    }
    
    setSavingAllergies(true)
    try {
      const response = await fetch('http://localhost:8000/api/user/profile/allergies', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ allergies })
      })
      
      if (response.ok) {
        alert('Allergies saved successfully!')
      } else {
        const data = await response.json()
        alert(data.detail || 'Failed to save allergies')
      }
    } catch (err) {
      console.error('Error saving allergies:', err)
      alert('Error saving allergies. Please try again.')
    } finally {
      setSavingAllergies(false)
    }
  }


  return (
    <div className="user-profile-page">
      {/* Navigation */}
      <nav className="navbar">
        <div className="nav-container">
          <div className="nav-logo">
            <div className="nav-logo-icon">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-5.5-2.5l7.51-3.49L17.5 6.5 9.99 9.99 6.5 17.5zm5.5-6.6c.61 0 1.1.49 1.1 1.1s-.49 1.1-1.1 1.1-1.1-.49-1.1-1.1.49-1.1 1.1-1.1z"/>
              </svg>
            </div>
            <a href="/" className="nav-logo-text">Smart Kitchen</a>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="user-profile-content">
        <div className="user-profile-container">
          {/* Back Button */}
          <a href="/" className="back-to-home-btn">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
            Back to Home
          </a>
          
          {/* Header */}
          <div className="user-profile-header">
            <div className="user-profile-avatar-section">
              <div className="user-profile-avatar">
                {user?.username ? user.username.charAt(0).toUpperCase() : 'U'}
              </div>
              <div className="user-profile-name-section">
                <h1 className="user-profile-title">{user?.username || 'User'}</h1>
                <p className="user-profile-subtitle">Manage your account settings and preferences</p>
              </div>
            </div>
          </div>

          {/* Dietary Restrictions & Allergies */}
          <div className="profile-card">
            <div className="profile-card-header">
              <h2 className="profile-card-title">Dietary Restrictions & Allergies</h2>
              <p className="profile-card-description">To help us recommend safe and suitable recipes for you.</p>
            </div>
            <div className="profile-card-body">
              <label className="profile-label">Add Allergies</label>
              <div className="allergies-input-wrapper">
                <div className="allergies-tags">
                  {allergies.map((allergy, index) => (
                    <div key={index} className="allergy-tag">
                      <span>{allergy}</span>
                      <button 
                        className="allergy-tag-remove"
                        onClick={() => handleRemoveAllergy(allergy)}
                        aria-label={`Remove ${allergy}`}
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <line x1="18" y1="6" x2="6" y2="18"></line>
                          <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                      </button>
                    </div>
                  ))}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1 }}>
                    <input
                      type="text"
                      className="allergy-input"
                      placeholder="Type an allergy and press Enter or click Add..."
                      value={allergyInput}
                      onChange={(e) => setAllergyInput(e.target.value)}
                      onKeyDown={handleAddAllergyKeyDown}
                      style={{ flex: 1 }}
                    />
                    <button
                      type="button"
                      onClick={handleAddAllergy}
                      style={{
                        padding: '6px 12px',
                        backgroundColor: '#16a34a',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '0.875rem',
                        fontWeight: '500'
                      }}
                      onMouseEnter={(e) => e.target.style.backgroundColor = '#15803d'}
                      onMouseLeave={(e) => e.target.style.backgroundColor = '#16a34a'}
                    >
                      Add
                    </button>
                  </div>
                </div>
              </div>
              <div className="profile-card-actions">
                <button 
                  className="btn-save" 
                  onClick={handleSaveAllergies}
                  disabled={savingAllergies || loadingAllergies}
                  style={{ opacity: (savingAllergies || loadingAllergies) ? 0.6 : 1 }}
                >
                  {savingAllergies ? 'Saving...' : 'Save Allergies'}
                </button>
              </div>
            </div>
          </div>


        </div>
      </div>
    </div>
  )
}

export default UserProfile

