<template>
  <div class="page-container">
    <!-- Hero section with background and scroll arrow -->
    <div class="hero-section">
      <div class="background-container"></div>
      <img src="/logo_noph.png" alt="Logo" class="background-logo">
      <div class="cover-arrow" @click="scrollToContent">
        <div class="cover-arrow__inner">
          <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="7.5 11 9 4" fill="white" width="24px" height="24px">
            <defs>
              <filter id="arrowShadow" x="-20%" y="-20%" width="140%" height="150%">
                <feDropShadow dx="0" dy="0.5" stdDeviation="0.5" flood-color="rgba(0,0,0,0.3)"/>
                <feDropShadow dx="0" dy="0" stdDeviation="0.2" flood-color="rgba(0,0,0,0.15)"/>
              </filter>
            </defs>
            <path class="arrow-path" fill="white" filter="url(#arrowShadow)" d="M9 11l3 3 3-3c.2-.2.5-.2.7 0 .2.2.2.5 0 .7l-3.5 3.5c-.2.2-.5.2-.7 0L8.3 11.7c-.2-.2-.2-.5 0-.7.2-.2.5-.2.7 0z"/>
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
  background-size: cover;
  background-position: center 57%;
  z-index: -1;
}

.background-logo {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  max-width: 250px;
  max-height: 250px;
  z-index: 1;
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
  width: 85px;
  height: 67px;
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
  width: 100%;
  height: 100%;
  shape-rendering: geometricPrecision;
  transition: all 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  will-change: transform;
  pointer-events: none;
}

.cover-arrow:hover .arrow-icon {
  transform: scale(0.85);
  opacity: 0.9;
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
    width: 70px;
    height: 55px;
    bottom: 20px;
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