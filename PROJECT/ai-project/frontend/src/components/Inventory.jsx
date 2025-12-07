import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import UserMenu from './UserMenu'
import './Inventory.css'

function Inventory() {
  const [showAddForm, setShowAddForm] = useState(false)
  const [formData, setFormData] = useState({
    item_name: '',
    quantity: '',
    unit: 'units'
  })
  const [inventory, setInventory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const { user } = useAuth()

  // Fetch inventory items on component mount
  useEffect(() => {
    fetchInventoryItems()
  }, [])

  const fetchInventoryItems = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      if (!token) {
        setError('You must be logged in')
        setLoading(false)
        return
      }

      console.log('Fetching inventory items...')
      const response = await fetch('http://localhost:8000/api/inventory', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      console.log('Fetch response status:', response.status)
      
      if (response.ok) {
        const data = await response.json()
        console.log('Fetched data:', data)
        // Handle both response formats: {inventory: [...]} or [...]
        const items = data.inventory || data || []
        console.log('Inventory items:', items)
        setInventory(items)
        setError(null)
      } else {
        const errorData = await response.json().catch(() => ({}))
        setError(errorData.detail || 'Failed to fetch inventory items')
        console.error('Fetch error:', errorData)
      }
    } catch (err) {
      setError('Error connecting to server: ' + err.message)
      console.error('Error fetching inventory:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = async (e) => {
    e.preventDefault()
    if (!formData.item_name || !formData.quantity) {
      setError('Please fill in all required fields')
      return
    }

    try {
      const token = localStorage.getItem('token')
      if (!token) {
        setError('You must be logged in to add items')
        return
      }

      const requestBody = {
        item_name: formData.item_name,
        quantity: parseFloat(formData.quantity),
        unit: formData.unit
      }

      console.log('Adding item:', requestBody)
      console.log('Token exists:', !!token)

      const response = await fetch('http://localhost:8000/api/inventory/add', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(requestBody)
      })
      
      console.log('Response status:', response.status)
      const responseData = await response.json()
      console.log('Response data:', responseData)
      
      if (response.ok) {
        setFormData({ item_name: '', quantity: '', unit: 'units' })
        setShowAddForm(false)
        setError(null)
        // Refresh inventory list with a small delay to ensure DB is updated
        setTimeout(() => {
          fetchInventoryItems()
        }, 100)
      } else {
        const errorMsg = responseData.detail || responseData.message || 'Failed to add item'
        setError(errorMsg)
        console.error('Error response:', responseData)
      }
    } catch (err) {
      const errorMsg = err.message || 'Error adding item to inventory'
      setError(errorMsg)
      console.error('Error adding item:', err)
    }
  }

  const handleRemove = async (itemName, quantity = null) => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('http://localhost:8000/api/inventory/remove', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          item_name: itemName,
          quantity: quantity
        })
      })
      
      if (response.ok) {
        setError(null)
        // Refresh inventory list
        fetchInventoryItems()
      } else {
        const errorData = await response.json()
        setError(errorData.detail || 'Failed to remove item')
      }
    } catch (err) {
      setError('Error removing item')
      console.error('Error removing item:', err)
    }
  }

  return (
    <div className="inventory-page">
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
            <a href="#meal-planner" className="app-nav-link">Meal Planner</a>
            <a href="#inventory" className="app-nav-link active">Inventory</a>
            <a href="#shopping-list" className="app-nav-link">Shopping List</a>
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
            <a href="#meal-planner" className="mobile-menu-link" onClick={() => setMobileMenuOpen(false)}>Meal Planner</a>
            <a href="#inventory" className="mobile-menu-link active" onClick={() => setMobileMenuOpen(false)}>Inventory</a>
            <a href="#shopping-list" className="mobile-menu-link" onClick={() => setMobileMenuOpen(false)}>Shopping List</a>
          </div>
        )}
      </nav>

      {/* Main Content */}
      <main className="inventory-content">
        <div className="inventory-container">
          {/* Back Button */}
          <a href="#home" className="back-to-home-btn">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
            Back to Home
          </a>

          {/* Inventory List Component (from AI Project) */}
          <div className="inventory-list">
            <div className="inventory-header-section">
              <h2>📦 Inventory</h2>
              <button 
                className="add-button"
                onClick={() => setShowAddForm(!showAddForm)}
              >
                {showAddForm ? 'Cancel' : '+ Add Item'}
              </button>
            </div>

            {/* Error Message */}
            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            {/* Add Form */}
            {showAddForm && (
              <form onSubmit={handleAdd} className="add-form">
                <input
                  type="text"
                  placeholder="Item name"
                  value={formData.item_name}
                  onChange={(e) => setFormData({ ...formData, item_name: e.target.value })}
                  required
                />
                <input
                  type="number"
                  step="0.1"
                  placeholder="Quantity"
                  value={formData.quantity}
                  onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                  required
                />
                <select
                  value={formData.unit}
                  onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
                >
                  <option value="units">units</option>
                  <option value="cups">cups</option>
                  <option value="grams">grams</option>
                  <option value="kilograms">kilograms</option>
                  <option value="liters">liters</option>
                  <option value="pieces">pieces</option>
                  <option value="tablespoons">tablespoons</option>
                  <option value="bottles">bottles</option>
                  <option value="cloves">cloves</option>
                  <option value="head">head</option>
                  <option value="loaf">loaf</option>
                </select>
                <button type="submit">Add</button>
              </form>
            )}

            {/* Loading State */}
            {loading ? (
              <div className="empty-state">
                <p>Loading inventory...</p>
              </div>
            ) : inventory.length === 0 ? (
              <div className="empty-state">
                <p>Your inventory is empty. Add some items to get started!</p>
              </div>
            ) : (
              <div className="inventory-grid">
                {inventory.map((item) => (
                  <div key={item.id} className="inventory-item">
                    <div className="item-info">
                      <h3>{item.name}</h3>
                      <p className="quantity">
                        {item.quantity} {item.unit || 'units'}
                      </p>
                    </div>
                    <div className="item-actions">
                      <button
                        className="remove-button"
                        onClick={() => handleRemove(item.name)}
                        title="Remove all"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                ))}
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

export default Inventory
