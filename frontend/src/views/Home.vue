<template>
  <div>
    <div class="background-container"></div>
    <img src="/logo_noph.png" alt="Logo" class="background-logo">
    <hr class="separator-line">
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

</template>

<style scoped>
.background-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 400px; /* Adjust height as needed */
  background-image: url('/background.jpg');
  background-size: cover;
  background-position: center 57%; /* Position the vertical center 80% down from the top, center horizontally */
  z-index: 1; /* Ensure it's behind the content */
}

.background-logo {
  position: absolute;
  top: 100px;
  left: 50%;
  transform: translate(-50%, 0);
  max-width: 250px; /* Adjust size as needed */
  max-height: 250px; /* Adjust size as needed */
  z-index: 1; /* Ensure it's behind the content */
}

.separator-line {
  position: relative;
  margin-top: 370px; /* Adjust to be below the background image */
  height: 2px;
  background-color: white;
  border: none;
  z-index: 2; /* Ensure it's above the background */
  width: 75%;
}

#seasons-container {
  position: relative; /* Essential for z-index to work correctly relative to the background */
  margin-top: 30px; /* Push content down by the height of the background */
  z-index: 2; /* Ensure content is above the background */
  /* Add other styles for your seasons container here */
  padding-bottom: 50px;
}
.error-message {
  text-align: center;
  margin: 50px 0;
  color: #ff5555; /* Red color for errors */
}

page-container {
  position: relative;
  min-height: 100vh;
}

.content-wrapper {
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 400px); /* Учитываем высоту хедера */
}

#seasons-container {
  flex: 1; /* Занимает все доступное пространство */
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
/* Добавляем отступ для основного контента */
#seasons-container {
  padding-bottom: 0px; /* Чтобы контент не перекрывался кнопкой */
}

</style>

<script>
import Season from '@/components/Season.vue'
import { mapActions, mapState, mapMutations } from 'vuex' // Import mapMutations

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
    ...mapMutations(['REMOVE_SEASON']), // Add mapMutations
    navigateToCard(cardId) { // Deprecated - use @card-clicked on card component directly
      this.$router.push(`/card/${cardId}`);
    },
    updateUserAllowedStatus(isAllowed) {
      console.log('Received user allowed status:', isAllowed);
      this.isUserAllowed = isAllowed;
    },
    navigateToAddCard() {
      // Реализуйте навигацию к странице добавления карточки
      // this.$router.push('/add-card'); // This method seems unused based on template. Leaving as comment.
    },
    async navigateToAddSeason() {
      try {
        // Assuming createSeason is imported from your api file
        const { createSeason } = await import('@/api'); // Import dynamically if not already imported
        const newSeason = await createSeason();
        console.log('New season created:', newSeason);
        await this.fetchSeasons(); // Refresh the list of seasons
        // Removed automatic navigation after season creation
        // this.$router.push(`/season/${newSeason.uuid}`); // Navigate to the new season's page
      } catch (error) {
        console.error('Error creating new season:', error);
        alert('Failed to create new season.'); // Provide user feedback
      }
    }
    ,
    // Add a new method to handle season deletion
    handleSeasonDeleted(deletedSeasonUuid) {
      // Call the mutation to remove the season from the VueX store
      this.REMOVE_SEASON(deletedSeasonUuid);
    }
  },
  mounted() {
    this.fetchSeasons()
  },
  // Add a new method to handle season deletion
  handleSeasonDeleted(deletedSeasonUuid) {
    // Call the mutation to remove the season from the VueX store
    this.REMOVE_SEASON(deletedSeasonUuid);
  }
}
</script>