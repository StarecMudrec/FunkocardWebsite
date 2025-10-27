<template>
  <div class="page-container">
    <!-- Hero section with background and scroll arrow -->
    <div class="hero-section">
      <div class="background-container"></div>
      <div class="logo-text">
        <h1 class="funko-text">FUNKO CARDS</h1>
      </div>
      <div class="cover-arrow" @click="scrollToContent">
        <div class="cover-arrow__inner">
          <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 106 65" fill="none">
            <path xmlns="http://www.w3.org/2000/svg" d="M54.4142 39.1858C53.6332 39.9669 52.3668 39.9669 51.5858 39.1858L13.7809 1.38091C12.9998 0.59986 11.7335 0.59986 10.9525 1.38091L1.41421 10.9192C0.633164 11.7002 0.633165 12.9665 1.41421 13.7476L51.5858 63.9192C52.3668 64.7002 53.6332 64.7002 54.4142 63.9192L104.586 13.7476C105.367 12.9665 105.367 11.7002 104.586 10.9192L95.0475 1.38091C94.2665 0.599859 93.0002 0.59986 92.2191 1.38091L54.4142 39.1858Z" fill="#FFFFFF"/>
          </svg>
        </div>
      </div>
    </div>
    
    <!-- Линия-разделитель -->
    <hr class="separator-line">
    
    <!-- Основной контент -->
    <div id="content-section" class="content">
      <h1 class="categories-title">Categories:</h1>
      
      <!-- Search and Sort Container -->
      <div class="search-sort-container">
        <!-- Search Bar -->
        <div class="search-container">
          <div class="search-input-wrapper">
            <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="30" height="25" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="8"></circle>
              <path d="m21 21-4.3-4.3"></path>
            </svg>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search categories..."
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
              <div class="sort-option" @click="sortBy('cards', 'asc')">Cards Amount (Low to High)</div>
              <div class="sort-option" @click="sortBy('cards', 'desc')">Cards Amount (High to Low)</div>
              <div class="sort-option" @click="sortBy('rarity', 'asc')">Rarity (Vinyl Figure💫 to Force🤷‍♂️)</div>
              <div class="sort-option" @click="sortBy('rarity', 'desc')">Rarity (Force🤷‍♂️ to Vinyl Figure💫)</div>
              <div class="sort-option" @click="sortBy('name', 'asc')">Name (A-Z)</div>
              <div class="sort-option" @click="sortBy('name', 'desc')">Name (Z-A)</div>
            </div>
          </transition>
        </div>
      </div>

      <div id="categories-container" class="categories-grid">
        <div v-if="loading" class="loading">Loading categories...</div>
        <div v-else-if="error" class="error-message">Error loading data: {{ error.message || error }}. Please try again later.</div>
        <div v-else-if="filteredCategories.length === 0" class="no-categories-message">
          {{ searchQuery ? 'No categories match your search' : 'No categories found' }}
        </div>
        
        <!-- Category Cards -->
        <transition-group name="search-animation" tag="div" class="categories-grid-transition">
          <div 
            v-for="(category, index) in filteredCategories" 
            :key="category.id"
            class="category-card"
            :class="getCategoryBackgroundClass(category, index)"
            @click="navigateToCategory(category)"
          >
            <!-- Video background for Limited category -->
            <video 
              v-if="category.name === 'Limited ⚠️' && getLimitedVideoSource(category)"
              class="category-card__video"
              :src="getLimitedVideoSource(category)"
              autoplay
              muted
              loop
              playsinline
            ></video>
            <div 
              v-else
              class="category-card__background" 
              :style="getCategoryBackgroundStyle(category)"
            ></div>
            <div class="category-card__content">
              <div class="category-card__header">
                <h3 class="category-card__title">{{ category.name }}</h3>
                <!-- <span class="category-card__count">{{ category.count || 0 }}</span> -->
              </div>
            </div>
          </div>
        </transition-group>
      </div>
    </div>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=BIZ+UDPMincho&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@400;500;600&family=Noto+Serif:ital,wght@0,400;0,500;1,400&display=swap');

.page-container {
  position: relative;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  font-family: 'Afacad', sans-serif;
  width: 100%;
  overflow-x: hidden; /* Prevent horizontal scrolling */
}

.hero-section {
  position: relative;
  height: 100vh;
  width: 100%;
  overflow: hidden;
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

.logo-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  z-index: 1;
}

