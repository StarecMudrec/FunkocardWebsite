<template>
  <div class="category-cards-page">
    <!-- Background container -->
    <div class="background-container"></div>
    
    <!-- Scroll to top button -->
    <transition name="fade">
      <button 
        v-if="showScrollTop" 
        @click="scrollToTop" 
        class="scroll-top-button"
        aria-label="Scroll to top"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="m18 15-6-6-6 6"/>
        </svg>
      </button>
    </transition>

    <div class="page-header">
      <!-- Centered category title and info -->
      <div class="category-header-content">
        <h1 class="category-title">{{ categoryName }}</h1>
        <div class="category-info">
          <span class="card-count">{{ cards.length }} cards</span>
        </div>
        
        <!-- Search Bar and Sort Controls -->
        <div class="search-sort-container">
          <div class="search-container">
            <div class="search-input-wrapper">
              <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="30" height="25" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="8"></circle>
                <path d="m21 21-4.3-4.3"></path>
              </svg>
              <input
                v-model="searchQuery"
                type="text"
                placeholder="Search cards..."
                class="search-input"
                @input="handleSearch"
              />
              <button
                v-if="searchQuery"
                @click="clearSearch"
                class="clear-search-button"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M18 6 6 18"></path>
                  <path d="m6 6 12 12"></path>
                </svg>
              </button>
            </div>
          </div>

          <!-- Sort Controls -->
          <div class="sort-controls">
            <div class="sort-icon" @click.stop="toggleSortDropdown">
              <svg width="52" height="44" viewBox="0 0 52 44" fill="none" xmlns="http://www.w3.org/2000/svg">
                <g filter="url(#filter0_d_110_20)">
                  <path d="M45.3209 18.0467H21.1236M45.3209 3.0233L6.60522 3.0233M45.3209 33.0701H35.642" stroke="white" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
                </g>
                <defs>
                  <filter id="filter0_d_110_20" x="0.105225" y="0.523315" width="51.7157" height="43.0468" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB">
                    <feFlood flood-opacity="0" result="BackgroundImageFix"/>
                    <feColorMatrix in="SourceAlpha" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0" result="hardAlpha"/>
                    <feOffset dy="4"/>
                    <feGaussianBlur stdDeviation="2"/>
                    <feComposite in2="hardAlpha" operator="out"/>
                    <feColorMatrix type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.25 0"/>
                    <feBlend mode="normal" in2="BackgroundImageFix" result="effect1_dropShadow_110_20"/>
                    <feBlend mode="normal" in="SourceGraphic" in2="effect1_dropShadow_110_20" result="shape"/>
                  </filter>
                </defs>
              </svg>
            </div>
            <transition name="sort-dropdown">
              <div class="sort-dropdown" v-if="showSortDropdown" v-click-outside="closeSortDropdown">
                <div class="sort-option" @click="sortBy('id', 'asc')">Old first</div>
                <div class="sort-option" @click="sortBy('id', 'desc')">New first</div>
                <div class="sort-option" @click="sortBy('amount', 'asc')">Points (Low to High)</div>
                <div class="sort-option" @click="sortBy('amount', 'desc')">Points (High to Low)</div>
                <div v-if="showRaritySort" class="sort-option" @click="sortBy('rarity', 'asc')">Rarity (Vinyl Figure💫 to Force🤷‍♂️)</div>
                <div v-if="showRaritySort" class="sort-option" @click="sortBy('rarity', 'desc')">Rarity (Force🤷‍♂️ to Vinyl Figure💫)</div>
                <div class="sort-option" @click="sortBy('name', 'asc')">Name (A-Z)</div>
                <div class="sort-option" @click="sortBy('name', 'desc')">Name (Z-A)</div>
              </div>
            </transition>
          </div>
        </div>
      </div>
    </div>

    <div class="cards-container-wrapper">
      <!-- Cards container with border -->
      <div class="cards-section-container">
        <!-- Line above cards container - centered -->
        <div class="cards-divider-wrapper">
          <div class="cards-divider"></div>
        </div>
      
        <div class="cards-container">
          <transition-group name="cards" tag="div" class="cards-transition-container">
            <Card
              v-for="card in filteredCards"
              :key="card.id"
              :card="card || {}"
              @card-clicked="handleCardClicked"
              class="card-item"
            />
          </transition-group>
          <div v-if="!loading && filteredCards.length === 0" class="no-cards-message">
            {{ searchQuery ? 'No cards match your search' : 'No cards found in this category' }}
          </div>
        </div>
        
        <div v-if="loading"  class="loading-spinner-container">
          <div class="loading-spinner"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Card from '@/components/Card.vue'
