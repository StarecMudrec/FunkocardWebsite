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
        <!-- ... loading spinner ... -->
      </div>

      <!-- Scroll container for horizontal snap -->
      <div class="cards-scroll-container" ref="scrollContainer">
        <div class="cards-scroll-wrapper">
          <div 
            v-for="(cardId, index) in visibleCards" 
            :key="cardId" 
            class="card-slide"
            :class="{ 'active': cardId === card.id.toString() }"
          >
            <div v-if="isCardLoaded(index)" class="card-detail-container">
              <!-- Render card content using getCardForSlide(index) -->
              <div class="card-detail">
                <div class="card-content-wrapper">
                  <div class="card-header-section">
                    <div class="title-container">
                      <h1 :ref="el => setCardNameRef(el, index)">
                        <span>{{ getCardForSlide(index).name }}</span>
                      </h1>
                    </div>
                    <div v-if="nameError" class="error-message">{{ nameError }}</div>
                    <div class="main-divider"></div>
                  </div>
                  
                  <h3 style="margin: 60px 0px 10px;font-size: 24px;line-height: 1.6;color: var(--text-color);text-align: start;left: 30px;position: relative;font-weight: normal;text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.5);">
                    <strong>Rarity: </strong>{{ getCardForSlide(index).category }}
                  </h3>
                  
                  <p style="margin: 0;margin-bottom: 10px;font-size: 24px;line-height: 1.6;color: var(--text-color);text-align: start;left: 30px;position: relative;font-weight: normal;text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.5);" v-html="formatDescription(getCardForSlide(index).description)"></p>

                  <div class="secondary-divider"></div>
                  
                  <div class="shop-section">
                    <div class="shop-info">
                      <h3>Available at shop:</h3>
                      <p :class="{ 'available-glow': isShopAvailable(getCardForSlide(index).shop) }">
                        {{ formatShopInfo(getCardForSlide(index).shop) }}
                      </p>
                    </div>
                  </div>

                  <div class="back-to-category-section">
                    <button @click="goBackToCategory" class="back-to-category-button">
                      ← Back to {{ getCategoryDisplayName() }}
                    </button>
                  </div>
                </div>
                
                <div class="card-image-container">
                  <!-- Media content for loaded cards -->
                  <video 
                    v-if="getCardForSlide(index).category === 'Limited ⚠️' && getCardForSlide(index).img && !mediaError" 
                    :src="`/api/card_image/${getCardForSlide(index).img}`" 
                    class="card-detail-media"
                    autoplay
                    loop
                    muted
                    playsinline
                    @error="mediaError = true"
                    @dblclick="handleMediaDoubleClick"
                    disablePictureInPicture
                  ></video>
                  
                  <img 
                    v-else-if="getCardForSlide(index).img && !mediaError" 
                    :src="`/api/card_image/${getCardForSlide(index).img}`" 
                    :alt="getCardForSlide(index).name" 
                    class="card-detail-media"
                    @error="mediaError = true"
                    @dblclick="handleMediaDoubleClick"
                  />
                  
                  <div v-else class="image-placeholder">No media available</div>
                </div>
              </div>
            </div>
            <div v-else class="card-detail-container">
              <div class="loading-overlay">
                <div class="loading-content">
                  <svg class="spinner" viewBox="0 0 50 50">
                    <circle class="path" cx="25" cy="25" r="20" fill="none" stroke-width="5"></circle>
                  </svg>
                  <div class="loading-text">Loading card...</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

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
  import { fetchCardInfo, checkUserPermission, fetchUserInfo, fetchCardsByCategory, fetchCardById } from '@/api'
  import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
  import { useRouter } from 'vue-router'

  export default {
    props: {
      id: {
        type: String,
        required: true
      }
    },
    setup(props) {
      const router = useRouter()
      const fileInput = ref(null)
      const nameInput = ref(null)
      const descriptionInput = ref(null)
      const categoryInput = ref(null)
      const scrollContainer = ref(null)

      const card = ref({})
      const editableCard = ref({})
      const loading = ref(true)
      const error = ref(null)
      const mediaError = ref(false)
      const saveError = ref(null)
      const nameError = ref(null)
      const descriptionError = ref(null)
      const categoryError = ref(null)
      const cardNameRefs = ref([])
      const isUserAllowed = ref(false)
      const editing = ref({
        name: false,
        description: false,
        category: false
      })

      // Card navigation with lazy loading
      const visibleCards = ref([]) // Only store currently visible cards
      const currentCardIndex = ref(-1)
      const cardIds = ref([]) // Store only IDs for the current category
      const loadedCards = ref({}) // Cache for loaded card data
      const loadingNeighbors = ref(false)

      const isFirstCard = computed(() => currentCardIndex.value <= 0)
      const isLastCard = computed(() => currentCardIndex.value >= cardIds.value.length - 1)

      // Computed property to check if current card is Limited
      const isLimitedCard = computed(() => {
        return card.value.category === 'Limited ⚠️';
      });

      // Function to set card name refs in the array
      const setCardNameRef = (el, index) => {
        if (el) {
          cardNameRefs.value[index] = el
        }
      }

      const loadCardIds = async () => {
        try {
          if (!card.value?.category) {
            console.log('No category on card:', card.value);
            return;
          }
          
          // Get the previous category and sort parameters from sessionStorage
          const previousCategory = sessionStorage.getItem('previousCategory');
          const savedSortState = sessionStorage.getItem(`category_state_${previousCategory}`);
          
          let sortField = 'id';
          let sortDirection = 'asc';
          
          // Use saved sort parameters if available
          if (savedSortState) {
            try {
              const state = JSON.parse(savedSortState);
              if (state.currentSort) {
                sortField = state.currentSort.field;
                sortDirection = state.currentSort.direction;
              }
            } catch (e) {
              console.warn('Failed to parse saved sort state:', e);
            }
          }
          
          // For navigation, we need to use the category ID format that matches the API
          const categoryId = previousCategory || `rarity_${card.value.category}`;
          console.log('Loading card IDs for category ID:', categoryId, 'with sort:', sortField, sortDirection);
          
          const response = await fetchCardsByCategory(categoryId, sortField, sortDirection);
          
          // Extract only the card IDs for navigation
          cardIds.value = (response.cards || []).map(card => card.id.toString());
          console.log('Loaded card IDs:', cardIds.value);
          
          // Find current card index
          currentCardIndex.value = cardIds.value.findIndex(id => id === props.id);
          console.log('Current card index:', currentCardIndex.value);
          
        } catch (error) {
          console.error('Error loading card IDs:', error);
          cardIds.value = [];
        }
      }

      const loadCardData = async (cardId) => {
        // Return cached card if available
        if (loadedCards.value[cardId]) {
          return loadedCards.value[cardId];
        }

        try {
          const cardData = await fetchCardInfo(cardId);
          loadedCards.value[cardId] = cardData;
          return cardData;
        } catch (error) {
          console.error('Error loading card data:', error);
          return null;
        }
      }

      const updateVisibleCards = async () => {
        if (currentCardIndex.value === -1 || cardIds.value.length === 0) return;

        loadingNeighbors.value = true;
        
        const newVisibleCards = [];
        
        // Always include current card
        const currentCardData = await loadCardData(cardIds.value[currentCardIndex.value]);
        if (currentCardData) {
          newVisibleCards[currentCardIndex.value] = currentCardData;
        }
        
        // Load previous card if exists
        if (currentCardIndex.value > 0) {
          const prevCardData = await loadCardData(cardIds.value[currentCardIndex.value - 1]);
          if (prevCardData) {
            newVisibleCards[currentCardIndex.value - 1] = prevCardData;
          }
        }
        
        // Load next card if exists
        if (currentCardIndex.value < cardIds.value.length - 1) {
          const nextCardData = await loadCardData(cardIds.value[currentCardIndex.value + 1]);
          if (nextCardData) {
            newVisibleCards[currentCardIndex.value + 1] = nextCardData;
          }
        }
        
        // Update visible cards array
        visibleCards.value = newVisibleCards;
        loadingNeighbors.value = false;
        
        console.log('Updated visible cards at indices:', Object.keys(newVisibleCards));
      }

      const scrollToCard = (index) => {
        if (!scrollContainer.value || index < 0 || index >= cardIds.value.length) return;
        
        const scrollWrapper = scrollContainer.value;
        const cardWidth = scrollWrapper.clientWidth;
        scrollWrapper.scrollTo({
          left: index * cardWidth,
          behavior: 'smooth'
        });
      }

      const handleScroll = async () => {
        if (!scrollContainer.value || loadingNeighbors.value) return;
        
        const scrollWrapper = scrollContainer.value;
        const scrollLeft = scrollWrapper.scrollLeft;
        const cardWidth = scrollWrapper.clientWidth;
        const newIndex = Math.round(scrollLeft / cardWidth);
        
        if (newIndex !== currentCardIndex.value && newIndex >= 0 && newIndex < cardIds.value.length) {
          console.log('Scrolling to index:', newIndex);
          currentCardIndex.value = newIndex;
          const newCardId = cardIds.value[newIndex];
          
          // Update URL without triggering full navigation
          if (newCardId && newCardId !== props.id) {
            router.replace(`/card/${newCardId}`);
          }
          
          // Load neighboring cards for the new position
          await updateVisibleCards();
          
          // Update current card reference
          if (visibleCards.value[newIndex]) {
            card.value = visibleCards.value[newIndex];
            editableCard.value = { ...card.value };
          }
        }
      }

      const getCardForSlide = (index) => {
        return visibleCards.value[index] || { id: cardIds.value[index], name: 'Loading...' };
      }

      const isCardLoaded = (index) => {
        return !!visibleCards.value[index];
      }

      const getCategoryDisplayName = () => {
        const previousCategory = sessionStorage.getItem('previousCategory');
        
        if (previousCategory) {
          if (previousCategory === 'all') return 'All Cards';
          if (previousCategory === 'shop') return 'Available at Shop';
          if (previousCategory.startsWith('rarity_')) {
            return previousCategory.replace('rarity_', '');
          }
          return previousCategory;
        } else {
          return card.value?.category || 'Category';
        }
      }
      
      const formatDescription = (description) => {
        if (!description) return '';
        return description.replace(/Points:/g, '<strong>Points:</strong>');
      }

      const formatShopInfo = (shopData) => {
        if (!shopData || shopData === '-' || shopData === 'null' || shopData === 'None') {
          return 'Not available';
        }
        
        if (typeof shopData === 'string') {
          return "Available";
        }
        
        return shopData.toString();
      }
      
      const isShopAvailable = (shopData) => {
        if (!shopData || shopData === '-' || shopData === 'null' || shopData === 'None') {
          return false;
        }
        
        if (typeof shopData === 'string') {
          return shopData !== '-' && shopData !== 'null' && shopData !== 'None';
        }
        
        return false;
      }

      const goBackToCategory = () => {
        if (router.meta) {
          router.meta.navigationType = 'to-category'
        }
        
        const previousCategory = sessionStorage.getItem('previousCategory');
        
        if (previousCategory) {
          router.push(`/category/${previousCategory}`)
        } else {
          if (card.value?.category) {
            const categoryId = `rarity_${card.value.category}`
            router.push(`/category/${categoryId}`)
          } else {
            router.go(-1)
          }
        }
      }

      // ... keep all your existing helper functions (isOverflown, resizeText, adjustFontSize, etc.)

      const goToPreviousCard = async () => {
        if (isFirstCard.value || currentCardIndex.value === -1 || cardIds.value.length === 0) {
          console.log('Cannot go to previous card - no cards loaded or at beginning');
          return;
        }
        
        const prevIndex = currentCardIndex.value - 1;
        scrollToCard(prevIndex);
      }

      const goToNextCard = async () => {
        if (isLastCard.value || currentCardIndex.value === -1 || cardIds.value.length === 0) {
          console.log('Cannot go to next card - no cards loaded or at end');
          return;
        }
        
        const nextIndex = currentCardIndex.value + 1;
        scrollToCard(nextIndex);
      }

      const loadData = async () => {
        try {
          loading.value = true;
          mediaError.value = false;
          
          // Load current card data
          card.value = await fetchCardInfo(props.id);
          editableCard.value = { ...card.value };
          
          // Load card IDs for navigation
          await loadCardIds();
          
          // Load initial visible cards (current + neighbors)
          await updateVisibleCards();
          
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
          
          // Scroll to current card after data is loaded
          nextTick(() => {
            scrollToCard(currentCardIndex.value);
            setTimeout(adjustFontSize, 100);
          });
        } catch (err) {
          error.value = err.message || 'Failed to load card details'
          console.error('Error loading card:', err)
        } finally {
          loading.value = false
        }
      }

      onMounted(() => {
        window.addEventListener('resize', adjustFontSize)
        loadData()
        
        // Add scroll event listener
        if (scrollContainer.value) {
          scrollContainer.value.addEventListener('scroll', handleScroll);
        }
        
        // Set navigation type when entering card detail
        if (router.meta) {
          router.meta.navigationType = 'from-card-detail';
        }
      })

      onUnmounted(() => {
        window.removeEventListener('resize', adjustFontSize)
        
        // Remove scroll event listener
        if (scrollContainer.value) {
          scrollContainer.value.removeEventListener('scroll', handleScroll);
        }
      })

      watch(() => props.id, async (newId) => {
        if (newId && card.value?.id !== newId) {
          await loadData()
        }
      })

      // ... keep all your existing watchers

      return {
        card,
        editableCard,
        categoryError,
        loading,
        error,
        nameError,
        descriptionError,
        saveError,
        mediaError,
        cardNameRefs,
        setCardNameRef,
        editing,
        isUserAllowed,
        nameInput,
        descriptionInput,
        categoryInput,
        fileInput,
        scrollContainer,
        handleMediaDoubleClick,
        handleFileChange,
        startEditing,
        saveField,
        toggleEdit,
        cancelEdit,
        fileInput,  
        handleMediaDoubleClick,
        handleFileChange,
        isFirstCard,
        isLastCard,
        goToPreviousCard,
        goToNextCard,
        goBackToCategory,
        formatShopInfo,
        isShopAvailable,
        formatDescription,
        getCategoryDisplayName,
        isLimitedCard,
        visibleCards: cardIds, // Use cardIds for the template loop
        getCardForSlide,
        isCardLoaded,
        loadingNeighbors
      }
    }
  }
