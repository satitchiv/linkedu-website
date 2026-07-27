// Auth indicator — shows signed-in state in every page header
(function () {
  const SUPABASE_URL = 'https://ufspivvuevllmkxmivbe.supabase.co'
  const SUPABASE_ANON_KEY = 'sb_publishable_5iAEih-Cq-6cIAihBLuSVQ_lKYf8a0x'

  const isLocal = window.location.hostname === 'localhost' ||
                  window.location.hostname === '127.0.0.1' ||
                  window.location.hostname === '100.100.120.57'

  const PORTAL_BASE = isLocal
    ? `http://${window.location.hostname}:8904`
    : 'https://linkedu-parent-portal.netlify.app'

  let _sb = null
  let _dropdownOpen = false

  function getInitial(email) {
    return (email || '?')[0].toUpperCase()
  }

  const GRAD_CAP_SVG = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>`

  function injectStyles() {
    if (document.getElementById('auth-indicator-styles')) return
    const style = document.createElement('style')
    style.id = 'auth-indicator-styles'
    style.textContent = `
      #auth-indicator-wrap {
        position: relative;
        display: flex;
        align-items: center;
        margin-right: 8px;
        flex-shrink: 0;
      }
      #auth-indicator-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        background: none;
        border: none;
        padding: 0;
        cursor: pointer;
        text-decoration: none;
      }
      #auth-indicator-btn .auth-avatar {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        background: #B8962E;
        color: #111;
        font-size: 12px;
        font-weight: 700;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: -apple-system, sans-serif;
        transition: opacity 0.2s;
      }
      #auth-indicator-btn .auth-avatar:hover { opacity: 0.8; }
      #auth-indicator-btn .auth-icon {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        border: 1.5px solid rgba(245,240,232,0.35);
        color: rgba(245,240,232,0.65);
        display: flex;
        align-items: center;
        justify-content: center;
        transition: border-color 0.2s, color 0.2s;
      }
      #auth-indicator-btn .auth-icon:hover {
        border-color: rgba(245,240,232,0.7);
        color: rgba(245,240,232,0.9);
      }
      #auth-indicator-dropdown {
        display: none;
        position: absolute;
        top: calc(100% + 10px);
        right: 0;
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 6px;
        min-width: 200px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.4);
        z-index: 9999;
        overflow: hidden;
      }
      #auth-indicator-dropdown.open { display: block; }
      .auth-dd-email {
        padding: 12px 16px 10px;
        font-family: -apple-system, sans-serif;
        font-size: 11px;
        color: #666;
        letter-spacing: 0.03em;
        border-bottom: 1px solid #2a2a2a;
        word-break: break-all;
      }
      .auth-dd-item {
        display: block;
        width: 100%;
        padding: 11px 16px;
        font-family: -apple-system, sans-serif;
        font-size: 13px;
        color: #ddd;
        text-decoration: none;
        background: none;
        border: none;
        text-align: left;
        cursor: pointer;
        transition: background 0.15s, color 0.15s;
        box-sizing: border-box;
      }
      .auth-dd-item:hover { background: #222; color: #fff; }
      .auth-dd-item.signout { color: #999; }
      .auth-dd-item.signout:hover { background: #222; color: #e74c3c; }
    `
    document.head.appendChild(style)
  }

  function closeDropdown() {
    const dd = document.getElementById('auth-indicator-dropdown')
    if (dd) dd.classList.remove('open')
    _dropdownOpen = false
  }

  function inject(email) {
    injectStyles()
    const actions = document.querySelector('.header-actions')
    if (!actions) return

    const existing = document.getElementById('auth-indicator-wrap')
    if (existing) existing.remove()

    const wrap = document.createElement('div')
    wrap.id = 'auth-indicator-wrap'

    if (email) {
      // Signed in — gold avatar with dropdown
      wrap.innerHTML = `
        <button id="auth-indicator-btn" title="${email}" aria-label="Account">
          <span class="auth-avatar">${getInitial(email)}</span>
        </button>
        <div id="auth-indicator-dropdown">
          <div class="auth-dd-email">${email}</div>
          <a class="auth-dd-item" href="${PORTAL_BASE}/?view=tools">My Account</a>
          <button class="auth-dd-item signout" id="auth-dd-signout">Sign out</button>
        </div>
      `
      wrap.querySelector('#auth-indicator-btn').addEventListener('click', function(e) {
        e.stopPropagation()
        const dd = document.getElementById('auth-indicator-dropdown')
        _dropdownOpen = !_dropdownOpen
        dd.classList.toggle('open', _dropdownOpen)
      })
      wrap.querySelector('#auth-dd-signout').addEventListener('click', async function() {
        closeDropdown()
        if (_sb) await _sb.auth.signOut()
      })
    } else {
      // Signed out — graduation cap icon, links to portal
      wrap.innerHTML = `
        <a id="auth-indicator-btn" href="${PORTAL_BASE}" title="Sign in to My Account" aria-label="Sign in">
          <span class="auth-icon">${GRAD_CAP_SVG}</span>
        </a>
      `
    }

    const hamburger = actions.querySelector('.hamburger')
    if (hamburger) {
      actions.insertBefore(wrap, hamburger)
    } else {
      actions.appendChild(wrap)
    }
  }

  // Close dropdown when clicking outside
  document.addEventListener('click', function() {
    if (_dropdownOpen) closeDropdown()
  })

  function init(sb) {
    _sb = sb
    sb.auth.getSession().then(({ data: { session } }) => {
      inject(session ? session.user.email : null)
    })
    sb.auth.onAuthStateChange((_event, session) => {
      inject(session ? session.user.email : null)
    })
  }

  function waitForSupabase(attempts) {
    if (window.supabase && window.supabase.createClient) {
      init(window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY))
      return
    }
    if (attempts <= 0) {
      const script = document.createElement('script')
      script.src = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2'
      script.onload = function () {
        init(window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY))
      }
      document.head.appendChild(script)
      return
    }
    setTimeout(() => waitForSupabase(attempts - 1), 100)
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => waitForSupabase(10))
  } else {
    waitForSupabase(10)
  }
})()