import { fetchCardsByCategory } from '@/api'

// Move debounce outside the component to avoid recreation
const debounce = (func, wait) => {
  let timeout
  const debounced = function(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
  
  debounced.cancel = function() {
    clearTimeout(timeout)
  }
  
  return debounced
}

// Add this directive definition
const clickOutside = {
  beforeMount(el, binding) {
    el.clickOutsideEvent = function(event) {
      if (!(el === event.target || el.contains(event.target))) {
        binding.value();
      }
    };
    document.addEventListener('click', el.clickOutsideEvent);
  },
  unmounted(el) {
    document.removeEventListener('click', el.clickOutsideEvent);
  },
};

export default {
  name: 'CategoryCards',
  components: {
    Card
  },
  directives: {
    'click-outside': clickOutside
  },
  props: {
    categoryId: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      cards: [],
      filteredCards: [],
      loading: false,
      error: null,
      categoryName: '',
      searchQuery: '',
      isSearching: false,
      debouncedSearch: null,
      showSortDropdown: false,
      currentSort: { field: 'id', direction: 'asc' },
      rarityOrder: {
        'Vinyl Figure💫': 1,
        'Legendary🧡': 2,
        'Special 🌟': 3,
        'Nameless 📛': 4,
        'Limited ⚠️': 5,
        'SuperCool🤟': 6,
        'Cool👍': 7,
        'Plain😼': 8,
        'Force🤷‍♂️': 9,
        'Scarface - Tony Montana': 10
      },
      showScrollTop: false,
      scrollThreshold: 300,
      scrollPosition: 0,
      scrollSaveTimeout: null
    }
  },
  computed: {
    showRaritySort() {
      // Show rarity sort only for 'all' and 'shop' categories
      return this.categoryId === 'all' || this.categoryId === 'shop'
    },
    // Generate a unique storage key for this category
    storageKey() {
      return `category_state_${this.categoryId}`
    }
  },
  async created() {
    this.debouncedSearch = debounce(this.performSearch, 300)
    
    // Load saved state if available
    this.loadSavedState()
    
    await this.loadCategoryCards()
    
    // Restore scroll position after cards are loaded
    this.$nextTick(() => {
      this.restoreScrollPosition()
    })
    
    window.addEventListener('scroll', this.handleScroll)
  },
  beforeUnmount() {
    // Only save state if we're navigating to a card detail page
    const navigationType = this.$route.meta?.navigationType
    console.log('CategoryCards unmounting, navigation type:', navigationType)
    
    if (navigationType === 'to-card-detail') {
      // Keep state when going to card detail
      this.saveState()
    } else {
      // Clear state when leaving category completely
      console.log('Clearing category state - navigating away from category')
      this.clearSavedState()
    }
    
    if (this.scrollSaveTimeout) {
      clearTimeout(this.scrollSaveTimeout)
    }
    
    window.removeEventListener('scroll', this.handleScroll)
  },
  watch: {
    categoryId: {
      handler: 'loadCategoryCards',
      immediate: false
    },
    searchQuery(newQuery) {
      // Save state when search changes
      this.saveState()
    },
    currentSort: {
      handler(newSort) {
        // Save state when sort changes
        this.saveState()
      },
      deep: true
    }
  },
  methods: {
    // Save current state to sessionStorage
    saveState() {
      const state = {
        searchQuery: this.searchQuery,
        currentSort: this.currentSort,
        scrollPosition: this.scrollPosition,
        timestamp: Date.now()
      }
      sessionStorage.setItem(this.storageKey, JSON.stringify(state))
    },
    
    // Load saved state from sessionStorage
    loadSavedState() {
      try {
        const saved = sessionStorage.getItem(this.storageKey)
        if (saved) {
          const state = JSON.parse(saved)
          
          // Check if state is not too old (e.g., 1 hour)
          if (Date.now() - state.timestamp < 60 * 60 * 1000) {
            this.searchQuery = state.searchQuery || ''
            this.currentSort = state.currentSort || { field: 'id', direction: 'asc' }
            this.scrollPosition = state.scrollPosition || 0
          } else {
            this.clearSavedState()
          }
        }
      } catch (error) {
        console.warn('Failed to load saved state:', error)
        this.clearSavedState()
      }
    },
    
    // Clear saved state
    clearSavedState() {
      sessionStorage.removeItem(this.storageKey)
    },
    
    // Restore scroll position
    restoreScrollPosition() {
      if (this.scrollPosition > 0) {
        setTimeout(() => {
          window.scrollTo(0, this.scrollPosition)
        }, 100)
      }
    },
    
    // Update scroll position handler
    handleScroll() {
      this.scrollPosition = window.scrollY
      this.showScrollTop = this.scrollPosition > this.scrollThreshold
      
      // Throttle saving scroll position to avoid too many writes
      if (!this.scrollSaveTimeout) {
        this.scrollSaveTimeout = setTimeout(() => {
          this.saveState()
          this.scrollSaveTimeout = null
        }, 500)
      }
    },
    
    scrollToTop() {
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      })
      this.scrollPosition = 0
      this.saveState()
    },

    async loadCategoryCards() {
      this.loading = true
      try {
        const response = await fetchCardsByCategory(this.categoryId)
        this.cards = response.cards
        
        // Apply saved search and sort - but only if we're returning from card detail
        const navigationType = this.$route.meta?.navigationType
        if (navigationType === 'to-category') {
          this.applySavedFilters()
        } else {
          // Reset to default when coming from elsewhere
          this.searchQuery = ''
          this.currentSort = { field: 'id', direction: 'asc' }
          this.filteredCards = [...this.cards]
          this.clearSavedState()
        }
        
        this.categoryName = this.getCategoryName(this.categoryId)
        
        console.log('Loaded category cards:', this.cards)
        console.log('Navigation type:', navigationType)
        
      } catch (err) {
        this.error = err
        console.error('Error loading category cards:', err)
      } finally {
        this.loading = false
        
        // Restore scroll position after cards are loaded, but only if returning from card detail
        this.$nextTick(() => {
          const navigationType = this.$route.meta?.navigationType
          if (navigationType === 'to-category' && this.scrollPosition > 0) {
            this.restoreScrollPosition()
          }
        })
      }
    },
    
    // Apply saved filters (search and sort) to the loaded cards
    applySavedFilters() {
      // First apply search if exists
      if (this.searchQuery.trim()) {
        this.performSearch()
      } else {
        this.filteredCards = [...this.cards]
      }
      
      // Then apply saved sort
      if (this.currentSort.field !== 'id' || this.currentSort.direction !== 'asc') {
        this.sortBy(this.currentSort.field, this.currentSort.direction, true)
      }
    },

    getCategoryName(categoryId) {
      // Extract category name from categoryId
      if (categoryId === 'all') return 'All Cards'
      if (categoryId === 'shop') return 'Available at Shop'
      if (categoryId.startsWith('rarity_')) {
        return categoryId.replace('rarity_', '')
      }
      return categoryId
    },
    
    handleCardClicked(cardId) {
      // Set navigation type before navigating to card detail
      if (this.$route.meta) {
        this.$route.meta.navigationType = 'to-card-detail'
      }
      this.$router.push(`/card/${cardId}`)
    },
    
    handleSearch() {
      this.isSearching = true
      this.debouncedSearch()
    },
    
    performSearch() {
      if (!this.searchQuery.trim()) {
        this.filteredCards = [...this.cards]
        this.isSearching = false
        return
      }
      
      const query = this.searchQuery.toLowerCase().trim()
      
      // Use requestAnimationFrame for smoother UI updates
      requestAnimationFrame(() => {
        this.filteredCards = this.cards.filter(card => 
          card.name?.toLowerCase().includes(query) ||
          card.rarity?.toLowerCase().includes(query)
        )
        
        this.isSearching = false
      })
    },
    
    clearSearch() {
      this.searchQuery = ''
      this.filteredCards = [...this.cards]
      this.isSearching = false
      // Cancel any pending debounced search
      this.debouncedSearch?.cancel()
      this.saveState()
    },

    toggleSortDropdown() {
      this.showSortDropdown = !this.showSortDropdown
    },

    closeSortDropdown() {
      this.showSortDropdown = false
    },

    sortBy(field, direction, silent = false) {
      this.currentSort = { field, direction }
      
      if (!silent) {
        this.showSortDropdown = false
      }
      
      let sortedCards = [...this.filteredCards]
      
      switch (field) {
        case 'id':
          sortedCards.sort((a, b) => {
            return direction === 'asc' ? a.id - b.id : b.id - a.id
          })
          break
        
        case 'amount':
          sortedCards.sort((a, b) => {
            const amountA = a.points || 0
            const amountB = b.points || 0
            return direction === 'asc' ? amountA - amountB : amountB - amountA
          })
          break
        
        case 'rarity':
          sortedCards.sort((a, b) => {
            const rarityA = this.rarityOrder[a.rarity] || 0
            const rarityB = this.rarityOrder[b.rarity] || 0
            return direction === 'asc' ? rarityA - rarityB : rarityB - rarityA
          })
          break
        
        case 'name':
          sortedCards.sort((a, b) => {
            const nameA = a.name?.toLowerCase() || ''
            const nameB = b.name?.toLowerCase() || ''
            if (direction === 'asc') {
              return nameA.localeCompare(nameB)
            } else {
              return nameB.localeCompare(nameA)
            }
          })
          break
      }
      
      this.filteredCards = sortedCards
      
      if (!silent) {
        this.saveState()
      }
    }
  }
}
</script>

