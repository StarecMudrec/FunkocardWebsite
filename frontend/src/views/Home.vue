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
      <h1 class="categories-title">Categories : </h1>
      
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

      <div 
        id="categories-container" 
        class="categories-grid-container"
        :class="{ 'search-active': searchQuery }"
        :style="{ height: containerHeight }"
        ref="categoriesContainer"
      >
        <div v-if="loading" class="loading">Loading categories...</div>
        <div v-else-if="error" class="error-message">Error loading data: {{ error.message || error }}. Please try again later.</div>
        <div v-else-if="filteredCategories.length === 0" class="no-categories-message">
          {{ searchQuery ? 'No categories match your search' : 'No categories found' }}
        </div>
        
        <!-- Category Cards -->
        <transition-group 
          name="search-animation" 
          tag="div" 
          class="categories-grid-transition"
          @before-enter="onBeforeEnter"
          @after-enter="onAfterEnter"
          @before-leave="onBeforeLeave"
        >
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

@media (max-width: 768px) {
  .funko-text {
    font-size: 4rem;
    letter-spacing: 2px;
  }
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

/* Search Container */
.search-container {
  display: flex;
  justify-content: center;
  width: 100%;
  max-width: 800px;
  margin: 30px auto 0;
}

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
}

.search-icon {
  position: absolute;
  left: 20px;
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

.no-categories-message {
  text-align: center;
  color: var(--text-color);
  opacity: 0.7;
  font-size: 1.2rem;
  padding: 40px 0;
  grid-column: 1 / -1;
}

/* Categories Grid Container with smooth height transitions */
.categories-grid-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  row-gap: 40px;
  column-gap: 67px;
  padding: 30px 20px;
  max-width: 1200px;
  margin: 0 auto;
  margin-top: 50px;
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  min-height: 200px; /* Minimum height to prevent jarring transitions */
  overflow: hidden;
  position: relative;
  height: auto; /* Default height */
  transition: height 0.5s cubic-bezier(0.4, 0, 0.2, 1), 
              grid-template-columns 0.3s ease,
              padding 0.3s ease;
}

/* When search is active, we'll use auto-fit for better responsiveness */
.categories-grid-container.search-active {
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
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

/* Responsive adjustments */
@media (max-width: 768px) {
  .categories-grid-container {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    padding: 20px 15px;
    gap: 15px;
    margin-top: 30px;
  }
  
  .categories-grid-container.search-active {
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  }
  
  .category-card__content {
    padding: 15px;
  }
  
  .category-card__title {
    font-size: 1.1rem;
  }
  
  .cover-arrow {
    width: 210px;
    height: 165px;
    bottom: 20px;
  }
  
  .arrow-icon {
    width: 108px;
    height: 108px;
  }

  .search-container {
    max-width: 90%;
    margin: 20px auto 0;
  }

  .search-input {
    padding: 12px 40px 12px 45px;
    font-size: 1rem;
  }

  .search-icon {
    left: 15px;
  }
}

@media (max-width: 480px) {
  .categories-grid-container {
    grid-template-columns: 1fr;
    padding: 15px 10px;
    margin-top: 20px;
  }
  
  .categories-grid-container.search-active {
    grid-template-columns: 1fr;
  }

  .search-input {
    padding: 10px 35px 10px 40px;
    font-size: 0.9rem;
  }

  .search-icon {
    left: 12px;
  }
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

export default {
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
      isAnimating: false,
      containerHeight: 'auto',
      resizeObserver: null
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
  watch: {
    filteredCategories: {
      handler() {
        // Update container height when categories change
        this.$nextTick(() => {
          setTimeout(() => this.updateContainerHeight(), 50);
        });
      },
      deep: true
    },
    
    searchQuery() {
      // Update container height when search query changes
      this.$nextTick(() => {
        setTimeout(() => this.updateContainerHeight(), 100);
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

    // Animation lifecycle methods
    onBeforeEnter() {
      this.isAnimating = true;
    },

    onAfterEnter() {
      this.isAnimating = false;
    },

    onBeforeLeave() {
      this.isAnimating = true;
    },
    
    updateContainerHeight() {
      this.$nextTick(() => {
        const container = this.$refs.categoriesContainer;
        if (!container) return;
        
        // Calculate the height of the content
        const contentHeight = container.scrollHeight;
        
        // Only update if height has changed significantly (more than 5px)
        // This prevents unnecessary transitions during small layout shifts
        const currentHeight = parseInt(this.containerHeight) || 0;
        if (Math.abs(contentHeight - currentHeight) > 5) {
          this.containerHeight = `${contentHeight}px`;
        }
      });
    },
    
    setupResizeObserver() {
      // Use ResizeObserver to detect when content height changes
      if (typeof ResizeObserver !== 'undefined') {
        this.resizeObserver = new ResizeObserver(() => {
          this.updateContainerHeight();
        });
        
        const container = this.$refs.categoriesContainer;
        if (container) {
          this.resizeObserver.observe(container);
        }
      }
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
    
    // Initialize container height
    this.$nextTick(() => {
      this.updateContainerHeight();
      this.setupResizeObserver();
    });
  },
  
  beforeDestroy() {
    // Clean up ResizeObserver
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
    }
  }
}
</script>