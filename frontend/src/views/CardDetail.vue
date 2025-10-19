<template>
  <div class="fixed-container">
    <div class="background-container"></div>
    <div class="card-detail-wrapper">
      <!-- Left Arrow -->
      <div 
        class="nav-arrow left-arrow" 
        :class="{ 'disabled': isFirstCard }"
        @click="goToPreviousCard"
      >
        <div class="arrow-icon-wrapper">
          <svg class="arrow-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M15 20.1L6.9 12 15 3.9z"/>
          </svg>
        </div>
      </div>

      <div v-if="loading" class="loading-overlay">
        <div class="loading-content">
          <svg class="spinner" viewBox="0 0 50 50">
            <circle class="path" cx="25" cy="25" r="20" fill="none" stroke-width="5"></circle>
          </svg>
          <div class="loading-text">Loading card details...</div>
        </div>
      </div>
      <div v-if="error" class="loading-overlay error-overlay">
        <div class="loading-content">
          <svg class="error-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div class="loading-text error-text">Error loading card: {{ error }}</div>
        </div>
      </div>

      <!-- Multi-card container -->
      <div class="multi-card-viewport" ref="multiCardViewport">
        <div class="multi-card-container" ref="multiCardContainer" :style="containerStyle">
          <!-- Previous Card -->
          <div class="card-page previous-card">
            <CardDetailContainer 
              v-if="displayedCards.previous"
              :card="displayedCards.previous"
              :is-active="false"
            />
            <div v-else class="empty-card-placeholder"></div>
          </div>

          <!-- Current Card -->
          <div class="card-page current-card">
            <CardDetailContainer 
              v-if="displayedCards.current"
              :card="displayedCards.current"
              :is-active="true"
              @media-double-click="handleMediaDoubleClick"
              @go-back="goBackToCategory"
              @save-error="handleSaveError"
            />
            <div v-else class="empty-card-placeholder"></div>
          </div>

          <!-- Next Card -->
          <div class="card-page next-card">
            <CardDetailContainer 
              v-if="displayedCards.next"
              :card="displayedCards.next"
              :is-active="false"
            />
            <div v-else class="empty-card-placeholder"></div>
          </div>
        </div>
      </div>

      <div v-if="saveError" class="error-message">{{ saveError }}</div>
      
      <!-- Right Arrow -->
      <div 
        class="nav-arrow right-arrow" 
        :class="{ 'disabled': isLastCard }"
        @click="goToNextCard"
      >
        <div class="arrow-icon-wrapper">
          <svg class="arrow-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M9 3.9L17.1 12 9 20.1z"/>
          </svg>
        </div>
      </div>
    </div>
    <input type="file" ref="fileInput" @change="handleFileChange" accept="image/*" style="display: none;">
  </div>
</template>

<script>
import { fetchCardInfo, checkUserPermission, fetchUserInfo, fetchCardsByCategory } from '@/api'
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import CardDetailContainer from './CardDetailContainer.vue'

