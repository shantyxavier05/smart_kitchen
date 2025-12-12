import { useState, useEffect } from 'react'
import UserMenu from './UserMenu'

function ShoppingList() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [items, setItems] = useState([])

  const [selectAll, setSelectAll] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [fetching, setFetching] = useState(true)

  // Fetch shopping list items from API
  useEffect(() => {
    const fetchShoppingList = async () => {
      const token = localStorage.getItem('token')
      if (!token) {
        setFetching(false)
        return
      }

      try {
        const response = await fetch('http://localhost:8000/api/shopping-list', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.ok) {
          const data = await response.json()
          setItems(data.items || [])
        } else {
          console.error('Failed to fetch shopping list')
        }
      } catch (err) {
        console.error('Error fetching shopping list:', err)
      } finally {
        setFetching(false)
      }
    }

    fetchShoppingList()
  }, [])

  const handleItemToggle = async (id) => {
    const token = localStorage.getItem('token')
    if (!token) {
      setError('You must be logged in to toggle items')
      return
    }

    try {
      const response = await fetch(`http://localhost:8000/api/shopping-list/${id}/toggle`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        // Update local state
        setItems(items.map(item => 
          item.id === id ? { ...item, checked: data.item.checked } : item
        ))
      } else {
        const errorData = await response.json().catch(() => ({}))
        setError(errorData.detail || 'Failed to toggle item')
      }
    } catch (err) {
      setError('Error toggling item. Please try again.')
      console.error('Error toggling item:', err)
    }
  }

  const handleSelectAll = () => {
    const newState = !selectAll
    setSelectAll(newState)
    setItems(items.map(item => ({ ...item, checked: newState })))
  }

  const handleDownloadPDF = () => {
    try {
      // Create a simple HTML content for the PDF
      const date = new Date().toLocaleDateString('en-US', { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
      })
      
      let htmlContent = `
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="UTF-8">
          <title>Shopping List</title>
          <style>
            @media print {
              @page {
                margin: 1cm;
              }
              body {
                print-color-adjust: exact;
                -webkit-print-color-adjust: exact;
              }
            }
            body {
              font-family: 'Segoe UI', Arial, sans-serif;
              padding: 40px;
              color: #1a1a1a;
              max-width: 800px;
              margin: 0 auto;
            }
            h1 {
              color: #16a34a;
              margin-bottom: 10px;
              font-size: 32px;
              font-weight: 700;
            }
            .subtitle {
              color: #6b7280;
              margin-bottom: 10px;
              font-size: 16px;
            }
            .date {
              color: #9ca3af;
              margin-bottom: 30px;
              font-size: 14px;
            }
            table {
              width: 100%;
              border-collapse: collapse;
              margin-top: 20px;
              box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            th {
              background-color: #16a34a;
              color: white;
              padding: 14px 12px;
              text-align: left;
              font-weight: 600;
              font-size: 14px;
            }
            td {
              padding: 12px;
              border-bottom: 1px solid #e5e7eb;
              font-size: 14px;
            }
            tr:last-child td {
              border-bottom: none;
            }
            tr:nth-child(even) {
              background-color: #f9fafb;
            }
            .item-number {
              width: 60px;
              color: #6b7280;
              text-align: center;
            }
            .item-name {
              font-weight: 500;
              color: #1a1a1a;
            }
            .item-quantity {
              color: #4b5563;
            }
            .footer {
              margin-top: 40px;
              padding-top: 20px;
              border-top: 2px solid #e5e7eb;
              color: #9ca3af;
              font-size: 12px;
              text-align: center;
            }
            .total {
              margin-top: 20px;
              padding: 12px;
              background-color: #f3f4f6;
              border-radius: 8px;
              font-weight: 600;
              color: #1a1a1a;
            }
          </style>
        </head>
        <body>
          <h1>Your Shopping List</h1>
          <div class="subtitle">Generated from your latest meal plan</div>
          <div class="date">${date}</div>
          <table>
            <thead>
              <tr>
                <th class="item-number">#</th>
                <th class="item-name">Item</th>
                <th class="item-quantity">Quantity</th>
              </tr>
            </thead>
            <tbody>
      `
      
      items.forEach((item, index) => {
        htmlContent += `
              <tr>
                <td class="item-number">${index + 1}</td>
                <td class="item-name">${item.name}</td>
                <td class="item-quantity">${item.quantity}</td>
              </tr>
        `
      })
      
      htmlContent += `
            </tbody>
          </table>
          <div class="total">Total Items: ${items.length}</div>
          <div class="footer">
            <p>Smart Kitchen - Generated on ${date}</p>
          </div>
        </body>
        </html>
      `
      
      // Open print dialog for PDF generation
      const printWindow = window.open('', '_blank')
      if (printWindow) {
        printWindow.document.write(htmlContent)
        printWindow.document.close()
        
        // Wait for content to load, then trigger print
        setTimeout(() => {
          printWindow.focus()
          printWindow.print()
        }, 250)
      } else {
        // Fallback: if popup blocked, create download link
        const blob = new Blob([htmlContent], { type: 'text/html' })
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `shopping-list-${new Date().toISOString().split('T')[0]}.html`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)
        
        alert('Please use your browser\'s print dialog and select "Save as PDF" as the destination.')
      }
    } catch (err) {
      console.error('Error generating PDF:', err)
      alert('Error generating PDF. Please try again.')
    }
  }

  // Parse quantity string like "1 loaf", "2 lbs", "3 ripe" into {quantity: number, unit: string}
  const parseQuantity = (quantityStr) => {
    if (!quantityStr) return { quantity: 1, unit: 'units' }
    
    // Remove extra spaces and convert to lowercase
    const cleaned = quantityStr.trim().toLowerCase()
    
    // Try to extract number and unit
    // Pattern: number followed by optional unit
    const match = cleaned.match(/^(\d+(?:\.\d+)?)\s*(.*)$/)
    
    if (match) {
      const quantity = parseFloat(match[1])
      let unit = match[2].trim() || 'units'
      
      // Clean up common unit variations
      if (unit === '' || unit === 'ripe' || unit === 'head' || unit === 'pint' || unit === 'bag') {
        // Keep as is
      } else if (unit.includes('loaf')) {
        unit = 'loaf'
      } else if (unit.includes('lb') || unit.includes('pound')) {
        unit = 'lbs'
      } else if (unit.includes('kg')) {
        unit = 'kg'
      } else if (unit.includes('g')) {
        unit = 'g'
      } else if (unit.includes('oz')) {
        unit = 'oz'
      }
      
      return { quantity, unit }
    }
    
    // Fallback: try to extract just a number
    const numberMatch = cleaned.match(/(\d+(?:\.\d+)?)/)
    if (numberMatch) {
      return { quantity: parseFloat(numberMatch[1]), unit: 'units' }
    }
    
    // Default fallback
    return { quantity: 1, unit: 'units' }
  }

  const handleAddToInventory = async () => {
    const selectedItems = items.filter(item => item.checked)
    
    if (selectedItems.length === 0) {
      setError('Please select at least one item to add to inventory')
      setSuccess(null)
      return
    }

    setLoading(true)
    setError(null)
    setSuccess(null)

    const token = localStorage.getItem('token')
    if (!token) {
      setError('You must be logged in to add items to inventory')
      setLoading(false)
      return
    }

    try {
      const addPromises = selectedItems.map(async (item) => {
        const { quantity, unit } = parseQuantity(item.quantity)
        
        console.log(`Adding ${item.name}: ${quantity} ${unit}`)
        
        const response = await fetch('http://localhost:8000/api/inventory/add', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            item_name: item.name,
            quantity: quantity,
            unit: unit
          })
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}))
          throw new Error(errorData.detail || `Failed to add ${item.name}`)
        }

        return await response.json()
      })

      await Promise.all(addPromises)
      
      // Delete items from shopping list
      const deletePromises = selectedItems.map(async (item) => {
        const response = await fetch(`http://localhost:8000/api/shopping-list/${item.id}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        
        if (!response.ok) {
          console.warn(`Failed to delete shopping list item ${item.id}`)
        }
      })
      
      await Promise.all(deletePromises)
      
      // Remove added items from local state
      const remainingItems = items.filter(item => !selectedItems.some(selected => selected.id === item.id))
      setItems(remainingItems)
      setSelectAll(false)
      setSuccess(`Successfully added ${selectedItems.length} item(s) to inventory!`)
      setError(null)
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000)
      
    } catch (err) {
      setError(err.message || 'Error adding items to inventory. Please try again.')
      setSuccess(null)
      console.error('Error adding items to inventory:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="shopping-list-page">
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
            <a href="/meal-planner" className="app-nav-link">Meal Planner</a>
            <a href="/inventory" className="app-nav-link">Inventory</a>
            <a href="/shopping-list" className="app-nav-link active">Shopping List</a>
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
            <a href="/meal-planner" className="mobile-menu-link" onClick={() => setMobileMenuOpen(false)}>Meal Planner</a>
            <a href="/inventory" className="mobile-menu-link" onClick={() => setMobileMenuOpen(false)}>Inventory</a>
            <a href="/shopping-list" className="mobile-menu-link active" onClick={() => setMobileMenuOpen(false)}>Shopping List</a>
          </div>
        )}
      </nav>

      {/* Main Content */}
      <main className="shopping-list-content">
        <div className="shopping-list-container">
          {/* Back Button */}
          <a href="/" className="back-to-home-btn">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
            Back to Home
          </a>

          {/* Header Section */}
          <div className="shopping-list-header">
            <div className="shopping-list-header-left">
              <h1 className="shopping-list-title">Your Shopping List</h1>
              <p className="shopping-list-subtitle">
                Generated from your latest meal plan.
              </p>
            </div>
            <button className="download-pdf-btn" onClick={handleDownloadPDF}>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              Download as PDF
            </button>
          </div>

          {/* Shopping List Items */}
          <div className="shopping-list-items">
            {fetching ? (
              <div style={{
                padding: '40px',
                textAlign: 'center',
                color: '#6b7280'
              }}>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ 
                  width: '48px', 
                  height: '48px', 
                  margin: '0 auto 16px',
                  animation: 'spin 1s linear infinite'
                }}>
                  <circle cx="12" cy="12" r="10" strokeDasharray="32" strokeDashoffset="32">
                    <animate attributeName="stroke-dasharray" dur="2s" values="0 32;16 16;0 32;0 32" repeatCount="indefinite"/>
                    <animate attributeName="stroke-dashoffset" dur="2s" values="0;-16;-32;-32" repeatCount="indefinite"/>
                  </circle>
                </svg>
                <p>Loading shopping list...</p>
              </div>
            ) : items.length === 0 ? (
              <div style={{
                padding: '40px',
                textAlign: 'center',
                color: '#6b7280'
              }}>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ 
                  width: '64px', 
                  height: '64px', 
                  margin: '0 auto 16px',
                  opacity: 0.5
                }}>
                  <path d="M9 2v4M15 2v4M3 10h18M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z"/>
                  <line x1="9" y1="14" x2="15" y2="14"/>
                </svg>
                <p style={{ fontSize: '1.1rem', marginBottom: '8px' }}>Your shopping list is empty</p>
                <p style={{ fontSize: '0.9rem', opacity: 0.8 }}>
                  Items will appear here when you confirm a meal plan with ingredients not in your inventory.
                </p>
              </div>
            ) : (
              <>
                {/* Select All Header */}
                <div className="shopping-list-item-header">
                  <label className="checkbox-label header-checkbox">
                    <input
                      type="checkbox"
                      checked={selectAll}
                      onChange={handleSelectAll}
                      className="custom-checkbox"
                    />
                    <span className="checkbox-custom"></span>
                    <span className="item-header-text">ITEM ({items.length})</span>
                  </label>
                </div>

                {/* Individual Items */}
                {items.map((item) => (
                  <div key={item.id} className={`shopping-list-item ${item.checked ? 'checked' : ''}`}>
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={item.checked}
                        onChange={() => handleItemToggle(item.id)}
                        className="custom-checkbox"
                      />
                      <span className={`checkbox-custom ${item.checked ? 'checked' : ''}`}>
                        {item.checked && (
                          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                            <polyline points="20 6 9 17 4 12"/>
                          </svg>
                        )}
                      </span>
                      <div className="item-details">
                        <span className={`item-name ${item.checked ? 'strikethrough' : ''}`}>
                          {item.name}
                        </span>
                        <span className="item-quantity">{item.quantity}</span>
                      </div>
                    </label>
                  </div>
                ))}
              </>
            )}
          </div>

          {/* Error/Success Messages */}
          {error && (
            <div className="shopping-list-message error-message" style={{
              padding: '12px 16px',
              marginBottom: '16px',
              backgroundColor: '#fee',
              color: '#c33',
              borderRadius: '8px',
              border: '1px solid #fcc'
            }}>
              {error}
            </div>
          )}
          {success && (
            <div className="shopping-list-message success-message" style={{
              padding: '12px 16px',
              marginBottom: '16px',
              backgroundColor: '#efe',
              color: '#3c3',
              borderRadius: '8px',
              border: '1px solid #cfc'
            }}>
              {success}
            </div>
          )}

          {/* Add to Inventory Button */}
          <div className="shopping-list-actions">
            <button 
              className="add-to-inventory-btn" 
              onClick={handleAddToInventory}
              disabled={loading || items.filter(item => item.checked).length === 0}
              style={{
                opacity: (loading || items.filter(item => item.checked).length === 0) ? 0.6 : 1,
                cursor: (loading || items.filter(item => item.checked).length === 0) ? 'not-allowed' : 'pointer'
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
                  Adding...
                </>
              ) : (
                <>
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="9" cy="21" r="1"/>
                    <circle cx="20" cy="21" r="1"/>
                    <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>
                  </svg>
                  Add Selected to Inventory
                </>
              )}
            </button>
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

export default ShoppingList

