import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

function UserProfile() {
  const { user } = useAuth()
  
  // Allergies state
  const [allergies, setAllergies] = useState(['Peanuts', 'Shellfish'])
  const [allergyInput, setAllergyInput] = useState('')
  
  // Dietary goals state
  const [dietaryGoals, setDietaryGoals] = useState(['Vegetarian', 'Vegan'])
  const availableDiets = ['Vegetarian', 'Vegan', 'Low-Carb', 'Gluten-Free', 'Keto']
  
  // Notification preferences state
  const [notifications, setNotifications] = useState({
    inventoryExpiry: true,
    mealPlanReminders: true,
    shoppingListUpdates: false,
    specialOffers: false
  })

  // Allergy handlers
  const handleAddAllergy = (e) => {
    if (e.key === 'Enter' && allergyInput.trim()) {
      if (!allergies.includes(allergyInput.trim())) {
        setAllergies([...allergies, allergyInput.trim()])
      }
      setAllergyInput('')
    }
  }

  const handleRemoveAllergy = (allergyToRemove) => {
    setAllergies(allergies.filter(allergy => allergy !== allergyToRemove))
  }

  // Dietary goals handlers
  const toggleDietaryGoal = (goal) => {
    if (dietaryGoals.includes(goal)) {
      setDietaryGoals(dietaryGoals.filter(g => g !== goal))
    } else {
      setDietaryGoals([...dietaryGoals, goal])
    }
  }

  // Notification handlers
  const toggleNotification = (key) => {
    setNotifications({
      ...notifications,
      [key]: !notifications[key]
    })
  }

  // Save handlers
  const handleSaveAllergies = () => {
    // TODO: Implement API call
    console.log('Saving allergies:', allergies)
    alert('Allergies saved successfully!')
  }

  const handleSaveGoals = () => {
    // TODO: Implement API call
    console.log('Saving dietary goals:', dietaryGoals)
    alert('Dietary goals saved successfully!')
  }

  const handleSaveNotifications = () => {
    // TODO: Implement API call
    console.log('Saving notifications:', notifications)
    alert('Notification preferences saved successfully!')
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
                  <input
                    type="text"
                    className="allergy-input"
                    placeholder="Type an allergy..."
                    value={allergyInput}
                    onChange={(e) => setAllergyInput(e.target.value)}
                    onKeyDown={handleAddAllergy}
                  />
                </div>
              </div>
              <div className="profile-card-actions">
                <button className="btn-save" onClick={handleSaveAllergies}>
                  Save Allergies
                </button>
              </div>
            </div>
          </div>

          {/* Dietary Goals */}
          <div className="profile-card">
            <div className="profile-card-header">
              <h2 className="profile-card-title">Dietary Goals</h2>
              <p className="profile-card-description">Select your dietary goals to personalize your meal plans.</p>
            </div>
            <div className="profile-card-body">
              <div className="dietary-goals-grid">
                {availableDiets.map((diet, index) => (
                  <button
                    key={index}
                    className={`dietary-goal-pill ${dietaryGoals.includes(diet) ? 'active' : ''}`}
                    onClick={() => toggleDietaryGoal(diet)}
                  >
                    {diet}
                  </button>
                ))}
              </div>
              <div className="profile-card-actions">
                <button className="btn-save" onClick={handleSaveGoals}>
                  Save Goals
                </button>
              </div>
            </div>
          </div>

          {/* Notification Preferences */}
          <div className="profile-card">
            <div className="profile-card-header">
              <h2 className="profile-card-title">Notification Preferences</h2>
              <p className="profile-card-description">Choose what you want to be notified about.</p>
            </div>
            <div className="profile-card-body">
              <div className="notification-options">
                <div className="notification-item">
                  <span className="notification-label">Inventory Expiry Alerts</span>
                  <button 
                    className={`notification-toggle ${notifications.inventoryExpiry ? 'active' : ''}`}
                    onClick={() => toggleNotification('inventoryExpiry')}
                    aria-label="Toggle inventory expiry alerts"
                  >
                    {notifications.inventoryExpiry ? (
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12"></polyline>
                      </svg>
                    ) : null}
                  </button>
                </div>
                
                <div className="notification-item">
                  <span className="notification-label">Meal Plan Reminders</span>
                  <button 
                    className={`notification-toggle ${notifications.mealPlanReminders ? 'active' : ''}`}
                    onClick={() => toggleNotification('mealPlanReminders')}
                    aria-label="Toggle meal plan reminders"
                  >
                    {notifications.mealPlanReminders ? (
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12"></polyline>
                      </svg>
                    ) : null}
                  </button>
                </div>
                
                <div className="notification-item">
                  <span className="notification-label">Shopping List Updates</span>
                  <button 
                    className={`notification-toggle ${notifications.shoppingListUpdates ? 'active' : ''}`}
                    onClick={() => toggleNotification('shoppingListUpdates')}
                    aria-label="Toggle shopping list updates"
                  >
                    {notifications.shoppingListUpdates ? (
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12"></polyline>
                      </svg>
                    ) : null}
                  </button>
                </div>
                
                <div className="notification-item">
                  <span className="notification-label">Special Offers</span>
                  <button 
                    className={`notification-toggle ${notifications.specialOffers ? 'active' : ''}`}
                    onClick={() => toggleNotification('specialOffers')}
                    aria-label="Toggle special offers"
                  >
                    {notifications.specialOffers ? (
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12"></polyline>
                      </svg>
                    ) : null}
                  </button>
                </div>
              </div>
              <div className="profile-card-actions">
                <button className="btn-save" onClick={handleSaveNotifications}>
                  Save Notifications
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