.funko-text {
  font-family: 'Afacad', sans-serif;
  font-size: 6rem;
  font-weight: 700;
  color: white;
  margin: 0;
  text-shadow: 3px 3px 10px rgba(0, 0, 0, 0.7);
  letter-spacing: 3px;
  line-height: 1;
}

.separator-line {
  position: absolute;
  top: 100vh;
  left: 0;
  width: 100%;
  height: 4px;
  margin: 0;
  border: none;
}

.content {
  position: relative;
  width: 100%;
  min-height: 52vh;
  left: 0;
  top: 4px;
  flex: 1;
}

.categories-title {
  text-align: center;
  font-size: 6rem;
  font-weight: 700;
  color: white;
  text-shadow: 3px 3px 10px rgba(0, 0, 0, 0.7);
  letter-spacing: 3px;
  line-height: 1;
  margin-top: 220px; 
}

/* Search and Sort Container */
.search-sort-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
  width: 100%;
  max-width: 1100px;
  margin: 30px auto 0;
  padding-left: 20px;
  padding-right: 20px;
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
  font-size: 1.2rem;
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
  transition: all 0.3s ease;
  width: 50px;
  height: 50px;
}

.sort-icon:hover {
  transform: scale(1.05);
}

.sort-icon svg {
  width: 100%;
  height: 100%;
}

.sort-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
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
  text-align: center;
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

.no-categories-message {
  text-align: center;
  color: var(--text-color);
  opacity: 0.7;
  font-size: 1.2rem;
  padding: 40px 0;
  grid-column: 1 / -1;
}

.categories-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  row-gap: 40px;
  column-gap: 67px;
  padding: 30px 20px;
  max-width: 1200px;
  margin: 0 auto;
  margin-top: 50px;
}

/* Transition group wrapper */
.categories-grid-transition {
  display: contents;
}

/* Search animation styles */
.search-animation-enter-active,
.search-animation-leave-active {
  transition: all 0.5s ease;
}

.search-animation-move {
  transition: transform 0.5s ease;
}

.search-animation-enter-from {
  opacity: 0;
  transform: scale(0.8) translateY(20px);
}

.search-animation-leave-to {
  opacity: 0;
  transform: scale(0.8) translateY(-20px);
}

.search-animation-leave-active {
  position: absolute;
}

.category-card {
  border-radius: 20px;
  box-shadow: 2px 7px 10px 2px rgba(0, 0, 0, 0.4);
  cursor: pointer;
  transition: all 0.3s ease;
  overflow: hidden;
  aspect-ratio: 0.8;
  position: relative;
  border: 3px solid #dadada;
}

/* Background element for better control */
.category-card__background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-size: cover;
  background-position: center;
  z-index: 0;
  transition: all 0.3s ease;
}

/* Video background for Limited category */
.category-card__video {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 0;
  transition: all 0.3s ease;
  filter: blur(2px); /* Apply same blur as rarity cards */
}

/* Apply specific backgrounds and blur effects */
.category-card.all-cards .category-card__background,
.category-card.shop .category-card__background,
.category-card.rarity .category-card__background {
  filter: blur(2px); /* Consistent blur for all category types */
}

/* Gradient overlay for better text readability */
.category-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(0,0,0,0.3) 0%, rgba(0,0,0,0.1) 50%, rgba(0,0,0,0.4) 100%);
  z-index: 1;
}

.category-card__content {
  padding: 20px;
  position: relative;
  z-index: 2;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.category-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
}

.category-card:hover .category-card__background,
.category-card:hover .category-card__video {
  transform: scale(1.02);
}

.category-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  flex-direction: column;
}

.category-card__title {
  font-size: 3.3rem;
  text-align: center;
  font-weight: 600;
  color: white;
  margin: 0;
  flex: 1;
  text-shadow: 0px 7px 16px rgba(0, 0, 0, 1);
}

.category-card__count {
  background: rgba(30, 30, 30, 0.7);
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  font-size: 0.9rem;
  font-weight: 600;
  min-width: 40px;
  text-align: center;
  backdrop-filter: blur(5px);
}

.error-message {
  text-align: center;
  margin: 50px 0;
  color: #ff5555;
  grid-column: 1 / -1;
}

.loading {
  text-align: center;
  margin: 50px 0;
  color: var(--text-color);
  grid-column: 1 / -1;
}

.cover-arrow {
  position: absolute;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  cursor: pointer;
  z-index: 10;
  width: 80px;
  height: 80px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.cover-arrow__inner {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  animation: bounce 2s infinite;
}

.arrow-icon {
  width: 144px;
  height: 144px;
  shape-rendering: geometricPrecision;
  transition: all 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  will-change: transform;
  pointer-events: none;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.4));
}

