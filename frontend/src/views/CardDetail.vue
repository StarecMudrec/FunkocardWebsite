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
          <svg width="107" height="107" viewBox="0 0 208 208" fill="none" xmlns="http://www.w3.org/2000/svg">
            <g filter="url(#filter0_d_26_86)">
              <path d="M93.6 104L133.467 143.867L121.333 156L69.3334 104L121.333 52L133.467 64.1333L93.6 104Z" fill="#FEF7FF"/>
            </g>
            <defs>
              <filter id="filter0_d_26_86" x="-4" y="0" width="216" height="216" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB">
                <feFlood flood-opacity="0" result="BackgroundImageFix"/>
                <feColorMatrix in="SourceAlpha" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0" result="hardAlpha"/>
                <feOffset dy="4"/>
                <feGaussianBlur stdDeviation="2"/>
                <feComposite in2="hardAlpha" operator="out"/>
                <feColorMatrix type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.25 0"/>
                <feBlend mode="normal" in2="BackgroundImageFix" result="effect1_dropShadow_26_86"/>
                <feBlend mode="normal" in="SourceGraphic" in2="effect1_dropShadow_26_86" result="shape"/>
              </filter>
            </defs>
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
      <div 
        class="multi-card-viewport" 
        ref="multiCardViewport"
        @touchstart="handleTouchStart"
        @touchmove="handleTouchMove"
        @touchend="handleTouchEnd"
      >
        <div class="multi-card-container" ref="multiCardContainer" :style="containerStyle">
          <!-- Previous Card -->
          <div class="card-page previous-card" ref="previousCard">
            <CardDetailContainer 
              v-if="displayedCards.previous"
              :card="displayedCards.previous"
              :is-active="false"
              ref="previousCardContainer"
            />
            <div v-else class="empty-card-placeholder"></div>
          </div>

          <!-- Current Card -->
          <div class="card-page current-card" ref="currentCard">
            <CardDetailContainer 
              v-if="displayedCards.current"
              :card="displayedCards.current"
              :is-active="true"
              @media-double-click="handleMediaDoubleClick"
              @go-back="goBackToCategory"
              @save-error="handleSaveError"
              ref="currentCardContainer"
            />
            <div v-else class="empty-card-placeholder"></div>
          </div>

          <!-- Next Card -->
          <div class="card-page next-card" ref="nextCard">
            <CardDetailContainer 
              v-if="displayedCards.next"
              :card="displayedCards.next"
              :is-active="false"
              ref="nextCardContainer"
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
          <svg width="107" height="107" viewBox="0 0 208 208" fill="none" xmlns="http://www.w3.org/2000/svg">
            <g filter="url(#filter0_d_26_86)">
              <path d="M93.6 104L133.467 143.867L121.333 156L69.3334 104L121.333 52L133.467 64.1333L93.6 104Z" fill="#FEF7FF" transform="rotate(180 104 104)"/>
            </g>
            <defs>
              <filter id="filter0_d_26_86" x="-4" y="0" width="216" height="216" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB">
                <feFlood flood-opacity="0" result="BackgroundImageFix"/>
                <feColorMatrix in="SourceAlpha" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0" result="hardAlpha"/>
                <feOffset dy="4"/>
                <feGaussianBlur stdDeviation="2"/>
                <feComposite in2="hardAlpha" operator="out"/>
                <feColorMatrix type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.25 0"/>
                <feBlend mode="normal" in2="BackgroundImageFix" result="effect1_dropShadow_26_86"/>
                <feBlend mode="normal" in="SourceGraphic" in2="effect1_dropShadow_26_86" result="shape"/>
              </filter>
            </defs>
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
    const allCards = ref([])
    const currentCardIndex = ref(0)
    const isScrolling = ref(false)
    const scrollDirection = ref(null) // 'left' or 'right'
    const currentTransform = ref(-100) // Current transform in vw units
    
    // Store displayed cards separately to ensure reactivity
    const displayedCards = ref({
      previous: null,
      current: null,
      next: null
    })

    // Track which cards have been preloaded
    const preloadedCards = ref(new Set())

    // Refs for card containers
    const previousCard = ref(null)
    const currentCard = ref(null)
    const nextCard = ref(null)
    const previousCardContainer = ref(null)
    const currentCardContainer = ref(null)
    const nextCardContainer = ref(null)

    // Touch/swipe handling
    const touchStartX = ref(0)
    const touchStartY = ref(0)
    const touchEndX = ref(0)
    const isSwiping = ref(false)
    const swipeThreshold = 50 // Minimum distance for swipe to trigger navigation

    // Scroll synchronization
    const isSyncingScroll = ref(false)

    const syncScrollPositions = (sourceElement, targetElements) => {
      if (isSyncingScroll.value) return
      
      isSyncingScroll.value = true
      
      const scrollTop = sourceElement.scrollTop
      const scrollHeight = sourceElement.scrollHeight
      const clientHeight = sourceElement.clientHeight
      
      // Calculate scroll percentage
      const scrollPercentage = scrollTop / (scrollHeight - clientHeight)
      
      // Apply same scroll percentage to target elements
      targetElements.forEach(target => {
        if (target && target.$el) {
          const targetScrollHeight = target.$el.scrollHeight
          const targetClientHeight = target.$el.clientHeight
          const targetScrollTop = scrollPercentage * (targetScrollHeight - targetClientHeight)
          target.$el.scrollTop = targetScrollTop
        }
      })
      
      // Use requestAnimationFrame to reset the flag
      requestAnimationFrame(() => {
        isSyncingScroll.value = false
      })
    }

    const setupScrollSync = () => {
      nextTick(() => {
        if (currentCardContainer.value && currentCardContainer.value.$el) {
          const currentCardEl = currentCardContainer.value.$el
          
          // Remove any existing listener first
          currentCardEl.removeEventListener('scroll', handleScrollSync)
          
          // Add scroll event listener to current card
          currentCardEl.addEventListener('scroll', handleScrollSync)
        }
      })
    }
    
    const handleScrollSync = () => {
      if (isSyncingScroll.value) return
      
      const currentEl = currentCardContainer.value?.$el
      if (!currentEl) return
      
      isSyncingScroll.value = true
      
      const scrollTop = currentEl.scrollTop
      const scrollHeight = currentEl.scrollHeight
      const clientHeight = currentEl.clientHeight
      
      // Calculate scroll percentage only if we can scroll
      const scrollPercentage = scrollHeight > clientHeight 
        ? scrollTop / (scrollHeight - clientHeight)
        : 0
      
      // Apply same scroll percentage to target elements
      const targets = []
      if (previousCardContainer.value) targets.push(previousCardContainer.value)
      if (nextCardContainer.value) targets.push(nextCardContainer.value)
      
      targets.forEach(target => {
        if (target && target.$el) {
          const targetEl = target.$el
          const targetScrollHeight = targetEl.scrollHeight
          const targetClientHeight = targetEl.clientHeight
          
          if (targetScrollHeight > targetClientHeight) {
            const targetScrollTop = scrollPercentage * (targetScrollHeight - targetClientHeight)
            targetEl.scrollTop = targetScrollTop
          }
        }
      })
      
      requestAnimationFrame(() => {
        isSyncingScroll.value = false
      })
    }

    const cleanupScrollSync = () => {
      if (currentCardContainer.value && currentCardContainer.value.$el) {
        const currentCardEl = currentCardContainer.value.$el
        currentCardEl.removeEventListener('scroll', handleScrollSync)
      }
    }

    // Touch/swipe handlers
    const handleTouchStart = (event) => {
      if (isScrolling.value) return
      
      const touch = event.touches[0]
      touchStartX.value = touch.clientX
      touchStartY.value = touch.clientY
      touchEndX.value = touch.clientX
      isSwiping.value = false
    }

    const handleTouchMove = (event) => {
      if (isScrolling.value) return
      
      const touch = event.touches[0]
      touchEndX.value = touch.clientX
      
      // Calculate swipe distance
      const deltaX = touchEndX.value - touchStartX.value
      
      // Only consider it swiping if we've moved enough horizontally
      if (Math.abs(deltaX) > 10) {
        isSwiping.value = true
        event.preventDefault() // Prevent scrolling while swiping
      }
    }

    const handleTouchEnd = () => {
      if (isScrolling.value || !isSwiping.value) return
      
      const deltaX = touchEndX.value - touchStartX.value
      const absDeltaX = Math.abs(deltaX)
      
      // Only trigger navigation if swipe distance exceeds threshold
      if (absDeltaX >= swipeThreshold) {
        if (deltaX > 0) {
          // Swipe right - go to previous card
          if (!isFirstCard.value) {
            goToPreviousCard()
          }
        } else {
          // Swipe left - go to next card
          if (!isLastCard.value) {
            goToNextCard()
          }
        }
      }
      
      // Reset touch state
      isSwiping.value = false
      touchStartX.value = 0
      touchEndX.value = 0
    }

    onUnmounted(() => {
      // Clean up saved card order when leaving the detail view
      sessionStorage.removeItem('currentCardOrder')
      cleanupScrollSync()
    })

    const isFirstCard = computed(() => currentCardIndex.value <= 0)
    const isLastCard = computed(() => currentCardIndex.value >= allCards.value.length - 1)

    // Dynamic transform based on scroll direction
    const containerStyle = computed(() => ({
      transform: `translateX(${currentTransform.value}vw)`,
      transition: isScrolling.value ? 'transform 0.3s ease' : 'none'
    }))

    const findCurrentCardIndex = () => {
      if (!props.id || !allCards.value.length) return 0
      
      // Find the index of the current card in the allCards array
      const index = allCards.value.findIndex(c => c.id.toString() === props.id.toString())
      
      if (index >= 0) {
        return index
      }
      
      // If current card not found, try to find it by loading it individually
      console.warn(`Current card ${props.id} not found in loaded cards, loading individually`)
      return 0
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

      // Setup scroll sync after cards are updated
      nextTick(() => {
        setupScrollSync()
      })
    }

    const loadAllCards = async () => {
      try {
        const previousCategory = sessionStorage.getItem('previousCategory')
        
        // Get the saved card order from sessionStorage
        const savedCardOrder = sessionStorage.getItem('currentCardOrder')
        
        if (savedCardOrder) {
          // Use the exact card order that was saved from CategoryCards
          const cardIds = JSON.parse(savedCardOrder)
          console.log('Loading cards using saved order:', cardIds)
          
          // Load ONLY BASIC card info first - don't fetch detailed info yet
          const loadPromises = cardIds.map(async (cardId) => {
            try {
              // Only load minimal card data initially
              const basicCardInfo = {
                id: cardId,
                name: 'Loading...', // Placeholder
                category: 'Loading...'
              }
              return basicCardInfo
            } catch (err) {
              console.error(`Failed to load card ${cardId}:`, err)
              return null
            }
          })
          
          const loadedCards = await Promise.all(loadPromises)
          allCards.value = loadedCards.filter(card => card !== null)
          
          console.log('Loaded basic cards in saved order:', allCards.value.map(c => ({ id: c.id })))
        } else {
          // Fallback: load with saved sort parameters (existing logic)
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
          // Only store basic card data initially
          allCards.value = (response.cards || []).map(card => ({
            id: card.id,
            name: card.name || 'Loading...',
            category: card.category || 'Loading...'
          }))
        }
        
        // Find current card index in the sorted array
        currentCardIndex.value = findCurrentCardIndex()
        console.log('Current card index:', currentCardIndex.value)
        
        // Reset transform to center
        currentTransform.value = -100
        
        // Update displayed cards immediately with basic data
        updateDisplayedCards()
        
        // Load detailed info ONLY for the 5 adjacent cards
        await loadDetailedCardInfo()
        
      } catch (error) {
        console.error('Error loading all cards:', error)
        allCards.value = []
      }
    }

    const getCardsToPreload = () => {
      const cardsToPreload = []
      const startIndex = Math.max(0, currentCardIndex.value - 5)
      const endIndex = Math.min(allCards.value.length - 1, currentCardIndex.value + 5)
      
      for (let i = startIndex; i <= endIndex; i++) {
        const cardId = allCards.value[i].id
        if (!preloadedCards.value.has(cardId)) {
          cardsToPreload.push(cardId)
        }
      }
      
      console.log(`Preloading ${cardsToPreload.length} cards from index ${startIndex} to ${endIndex}`)
      return cardsToPreload
    }

    const loadDetailedCardInfo = async () => {
      if (!allCards.value.length) return

      // Get cards to preload (5 on each side of current card)
      const cardsToLoad = getCardsToPreload()

      console.log('Loading detailed info for cards:', cardsToLoad)

      try {
        const loadPromises = cardsToLoad.map(async (cardId) => {
          try {
            const detailedCard = await fetchCardInfo(cardId)
            // Update the card in allCards with detailed info
            const index = allCards.value.findIndex(c => c.id === cardId)
            if (index >= 0) {
              // Merge detailed info with existing data
              allCards.value[index] = { 
                ...allCards.value[index], // Keep any existing data
                ...detailedCard  // Add detailed info
              }
              // Mark as preloaded
              preloadedCards.value.add(cardId)
              console.log(`Loaded detailed info for card ${cardId}`)
            }
          } catch (err) {
            console.error(`Failed to load detailed info for card ${cardId}:`, err)
            // If detailed loading fails, at least we have the basic card info
          }
        })

        await Promise.all(loadPromises)
        
        // Update displayed cards with any new detailed data
        updateDisplayedCards()
        
      } catch (err) {
        console.error('Error loading detailed card info:', err)
      }
    }

    const navigateToCard = async (targetIndex, direction) => {
      if (isScrolling.value || targetIndex < 0 || targetIndex >= allCards.value.length) return

      isScrolling.value = true
      scrollDirection.value = direction

      // Clean up existing scroll sync
      cleanupScrollSync()

      // Update URL without triggering navigation
      const newCardId = allCards.value[targetIndex].id
      window.history.replaceState({}, '', `/card/${newCardId}`)

      // STEP 1: Scroll to adjacent card
      let targetTransform
      if (direction === 'left') {
        targetTransform = 0 // Move to show previous card
      } else {
        targetTransform = -200 // Move to show next card
      }

      // Animate to the target position
      currentTransform.value = targetTransform

      // Wait for the scroll animation to complete
      await new Promise(resolve => setTimeout(resolve, 300))

      // STEP 2: Replace the center section card with the new card
      currentCardIndex.value = targetIndex
      
      // Update displayed cards - this replaces the center card
      updateDisplayedCards()

      // STEP 3: Teleport back to center position without animation
      isScrolling.value = false // Disable transition for instant teleport
      currentTransform.value = -100 // Reset to center
      
      // Force a reflow to ensure the teleport happens immediately
      await nextTick()
      
      // STEP 4: Preload adjacent cards for the new position
      await loadDetailedCardInfo()

      // Setup scroll sync for the new cards
      setupScrollSync()

      // Final cleanup
      isScrolling.value = false
      scrollDirection.value = null
    }

    const goToPreviousCard = () => {
      if (isFirstCard.value || isScrolling.value) return
      navigateToCard(currentCardIndex.value - 1, 'left')
    }

    const goToNextCard = () => {
      if (isLastCard.value || isScrolling.value) return
      navigateToCard(currentCardIndex.value + 1, 'right')
    }

    const goBackToCategory = () => {
      if (router.meta) {
        router.meta.navigationType = 'to-category'
      }
      
      // Clear the saved card order when going back to category
      sessionStorage.removeItem('currentCardOrder')
      
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
        
        // Update preloaded status
        preloadedCards.value.add(displayedCards.value.current.id)
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
        preloadedCards.value.clear()
        
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
      previousCard,
      currentCard,
      nextCard,
      previousCardContainer,
      currentCardContainer,
      nextCardContainer,
      goToPreviousCard,
      goToNextCard,
      goBackToCategory,
      handleMediaDoubleClick,
      handleSaveError,
      handleFileChange,
      handleTouchStart,
      handleTouchMove,
      handleTouchEnd
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

.multi-card-viewport {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  position: relative;
  touch-action: pan-y; /* Allow vertical scrolling but prevent horizontal */
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

.card-page.previous-card {
  /* Previous card is on the left */
  order: 1;
}

.card-page.current-card {
  /* Current card is in the middle */
  order: 2;
}

.card-page.next-card {
  /* Next card is on the right */
  order: 3;
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
  height: 213px; /* 1.5x smaller from 320px (320 / 1.5 = 213.33) */
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 100;
  opacity: 1;
  transition: all 0.3s ease;
  will-change: transform;
}

.nav-arrow:hover {
  opacity: 0.8;
  transform: translateY(-50%) scale(1.05);
}

.nav-arrow.disabled {
  opacity: 0.3;
  pointer-events: none;
  cursor: not-allowed;
}

.nav-arrow.disabled:hover {
  transform: translateY(-50%) scale(1);
}

.left-arrow {
  left: 10px;
}

.right-arrow {
  right: 10px;
}

.arrow-icon-wrapper {
  width: 107px; /* 1.5x smaller from 160px (160 / 1.5 = 106.67) */
  height: 107px; /* 1.5x smaller from 160px (160 / 1.5 = 106.67) */
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
  transition: all 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.4));
}

