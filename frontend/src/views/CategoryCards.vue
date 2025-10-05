<template>
  <div class="category-cards-page">
    <!-- Background container -->
    <div class="background-container"></div>
    
    <div class="page-header">
      <!-- <button @click="$router.back()" class="back-button">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        Back to Categories
      </button> -->
      
      <!-- Centered category title and info -->
      <div class="category-header-content">
        <h1 class="category-title">{{ categoryName }}</h1>
        <div class="category-info">
          <span class="card-count">{{ cards.length }} cards</span>
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
            v-for="card in cards"
            :key="card.id"
            :card="card || {}"
            @card-clicked="handleCardClicked"
            class="card-item"
          />
          <div v-if="!loading && cards.length === 0" class="no-cards-message">
            No cards found in this category
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
      loading: false,
      error: null,
      categoryName: ''
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
        this.categoryName = this.getCategoryName(this.categoryId)
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
  margin: 167px auto 100px;
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
}

.card-count {
  color: var(--text-color);
  opacity: 0.8;
  font-size: 1.1rem;
  text-shadow: 0px 3px 5px rgba(0, 0, 0, 0.27);
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
  row-gap: 0px;
  justify-items: center; /* Center items within grid cells */
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
  
  .cards-section-container {
    padding: 10px;
  }
  
  .cards-divider-wrapper {
    margin: 30px 0 12px 0;
  }
}
</style>