.cover-arrow:hover .arrow-icon {
  transform: scale(0.85);
  opacity: 0.9;
  filter: drop-shadow(0 6px 12px rgba(0, 0, 0, 0.5));
}

.cover-arrow:hover .cover-arrow__inner {
  animation-play-state: paused;
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-10px);
  }
  60% {
    transform: translateY(-5px);
  }
}


@media (max-width: 700px) {
  .page-container {
    width: 100%;
    min-width: 100%;
  }
  
  .content {
    width: 100%;
    padding: 0;
    margin: 0;
  }
  
  .categories-grid {
    width: 100%;
    padding: 20px 10px;
    margin: 0;
    grid-template-columns: 1fr; /* Single column on mobile */
    gap: 20px;
  }
  
  .search-sort-container {
    width: 100%;
    max-width: 100%;
    padding: 0 15px;
    margin: 20px auto 0;
    /* flex-direction: column; */
    gap: 15px;
  }

  .sort-dropdown {
    left: auto;
  }
  
  .search-container {
    width: 100%;
    max-width: 100%;
  }
  
  .search-input {
    width: 100%;
    box-sizing: border-box;
  }
  
  .categories-title {
    font-size: 3.5rem;
    margin-top: 150px;
    padding: 0 15px;
  }
  
  .funko-text {
    font-size: 3.5rem;
  }
}

.hero-section,
.background-container,
.content {
  max-width: 100vw;
  box-sizing: border-box;
}
</style>

<script>
import { mapActions, mapState } from 'vuex'

