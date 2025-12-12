import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext'
import UserMenu from './UserMenu'
import './Inventory.css'

function Inventory() {
  const [showAddModal, setShowAddModal] = useState(false)
  const [quickAddText, setQuickAddText] = useState('')
  const [formData, setFormData] = useState({
    item_name: '',
    quantity: '',
    unit: 'units'
  })
  const [inventory, setInventory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [activeMenuId, setActiveMenuId] = useState(null)
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' })
  const [filterText, setFilterText] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [voiceError, setVoiceError] = useState(null)
  const [pendingFormData, setPendingFormData] = useState(null)
  const [editingItem, setEditingItem] = useState(null) // Track if we're editing an item
  const { user } = useAuth()
  const menuRef = useRef(null)
  const recognitionRef = useRef(null)
  const menuOpenTimeRef = useRef(0)

  // Fetch inventory items on component mount
  useEffect(() => {
    fetchInventoryItems()
  }, [])

  // Open modal when pendingFormData is set
  useEffect(() => {
    if (pendingFormData) {
      console.log('Applying pending form data and opening modal:', pendingFormData)
      setFormData(pendingFormData)
      setShowAddModal(true)
      setPendingFormData(null) // Clear pending data
    }
  }, [pendingFormData])

  // Debug: Log activeMenuId changes
  useEffect(() => {
    console.log('Active menu ID changed to:', activeMenuId)
  }, [activeMenuId])

  // Close menu when clicking outside - use 'click' instead of 'mousedown'
  useEffect(() => {
    const handleClickOutside = (event) => {
      // Check if enough time has passed since menu opened (prevent immediate close)
      const timeSinceOpen = Date.now() - menuOpenTimeRef.current
      if (timeSinceOpen < 200) {
        console.log('Menu just opened, ignoring click')
        return
      }
      
      // Check if click is on the action menu container or its children
      const isActionMenu = event.target.closest('.action-menu')
      
      if (!isActionMenu && activeMenuId !== null) {
        console.log('Clicking outside action menu, closing')
        setActiveMenuId(null)
      }
    }

    // Use 'click' event instead of 'mousedown' to let button clicks fire first
    document.addEventListener('click', handleClickOutside, true)
    return () => document.removeEventListener('click', handleClickOutside, true)
  }, [activeMenuId])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort()
        } catch (err) {
          console.log('Cleanup error:', err)
        }
      }
    }
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

      // Determine if we're adding or updating
      const isEditing = editingItem !== null
      const endpoint = isEditing 
        ? 'http://localhost:8000/api/inventory/update' 
        : 'http://localhost:8000/api/inventory/add'
      const method = isEditing ? 'PUT' : 'POST'

      console.log(isEditing ? 'Updating item:' : 'Adding item:', requestBody)
      console.log('Token exists:', !!token)

      const response = await fetch(endpoint, {
        method: method,
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
        setShowAddModal(false)
        setEditingItem(null) // Clear edit mode
        setError(null)
        // Refresh inventory list with a small delay to ensure DB is updated
        setTimeout(() => {
          fetchInventoryItems()
        }, 100)
      } else {
        const errorMsg = responseData.detail || responseData.message || (isEditing ? 'Failed to update item' : 'Failed to add item')
        setError(errorMsg)
        console.error('Error response:', responseData)
      }
    } catch (err) {
      const errorMsg = err.message || (editingItem ? 'Error updating item' : 'Error adding item to inventory')
      setError(errorMsg)
      console.error('Error:', err)
    }
  }

  const handleRemove = async (itemName, quantity = null) => {
    // Confirmation for full delete
    if (quantity === null) {
      const confirmed = window.confirm(`Are you sure you want to delete "${itemName}" from your inventory?`)
      if (!confirmed) {
        setActiveMenuId(null)
        return
      }
    }

    try {
      console.log('Removing item:', itemName, 'quantity:', quantity)
      const token = localStorage.getItem('token')
      
      if (!token) {
        setError('You must be logged in')
        return
      }
      
      const requestBody = {
        item_name: itemName,
        quantity: quantity
      }
      
      console.log('Remove request body:', requestBody)
      
      const response = await fetch('http://localhost:8000/api/inventory/remove', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(requestBody)
      })
      
      console.log('Remove response status:', response.status)
      
      if (response.ok) {
        const responseData = await response.json()
        console.log('Remove response:', responseData)
        setError(null)
        setActiveMenuId(null)
        // Refresh inventory list
        setTimeout(() => {
          fetchInventoryItems()
        }, 100)
      } else {
        const errorData = await response.json()
        console.error('Remove error:', errorData)
        setError(errorData.detail || 'Failed to remove item')
      }
    } catch (err) {
      setError('Error removing item: ' + err.message)
      console.error('Error removing item:', err)
    }
  }

  // Format time ago
  const formatTimeAgo = (dateString) => {
    if (!dateString) return 'Just now'
    
    const date = new Date(dateString)
    const now = new Date()
    const diffInMs = now - date
    const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24))
    
    if (diffInDays === 0) return 'Today'
    if (diffInDays === 1) return '1 day ago'
    if (diffInDays < 7) return `${diffInDays} days ago`
    if (diffInDays < 30) return `${Math.floor(diffInDays / 7)} weeks ago`
    return `${Math.floor(diffInDays / 30)} months ago`
  }

  // Sort inventory
  const handleSort = (key) => {
    let direction = 'asc'
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc'
    }
    setSortConfig({ key, direction })
  }

  // Get sorted and filtered inventory
  const getSortedAndFilteredInventory = () => {
    let filtered = [...inventory]
    
    // Apply filter
    if (filterText) {
      filtered = filtered.filter(item => 
        item.name?.toLowerCase().includes(filterText.toLowerCase())
      )
    }
    
    // Apply sort
    if (sortConfig.key) {
      filtered.sort((a, b) => {
        let aValue = a[sortConfig.key]
        let bValue = b[sortConfig.key]
        
        if (sortConfig.key === 'name') {
          aValue = aValue?.toLowerCase() || ''
          bValue = bValue?.toLowerCase() || ''
        }
        
        if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1
        if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1
        return 0
      })
    }
    
    return filtered
  }

  // Map AI-returned units to dropdown values
  const mapUnitToDropdown = (aiUnit) => {
    const unitMapping = {
      // Weight units
      'kg': 'kilograms',
      'g': 'grams',
      'mg': 'grams', // fallback to grams for mg
      'lb': 'kilograms', // fallback to kg for pounds
      'oz': 'grams', // fallback to grams for ounces
      
      // Volume units
      'l': 'liters',
      'ml': 'liters', // fallback to liters for ml
      
      // Count units
      'tbsp': 'tablespoons',
      'tsp': 'tablespoons', // fallback to tablespoons for teaspoons
      'cup': 'cups',
      'cups': 'cups',
      'pieces': 'pieces',
      'piece': 'pieces',
      'pcs': 'pieces',
      
      // Container units
      'can': 'units',
      'cans': 'units',
      'bottle': 'bottles',
      'bottles': 'bottles',
      'bag': 'units',
      'bags': 'units',
      'box': 'units',
      'boxes': 'units',
      'pack': 'units',
      'packs': 'units',
      
      // Already matching units
      'units': 'units',
      'pint': 'pint',
      'gallon': 'gallon',
      'loaf': 'loaf',
      'remaining': 'remaining',
      'grams': 'grams',
      'kilograms': 'kilograms',
      'liters': 'liters',
      'tablespoons': 'tablespoons',
      'cloves': 'cloves',
      'head': 'head'
    }
    
    // Return mapped unit or default to 'units' if not found
    return unitMapping[aiUnit.toLowerCase()] || 'units'
  }

  // Parse ingredient text using AI API
  const parseAndOpenModal = async (text) => {
    if (!text.trim()) return
    
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        setError('You must be logged in')
        return
      }

      // Show loading state
      setLoading(true)
      
      const response = await fetch('http://localhost:8000/api/inventory/parse', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ text })
      })

      if (response.ok) {
        const parsed = await response.json()
        console.log('AI parsed result:', parsed)
        
        // Map the unit to match dropdown values
        const mappedUnit = mapUnitToDropdown(parsed.unit)
        console.log(`Unit mapping: ${parsed.unit} -> ${mappedUnit}`)
        
        const newFormData = {
          item_name: parsed.item_name,
          quantity: parsed.quantity,
          unit: mappedUnit
        }
        
        console.log('Setting pending form data:', newFormData)
        
        // Set pending data - useEffect will handle opening modal
        setPendingFormData(newFormData)
        setQuickAddText('')
      } else {
        const errorData = await response.json()
        setError(errorData.detail || 'Failed to parse ingredient')
        console.error('Parse error:', errorData)
      }
    } catch (err) {
      setError('Error parsing ingredient: ' + err.message)
      console.error('Error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleQuickAdd = (e) => {
    e.preventDefault()
    if (!quickAddText.trim()) return
    
    parseAndOpenModal(quickAddText)
  }

  // Voice input handler
  const handleVoiceInput = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    
    if (!SpeechRecognition) {
      setVoiceError('Voice input is not supported in your browser. Please use Chrome, Edge, or Safari.')
      setTimeout(() => setVoiceError(null), 5000)
      return
    }

    // If already listening, stop
    if (isListening && recognitionRef.current) {
      try {
        recognitionRef.current.stop()
      } catch (err) {
        console.log('Stop error:', err)
      }
      setIsListening(false)
      recognitionRef.current = null
      return
    }

    try {
      // Create a fresh recognition instance each time
      const recognition = new SpeechRecognition()
      recognition.continuous = false
      recognition.interimResults = false
      recognition.lang = 'en-US'

      recognition.onresult = (event) => {
        let finalTranscript = ''

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript
          if (event.results[i].isFinal) {
            finalTranscript += transcript + ' '
          }
        }

        if (finalTranscript) {
          const text = finalTranscript.trim()
          console.log('Voice recognized:', text)
          setQuickAddText(text)
          // Auto-parse and open modal after a short delay
          setTimeout(() => {
            parseAndOpenModal(text)
          }, 800)
        }
      }

      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error)
        setIsListening(false)
        recognitionRef.current = null
        
        // Don't show error for manual abort
        if (event.error === 'aborted') {
          return
        }
        
        let errorMessage = 'Voice input error. Please try again.'
        switch (event.error) {
          case 'no-speech':
            errorMessage = 'No speech detected. Please try speaking.'
            break
          case 'audio-capture':
            errorMessage = 'Microphone not found. Please check your device.'
            break
          case 'not-allowed':
            errorMessage = 'Microphone access denied. Please enable permissions in your browser.'
            break
          case 'network':
            errorMessage = 'Network error occurred.'
            break
          default:
            errorMessage = `Voice error: ${event.error}`
        }
        
        setVoiceError(errorMessage)
        setTimeout(() => setVoiceError(null), 5000)
      }

      recognition.onend = () => {
        setIsListening(false)
        recognitionRef.current = null
      }

      recognition.onstart = () => {
        setIsListening(true)
        setVoiceError(null)
      }

      recognitionRef.current = recognition
      recognition.start()
      
    } catch (err) {
      console.error('Error starting voice recognition:', err)
      setVoiceError('Failed to start voice input. Please try again.')
      setTimeout(() => setVoiceError(null), 5000)
      setIsListening(false)
      recognitionRef.current = null
    }
  }

  // Handle edit item
  const handleEdit = (item) => {
    console.log('Editing item:', item)
    setEditingItem(item.name) // Store the original name for updating
    setFormData({
      item_name: item.name,
      quantity: item.quantity.toString(),
      unit: item.unit || 'units'
    })
    setShowAddModal(true)
    setActiveMenuId(null)
  }

  const sortedAndFilteredInventory = getSortedAndFilteredInventory()

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
      <main className="main-content">
        <div className="content-wrapper">
          {/* Back Button */}
          <a href="/" className="back-to-home-btn">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
            Back to Home
          </a>

          {/* Page Header */}
          <div className="page-header">
            <div className="header-text">
              <h1>Your Kitchen Inventory</h1>
              <p>Keep track of what you have, reduce waste, and plan meals easily. 
                <span style={{ 
                  display: 'inline-block', 
                  marginLeft: '8px',
                  padding: '4px 12px', 
                  backgroundColor: '#f0fdf4', 
                  color: '#166534', 
                  borderRadius: '6px', 
                  fontSize: '0.85rem', 
                  fontWeight: '500' 
                }}>
                  🎤 Try voice input!
                </span>
              </p>
            </div>
            <button className="add-item-btn" onClick={() => {
              setEditingItem(null) // Clear edit mode
              setFormData({ item_name: '', quantity: '', unit: 'units' })
              setShowAddModal(true)
            }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="12" y1="5" x2="12" y2="19"/>
                <line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              Add Item
            </button>
          </div>

          {/* Quick Add Search Bar */}
          <form onSubmit={handleQuickAdd} className="quick-add-bar">
            <input
              type="text"
              placeholder={isListening ? "🎤 Listening... Speak now!" : "Type or speak to add, e.g., '2 kg tomatoes' or '5 avocados'"}
              value={quickAddText}
              onChange={(e) => setQuickAddText(e.target.value)}
            />
            <button 
              type="button" 
              className={`mic-btn ${isListening ? 'listening' : ''}`}
              onClick={handleVoiceInput}
              title={isListening ? "Stop recording" : "Start voice input"}
              style={isListening ? {
                background: '#16a34a',
                animation: 'pulse 1.5s ease-in-out infinite'
              } : {}}
              aria-label="Voice input"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                {isListening ? (
                  <rect x="6" y="6" width="12" height="12" rx="2"/>
                ) : (
                  <>
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                    <line x1="12" y1="19" x2="12" y2="23"/>
                    <line x1="8" y1="23" x2="16" y2="23"/>
                  </>
                )}
              </svg>
            </button>
          </form>

          {/* Voice Error Message */}
          {voiceError && (
            <div style={{
              margin: '12px 0',
              padding: '12px 16px',
              backgroundColor: '#fef2f2',
              border: '1px solid #fecaca',
              borderRadius: '8px',
              color: '#991b1b',
              fontSize: '0.9rem',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              {voiceError}
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="alert-error">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12" stroke="white" strokeWidth="2"/>
                <line x1="12" y1="16" x2="12.01" y2="16" stroke="white" strokeWidth="2"/>
              </svg>
              {error}
            </div>
          )}

          {/* Inventory Section */}
          <div className="inventory-section">
            <div className="section-header">
              <h2>Current Stock ({sortedAndFilteredInventory.length} items)</h2>
              <div className="header-actions">
                <button className="icon-btn" onClick={() => handleSort('name')} aria-label="Sort">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="3" y1="6" x2="21" y2="6"/>
                    <line x1="3" y1="12" x2="21" y2="12"/>
                    <line x1="3" y1="18" x2="15" y2="18"/>
                  </svg>
                </button>
                <button className="icon-btn" aria-label="Filter">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
                  </svg>
                </button>
              </div>
            </div>

            {/* Loading State */}
            {loading ? (
              <div className="empty-message">
                <p>Loading inventory...</p>
              </div>
            ) : sortedAndFilteredInventory.length === 0 ? (
              <div className="empty-message">
                <p>Your inventory is empty. Add some items to get started!</p>
              </div>
            ) : (
              <>
                {/* Desktop Table View */}
                <div className="table-container">
                  <table className="inventory-table">
                    <thead>
                      <tr>
                        <th onClick={() => handleSort('name')} className="sortable">ITEM NAME</th>
                        <th onClick={() => handleSort('quantity')} className="sortable">QUANTITY</th>
                        <th>STOCKED</th>
                        <th>ACTIONS</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sortedAndFilteredInventory.map((item) => (
                        <tr key={item.id}>
                          <td className="item-name">{item.name}</td>
                          <td className="item-quantity">
                            {item.quantity} {item.unit || 'units'}
                          </td>
                          <td className="item-stocked">
                            {formatTimeAgo(item.created_at || item.updated_at)}
                          </td>
                          <td className="item-actions">
                            <div className="action-menu">
                              <button 
                                className="menu-trigger"
                                onClick={() => {
                                  console.log('Menu button clicked for item:', item.id)
                                  const newMenuId = activeMenuId === item.id ? null : item.id
                                  if (newMenuId !== null) {
                                    menuOpenTimeRef.current = Date.now()
                                    console.log('Opening menu at:', menuOpenTimeRef.current)
                                  }
                                  setActiveMenuId(newMenuId)
                                }}
                                aria-label="Actions"
                              >
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                                  <circle cx="12" cy="5" r="2"/>
                                  <circle cx="12" cy="12" r="2"/>
                                  <circle cx="12" cy="19" r="2"/>
                                </svg>
                              </button>
                              {activeMenuId === item.id && (
                                <div className="dropdown-menu" ref={menuRef} onClick={(e) => e.stopPropagation()}>
                                  <button onClick={() => {
                                    console.log('Edit clicked for:', item.name)
                                    handleEdit(item)
                                  }}>Edit</button>
                                  <button onClick={() => {
                                    console.log('Delete clicked for:', item.name)
                                    handleRemove(item.name, null)
                                  }} className="delete-action">
                                    Delete
                                  </button>
                                </div>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Mobile Card View */}
                <div className="mobile-cards">
                  {sortedAndFilteredInventory.map((item) => (
                    <div key={item.id} className="item-card">
                      <div className="card-header">
                        <h3>{item.name}</h3>
                        <div className="action-menu">
                          <button 
                            className="menu-trigger"
                            onClick={() => {
                              console.log('Mobile menu button clicked for item:', item.id)
                              const newMenuId = activeMenuId === item.id ? null : item.id
                              if (newMenuId !== null) {
                                menuOpenTimeRef.current = Date.now()
                                console.log('Opening mobile menu at:', menuOpenTimeRef.current)
                              }
                              setActiveMenuId(newMenuId)
                            }}
                            aria-label="Actions"
                          >
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                              <circle cx="12" cy="5" r="2"/>
                              <circle cx="12" cy="12" r="2"/>
                              <circle cx="12" cy="19" r="2"/>
                            </svg>
                          </button>
                          {activeMenuId === item.id && (
                            <div className="dropdown-menu" ref={menuRef} onClick={(e) => e.stopPropagation()}>
                              <button onClick={() => {
                                console.log('Mobile Edit clicked for:', item.name)
                                handleEdit(item)
                              }}>Edit</button>
                              <button onClick={() => {
                                console.log('Mobile Delete clicked for:', item.name)
                                handleRemove(item.name, null)
                              }} className="delete-action">
                                Delete
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="card-details">
                        <div className="detail-row">
                          <span className="detail-label">Quantity:</span>
                          <span className="detail-value">{item.quantity} {item.unit || 'units'}</span>
                        </div>
                        <div className="detail-row">
                          <span className="detail-label">Stocked:</span>
                          <span className="detail-value">{formatTimeAgo(item.created_at || item.updated_at)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      </main>

      {/* Add/Edit Modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => {
          setShowAddModal(false)
          setEditingItem(null)
          setPendingFormData(null)
        }}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingItem ? 'Edit Item' : 'Add Item'}</h2>
              <button className="close-btn" onClick={() => {
                setShowAddModal(false)
                setEditingItem(null)
                setPendingFormData(null)
              }}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
            <form onSubmit={handleAdd} className="modal-form">
              <div className="form-group">
                <label>Item Name</label>
                <input
                  type="text"
                  placeholder="e.g., Organic Avocados"
                  value={formData.item_name}
                  onChange={(e) => setFormData({ ...formData, item_name: e.target.value })}
                  required
                  autoFocus
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Quantity</label>
                  <input
                    type="number"
                    step="0.1"
                    placeholder="0"
                    value={formData.quantity}
                    onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Unit</label>
                  <select
                    value={formData.unit}
                    onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
                  >
                    <option value="units">units</option>
                    <option value="pieces">pieces</option>
                    <option value="kilograms">kilograms (kg)</option>
                    <option value="grams">grams (g)</option>
                    <option value="liters">liters (l)</option>
                    <option value="cups">cups</option>
                    <option value="tablespoons">tablespoons (tbsp)</option>
                    <option value="pint">pint</option>
                    <option value="gallon">gallon</option>
                    <option value="bottles">bottles</option>
                    <option value="loaf">loaf</option>
                    <option value="cloves">cloves</option>
                    <option value="head">head</option>
                    <option value="remaining">remaining</option>
                  </select>
                </div>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-cancel" onClick={() => {
                  setShowAddModal(false)
                  setEditingItem(null)
                  setPendingFormData(null)
                }}>
                  Cancel
                </button>
                <button type="submit" className="btn-submit">
                  {editingItem ? 'Update Item' : 'Add to Inventory'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

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
