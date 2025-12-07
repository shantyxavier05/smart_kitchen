import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import UserMenu from './UserMenu'

function Landing() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const { isAuthenticated, user } = useAuth()

  return (
    <div className="landing-page">
      {/* Navigation */}
      <nav className="navbar">
        <div className="nav-container">
          <div className="nav-logo">
            <div className="nav-logo-icon">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-5.5-2.5l7.51-3.49L17.5 6.5 9.99 9.99 6.5 17.5zm5.5-6.6c.61 0 1.1.49 1.1 1.1s-.49 1.1-1.1 1.1-1.1-.49-1.1-1.1.49-1.1 1.1-1.1z"/>
              </svg>
            </div>
            <span className="nav-logo-text">Smart Kitchen</span>
          </div>
          {isAuthenticated && (
            <div className="nav-center-links">
              <a href="#dashboard" className="nav-center-link">Dashboard</a>
              <a href="/meal-planner" className="nav-center-link">Meal Planner</a>
              <a href="/inventory" className="nav-center-link">Inventory</a>
              <a href="/shopping-list" className="nav-center-link">Shopping List</a>
            </div>
          )}
          
          <div className="nav-buttons">
            {isAuthenticated ? (
              <UserMenu />
            ) : (
              <>
                <a href="/login" className="nav-btn-login">Log In</a>
                <a href="/signup" className="nav-btn-signup">Sign Up</a>
              </>
            )}
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
            {isAuthenticated ? (
              <>
                <a href="#dashboard" className="mobile-menu-link" onClick={() => setMobileMenuOpen(false)}>Dashboard</a>
                <a href="/meal-planner" className="mobile-menu-link" onClick={() => setMobileMenuOpen(false)}>Meal Planner</a>
                <a href="/inventory" className="mobile-menu-link" onClick={() => setMobileMenuOpen(false)}>Inventory</a>
                <a href="/shopping-list" className="mobile-menu-link" onClick={() => setMobileMenuOpen(false)}>Shopping List</a>
                <div className="mobile-menu-divider"></div>
                <div className="mobile-menu-user-section">
                  <UserMenu />
                </div>
              </>
            ) : (
              <>
                <a href="/login" className="mobile-menu-link" onClick={() => setMobileMenuOpen(false)}>Log In</a>
                <a href="/signup" className="mobile-menu-link highlight" onClick={() => setMobileMenuOpen(false)}>Sign Up</a>
              </>
            )}
          </div>
        )}
      </nav>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-container">
          <div className="hero-content">
            <h1 className="hero-title">
              {isAuthenticated ? `Welcome back, ${user?.username || 'User'}!` : 'The future of your kitchen is here.'}
            </h1>
            <p className="hero-subtitle">
              {isAuthenticated 
                ? 'Your smart kitchen assistant is ready to help you plan meals, manage inventory, and create shopping lists.'
                : 'Let AI manage your inventory, plan your meals, and handle your shopping. Spend less time worrying and more time enjoying delicious food.'
              }
            </p>
            <div className="hero-buttons">
              {isAuthenticated ? (
                <>
                  <a href="/meal-planner" className="btn-primary">Start Planning</a>
                  <a href="/inventory" className="btn-secondary">View Inventory</a>
                </>
              ) : (
                <>
                  <a href="/signup" className="btn-primary">Get Started Free</a>
                  <a href="#features" className="btn-secondary">Learn More</a>
                </>
              )}
            </div>
          </div>
          <div className="hero-image">
            <img 
              src="https://images.unsplash.com/photo-1512621776951-a57141f2eefd?q=80&w=1000&auto=format&fit=crop" 
              alt="Healthy food bowl"
            />
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section" id="features">
        <div className="features-container">
          <h2 className="features-title">How Smart Kitchen Works</h2>
          <p className="features-subtitle">
            We simplify your life with three powerful features, all powered by intelligent AI.
          </p>
          
          <div className="features-grid">
            {/* Feature 1 - Smart Meal Planning */}
            <a href="/meal-planner" className="feature-card-link">
              <div className="feature-card">
                <div className="feature-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2M7 2v20M21 15V2v0a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3Zm0 0v7"/>
                  </svg>
                </div>
                <h3 className="feature-title">Smart Meal Planning</h3>
                <p className="feature-description">
                  Receive personalized meal plans and recipes based on your dietary 
                  preferences and available ingredients.
                </p>
              </div>
            </a>

            {/* Feature 2 - AI Inventory Management */}
            <a href="/inventory" className="feature-card-link">
              <div className="feature-card">
                <div className="feature-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                    <line x1="3" y1="9" x2="21" y2="9"/>
                    <line x1="9" y1="21" x2="9" y2="9"/>
                  </svg>
                </div>
                <h3 className="feature-title">AI Inventory Management</h3>
                <p className="feature-description">
                  Automatically track what's in your pantry and fridge. Get alerts before you 
                  run out of your favorite ingredients.
                </p>
              </div>
            </a>

            {/* Feature 3 */}
            <a href="/shopping-list" className="feature-card-link">
              <div className="feature-card">
                <div className="feature-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="9" cy="21" r="1"/>
                    <circle cx="20" cy="21" r="1"/>
                    <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>
                  </svg>
                </div>
                <h3 className="feature-title">Effortless Shopping</h3>
                <p className="feature-description">
                  Generate shopping lists automatically from your meal plan and inventory. 
                  Order groceries with just one click.
                </p>
              </div>
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-container">
          <p className="footer-copyright">
            © 2024 Smart Kitchen. All rights reserved.
          </p>
          <div className="footer-links">
            <a href="#">Privacy</a>
            <a href="#">Terms</a>
            <a href="#">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default Landing