// Debounce function for search
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
  name: 'Home',
  directives: {
    'click-outside': clickOutside
  },
  data() {
    return {
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
      rarityNewestCards: {}, // Store newest card images for each category
      allCategoriesNewestCards: {}, // Store newest cards for all categories
      searchQuery: '',
      filteredCategories: [],
      debouncedSearch: null,
      showSortDropdown: false,
      currentSort: { field: 'default', direction: 'asc' }
    }
  },
  computed: {
    ...mapState({
      categories: state => state.categories || [],
      loading: state => state.loading,
      error: state => state.error
    }),
    
    rarityCategories() {
      return this.categories.filter(category => {
        const name = category.name.toLowerCase();
        return !name.includes('all') && !name.includes('general') && !name.includes('shop');
      });
    },
    
    sortedCategories() {
      if (!this.categories || this.categories.length === 0) return [];
      
      return [...this.categories].sort((a, b) => {
        const orderA = this.rarityOrder[a.name] || 999;
        const orderB = this.rarityOrder[b.name] || 999;
        
        if (a.name.toLowerCase().includes('all') || a.name.toLowerCase().includes('general')) return -1;
        if (b.name.toLowerCase().includes('all') || b.name.toLowerCase().includes('general')) return 1;
        if (a.name.toLowerCase().includes('shop')) return -1;
        if (b.name.toLowerCase().includes('shop')) return 1;
        
        return orderA - orderB;
      });
    }
  },
  methods: {
    ...mapActions(['fetchCategories']),
    
    async fetchRarityNewestCards() {
      try {
        const response = await fetch('/api/rarity_newest_cards');
        if (response.ok) {
          this.rarityNewestCards = await response.json();
          console.log('Newest rarity cards:', this.rarityNewestCards);
        } else {
          console.error('Failed to fetch newest rarity cards');
        }
      } catch (error) {
        console.error('Error fetching newest rarity cards:', error);
      }
    },
    
    async fetchAllCategoriesNewestCards() {
      try {
        const response = await fetch('/api/all_categories_newest_cards');
        if (response.ok) {
          this.allCategoriesNewestCards = await response.json();
          console.log('Newest cards for all categories:', this.allCategoriesNewestCards);
        } else {
          console.error('Failed to fetch newest cards for all categories');
        }
      } catch (error) {
        console.error('Error fetching newest cards for all categories:', error);
      }
    },
    
    navigateToCategory(category) {
      console.log('Navigating to category:', category);
      
      // Clear any existing category state when navigating to a new category
      Object.keys(sessionStorage).forEach(key => {
        if (key.startsWith('category_state_')) {
          sessionStorage.removeItem(key);
        }
      });
      
      this.$router.push(`/category/${category.id}`);
    },
    
    getCategoryBackgroundClass(category, index) {
      const name = category.name.toLowerCase();
      
      if (name.includes('all') || name.includes('general')) {
        return 'all-cards';
      } else if (name.includes('shop')) {
        return 'shop';
      } else {
        return 'rarity';
      }
    },
    
    getLimitedVideoSource(category) {
      const newestCard = this.rarityNewestCards[category.name] || this.allCategoriesNewestCards[category.name];
      if (newestCard && newestCard.photo) {
        return `/api/card_image/${newestCard.photo}`;
      }
      return null;
    },
    
    getCategoryBackgroundStyle(category) {
      const name = category.name.toLowerCase();
      
      // For all categories, use the newest card image
      const newestCard = this.rarityNewestCards[category.name] || this.allCategoriesNewestCards[category.name];
      if (newestCard && newestCard.photo) {
        return {
          backgroundImage: `url(/api/card_image/${newestCard.photo})`
        };
      }
      
      // Fallback to static images if no newest card found
      if (name.includes('all') || name.includes('general')) {
        return {
          backgroundImage: `url('/All.png')`
        };
      } else if (name.includes('shop')) {
        return {
          backgroundImage: `url('/shop.png')`
        };
      }
      
      return {};
    },
    
    scrollToContent() {
      const contentSection = document.querySelector('.content');
      if (contentSection) {
        contentSection.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start'
        });
      }
    },

    // Search methods
    handleSearch() {
      this.debouncedSearch();
    },
    
    performSearch() {
      if (!this.searchQuery.trim()) {
        this.filteredCategories = [...this.sortedCategories];
        return;
      }
      
      const query = this.searchQuery.toLowerCase().trim();
      
      requestAnimationFrame(() => {
        this.filteredCategories = this.sortedCategories.filter(category => 
          category.name?.toLowerCase().includes(query)
        );
      });
    },
    
    clearSearch() {
      this.searchQuery = '';
      this.filteredCategories = [...this.sortedCategories];
      this.debouncedSearch?.cancel();
    },

    // Sort methods
    toggleSortDropdown() {
      this.showSortDropdown = !this.showSortDropdown;
    },

    closeSortDropdown() {
      this.showSortDropdown = false;
    },

    sortBy(field, direction) {
      this.currentSort = { field, direction };
      this.showSortDropdown = false;
      
      let sortedCategories = [...this.sortedCategories];
      
      switch (field) {
        case 'cards':
          sortedCategories.sort((a, b) => {
            const countA = a.count || 0;
            const countB = b.count || 0;
            return direction === 'asc' ? countA - countB : countB - countA;
          });
          break;
        
        case 'rarity':
          sortedCategories.sort((a, b) => {
            // For "All Cards" and "Shop" categories, keep them at the top
            const isASpecial = a.name.toLowerCase().includes('all') || a.name.toLowerCase().includes('shop');
            const isBSpecial = b.name.toLowerCase().includes('all') || b.name.toLowerCase().includes('shop');
            
            if (isASpecial && !isBSpecial) return -1;
            if (!isASpecial && isBSpecial) return 1;
            if (isASpecial && isBSpecial) {
              // Both are special categories, sort them by name
              return a.name.localeCompare(b.name);
            }
            
            // Both are rarity categories, sort by rarity order
            const rarityA = this.rarityOrder[a.name] || 999;
            const rarityB = this.rarityOrder[b.name] || 999;
            return direction === 'asc' ? rarityA - rarityB : rarityB - rarityA;
          });
          break;
        
        case 'name':
          sortedCategories.sort((a, b) => {
            const nameA = a.name?.toLowerCase() || '';
            const nameB = b.name?.toLowerCase() || '';
            if (direction === 'asc') {
              return nameA.localeCompare(nameB);
            } else {
              return nameB.localeCompare(nameA);
            }
          });
          break;
        
        default:
          // Default sorting (original order)
          sortedCategories = [...this.sortedCategories];
          break;
      }
      
      this.filteredCategories = sortedCategories;
    }
  },
  async mounted() {
    // Initialize debounced search
    this.debouncedSearch = debounce(this.performSearch, 300);
    
    try {
      await this.fetchCategories();
      await this.fetchRarityNewestCards(); // Fetch newest cards for rarity categories
      await this.fetchAllCategoriesNewestCards(); // Fetch newest cards for all categories
      
      // Initialize filtered categories with all sorted categories
      this.filteredCategories = [...this.sortedCategories];
      
      console.log('Categories after fetch:', this.categories);
      console.log('Sorted categories:', this.sortedCategories);
      console.log('Rarity categories:', this.rarityCategories);
    } catch (error) {
      console.error('Failed to fetch categories:', error);
      // Continue even if one of the API calls fails
    }
  }
}
</script>