</script>

<style scoped>
  html {
    overflow: hidden;
    width: 100%;
    height: 100%;
  }
  body {
    position: fixed;
    overflow: hidden;
    width: 100%;
    height: 100%;
  }

  .back-to-category-section {
    text-align: center;
    margin-top: 20px;
  }

  .back-to-category-button {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: transparent;
    border: none;
    color: var(--accent-color);
    padding: 10px 0;
    cursor: pointer;
    font-size: 17px;
    font-family: 'Afacad', sans-serif;
    text-decoration: none;
    position: relative;
    padding-bottom: 2px;
    transition: all 0.3s ease;
    text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.5);
  }

  .back-to-category-button::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 50%;
    width: 0;
    height: 1px;
    background-color: var(--accent-color);
    transition: all 0.3s ease;
    transform: translateX(-50%);
  }

  .back-to-category-button:hover {
    transform: scale(1.05);
    background: transparent;
    box-shadow: none;
    color: var(--accent-color);
  }

  .back-to-category-button:hover::after {
    width: 100%;
  }

  /* Mobile responsive adjustments */
  @media (max-width: 768px) {
    .back-to-category-button {
      padding: 8px 0;
      font-size: 16px;
    }
  }
  /* Hide scrollbar for Chrome, Safari and Opera */
  ::-webkit-scrollbar {
    display: none;
    width: 0 !important;
    height: 0 !important;
    -webkit-appearance: none;
    background: transparent;
  }

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
    display: flex; /* Add this */
    align-items: center; /* Add this for vertical centering */
    justify-content: center; /* Add this for horizontal centering */
  }

  /* Transition styles */
  .slide-left-enter-active,
  .slide-left-leave-active,
  .slide-right-enter-active,
  .slide-right-leave-active {
    transition: 
      transform 0.5s ease,
      opacity 0.4s ease 0.1s;
    position: absolute;
    width: 100%;
    height: 100%;
  }

  .slide-left-enter-from {
    transform: translateX(100%); /* Added translateY */
    opacity: 0;
  }

  .slide-left-enter-to {
    transform: translateX(0); /* Added translateY */
    opacity: 1;
  }

  .slide-left-leave-from {
    transform: translateX(0);
    opacity: 1;
  }

  .slide-left-leave-to {
    transform: translateX(-100%);
    opacity: 0;
  }

  .slide-right-enter-from {
    transform: translateX(-100%); /* Added translateY */
    opacity: 0;
  }

  .slide-right-enter-to {
    transform: translateX(0); /* Added translateY */
    opacity: 1;
  }

  .slide-right-leave-from {
    transform: translateX(0);
    opacity: 1;
  }

  .slide-right-leave-to {
    transform: translateX(100%);
    opacity: 0;
  }

  .card-detail-container {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    overflow-y: auto;
    -ms-overflow-style: none;
    scrollbar-width: none;
    width: 100%;
    overflow: hidden;
    -ms-overflow-style: none;  /* IE and Edge */
    scrollbar-width: none;  /* Firefox */
  }

  /* Force hide scrollbars on all browsers */
  .card-detail-container::-webkit-scrollbar {
    width: 0 !important;
    height: 0 !important;
    display: none;
    background: transparent;
  }

  /* Disable overscroll behavior */
  .card-detail-container {
    overscroll-behavior: contain;
  }
  
  .nav-arrow.disabled {
    opacity: 0.2;
    pointer-events: none;
    cursor: not-allowed;
  }
  .transition-container {
    position: relative;
    width: 100%;
    max-height: 100vh;
    overflow: hidden;
  }
  /* Add these new styles */
  .card-detail-wrapper {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    overflow: hidden;
    -ms-overflow-style: none;  /* IE and Edge */
    scrollbar-width: none;  /* Firefox */
    position: relative;
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
    pointer-events: none; /* Makes only the icon clickable */
  }

  .arrow-icon {
    width: 100%;
    height: 100%;
    fill: var(--accent-color);
    pointer-events: auto; /* Re-enable pointer events for the icon */
  }

  /* Make sure your card container has proper z-index */
  .card-detail-container {
    position: relative;
    z-index: 1;
  }

  /* Add these new styles at the end of your style section */
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

  /* New error-specific styles */
  .error-overlay {
    background-color: rgba(0, 0, 0, 0.7); /* Slightly darker for errors */
  }

  .error-icon {
    width: 50px;
    height: 50px;
    color: #ff4444; /* Red color for error icon */
  }

  .error-text {
    color: #ff6b6b; /* Lighter red for error text */
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

  /* Существующие стили остаются без изменений */
  .edit-icon {
    margin-left: 10px;
    cursor: pointer;
    opacity: 0.7;
    transition: opacity 0.2s ease;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    border-radius: 50%;
  }

  .edit-icon:hover {
    opacity: 1;
    background-color: rgba(255, 255, 255, 0.1);
  }

  .edit-icon svg {
    width: 16px;
    height: 16px;
  }

  .category-container {
    background: none;
    padding: 12px 20px;
    border-radius: 8px;
    margin-top: 8px;
    min-height: 50px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 20px;
    text-align: center;
  }

  .shop-section {
    /* padding: 20px 0; */
    text-align: center;
    text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.5);
  }

  .shop-info h3 {
    font-size: 25px;
    color: var(--accent-color);
    margin: 0;
    margin-top: 27px;
    margin-bottom: 7px;
  }

  .shop-info p {
    font-size: 20px;
    line-height: 1.6;
    color: #888888;
    margin: 0;
    margin-bottom: 30px;
  }

  .available-glow {
    color: #4ade80 !important; /* Green color */
    text-shadow: 
      0 0 5px #4ade80,
      0 0 10px #4ade80,
      0 0 15px #4ade80,
      0 0 20px #4ade80 !important;
    animation: glow-pulse 2s ease-in-out infinite alternate;
  }

  @keyframes glow-pulse {
    from {
      text-shadow: 
        0 0 5px #4ade80,
        0 0 10px #4ade80,
        0 0 15px #4ade80,
        0 0 20px #4ade80;
    }
    to {
      text-shadow: 
        0 0 10px #4ade80,
        0 0 15px #4ade80,
        0 0 20px #4ade80,
        0 0 25px #4ade80,
        0 0 30px #4ade80;
    }
  }


  /* Стили для полей ввода при редактировании */
  .edit-input {
    font-size: inherit;
    font-family: inherit;
    color: inherit;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid var(--accent-color);
    border-radius: 4px;
    padding: 5px;
    width: 80%;
    text-align: inherit;
    transition: inherit;
    text-shadow: inherit;
    letter-spacing: inherit;
  }
  .edit-input:focus {
    box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.3);
  }

  .edit-input-select {
    width: 50%;
    padding: 12px 20px;
    border: none;
    border-radius: 8px;
    background: transparent;
    color: white;
    font-size: 20px;
    text-align: center; 
    cursor: pointer;
    appearance: none; /* Remove default dropdown arrow */
    margin-top: 6px;
    background-image: url('data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2020%2020%22%20fill%3D%22none%22%20stroke%3D%22%23ffffff%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpolyline%20points%3D%226%209%2012%2015%2018%209%22%2F%3E%3C%2Fsvg%3E'); /* Custom dropdown arrow */
    background-repeat: no-repeat;
    background-position: right 15px center;
    background-size: 1em;
    font-family: inherit;
  }

  .edit-input-select option { 
    color: inherit;
    background: var(--bg-color);
  }

  .edit-textarea {
    font-size: inherit;
    font-family: inherit;
    color: inherit;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid var(--accent-color);
    border-radius: 4px;
    padding: 10px;
    width: 100%;
    min-height: 100px;
    resize: vertical;
  }

  .edit-input-select:focus {
    outline: none;
    box-shadow: none;
    background-color: transparent;
  }

  .replace-image-button {
    display: block;
    width: 100%;
    padding: 10px;
    background-color: var(--bg-color);
    color: white;
    border: none;
    border-radius: 5px;
    /* cursor: pointer; */
    font-size: 26px;
    font-family: var(--font-family-main);
    font-weight: 500;
    transition: background-color 0.3s ease;
  }

  /* Остальные существующие стили без изменений */
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

  .card-detail-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 67px;
    height: 100%;
    display: flex;
    align-items: stretch;
  }

  .card-detail {
    display: grid;
    grid-template-columns: 350px 1fr; /* Change from 1fr 2fr to equal columns */
    gap: 40px;
    background-color: var(--card-bg);
    backdrop-filter: blur(5px);
    padding-left: 40px;
    border-radius: 17px;
    border: 2px solid #333;
    box-shadow: 0 4px 3px rgba(0, 0, 0, 0.2);
    /* Set a fixed height for the card */
    height: 600px; /* Fixed height for consistency */
    max-width: 1200px; /* Limit maximum width */
    width: 100%;
    align-items: stretch;
    overflow: hidden;
  }

  .card-image-container {
    position: relative;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  }

  .card-detail-image {
    max-height: 100%; /* Limit height to container */
    max-width: 100%; /* Limit width to container */
    width: auto; /* Let width adjust based on aspect ratio */
    height: auto; /* Let height adjust based on aspect ratio */
    object-fit: contain; /* Ensure entire image is visible */
    /* border-radius: 17px; */
    background-color: #1e1e1e;
  }

  .card-detail-media {
    max-height: 100%; /* Limit height to container */
    max-width: 100%; /* Limit width to container */
    width: auto; /* Let width adjust based on aspect ratio */
    height: auto; /* Let height adjust based on aspect ratio */
    object-fit: contain; /* Ensure entire media is visible */
    /* border-radius: 17px; */
    background-color: #1e1e1e;
  }

  .image-placeholder {
    width: 100%;
    height: 100%;
    aspect-ratio: 0.8;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #1e1e1e;
    color: #666;
    /* border-radius: 17px; */
  }

  .card-content-wrapper {
    display: flex;
    flex-direction: column;
    height: 100%;
    max-width: 350px;
    justify-content: center;
  }

  .card-header-section {
    /* margin-top: 64px; */
    position: relative;
    min-height: 150px;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
  }

  .title-container {
    position: absolute;
    bottom: 17px;
    width: 100%;
    text-align: center;
  }

  .card-header-section h1 {
    margin: 0;
    padding: 0;
    font-size: 48px;
    white-space: nowrap;
    font-size: 100px;
    line-height: 1;
    color: var(--text-color);
    display: inline-block;
    vertical-align: bottom;
    transform-origin: left bottom;
    transition: font-size 0.3s ease, line-height 0.3s ease, white-space 0.3s ease;
    text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.7);
    word-break: break-word; /* Add this for better text wrapping */
  }

  .card-header-section h1.wrapped {
    white-space: normal;
    line-height: 1.1;
    word-break: break-word;
    overflow-wrap: break-word;
    hyphens: auto;
  }

  .main-divider {
    height: 2px;
    width: 100%;
    background-color: #333;
    top: 20%;
    position: relative;
    bottom: -20px;
  }

  .card-description-section {
    padding: 30px 0;
  }

  .card-description {
    font-size: 18px;
    line-height: 1.6;
    color: var(--text-color);
    text-align: center; 
    position: relative;
  }

  .secondary-divider {
    height: 2px;
    width: 90%;
    transform: translateX(-50%);
    margin-left: 50%;
    background-color: #333;
    margin-top: 20px;
  }

  .card-info-section {
    padding: 30px 0;
  }

  .card-info-columns {
    display: flex;
    justify-content: space-around;
  }

  .card-info-column {
    flex: 1;
    text-align: center;
    position: relative;
  }

  .card-info-column h3 {
    font-size: 25px;
    margin-bottom: 10px;
    color: var(--accent-color);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: normal;
    gap: 10px;
  }

  .card-info-column p {
    font-size: 20px;
    line-height: 1.6;
    color: var(--text-color);
  }

  .comments-section {
    margin-top: auto;
    padding-top: 40px;
    text-align: center;
  }

  .no-comments {
    color: #666;
    font-style: italic;
    -webkit-touch-callout: none;
    -webkit-user-select: none;
    -khtml-user-select: none;
    -moz-user-select: none;
    -ms-user-select: none;
    user-select: none;
  }

  .comments-list {
    max-width: 800px;
    margin: 0 auto;
  }

  .comment {
    background-color: #1e1e1e;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 15px;
    text-align: left;
  }

  .comment-text {
    margin-bottom: 8px;
    color: var(--text-color);
  }

  .comment-meta {
    font-size: 14px;
    color: #aaa;
  }

  @media (max-width: 768px) {
    .card-detail {
      display: flex;
      flex-direction: column;
      gap: 20px;
      /* Reset height for mobile */
      height: auto;
    }
    .card-image-container {
      /* Reset height for mobile */
      height: auto;
    }
    .card-header-section {
      text-align: center;
      margin-top: -10px;
      min-height: 57px;
    }

    .card-content-wrapper {
      max-width: 100%;
      width: 100%; /* Full width on mobile */
      padding: 0 15px;
    }
    .title-container {
      max-width: 100%;
      overflow: hidden;
      position: relative;
      bottom: auto;
    }

    .card-header-section h1 {
      font-size: 36px;
      line-height: 1.1;
      margin: 0;
      padding: 0;
      white-space: nowrap;
      transition: all 0.3s ease;
      word-break: break-word;
    }
    .card-header-section h1.wrapped {
      line-height: 1.2;
      word-break: break-word;
    }

    .main-divider {
      margin-top: 15px;
    }
    .card-description {
      position: relative;
      left: -5%;
      width: 110%;
    }

    .card-detail-image {
      border-radius: 15px;
      /* Keep border on mobile if needed, but adjust height */
      height: 400px; /* Or whatever height works for mobile */
    }

    .edit-input {
      width: 100%;
    }
  }
</style>