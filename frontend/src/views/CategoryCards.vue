<template>
  <div class="category-cards-page">
    <!-- Background container -->
    <div class="background-container"></div>
    
    <div class="page-header">
      <!-- Centered category title and info -->
      <div class="category-header-content">
        <h1 class="category-title">{{ categoryName }}</h1>
        <div class="category-info">
          <span class="card-count">{{ cards.length }} cards</span>
        </div>
        
        <!-- Search Bar -->
        <div class="search-container">
          <div class="search-input-wrapper">
            <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
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
      </div>
    </div>

    <div class="cards-container-wrapper">
      <div v-if="loading" class="loading-spinner-container">
        <div class="loading-spinner"></div>
      </div>
      
      <!-- Cards container with border -->
      <div class="cards-section-container">
        <!-- Line above cards container - centered -->
        <div class="cards-divider-wrapper">
          <div class="cards-divider"></div>
        </div>
      
        <div class="cards-container">
          <Card
            v-for="card in filteredCards"
            :key="card.id"
            :card="card || {}"
            @card-clicked="handleCardClicked"
            class="card-item"
          />
          <div v-if="!loading && filteredCards.length === 0" class="no-cards-message">
            {{ searchQuery ? 'No cards match your search' : 'No cards found in this category' }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Card from '@/components/Card.vue'
import { fetchCardsByCategory } from '@/api'

export default {
  name: 'CategoryCards',
  components: {
    Card
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
      searchTimeout: null
    }
  },
  async created() {
    await this.loadCategoryCards()
  },
  watch: {
    categoryId: {
      handler: 'loadCategoryCards',
      immediate: false
    }
  },
  methods: {
    async loadCategoryCards() {
      this.loading = true
      try {
        const response = await fetchCardsByCategory(this.categoryId)
        this.cards = response.cards
        this.filteredCards = [...this.cards]
        this.categoryName = this.getCategoryName(this.categoryId)
        this.searchQuery = '' // Reset search when category changes
        console.log('Loaded category cards:', this.cards)
      } catch (err) {
        this.error = err
        console.error('Error loading category cards:', err)
      } finally {
        this.loading = false
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
      this.$router.push(`/card/${cardId}`)
    },
    
    handleSearch() {
      // Debounce the search to reduce lag
      if (this.searchTimeout) {
        clearTimeout(this.searchTimeout)
      }
      
      this.searchTimeout = setTimeout(() => {
        if (!this.searchQuery.trim()) {
          this.filteredCards = [...this.cards]
          return
        }
        
        const query = this.searchQuery.toLowerCase().trim()
        this.filteredCards = this.cards.filter(card => 
          card.name?.toLowerCase().includes(query) ||
          card.rarity?.toLowerCase().includes(query)
        )
      }, 100) // Reduced to 100ms for better responsiveness
    },
    
    clearSearch() {
      this.searchQuery = ''
      this.filteredCards = [...this.cards]
    }
  }
}
</script>

<style scoped>
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

/* Search Container */
.search-container {
  width: 100%;
  max-width: 950px;
  margin: 0 auto;
}

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
}

.search-icon {
  position: absolute;
  left: 15px;
  color: var(--text-color);
  opacity: 0.7;
  z-index: 2;
}

.search-input {
  width: 100%;
  padding: 15px 45px 15px 45px;
  background: var(--card-bg);
  border: 1px solid #333;
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
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: var(--accent-color);
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.cards-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  column-gap: 30px;
  row-gap: 20px; /* Added some row gap for better spacing */
  justify-items: center;
}

.card-item {
  width: 100%;
  max-width: 220px;
  /* Optimized transitions - only opacity for better performance */
  transition: opacity 0.3s ease;
}

/* Smooth fade in/out for search */
.card-item {
  animation: fadeInUp 0.4s ease forwards;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(15px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Stagger the animations for initial load only */
.card-item:nth-child(1) { animation-delay: 0.05s; }
.card-item:nth-child(2) { animation-delay: 0.08s; }
.card-item:nth-child(3) { animation-delay: 0.11s; }
.card-item:nth-child(4) { animation-delay: 0.14s; }
.card-item:nth-child(5) { animation-delay: 0.17s; }
.card-item:nth-child(6) { animation-delay: 0.2s; }
.card-item:nth-child(7) { animation-delay: 0.23s; }
.card-item:nth-child(8) { animation-delay: 0.26s; }
.card-item:nth-child(9) { animation-delay: 0.29s; }
.card-item:nth-child(10) { animation-delay: 0.32s; }
.card-item:nth-child(11) { animation-delay: 0.35s; }
.card-item:nth-child(12) { animation-delay: 0.38s; }

/* For search transitions, use a simpler fade */
.cards-container {
  /* This enables smooth grid transitions */
  transition: grid-template-rows 0.3s ease;
}

.no-cards-message {
  grid-column: 1 / -1;
  text-align: center;
  color: var(--text-color);
  opacity: 0.7;
  font-size: 1.2rem;
  padding: 40px 0;
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 0.7; }
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
  
  .search-container {
    max-width: 400px;
  }
  
  .search-input {
    padding: 12px 40px 12px 40px;
    font-size: 0.9rem;
  }
  
  .cards-section-container {
    padding: 15px;
  }
  
  .cards-container {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 15px;
  }
  
  .card-item {
    max-width: 160px;
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
    max-width: none;
  }
  
  .category-title {
    font-size: 1.5rem;
  }
  
  .category-info {
    margin-bottom: 15px;
  }
  
  .search-container {
    max-width: 100%;
  }
  
  .cards-section-container {
    padding: 10px;
  }
  
  .cards-divider-wrapper {
    margin: 30px 0 12px 0;
  }
}
</style>