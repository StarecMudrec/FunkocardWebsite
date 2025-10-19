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

      <!-- Scroll container for horizontal snap -->
      <div class="cards-scroll-container" ref="scrollContainer">
        <div class="cards-scroll-wrapper">
          <!-- Previous card placeholder -->
          <div 
            v-if="hasPreviousCard" 
            class="card-slide"
            @click="goToPreviousCard"
          >
            <div class="card-placeholder">
              <div class="placeholder-content">
                <svg class="placeholder-arrow" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path d="M15 20.1L6.9 12 15 3.9z"/>
                </svg>
                <div class="placeholder-text">Previous Card</div>
              </div>
            </div>
          </div>

          <!-- Current card -->
          <div class="card-slide active">
            <div class="card-detail-container">
              <div class="card-detail">
                <div class="card-content-wrapper">
                  <!-- Название карточки и главная разделительная линия -->
                  <div class="card-header-section">
                    <div class="title-container">
                      <h1 ref="currentCardNameRef">
                        <span>{{ card.name }}</span>
                      </h1>
                    </div>
                    <div v-if="nameError" class="error-message">{{ nameError }}</div>
                    <div class="main-divider"></div>
                  </div>
                  
                  <!-- Rarity and Points section under main divider -->
                  <h3 style="margin: 60px 0px 10px;font-size: 24px;line-height: 1.6;color: var(--text-color);text-align: start;left: 30px;position: relative;font-weight: normal;text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.5);">
                    <strong>Rarity: </strong>{{ card.category }}
                  </h3>
                  <div v-if="categoryError" class="error-message">{{ categoryError }}</div>
                  
                  <p style="margin: 0;margin-bottom: 10px;font-size: 24px;line-height: 1.6;color: var(--text-color);text-align: start;left: 30px;position: relative;font-weight: normal;text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.5);" v-html="formatDescription(card.description)"></p>
                  <div v-if="descriptionError" class="error-message">{{ descriptionError }}</div>

                  
                  <div class="secondary-divider"></div>
                  
                  <!-- Available at shop section under secondary divider -->
                  <div class="shop-section">
                    <div class="shop-info">
                      <h3>Available at shop:</h3>
                      <p :class="{ 'available-glow': isShopAvailable(card.shop) }">
                        {{ formatShopInfo(card.shop) }}
                      </p>
                    </div>
                  </div>

                  <!-- Back to category button -->
                  <div class="back-to-category-section">
                    <button @click="goBackToCategory" class="back-to-category-button">
                      ← Back to {{ getCategoryDisplayName() }}
                    </button>
                  </div>
                </div>
                
                <div class="card-image-container">
                  <!-- Video for Limited cards -->
                  <video 
                    v-if="isLimitedCard && card.img && !mediaError" 
                    :src="`/api/card_image/${card.img}`" 
                    class="card-detail-media"
                    autoplay
                    loop
                    muted
                    playsinline
                    @error="mediaError = true"
                    @dblclick="handleMediaDoubleClick"
                    disablePictureInPicture
                  ></video>
                  
                  <!-- Image for non-Limited cards -->
                  <img 
                    v-else-if="card.img && !mediaError" 
                    :src="`/api/card_image/${card.img}`" 
                    :alt="card.name" 
                    class="card-detail-media"
                    @error="mediaError = true"
                    @dblclick="handleMediaDoubleClick"
                  />
                  
                  <div v-else class="image-placeholder">No media available</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Next card placeholder -->
          <div 
            v-if="hasNextCard" 
            class="card-slide"
            @click="goToNextCard"
          >
            <div class="card-placeholder">
              <div class="placeholder-content">
                <svg class="placeholder-arrow" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path d="M9 3.9L17.1 12 9 20.1z"/>
                </svg>
                <div class="placeholder-text">Next Card</div>
              </div>
            </div>
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
      const scrollContainer = ref(null)
      const currentCardNameRef = ref(null)

      const card = ref({})
      const editableCard = ref({})
      const loading = ref(true)
      const error = ref(null)
      const mediaError = ref(false)
      const saveError = ref(null)
      const nameError = ref(null)
      const descriptionError = ref(null)
      const categoryError = ref(null)
      const isUserAllowed = ref(false)

      // Card navigation
      const sortedCards = ref([])
      const currentCardIndex = ref(-1)
      const navigationInProgress = ref(false)

      const isFirstCard = computed(() => currentCardIndex.value <= 0)
      const isLastCard = computed(() => currentCardIndex.value >= sortedCards.value.length - 1)
      const hasPreviousCard = computed(() => !isFirstCard.value)
      const hasNextCard = computed(() => !isLastCard.value)

      // Computed property to check if current card is Limited
      const isLimitedCard = computed(() => {
        return card.value.category === 'Limited ⚠️';
      });

      const findCurrentCardIndex = () => {
        if (!card.value?.id || !sortedCards.value.length) return -1;
        
        const currentCardId = card.value.id.toString();
        return sortedCards.value.findIndex(c => c.id.toString() === currentCardId);
      }

      const scrollToCurrentCard = () => {
        if (!scrollContainer.value) return;
        
        const scrollWrapper = scrollContainer.value;
        const cardWidth = scrollWrapper.clientWidth;
        scrollWrapper.scrollTo({
          left: cardWidth,
          behavior: 'smooth'
        });
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

      const loadSortedCards = async () => {
        try {
          if (!card.value?.category) {
            console.log('No category on card:', card.value);
            return;
          }
          
          const previousCategory = sessionStorage.getItem('previousCategory');
          const savedSortState = sessionStorage.getItem(`category_state_${previousCategory}`);
          
          let sortField = 'id';
          let sortDirection = 'asc';
          
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
          
          const categoryId = previousCategory || `rarity_${card.value.category}`;
          console.log('Loading cards for category ID:', categoryId, 'with sort:', sortField, sortDirection);
          
          const response = await fetchCardsByCategory(categoryId, sortField, sortDirection);
          sortedCards.value = response.cards || [];
          currentCardIndex.value = findCurrentCardIndex();
          
          console.log('Loaded cards by category with sort:', sortedCards.value.length, 'cards');
          console.log('Current card ID:', card.value.id);
          console.log('Current card index:', currentCardIndex.value);
        } catch (error) {
          console.error('Error loading sorted cards by category:', error);
          sortedCards.value = [];
        }
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

      const adjustFontSize = () => {
        nextTick(() => {
          if (!currentCardNameRef.value) return;
          
          const element = currentCardNameRef.value;
          
          // Reset styles
          element.style.fontSize = '';
          element.style.whiteSpace = 'nowrap';
          element.style.lineHeight = '1';
          element.style.width = 'auto';
          element.style.height = 'auto';
          element.classList.remove('wrapped');
          
          const maxWidth = 350;
          const maxHeight = 150;
          const minSize = 32;
          const maxSize = 60;
          
          // Simple font size adjustment
          let fontSize = maxSize;
          let needsWrap = false;
          
          // Create temporary element for measurement
          const tempElement = element.cloneNode(true);
          tempElement.style.visibility = 'hidden';
          tempElement.style.position = 'absolute';
          tempElement.style.whiteSpace = 'nowrap';
          document.body.appendChild(tempElement);
          
          // Try without wrapping first
          let foundFit = false;
          for (let testSize = maxSize; testSize >= minSize; testSize -= 2) {
            tempElement.style.fontSize = `${testSize}px`;
            void tempElement.offsetWidth;
            
            if (tempElement.scrollWidth <= maxWidth) {
              fontSize = testSize;
              foundFit = true;
              break;
            }
          }
          
          // If no fit found without wrapping, try with wrapping
          if (!foundFit) {
            needsWrap = true;
            tempElement.style.whiteSpace = 'normal';
            tempElement.style.lineHeight = '1.1';
            tempElement.style.width = `${maxWidth}px`;
            
            for (let testSize = maxSize; testSize >= minSize; testSize -= 2) {
              tempElement.style.fontSize = `${testSize}px`;
              void tempElement.offsetWidth;
              
              if (tempElement.scrollHeight <= maxHeight) {
                fontSize = testSize;
                foundFit = true;
                break;
              }
            }
            
            if (!foundFit) {
              fontSize = minSize;
            }
          }
          
          // Clean up
          document.body.removeChild(tempElement);
          
          // Apply the calculated size
          element.style.fontSize = `${fontSize}px`;
          
          if (needsWrap) {
            element.classList.add('wrapped');
            element.style.whiteSpace = 'normal';
            element.style.lineHeight = '1.1';
            element.style.width = '100%';
          } else {
            element.style.whiteSpace = 'nowrap';
            element.style.lineHeight = '1';
            element.style.width = 'auto';
          }
        });
      };

      const handleMediaDoubleClick = () => {
        if (isUserAllowed.value && fileInput.value) {
          fileInput.value.click();
        }
      };

      const handleFileChange = async (event) => {
        const file = event.target.files[0];
        if (!file || !isUserAllowed.value) return;

        const formData = new FormData();
        formData.append('image', file);

        try {
          const response = await fetch(`/api/cards/${card.value.id}/image`, {
            method: 'PUT',
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            },
            body: formData
          });

          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to upload image');
          }

          loadData();
        } catch (err) {
          console.error('Error uploading image:', err);
        }
      };

      const loadData = async () => {
        try {
          loading.value = true;
          mediaError.value = false;
          navigationInProgress.value = false;
          
          card.value = await fetchCardInfo(props.id);
          editableCard.value = { ...card.value };
          
          await loadSortedCards();
          
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
          
          nextTick(() => {
            scrollToCurrentCard();
            setTimeout(adjustFontSize, 100);
          });
        } catch (err) {
          error.value = err.message || 'Failed to load card details'
          console.error('Error loading card:', err)
        } finally {
          loading.value = false
        }
      }

      const goToPreviousCard = () => {
        if (isFirstCard.value || currentCardIndex.value === -1 || sortedCards.value.length === 0 || navigationInProgress.value) {
          return;
        }
        
        navigationInProgress.value = true;
        const prevCard = sortedCards.value[currentCardIndex.value - 1];
        
        if (prevCard) {
          console.log('Navigating to previous card:', prevCard.id);
          router.push(`/card/${prevCard.id}`);
        }
      }

      const goToNextCard = () => {
        if (isLastCard.value || currentCardIndex.value === -1 || sortedCards.value.length === 0 || navigationInProgress.value) {
          return;
        }
        
        navigationInProgress.value = true;
        const nextCard = sortedCards.value[currentCardIndex.value + 1];
        
        if (nextCard) {
          console.log('Navigating to next card:', nextCard.id);
          router.push(`/card/${nextCard.id}`);
        }
      }

      onMounted(() => {
        window.addEventListener('resize', adjustFontSize)
        loadData()
        
        if (router.meta) {
          router.meta.navigationType = 'from-card-detail';
        }
      })

      onUnmounted(() => {
        window.removeEventListener('resize', adjustFontSize)
      })

      watch(() => props.id, async (newId) => {
        if (newId && card.value?.id !== newId) {
          await loadData()
        }
      })

      watch(() => card.value.name, (newName, oldName) => {
        if (newName !== oldName) {
          setTimeout(adjustFontSize, 100);
        }
      });

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
        currentCardNameRef,
        isUserAllowed,
        fileInput,
        scrollContainer,
        handleMediaDoubleClick,
        handleFileChange,
        isFirstCard,
        isLastCard,
        hasPreviousCard,
        hasNextCard,
        goToPreviousCard,
        goToNextCard,
        goBackToCategory,
        formatShopInfo,
        isShopAvailable,
        formatDescription,
        getCategoryDisplayName,
        isLimitedCard
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

  /* Scroll Snap Styles */
  .cards-scroll-container {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    overflow-x: auto;
    overflow-y: hidden;
    scroll-snap-type: x mandatory;
    scroll-behavior: smooth;
    -webkit-overflow-scrolling: touch;
    -ms-overflow-style: none;
    scrollbar-width: none;
  }

  .cards-scroll-container::-webkit-scrollbar {
    display: none;
  }

  .cards-scroll-wrapper {
    display: flex;
    height: 100%;
    width: 100%;
  }

  .card-slide {
    flex: 0 0 100%;
    height: 100%;
    scroll-snap-align: start;
    scroll-snap-stop: always;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 20px;
  }

  .card-slide.active {
    scroll-snap-align: center;
  }

  .card-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: rgba(30, 30, 30, 0.5);
    border-radius: 17px;
    border: 2px dashed #444;
    cursor: pointer;
    transition: all 0.3s ease;
  }

  .card-placeholder:hover {
    background-color: rgba(30, 30, 30, 0.7);
    border-color: var(--accent-color);
  }

  .placeholder-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 20px;
    color: var(--accent-color);
  }

  .placeholder-arrow {
    width: 60px;
    height: 60px;
    fill: var(--accent-color);
    opacity: 0.7;
  }

  .placeholder-text {
    font-size: 24px;
    font-weight: 500;
    text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.5);
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
    
    .card-slide {
      padding: 0 10px;
    }
    
    .placeholder-text {
      font-size: 18px;
    }
    
    .placeholder-arrow {
      width: 40px;
      height: 40px;
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
    display: flex;
    align-items: center;
    justify-content: center;
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

  .card-detail-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 67px;
    height: 100%;
    display: flex;
    align-items: stretch;
    width: 100%;
  }

  .card-detail {
    display: grid;
    grid-template-columns: 350px 1fr;
    gap: 40px;
    background-color: var(--card-bg);
    backdrop-filter: blur(5px);
    padding-left: 40px;
    border-radius: 17px;
    border: 2px solid #333;
    box-shadow: 0 4px 3px rgba(0, 0, 0, 0.2);
    height: 600px;
    max-width: 1200px;
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
    max-height: 100%;
    max-width: 100%;
    width: auto;
    height: auto;
    object-fit: contain;
    background-color: #1e1e1e;
  }

  .card-detail-media {
    max-height: 100%;
    max-width: 100%;
    width: auto;
    height: auto;
    object-fit: contain;
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
  }

  .card-content-wrapper {
    display: flex;
    flex-direction: column;
    height: 100%;
    max-width: 350px;
    justify-content: center;
  }

  .card-header-section {
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
    word-break: break-word;
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

  .nav-arrow.disabled {
    opacity: 0.2;
    pointer-events: none;
    cursor: not-allowed;
  }

  .card-detail-wrapper {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    overflow: hidden;
    -ms-overflow-style: none;
    scrollbar-width: none;
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
    pointer-events: none;
  }

  .arrow-icon {
    width: 100%;
    height: 100%;
    fill: var(--accent-color);
    pointer-events: auto;
  }

  .card-detail-container {
    position: relative;
    z-index: 1;
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
    color: #4ade80 !important;
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
    appearance: none;
    margin-top: 6px;
    background-image: url('data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2020%2020%22%20fill%3D%22none%22%20stroke%3D%22%23ffffff%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpolyline%20points%3D%226%209%2012%2015%2018%209%22%2F%3E%3C%2Fsvg%3E');
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
    font-size: 26px;
    font-family: var(--font-family-main);
    font-weight: 500;
    transition: background-color 0.3s ease;
  }

  @media (max-width: 768px) {
    .card-detail {
      display: flex;
      flex-direction: column;
      gap: 20px;
      height: auto;
    }
    .card-image-container {
      height: auto;
    }
    .card-header-section {
      text-align: center;
      margin-top: -10px;
      min-height: 57px;
    }

    .card-content-wrapper {
      max-width: 100%;
      width: 100%;
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
      height: 400px;
    }

    .edit-input {
      width: 100%;
    }
  }
</style>