<style scoped>
/* Scroll to top button styles */
.scroll-top-button {
  position: fixed;
  bottom: 30px;
  right: 30px;
  width: 50px;
  height: 50px;
  background: var(--card-bg);
  border: none;
  border-radius: 50%;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
  z-index: 1000;
}

.scroll-top-button svg {
  width: 48px; /* Increased from 24px */
  height: 48px; /* Increased from 24px */
}

.scroll-top-button:hover {
  background: rgba(53, 53, 53, 0.45);
  transform: translateY(-3px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
}

.scroll-top-button:active {
  transform: translateY(-1px);
}

/* Fade transition for the button */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .scroll-top-button {
    bottom: 20px;
    right: 20px;
    width: 45px;
    height: 45px;
  }
}

@media (max-width: 480px) {
  .scroll-top-button {
    bottom: 15px;
    right: 15px;
    width: 40px;
    height: 40px;
  }
  
  .scroll-top-button svg {
    width: 20px;
    height: 20px;
  }
}

/* Your existing styles remain the same */
.category-cards-page {
  min-height: 100vh;
  /* background: var(--bg-color); */
  padding: 20px;
  font-family: 'Afacad', sans-serif;
  position: relative;
}

.background-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: url('/background.jpg');
  filter: blur(10px);
  background-size: cover;
  background-position: center 57%;
  z-index: -1;
}

