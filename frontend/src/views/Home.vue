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
          <!-- <svg class="arrow-icon" viewBox="0 0 16 16" fill="white">
            <path d="M8 12L3 7l1.5-1.5L8 9l3.5-3.5L13 7l-5 5z" style="fill:white;"/>
          </svg> -->
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
      <div id="seasons-container">
        <div v-if="loading" class="loading">Loading cards...</div>
        <div v-else-if="error" class="error-message">Error loading data: {{ error.message || error }}. Please try again later.</div>
        <div v-else-if="seasons.length === 0" class="loading">No seasons found</div>
        <Season 
          v-for="season in seasons" 
          :key="season.uuid" 
          :season="season" 
          @card-clicked="navigateToCard" deprecated
          @add-card="navigateToAddCard"
          @emitUserAllowedStatus="updateUserAllowedStatus"
          @season-deleted="handleSeasonDeleted"
        />
      </div>
      <div v-if="isUserAllowed" class="add-season-footer">
        <div class="add-new-season-btn" @click="navigateToAddSeason">
          + Add New Season
        </div>
      </div>
      <div>
        <h2>.</h2>
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
  background: linear-gradient(to bottom, #f0e9e100 0%, #e7e2dc 100%);
}

#seasons-container {
  position: relative;
  margin-top: 30px;
  z-index: 2;
  padding-bottom: 50px;
}

.error-message {
  text-align: center;
  margin: 50px 0;
  color: #ff5555;
}

.add-season-footer {
  padding: 20px 0 50px;
  text-align: center;
}

.add-new-season-btn {
  background: var(--card-bg);
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  display: inline-flex;
  justify-content: center;
  align-items: center;
  color: var(--text-color);
  font-size: 1.1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  min-height: 60px;
  padding: 0 30px;
  border: 2px dashed #555;
  margin: 0 auto;
}

.add-new-season-btn:hover {
  transform: translateY(-5px);
  border-color: var(--accent-color);
  color: var(--accent-color);
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
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.4)); /* Добавляем тень */
}

.cover-arrow:hover .arrow-icon {
  transform: scale(0.85);
  opacity: 0.9;
  filter: drop-shadow(0 6px 12px rgba(0, 0, 0, 0.5)); /* Усиливаем тень при hover */
}

.cover-arrow:hover .cover-arrow__inner {
  animation-play-state: paused;
}

.arrow-path {
  transition: fill 0.3s ease;
  transform-origin: center;
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
  .background-logo {
    max-width: 200px;
    max-height: 200px;
  }
  
  .cover-arrow {
    width: 210px; /* 70px * 3 */
    height: 165px; /* 55px * 3 */
    bottom: 20px;
  }
  
  .arrow-icon {
    width: 108px; /* 36px * 3 */
    height: 108px;
  }
}
</style>

<script>
import Season from '@/components/Season.vue'
import { mapActions, mapState, mapMutations } from 'vuex'

export default {
  components: {
    Season
  },
  computed: {
    ...mapState(['seasons', 'loading', 'error'])
  },
  data() {
    return {
      isUserAllowed: false
    };
  },
  methods: {
    ...mapActions(['fetchSeasons']),
    ...mapMutations(['REMOVE_SEASON']),
    
    navigateToCard(cardId) {
      this.$router.push(`/card/${cardId}`);
    },
    
    updateUserAllowedStatus(isAllowed) {
      console.log('Received user allowed status:', isAllowed);
      this.isUserAllowed = isAllowed;
    },
    
    navigateToAddCard() {
      // Реализуйте навигацию к странице добавления карточки
    },
    
    async navigateToAddSeason() {
      try {
        const { createSeason } = await import('@/api');
        const newSeason = await createSeason();
        console.log('New season created:', newSeason);
        await this.fetchSeasons();
      } catch (error) {
        console.error('Error creating new season:', error);
        alert('Failed to create new season.');
      }
    },
    
    handleSeasonDeleted(deletedSeasonUuid) {
      this.REMOVE_SEASON(deletedSeasonUuid);
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
  mounted() {
    this.fetchSeasons()
  }
}
</script>