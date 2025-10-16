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
      <div id="categories-container" class="categories-grid">
        <div v-if="loading" class="loading">Loading categories...</div>
        <div v-else-if="error" class="error-message">Error loading data: {{ error.message || error }}. Please try again later.</div>
        <div v-else-if="sortedCategories.length === 0" class="loading">No categories found</div>
        
        <!-- Category Cards -->
        <div 
          v-for="(category, index) in sortedCategories" 
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

.categories-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  row-gap: 40px;
  column-gap: 67px;
  padding: 30px 20px;
  max-width: 1200px;
  margin: 0 auto;
  margin-top: 100px;
}

.category-card {
  border-radius: 12px;
  box-shadow: 2px 7px 10px 2px rgba(0, 0, 0, 0.4);
  cursor: pointer;
  transition: all 0.3s ease;
  overflow: hidden;
  aspect-ratio: 0.8;
  position: relative;
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
  filter: blur(8px); /* Apply same blur as rarity cards */
}

/* Apply specific backgrounds and blur effects */
.category-card.all-cards .category-card__background {
  background-image: url('/All.png');
  filter: blur(5px);
}

.category-card.shop .category-card__background {
  background-image: url('/shop.png');
  filter: blur(5px); /* No blur for shop category */
}

.category-card.rarity .category-card__background,
.category-card.rarity .category-card__video {
  background-size: cover;
  background-position: center;
  filter: blur(8px); /* Stronger blur for rarity cards */
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
  transform: scale(1.05);
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
  text-shadow: 0px 7px 10px rgba(0, 0, 0, 0.7);
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
  .categories-grid {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    padding: 20px 15px;
    gap: 15px;
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
}

@media (max-width: 480px) {
  .categories-grid {
    grid-template-columns: 1fr;
  }
}
</style>

<script>
import { mapActions, mapState } from 'vuex'

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
      rarityNewestCards: {} // Store newest card images for each rarity
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
    
    navigateToCategory(category) {
      console.log('Navigating to category:', category);
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
      const newestCard = this.rarityNewestCards[category.name];
      if (newestCard && newestCard.photo) {
        return `/api/card_image/${newestCard.photo}`;
      }
      return null;
    },
    
    getCategoryBackgroundStyle(category) {
      const name = category.name.toLowerCase();
      
      // For rarity categories (except Limited), use the newest card image
      if (!name.includes('all') && !name.includes('general') && !name.includes('shop') && category.name !== 'Limited ⚠️') {
        const newestCard = this.rarityNewestCards[category.name];
        if (newestCard && newestCard.photo) {
          return {
            backgroundImage: `url(/api/card_image/${newestCard.photo})`
          };
        }
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
    }
  },
  async mounted() {
    try {
      await this.fetchCategories();
      await this.fetchRarityNewestCards(); // Fetch newest cards after categories
      console.log('Categories after fetch:', this.categories);
      console.log('Sorted categories:', this.sortedCategories);
      console.log('Rarity categories:', this.rarityCategories);
    } catch (error) {
      console.error('Failed to fetch categories:', error);
    }
  }
}
</script>