.page-header {
  max-width: 1200px;
  margin: 227px auto 50px;
  padding: 20px;
  /* background: var(--card-bg); */
  border-radius: 12px;
  /* border: 1px solid #333; */
  position: relative;
  /* backdrop-filter: blur(5px); */
}

.back-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: none;
  border: none;
  color: var(--accent-color);
  cursor: pointer;
  font-size: 16px;
  padding: 8px 16px;
  border-radius: 6px;
  transition: all 0.3s ease;
  margin-bottom: 15px;
  text-shadow: 0px 3px 5px rgba(0, 0, 0, 0.17);
}

.back-button:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateX(-5px);
}

.back-button svg {
  width: 18px;
  height: 18px;
}

/* Centered category header content */
.category-header-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  width: 100%;
}

.category-title {
  font-size: 5.5rem;
  color: var(--accent-color);
  margin: 0 0 -10px 0;
  font-weight: 600;
  text-shadow: 0px 3px 5px rgba(0, 0, 0, 0.27);
}

.category-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
  margin-bottom: 30px;
}

.card-count {
  color: var(--text-color);
  opacity: 0.8;
  font-size: 1.1rem;
  text-shadow: 0px 3px 5px rgba(0, 0, 0, 0.27);
}

/* Search and Sort Container */
.search-sort-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;
}

/* Search Container */
.search-container {
  flex: 1;
  max-width: 950px;
}

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
}

.search-icon {
  position: absolute;
  left: 1.7%;
  color: var(--text-color);
  opacity: 0.7;
  z-index: 2;
}

