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
      <div class="multi-card-container" ref="multiCardContainer">
        <!-- Previous Card -->
        <div 
          class="card-page previous-card" 
          :class="{ 'hidden': !hasPreviousCard }"
          @click="scrollToCard(currentCardIndex - 1)"
        >
          <CardDetailContainer 
            v-if="cardsData[currentCardIndex - 1]"
            :card="cardsData[currentCardIndex - 1]"
            :is-active="false"
          />
        </div>

        <!-- Current Card -->
        <div class="card-page current-card" ref="currentCard">
          <CardDetailContainer 
            v-if="cardsData[currentCardIndex]"
            :card="cardsData[currentCardIndex]"
            :is-active="true"
            @media-double-click="handleMediaDoubleClick"
            @go-back="goBackToCategory"
          />
        </div>

        <!-- Next Card -->
        <div 
          class="card-page next-card" 
          :class="{ 'hidden': !hasNextCard }"
          @click="scrollToCard(currentCardIndex + 1)"
        >
          <CardDetailContainer 
            v-if="cardsData[currentCardIndex + 1]"
            :card="cardsData[currentCardIndex + 1]"
            :is-active="false"
          />
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
    const multiCardContainer = ref(null)
    const currentCard = ref(null)

    const cardsData = ref([]) // Array to hold current and adjacent cards
    const loading = ref(true)
    const error = ref(null)
    const saveError = ref(null)
    const isUserAllowed = ref(false)

    // Card navigation
    const sortedCards = ref([])
    const currentCardIndex = ref(-1)
    const isScrolling = ref(false)

    const isFirstCard = computed(() => currentCardIndex.value <= 0)
    const isLastCard = computed(() => currentCardIndex.value >= sortedCards.value.length - 1)
    const hasPreviousCard = computed(() => currentCardIndex.value > 0)
    const hasNextCard = computed(() => currentCardIndex.value < sortedCards.value.length - 1)

    const findCurrentCardIndex = () => {
      if (!props.id || !sortedCards.value.length) return -1
      return sortedCards.value.findIndex(c => c.id.toString() === props.id.toString())
    }

    const getCategoryDisplayName = () => {
      const previousCategory = sessionStorage.getItem('previousCategory')
      if (previousCategory) {
        if (previousCategory === 'all') return 'All Cards'
        if (previousCategory === 'shop') return 'Available at Shop'
        if (previousCategory.startsWith('rarity_')) {
          return previousCategory.replace('rarity_', '')
        }
        return previousCategory
      } else {
        return cardsData.value[currentCardIndex.value]?.category || 'Category'
      }
    }

    const loadSortedCards = async () => {
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
        
        const categoryId = previousCategory || `rarity_${cardsData.value[currentCardIndex.value]?.category}`
        console.log('Loading cards for category ID:', categoryId, 'with sort:', sortField, sortDirection)
        
        const response = await fetchCardsByCategory(categoryId, sortField, sortDirection)
        sortedCards.value = response.cards || []
        currentCardIndex.value = findCurrentCardIndex()
        
        console.log('Loaded cards by category:', sortedCards.value.length)
        console.log('Current card index:', currentCardIndex.value)
        
        // Load current and adjacent cards
        await loadCurrentAndAdjacentCards()
      } catch (error) {
        console.error('Error loading sorted cards by category:', error)
        sortedCards.value = []
      }
    }

    const loadCurrentAndAdjacentCards = async () => {
      if (!sortedCards.value.length || currentCardIndex.value === -1) return

      const cardsToLoad = []

      // Previous card
      if (currentCardIndex.value > 0) {
        cardsToLoad.push({
          index: currentCardIndex.value - 1,
          cardId: sortedCards.value[currentCardIndex.value - 1].id
        })
      }

      // Current card
      cardsToLoad.push({
        index: currentCardIndex.value,
        cardId: sortedCards.value[currentCardIndex.value].id
      })

      // Next card
      if (currentCardIndex.value < sortedCards.value.length - 1) {
        cardsToLoad.push({
          index: currentCardIndex.value + 1,
          cardId: sortedCards.value[currentCardIndex.value + 1].id
        })
      }

      try {
        const loadPromises = cardsToLoad.map(async ({ index, cardId }) => {
          // Only load if not already loaded or if it's a different card
          if (!cardsData.value[index] || cardsData.value[index].id !== cardId) {
            const cardData = await fetchCardInfo(cardId)
            cardsData.value[index] = cardData
          }
        })

        await Promise.all(loadPromises)
      } catch (err) {
        console.error('Error loading adjacent cards:', err)
      }
    }

    const scrollToCard = async (targetIndex) => {
      if (isScrolling.value || targetIndex < 0 || targetIndex >= sortedCards.value.length) return

      isScrolling.value = true

      // Update URL without triggering navigation
      const newCardId = sortedCards.value[targetIndex].id
      window.history.replaceState({}, '', `/card/${newCardId}`)

      // Update current index
      currentCardIndex.value = targetIndex

      // Load new adjacent cards
      await loadCurrentAndAdjacentCards()

      // Reset scroll position
      if (multiCardContainer.value) {
        multiCardContainer.value.scrollLeft = multiCardContainer.value.clientWidth
      }

      // Allow time for DOM update and scrolling
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
        if (cardsData.value[currentCardIndex.value]?.category) {
          const categoryId = `rarity_${cardsData.value[currentCardIndex.value].category}`
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

    const handleFileChange = async (event) => {
      const file = event.target.files[0]
      if (!file || !isUserAllowed.value) return

      const formData = new FormData()
      formData.append('image', file)

      try {
        const currentCardData = cardsData.value[currentCardIndex.value]
        const response = await fetch(`/api/cards/${currentCardData.id}/image`, {
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
        const updatedCard = await fetchCardInfo(currentCardData.id)
        cardsData.value[currentCardIndex.value] = updatedCard
      } catch (err) {
        console.error('Error uploading image:', err)
      }
    }

    const loadData = async () => {
      try {
        loading.value = true
        
        // Load initial card
        const initialCard = await fetchCardInfo(props.id)
        
        // Initialize cardsData with the initial card
        cardsData.value = []
        currentCardIndex.value = 0
        
        // Load sorted cards for navigation
        await loadSortedCards()
        
        // Check user permissions
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

      // Initialize scroll position after mount
      nextTick(() => {
        if (multiCardContainer.value) {
          multiCardContainer.value.scrollLeft = multiCardContainer.value.clientWidth
        }
      })
    })

    onUnmounted(() => {
      // Cleanup if needed
    })

    watch(() => props.id, async (newId) => {
      if (newId) {
        await loadData()
      }
    })

    return {
      cardsData,
      loading,
      error,
      saveError,
      isUserAllowed,
      fileInput,
      multiCardContainer,
      currentCard,
      isFirstCard,
      isLastCard,
      hasPreviousCard,
      hasNextCard,
      goToPreviousCard,
      goToNextCard,
      scrollToCard,
      goBackToCategory,
      handleMediaDoubleClick,
      handleFileChange,
      getCategoryDisplayName
    }
  }
}
</script>

<style scoped>
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

.multi-card-container {
  display: flex;
  width: 100%;
  height: 100%;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  scroll-behavior: smooth;
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.multi-card-container::-webkit-scrollbar {
  display: none;
}

.card-page {
  flex: 0 0 100%;
  width: 100%;
  height: 100%;
  scroll-snap-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  box-sizing: border-box;
  position: relative;
}

.card-page.previous-card,
.card-page.next-card {
  cursor: pointer;
  opacity: 0.7;
  transition: opacity 0.3s ease;
}

.card-page.previous-card:hover,
.card-page.next-card:hover {
  opacity: 0.9;
}

.card-page.hidden {
  opacity: 0;
  pointer-events: none;
}

.card-page.current-card {
  opacity: 1;
}

/* Keep all your existing styles below */
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
}
</style>