export default {
  props: {
    id: {
      type: String,
      required: true
    }
  },
  components: {
    CardDetailContainer
  },
  setup(props) {
    const router = useRouter()
    const fileInput = ref(null)

    const loading = ref(true)
    const error = ref(null)
    const saveError = ref(null)
    const isUserAllowed = ref(false)

    // Card navigation
    const allCards = ref([]) // All cards in the current category
    const currentCardIndex = ref(0)
    const isScrolling = ref(false)
    
    // Store displayed cards separately to ensure reactivity
    const displayedCards = ref({
      previous: null,
      current: null,
      next: null
    })

    const isFirstCard = computed(() => currentCardIndex.value <= 0)
    const isLastCard = computed(() => currentCardIndex.value >= allCards.value.length - 1)

    const containerStyle = computed(() => ({
      transform: `translateX(-${currentCardIndex.value * 100}vw)`,
      transition: isScrolling.value ? 'transform 0.3s ease' : 'none'
    }))

    const findCurrentCardIndex = () => {
      if (!props.id || !allCards.value.length) return 0
      const index = allCards.value.findIndex(c => c.id.toString() === props.id.toString())
      return index >= 0 ? index : 0
    }

    const updateDisplayedCards = () => {
      console.log('Updating displayed cards, current index:', currentCardIndex.value)
      
      displayedCards.value = {
        previous: currentCardIndex.value > 0 ? allCards.value[currentCardIndex.value - 1] : null,
        current: allCards.value[currentCardIndex.value] || null,
        next: currentCardIndex.value < allCards.value.length - 1 ? allCards.value[currentCardIndex.value + 1] : null
      }
      
      console.log('Displayed cards updated:', {
        previous: displayedCards.value.previous?.name,
        current: displayedCards.value.current?.name,
        next: displayedCards.value.next?.name
      })
    }

    const loadAllCards = async () => {
      try {
        const previousCategory = sessionStorage.getItem('previousCategory')
        const savedSortState = sessionStorage.getItem(`category_state_${previousCategory}`)
        
        let sortField = 'id'
        let sortDirection = 'asc'
        
        if (savedSortState) {
          try {
            const state = JSON.parse(savedSortState)
            if (state.currentSort) {
              sortField = state.currentSort.field
              sortDirection = state.currentSort.direction
            }
          } catch (e) {
            console.warn('Failed to parse saved sort state:', e)
          }
        }
        
        const categoryId = previousCategory
        console.log('Loading cards for category ID:', categoryId, 'with sort:', sortField, sortDirection)
        
        const response = await fetchCardsByCategory(categoryId, sortField, sortDirection)
        allCards.value = response.cards || []
        
        console.log('Loaded all cards:', allCards.value.length)
        console.log('All cards:', allCards.value.map(c => ({ id: c.id, name: c.name })))
        
        // Find current card index
        currentCardIndex.value = findCurrentCardIndex()
        console.log('Current card index:', currentCardIndex.value)
        
        // Update displayed cards immediately with basic data
        updateDisplayedCards()
        
        // Load detailed info for current and adjacent cards
        await loadDetailedCardInfo()
        
      } catch (error) {
        console.error('Error loading all cards:', error)
        allCards.value = []
      }
    }

    const loadDetailedCardInfo = async () => {
      if (!allCards.value.length) return

      const cardsToLoad = []

      // Always load current card
      if (displayedCards.value.current) {
        cardsToLoad.push(displayedCards.value.current.id)
      }

      // Load previous card if exists
      if (displayedCards.value.previous) {
        cardsToLoad.push(displayedCards.value.previous.id)
      }

      // Load next card if exists
      if (displayedCards.value.next) {
        cardsToLoad.push(displayedCards.value.next.id)
      }

      console.log('Loading detailed info for cards:', cardsToLoad)

      try {
        const loadPromises = cardsToLoad.map(async (cardId) => {
          try {
            const detailedCard = await fetchCardInfo(cardId)
            // Update the card in allCards with detailed info
            const index = allCards.value.findIndex(c => c.id === cardId)
            if (index >= 0) {
              // Preserve the original card data and merge with detailed info
              allCards.value[index] = { 
                ...allCards.value[index], 
                ...detailedCard 
              }
              console.log(`Loaded detailed info for card ${cardId}:`, detailedCard.name)
            }
          } catch (err) {
            console.error(`Failed to load detailed info for card ${cardId}:`, err)
            // Keep the basic card info if detailed loading fails
          }
        })

        await Promise.all(loadPromises)
        
        // Update displayed cards with the new detailed data
        updateDisplayedCards()
        
        console.log('Updated allCards with detailed info')
      } catch (err) {
        console.error('Error loading detailed card info:', err)
      }
    }

    const scrollToCard = async (targetIndex) => {
      if (isScrolling.value || targetIndex < 0 || targetIndex >= allCards.value.length) return

      isScrolling.value = true

      // Update URL without triggering navigation
      const newCardId = allCards.value[targetIndex].id
      window.history.replaceState({}, '', `/card/${newCardId}`)

      // Update current index
      currentCardIndex.value = targetIndex

      // Update displayed cards immediately
      updateDisplayedCards()

      // Load detailed info for new adjacent cards
      await loadDetailedCardInfo()

      // Wait for transition to complete
      setTimeout(() => {
        isScrolling.value = false
      }, 300)
    }

    const goToPreviousCard = () => {
      if (isFirstCard.value || isScrolling.value) return
      scrollToCard(currentCardIndex.value - 1)
    }

    const goToNextCard = () => {
      if (isLastCard.value || isScrolling.value) return
      scrollToCard(currentCardIndex.value + 1)
    }

    const goBackToCategory = () => {
      if (router.meta) {
        router.meta.navigationType = 'to-category'
      }
      
      const previousCategory = sessionStorage.getItem('previousCategory')
      if (previousCategory) {
        router.push(`/category/${previousCategory}`)
      } else {
        if (displayedCards.value.current?.category) {
          const categoryId = `rarity_${displayedCards.value.current.category}`
          router.push(`/category/${categoryId}`)
        } else {
          router.go(-1)
        }
      }
    }

    const handleMediaDoubleClick = () => {
      if (isUserAllowed.value && fileInput.value) {
        fileInput.value.click()
      }
    }

    const handleSaveError = (error) => {
      saveError.value = error
    }

    const handleFileChange = async (event) => {
      const file = event.target.files[0]
      if (!file || !isUserAllowed.value) return

      const formData = new FormData()
      formData.append('image', file)

      try {
        const response = await fetch(`/api/cards/${displayedCards.value.current.id}/image`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`
          },
          body: formData
        })

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.error || 'Failed to upload image')
        }

        // Reload current card data
        const updatedCard = await fetchCardInfo(displayedCards.value.current.id)
        const cardIndex = allCards.value.findIndex(c => c.id === displayedCards.value.current.id)
        if (cardIndex >= 0) {
          allCards.value[cardIndex] = updatedCard
          updateDisplayedCards()
        }
      } catch (err) {
        console.error('Error uploading image:', err)
        saveError.value = err.message
      }
    }

    const checkUserPermissions = async () => {
      try {
        const userInfo = await fetchUserInfo()
        if (userInfo?.username) {
          const permissionResponse = await checkUserPermission(userInfo.username)
          isUserAllowed.value = permissionResponse.is_allowed
        }
      } catch (authError) {
        console.log('User not authenticated, editing disabled')
        isUserAllowed.value = false
      }
    }

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
        
        // Reset data
        allCards.value = []
        currentCardIndex.value = 0
        displayedCards.value = {
          previous: null,
          current: null,
          next: null
        }
        
        console.log('Starting to load data for card ID:', props.id)
        
        // Load all cards first
        await loadAllCards()
        
        // Check user permissions
        await checkUserPermissions()
        
        console.log('Data loading completed')
        console.log('Total cards:', allCards.value.length)
        console.log('Current card index:', currentCardIndex.value)
        console.log('Displayed cards:', displayedCards.value)
        
      } catch (err) {
        error.value = err.message || 'Failed to load card details'
        console.error('Error loading card:', err)
      } finally {
        loading.value = false
      }
    }

    onMounted(() => {
      loadData()
      
      if (router.meta) {
        router.meta.navigationType = 'from-card-detail'
      }
    })

    watch(() => props.id, async (newId) => {
      if (newId) {
        await loadData()
      }
    })

    return {
      displayedCards,
      loading,
      error,
      saveError,
      isUserAllowed,
      fileInput,
      isFirstCard,
      isLastCard,
      containerStyle,
      goToPreviousCard,
      goToNextCard,
      goBackToCategory,
      handleMediaDoubleClick,
      handleSaveError,
      handleFileChange
    }
  }
}
</script>

<style scoped>
/* Your existing styles remain exactly the same */
.fixed-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  height: 100vh;
  width: 100vw;
  font-family: 'Afacad', sans-serif;
  display: flex;
  align-items: center;
  justify-content: center;
}

.multi-card-viewport {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  position: relative;
}

.multi-card-container {
  display: flex;
  width: 300vw; /* 3 viewport widths for 3 cards */
  height: 100%;
  transition: transform 0.3s ease;
}

.card-page {
  flex: 0 0 100vw; /* Each card takes full viewport width */
  width: 100vw;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  box-sizing: border-box;
}

.card-page.previous-card,
.card-page.next-card {
  opacity: 0.3;
  transition: opacity 0.3s ease;
}

.card-page.previous-card:hover,
.card-page.next-card:hover {
  opacity: 0.6;
  cursor: pointer;
}

.card-page.current-card {
  opacity: 1;
}

.empty-card-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  font-size: 18px;
}

.background-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: url('/background.jpg');
  background-size: cover;
  background-position: center 57%;
  z-index: -1;
  filter: blur(10px);
}

.nav-arrow {
  position: fixed;
  top: 50%;
  transform: translateY(-50%);
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 100;
  opacity: 0.5;
  transition: opacity 0.2s ease;
}

.nav-arrow:hover {
  opacity: 1;
}

.nav-arrow.disabled {
  opacity: 0.2;
  pointer-events: none;
  cursor: not-allowed;
}

.left-arrow {
  left: 10px;
}

.right-arrow {
  right: 10px;
}

.arrow-icon-wrapper {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.arrow-icon {
  width: 100%;
  height: 100%;
  fill: var(--accent-color);
  pointer-events: auto;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.loading-text {
  color: white;
  font-size: 20px;
  font-weight: 500;
}

.spinner {
  width: 50px;
  height: 50px;
  animation: rotate 2s linear infinite;
}

.spinner .path {
  stroke: var(--accent-color);
  stroke-linecap: round;
  animation: dash 1.5s ease-in-out infinite;
}

.error-overlay {
  background-color: rgba(0, 0, 0, 0.7);
}

.error-icon {
  width: 50px;
  height: 50px;
  color: #ff4444;
}

.error-text {
  color: #ff6b6b;
}

.error-message {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(255, 107, 107, 0.9);
  color: white;
  padding: 10px 20px;
  border-radius: 5px;
  z-index: 1000;
  max-width: 80%;
  text-align: center;
}

@keyframes rotate {
  100% {
    transform: rotate(360deg);
  }
}

@keyframes dash {
  0% {
    stroke-dasharray: 1, 150;
    stroke-dashoffset: 0;
  }
  50% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -35;
  }
  100% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -124;
  }
}

/* Add responsive design */
@media (max-width: 768px) {
  .card-page {
    padding: 10px;
  }
  
  .nav-arrow {
    height: 60px;
  }
  
  .left-arrow {
    left: 5px;
  }
  
  .right-arrow {
    right: 5px;
  }
  
  .arrow-icon-wrapper {
    width: 30px;
    height: 30px;
  }
  
  .multi-card-container {
    width: 300vw;
  }
  
  .card-page {
    flex: 0 0 100vw;
  }
}
</style>