.nav-arrow:hover .arrow-icon-wrapper {
  filter: drop-shadow(0 6px 12px rgba(0, 0, 0, 0.5));
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

/* Responsive design - similar to Home.vue */
@media (max-width: 1200px) {
  .nav-arrow {
    height: 180px;
  }
  
  .arrow-icon-wrapper {
    width: 90px;
    height: 90px;
  }
}

@media (max-width: 992px) {
  .nav-arrow {
    height: 160px;
  }
  
  .arrow-icon-wrapper {
    width: 80px;
    height: 80px;
  }
}

@media (max-width: 768px) {
  .card-page {
    padding: 10px;
  }
  
  .nav-arrow {
    height: 80px; /* 1.5x smaller from 120px (120 / 1.5 = 80) */
  }
  
  .left-arrow {
    left: 5px;
  }
  
  .right-arrow {
    right: 5px;
  }
  
  .arrow-icon-wrapper {
    width: 40px; /* 1.5x smaller from 60px (60 / 1.5 = 40) */
    height: 40px; /* 1.5x smaller from 60px (60 / 1.5 = 40) */
  }
  
  .multi-card-container {
    width: 300vw;
  }
  
  .card-page {
    flex: 0 0 100vw;
  }
}

@media (max-width: 480px) {
  .nav-arrow {
    height: 60px;
  }
  
  .arrow-icon-wrapper {
    width: 30px;
    height: 30px;
  }
  
  .left-arrow {
    left: 2px;
  }
  
  .right-arrow {
    right: 2px;
  }
}


@media (max-width: 1050px) {
  .card-page {
    padding-bottom: 0;
    padding-top: 0;
  }
  .multi-card-viewport {
    touch-action: pan-y;
  }
}


/* Touch device optimizations */
@media (hover: none) and (pointer: coarse) {
  .nav-arrow {
    opacity: 0.9;
  }
  
  .nav-arrow:hover {
    transform: translateY(-50%) scale(1);
    opacity: 0.9;
  }
}

/* Reduced motion preferences */
@media (prefers-reduced-motion: reduce) {
  .nav-arrow,
  .arrow-icon-wrapper,
  .multi-card-container {
    transition: none;
  }
  
  .nav-arrow:hover {
    transform: translateY(-50%);
  }
}
</style>