.search-input {
  width: 100%;
  padding: 15px 45px 15px 55px;
  background: var(--card-bg);
  border: 2px solid #333;
  border-radius: 32px;
  color: var(--text-color);
  font-size: 1.4rem;
  font-family: 'Afacad', sans-serif;
  backdrop-filter: blur(5px);
  transition: all 0.3s ease;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.search-input:focus {
  outline: none;
  border-color: #555555;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.search-input::placeholder {
  color: var(--text-color);
  opacity: 0.6;
}

.clear-search-button {
  position: absolute;
  right: 17px;
  background: none;
  border: none;
  color: var(--text-color);
  opacity: 0.7;
  cursor: pointer;
  padding: 4px;
  border-radius: 20px;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.clear-search-button:hover {
  opacity: 1;
  background: rgba(255, 255, 255, 0.1);
  scale: 1.1;
}

/* Sort Controls */
.sort-controls {
  position: relative;
  display: flex;
  align-items: center;
}

.sort-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  /* background: var(--card-bg);
  border: 1px solid #333; */
  transition: all 0.3s ease;
  width: 50px;
  height: 50px;
}

.sort-icon:hover {
  /* background: rgba(255, 255, 255, 0.1); */
  transform: scale(1.05);
}

.sort-icon svg {
  width: 100%;
  height: 100%;
}

.sort-dropdown {
  position: absolute;
  top: 100%;
  left: -100%;
  margin-top: 10px;
  background-color: #1e1e1eeb;
  color: var(--text-color);
  border: 1px solid #333;
  border-radius: 8px;
  padding: 10px 0;
  z-index: 100;
  min-width: 190px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

@media (max-width: 1317px) {
  .sort-dropdown {
    right: 0;
    left: auto; 
  }
}

.sort-option {
  padding: 8px 15px;
  cursor: pointer;
  transition: background-color 0.2s ease;
  -webkit-touch-callout: none;
  -webkit-user-select: none;
  -khtml-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  user-select: none;
}

.sort-option:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.sort-dropdown-enter-active,
.sort-dropdown-leave-active {
  transition: all 0.3s ease;
}

.sort-dropdown-enter-from,
.sort-dropdown-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.cards-container-wrapper {
  max-width: 1300px;
  margin: 0 auto;
  position: relative;
  min-height: 200px;
}

/* Wrapper to center the line */
.cards-divider-wrapper {
  display: flex;
  justify-content: center;
  margin: 52px 0 17px 0;
}

/* Line above the cards - centered and same width as cards container */
.cards-divider {
  height: 2px;
  background: linear-gradient(90deg, #434343a1, #434343, #434343a1);
  width: 100%;
  max-width: 1300px;
}

/* Cards section container */
.cards-section-container {
  background: var(--card-bg);
  border-radius: 12px;
  border: 1px solid #333;
  padding: 25px;
  backdrop-filter: blur(5px);
  max-width: 1300px;
  margin: 0 auto;
}

.loading-spinner-container {
  /* position: absolute; */
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10;
  padding: 10px 0; /* Add 20px padding top and bottom */
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: var(--accent-color);
  animation: spin 1s ease-in-out infinite;
  /* margin-top: 20px;
  margin-bottom: 20px; */
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.cards-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  column-gap: 30px;
  row-gap: 0px;
  justify-items: center; /* Center items within grid cells */
}

.cards-transition-container {
  display: contents; /* This allows the grid layout to work with transition-group */
}

.card-item {
  width: 100%; /* Ensure cards take full width of their grid cell */
  max-width: 220px; /* Match the minmax value */
}

.no-cards-message {
  grid-column: 1 / -1;
  text-align: center;
  color: var(--text-color);
  opacity: 0.7;
  font-size: 1.2rem;
  padding: 40px 0;
}

/* Card transition animations - Only fade, no movement */
.cards-enter-active,
.cards-leave-active {
  transition: opacity 0.3s ease;
}

.cards-enter-from {
  opacity: 0;
}

.cards-enter-to {
  opacity: 1;
}

.cards-leave-from {
  opacity: 1;
}

.cards-leave-to {
  opacity: 0;
}

/* Responsive design */
@media (max-width: 768px) {
  .category-cards-page {
    padding: 10px;
  }
  
  .page-header {
    padding: 15px;
    margin-bottom: 20px;
  }
  
  .category-title {
    font-size: 2rem;
  }
  
  .category-info {
    margin-bottom: 20px;
  }
  
  .search-sort-container {
    flex-direction: column;
    gap: 10px;
    max-width: 400px;
  }
  
  .search-container {
    max-width: 100%;
  }
  
  .search-input {
    padding: 12px 40px 12px 40px;
    font-size: 0.9rem;
  }
  
  .sort-controls {
    align-self: flex-end;
  }
  
  .sort-icon {
    width: 50px;
    height: 42px;
  }
  
  .cards-section-container {
    padding: 15px;
  }
  
  .cards-container {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 15px;
  }
  
  .card-item {
    max-width: 160px; /* Match the minmax value for mobile */
  }
  
  .cards-divider-wrapper {
    margin: 40px 0 15px 0;
  }
}

@media (max-width: 480px) {
  .cards-container {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }
  
  .card-item {
    max-width: none; /* Remove max-width constraint on very small screens */
  }
  
  .category-title {
    font-size: 1.5rem;
  }
  
  .category-info {
    margin-bottom: 15px;
  }
  
  .search-sort-container {
    max-width: 100%;
  }
  
  .sort-icon {
    width: 45px;
    height: 38px;
  }
  
  .cards-section-container {
    padding: 10px;
  }
  
  .cards-divider-wrapper {
    margin: 30px 0 12px 0;
  }
}
</style>