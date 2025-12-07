import { useState } from 'react'
import UserMenu from './UserMenu'

function MealPlanner() {
  const [searchQuery, setSearchQuery] = useState('')
  const [inventoryUsage, setInventoryUsage] = useState('strict')
  const [mealPlan, setMealPlan] = useState(null)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [cuisine, setCuisine] = useState('')
  const [servings, setServings] = useState(4)
  const [dietaryPreferences, setDietaryPreferences] = useState('')

  const handleGenerate = async () => {
    setLoading(true)
    setError(null)
    setMealPlan(null)

    const token = localStorage.getItem('token')
    if (!token) {
      setError('You must be logged in to generate a meal plan')
      setLoading(false)
      return
    }

    try {
      console.log('Generating meal plan with:', { searchQuery, inventoryUsage })
      
      // Build preferences string
      let preferences = ''
      if (cuisine) preferences += `${cuisine} cuisine. `
      if (dietaryPreferences) preferences += `${dietaryPreferences}. `
      if (searchQuery) preferences += searchQuery
      
      const response = await fetch('http://localhost:8000/api/meal-plan/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          preferences: preferences.trim() || null,
          servings: servings || 4,
          cuisine: cuisine || null,
          inventory_usage: inventoryUsage
        })
      })

      console.log('Response status:', response.status)
      const data = await response.json()
      console.log('Response data:', data)

      if (response.ok) {
        setMealPlan(data.recipe || data)
        setError(null)
      } else {
        setError(data.detail || data.message || 'Failed to generate meal plan')
        setMealPlan(null)
      }
    } catch (err) {
      setError(err.message || 'Error connecting to server. Please try again.')
      setMealPlan(null)
      console.error('Error generating meal plan:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleVoiceInput = () => {
    // Placeholder for voice input
    console.log('Voice input activated')
    // TODO: Add voice recognition
  }

  return (
    <div className="meal-planner-page">
      {/* Navigation Bar */}
      <nav className="app-navbar">
        <div className="app-nav-container">
          <div className="app-nav-left">
            <a href="/" className="app-logo">
              <div className="app-logo-icon">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-5.5-2.5l7.51-3.49L17.5 6.5 9.99 9.99 6.5 17.5zm5.5-6.6c.61 0 1.1.49 1.1 1.1s-.49 1.1-1.1 1.1-1.1-.49-1.1-1.1.49-1.1 1.1-1.1z"/>
                </svg>
              </div>
              <span className="app-logo-text">Smart Kitchen</span>
            </a>
          </div>
          
          <div className="app-nav-center">
            <a href="#dashboard" className="app-nav-link">Dashboard</a>
            <a href="/meal-planner" className="app-nav-link active">Meal Planner</a>
            <a href="/inventory" className="app-nav-link">Inventory</a>
            <a href="/shopping-list" className="app-nav-link">Shopping List</a>
          </div>
          
          <div className="app-nav-right">
            <button className="notification-btn">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
              </svg>
            </button>
            <UserMenu />
          </div>

          {/* Mobile Hamburger Menu */}
          <button 
            className="mobile-menu-btn" 
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {mobileMenuOpen ? (
                <>
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </>
              ) : (
                <>
                  <line x1="3" y1="12" x2="21" y2="12"/>
                  <line x1="3" y1="6" x2="21" y2="6"/>
                  <line x1="3" y1="18" x2="21" y2="18"/>
                </>
              )}
            </svg>
          </button>
        </div>

        {/* Mobile Menu Dropdown */}
        {mobileMenuOpen && (
          <div className="mobile-menu">
            <a href="#dashboard" className="mobile-menu-link" onClick={() => setMobileMenuOpen(false)}>Dashboard</a>
            <a href="/meal-planner" className="mobile-menu-link active" onClick={() => setMobileMenuOpen(false)}>Meal Planner</a>
            <a href="/inventory" className="mobile-menu-link" onClick={() => setMobileMenuOpen(false)}>Inventory</a>
            <a href="/shopping-list" className="mobile-menu-link" onClick={() => setMobileMenuOpen(false)}>Shopping List</a>
          </div>
        )}
      </nav>

      {/* Main Content */}
      <main className="meal-planner-content">
        <div className="meal-planner-container">
          {/* Back Button */}
          <a href="/" className="back-to-home-btn">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
            Back to Home
          </a>

          {/* Header Section */}
          <div className="meal-planner-header">
            <h1 className="meal-planner-title">Generate Your Weekly Meal Plan</h1>
            <p className="meal-planner-subtitle">
              Tell us what you're in the mood for, and we'll create a delicious plan based on your kitchen's inventory.
            </p>
          </div>

          {/* Search and Options */}
          <div className="meal-planner-controls">
            <div className="search-container">
              <div className="search-input-wrapper">
                <svg className="search-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="11" cy="11" r="8"/>
                  <path d="m21 21-4.35-4.35"/>
                </svg>
                <input
                  type="text"
                  className="search-input"
                  placeholder="e.g., 'a week of healthy vegetarian meals' or 'something with chicken and broccoli'"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                <button className="voice-input-btn" onClick={handleVoiceInput}>
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                    <line x1="12" y1="19" x2="12" y2="22"/>
                  </svg>
                </button>
              </div>
            </div>

            <div className="controls-row" style={{ flexWrap: 'wrap', gap: '20px' }}>
              <div className="form-group" style={{ flex: '1', minWidth: '200px' }}>
                <label className="inventory-label">Cuisine Type</label>
                <select
                  value={cuisine}
                  onChange={(e) => setCuisine(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    borderRadius: '8px',
                    border: '1px solid #e5e7eb',
                    fontSize: '0.95rem',
                    backgroundColor: 'white'
                  }}
                >
                  <option value="">Any Cuisine</option>
                  <option value="Italian">Italian</option>
                  <option value="Mexican">Mexican</option>
                  <option value="Chinese">Chinese</option>
                  <option value="Indian">Indian</option>
                  <option value="Thai">Thai</option>
                  <option value="Japanese">Japanese</option>
                  <option value="Mediterranean">Mediterranean</option>
                  <option value="American">American</option>
                  <option value="French">French</option>
                  <option value="Greek">Greek</option>
                </select>
              </div>

              <div className="form-group" style={{ flex: '1', minWidth: '150px' }}>
                <label className="inventory-label">Number of Servings</label>
                <input
                  type="number"
                  min="1"
                  max="20"
                  value={servings}
                  onChange={(e) => setServings(parseInt(e.target.value) || 4)}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    borderRadius: '8px',
                    border: '1px solid #e5e7eb',
                    fontSize: '0.95rem'
                  }}
                />
              </div>

              <div className="form-group" style={{ flex: '1', minWidth: '200px' }}>
                <label className="inventory-label">Dietary Preferences</label>
                <input
                  type="text"
                  placeholder="e.g., vegetarian, vegan, gluten-free"
                  value={dietaryPreferences}
                  onChange={(e) => setDietaryPreferences(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    borderRadius: '8px',
                    border: '1px solid #e5e7eb',
                    fontSize: '0.95rem'
                  }}
                />
              </div>
            </div>

            <div className="controls-row" style={{ marginTop: '20px' }}>
              <div className="inventory-usage">
                <label className="inventory-label">Inventory Usage</label>
                <div className="radio-group">
                  <label className="radio-option">
                    <input
                      type="radio"
                      name="inventoryUsage"
                      value="strict"
                      checked={inventoryUsage === 'strict'}
                      onChange={(e) => setInventoryUsage(e.target.value)}
                    />
                    <span className="radio-text">Strictly follow inventory</span>
                  </label>
                  <label className="radio-option">
                    <input
                      type="radio"
                      name="inventoryUsage"
                      value="main"
                      checked={inventoryUsage === 'main'}
                      onChange={(e) => setInventoryUsage(e.target.value)}
                    />
                    <span className="radio-text">Main items from inventory</span>
                  </label>
                </div>
              </div>

              <button 
                className="generate-btn" 
                onClick={handleGenerate}
                disabled={loading}
                style={{
                  opacity: loading ? 0.7 : 1,
                  cursor: loading ? 'not-allowed' : 'pointer'
                }}
              >
                {loading ? (
                  <>
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation: 'spin 1s linear infinite' }}>
                      <circle cx="12" cy="12" r="10" strokeDasharray="32" strokeDashoffset="32">
                        <animate attributeName="stroke-dasharray" dur="2s" values="0 32;16 16;0 32;0 32" repeatCount="indefinite"/>
                        <animate attributeName="stroke-dashoffset" dur="2s" values="0;-16;-32;-32" repeatCount="indefinite"/>
                      </circle>
                    </svg>
                    Generating...
                  </>
                ) : (
                  <>
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                      <polyline points="7.5 4.21 12 6.81 16.5 4.21"/>
                      <polyline points="7.5 19.79 7.5 14.6 3 12"/>
                      <polyline points="21 12 16.5 14.6 16.5 19.79"/>
                      <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
                      <line x1="12" y1="22.08" x2="12" y2="12"/>
                    </svg>
                    Generate Plan
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div style={{
              padding: '16px',
              marginBottom: '16px',
              backgroundColor: '#fee',
              color: '#c33',
              borderRadius: '8px',
              border: '1px solid #fcc'
            }}>
              {error}
            </div>
          )}

          {/* Meal Plan Display Area */}
          <div className="meal-plan-result">
            {!mealPlan ? (
              <div className="meal-plan-placeholder">
                <svg className="placeholder-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2"/>
                  <path d="M7 2v20"/>
                  <path d="M21 15V2v0a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3Zm0 0v7"/>
                </svg>
                <p className="placeholder-text">Your generated meal plan will appear here.</p>
              </div>
            ) : (
              <div className="meal-plan-content" style={{
                padding: '32px',
                textAlign: 'left'
              }}>
                <h2 style={{
                  fontSize: '1.8rem',
                  fontWeight: '700',
                  color: '#1a1a1a',
                  marginBottom: '12px'
                }}>
                  {mealPlan.name || 'Meal Plan'}
                </h2>
                
                {mealPlan.description && (
                  <p style={{
                    fontSize: '1.1rem',
                    color: '#4b5563',
                    marginBottom: '24px',
                    lineHeight: '1.6'
                  }}>
                    {mealPlan.description}
                  </p>
                )}

                {mealPlan.servings && (
                  <p style={{
                    fontSize: '0.95rem',
                    color: '#6b7280',
                    marginBottom: '24px'
                  }}>
                    Serves: {mealPlan.servings} people
                  </p>
                )}

                {mealPlan.ingredients && mealPlan.ingredients.length > 0 && (
                  <div style={{ marginBottom: '32px' }}>
                    <h3 style={{
                      fontSize: '1.3rem',
                      fontWeight: '600',
                      color: '#1a1a1a',
                      marginBottom: '16px'
                    }}>
                      Ingredients:
                    </h3>
                    <ul style={{
                      listStyle: 'none',
                      padding: 0,
                      margin: 0
                    }}>
                      {mealPlan.ingredients.map((ingredient, index) => (
                        <li key={index} style={{
                          padding: '12px 16px',
                          marginBottom: '8px',
                          backgroundColor: '#f9fafb',
                          borderRadius: '8px',
                          border: '1px solid #e5e7eb',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center'
                        }}>
                          <span style={{ fontWeight: '500', color: '#1a1a1a' }}>
                            {ingredient.name}
                          </span>
                          <span style={{ color: '#6b7280', fontSize: '0.9rem' }}>
                            {ingredient.quantity} {ingredient.unit || 'units'}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {mealPlan.instructions && mealPlan.instructions.length > 0 && (
                  <div>
                    <h3 style={{
                      fontSize: '1.3rem',
                      fontWeight: '600',
                      color: '#1a1a1a',
                      marginBottom: '16px'
                    }}>
                      Instructions:
                    </h3>
                    <ol style={{
                      paddingLeft: '20px',
                      margin: 0
                    }}>
                      {mealPlan.instructions.map((instruction, index) => (
                        <li key={index} style={{
                          padding: '12px 0',
                          color: '#4b5563',
                          lineHeight: '1.6',
                          fontSize: '1rem'
                        }}>
                          {instruction}
                        </li>
                      ))}
                    </ol>
                  </div>
                )}

                {(!mealPlan.ingredients || mealPlan.ingredients.length === 0) && 
                 (!mealPlan.instructions || mealPlan.instructions.length === 0) && (
                  <p style={{ color: '#6b7280', fontStyle: 'italic' }}>
                    No detailed recipe information available. Please add items to your inventory for better meal suggestions.
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <div className="app-footer-container">
          <p className="app-footer-copyright">© 2024 Smart Kitchen. All rights reserved.</p>
          <div className="app-footer-links">
            <a href="#">Privacy</a>
            <a href="#">Terms</a>
            <a href="#">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default MealPlanner

