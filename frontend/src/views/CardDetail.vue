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

      <transition :name="showTransition ? transitionName : ''">
        <div :key="card.id" class="card-detail-container">
          <div class="card-detail">
            <div class="card-content-wrapper">
              <!-- Название карточки и главная разделительная линия -->
              <div class="card-header-section">
                <div class="title-container">
                  <h1 ref="cardNameRef">
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
            </div>
            
            <div class="card-image-container">
              <img 
                v-if="card.img && !imageError" 
                :src="`/api/card_image/${card.img}`" 
                :alt="card.name" 
                class="card-detail-image"
                @error="imageError = true"
                @dblclick="handleImageDoubleClick"
              />
              <!-- <button v-if="isUserAllowed" class="replace-image-button">Replace Image</button> -->
              <div v-else class="image-placeholder">No image available</div>
            </div>
          </div>
        </div>
      </transition>
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
  // import $ from 'jquery';
  // import 'jquery-textfill';

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

      const card = ref({})
      const editableCard = ref({})
      const loading = ref(true)
      const error = ref(null)
      const imageError = ref(false)
      const saveError = ref(null)
      const nameError = ref(null)
      const descriptionError = ref(null)
      const categoryError = ref(null)
      const cardNameRef = ref(null)
      const isUserAllowed = ref(false)
      const editing = ref({
        name: false,
        description: false,
        category: false
      })
      const transitionName = ref('slide-left');

      // Card navigation
      const sortedCards = ref([])
      const currentCardIndex = ref(-1)

      const isFirstCard = computed(() => currentCardIndex.value <= 0)
      const isLastCard = computed(() => currentCardIndex.value >= sortedCards.value.length - 1)

      const preloadedCards = ref({})
      const isPreloading = ref(false)
      const preloadError = ref(null)

      const showTransition = ref(false);

      const findCurrentCardIndex = () => {
        if (!card.value?.id || !sortedCards.value.length) return -1;
        
        // Convert both IDs to strings for comparison
        const currentCardId = card.value.id.toString();
        return sortedCards.value.findIndex(c => c.id.toString() === currentCardId);
      }
      
      const formatDescription = (description) => {
        if (!description) return '';
        // Make "Points:" bold
        return description.replace(/Points:/g, '<strong>Points:</strong>');
      }

      const loadSortedCards = async () => {
        try {
          if (!card.value?.category) {
            console.log('No category on card:', card.value);
            return;
          }
          
          const cards = await fetchCardsByCategory(card.value.category, 'id', 'asc');
          sortedCards.value = cards;
          currentCardIndex.value = findCurrentCardIndex();
          
          console.log('Loaded cards by category:', cards);
          console.log('Current card ID:', card.value.id);
          console.log('Current card index:', currentCardIndex.value);
          console.log('Card IDs in sortedCards:', sortedCards.value.map(c => c.id));
          
          // Preload adjacent cards after we have the sorted list
          preloadAdjacentCards();
        } catch (error) {
          console.error('Error loading sorted cards by category:', error);
        }
      }

      // Add this new function to preload adjacent cards
      const preloadAdjacentCards = async () => {
        if (isPreloading.value || !sortedCards.value.length) return;
        
        isPreloading.value = true;
        preloadError.value = null;
        
        try {
          const preloadPromises = [];
          
          // Preload previous card if it exists
          if (currentCardIndex.value > 0) {
            const prevCardId = sortedCards.value[currentCardIndex.value - 1].id;
            if (!preloadedCards.value[prevCardId]) {
              preloadPromises.push(
                fetchCardInfo(prevCardId)
                  .then(cardData => {
                    preloadedCards.value[prevCardId] = cardData;
                  })
                  .catch(err => {
                    console.error(`Failed to preload card ${prevCardId}:`, err);
                  })
              );
            }
          }
          
          // Preload next card if it exists
          if (currentCardIndex.value < sortedCards.value.length - 1) {
            const nextCardId = sortedCards.value[currentCardIndex.value + 1].id;
            if (!preloadedCards.value[nextCardId]) {
              preloadPromises.push(
                fetchCardInfo(nextCardId)
                  .then(cardData => {
                    preloadedCards.value[nextCardId] = cardData;
                  })
                  .catch(err => {
                    console.error(`Failed to preload card ${nextCardId}:`, err);
                  })
              );
            }
          }
          
          await Promise.all(preloadPromises);
        } catch (err) {
          preloadError.value = err.message || 'Failed to preload cards';
          console.error('Error preloading cards:', err);
        } finally {
          isPreloading.value = false;
        }
      }

      const formatShopInfo = (shopData) => {
        if (!shopData || shopData === '-' || shopData === 'null' || shopData === 'None') {
          return 'Not available';
        }
        
        // If shop data is a simple string, return it as is
        if (typeof shopData === 'string') {
          return "Availible";
        }
        
        // If shop data is an object or needs formatting, handle it here
        return shopData.toString();
      }
      
      const isShopAvailable = (shopData) => {
        if (!shopData || shopData === '-' || shopData === 'null' || shopData === 'None') {
          return false;
        }
        
        // Check if the shop data indicates availability
        if (typeof shopData === 'string') {
          // You can add more conditions here if needed
          return shopData !== '-' && shopData !== 'null' && shopData !== 'None';
        }
        
        return false;
      }

      const isOverflown = ({ clientWidth, clientHeight, scrollWidth, scrollHeight }) => 
        scrollWidth > clientWidth || scrollHeight > clientHeight

      const resizeText = ({ 
        element, 
        minSize = 32, 
        maxSize = 60, 
        step = 1,
        maxWidth = 350,
        maxHeight = 150
      }) => {
        // Create a temporary parent container for measurement
        const tempParent = document.createElement('div');
        tempParent.style.width = `${maxWidth}px`;
        tempParent.style.height = `${maxHeight}px`;
        tempParent.style.visibility = 'hidden';
        tempParent.style.position = 'absolute';
        tempParent.style.top = '0';
        tempParent.style.left = '0';
        tempParent.style.overflow = 'hidden';
        
        const tempElement = element.cloneNode(true);
        tempElement.style.whiteSpace = 'nowrap';
        tempElement.style.width = 'auto';
        tempElement.style.height = 'auto';
        tempElement.style.lineHeight = '1';
        
        tempParent.appendChild(tempElement);
        document.body.appendChild(tempParent);
        
        // Try without wrapping first
        let i = minSize;
        let overflow = false;
        let needsWrap = false;
        
        while (!overflow && i < maxSize) {
          tempElement.style.fontSize = `${i}px`;
          
          // Force reflow
          void tempElement.offsetWidth;
          
          // Check for overflow
          overflow = isOverflown({
            clientWidth: maxWidth,
            clientHeight: maxHeight,
            scrollWidth: tempElement.scrollWidth,
            scrollHeight: tempElement.scrollHeight
          });
          
          if (!overflow) i += step;
        }
        
        let optimalSize = overflow ? i - step : i;
        
        // If text doesn't fit even at minimum size, try with text wrapping
        if (optimalSize <= minSize && overflow) {
          // Reset for wrapped text
          tempElement.style.whiteSpace = 'normal';
          tempElement.style.lineHeight = '1.1';
          tempElement.style.width = '100%';
          
          i = minSize;
          overflow = false;
          
          while (!overflow && i < maxSize) {
            tempElement.style.fontSize = `${i}px`;
            
            // Force reflow
            void tempElement.offsetWidth;
            
            // Check only vertical overflow for wrapped text
            overflow = tempElement.scrollHeight > maxHeight;
            
            if (!overflow) i += step;
          }
          
          optimalSize = overflow ? i - step : i;
          needsWrap = true;
        }
        
        // Clean up
        document.body.removeChild(tempParent);
        
        return { optimalSize, needsWrap };
      }

      const adjustFontSize = () => {
        nextTick(() => {
          if (!cardNameRef.value) return;
          
          const element = cardNameRef.value;
          
          // Reset styles
          element.style.fontSize = '';
          element.style.whiteSpace = 'nowrap';
          element.style.lineHeight = '1';
          element.style.width = 'auto';
          element.style.height = 'auto';
          element.classList.remove('wrapped');
          
          const { optimalSize, needsWrap } = resizeText({
            element: element,
            minSize: 32,
            maxSize: 60,
            step: 1,
            maxWidth: 350,
            maxHeight: 150
          });
          
          // Apply the calculated size to the actual element
          element.style.fontSize = `${optimalSize}px`;
          
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
          
          console.log('Configurable approach - Font size:', optimalSize, 'Wrapped:', needsWrap);
        });
      };
      const fallbackAdjustFontSize  = () => {
        nextTick(() => {
          if (!cardNameRef.value) return;
          
          const element = cardNameRef.value;
          const container = element.parentElement;
          
          if (!container) return;
          
          // Reset styles
          element.style.fontSize = '';
          element.classList.remove('wrapped');
          element.style.whiteSpace = 'nowrap';
          element.style.lineHeight = '1';
          element.style.width = 'auto';
          element.style.height = 'auto';
          
          const containerWidth = container.clientWidth;
          const containerHeight = 150;
          const maxWidth = 350;
          
          // Get the actual text content
          const text = element.textContent || element.innerText;
          
          let fontSize = 60;
          let needsWrap = false;
          
          // Create a temporary clone to measure text more accurately
          const tempElement = element.cloneNode(true);
          tempElement.style.visibility = 'hidden';
          tempElement.style.position = 'absolute';
          tempElement.style.whiteSpace = 'nowrap';
          document.body.appendChild(tempElement);
          
          // First, try without wrapping
          let foundFit = false;
          for (let testSize = 60; testSize >= 32; testSize -= 2) {
            tempElement.style.fontSize = `${testSize}px`;
            
            // Force reflow
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
            
            // Reset to find best size with wrapping
            for (let testSize = 60; testSize >= 32; testSize -= 2) {
              tempElement.style.fontSize = `${testSize}px`;
              
              // Force reflow
              void tempElement.offsetWidth;
              
              if (tempElement.scrollHeight <= containerHeight) {
                fontSize = testSize;
                foundFit = true;
                break;
              }
            }
            
            // If still no fit, use minimum size
            if (!foundFit) {
              fontSize = 32;
            }
          }
          
          // Clean up temporary element
          document.body.removeChild(tempElement);
          
          // Apply the calculated size to the actual element
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
          
          console.log('Final font size:', fontSize, 'Wrapped:', needsWrap, 'Text:', text);
        });
      };

      const toggleEdit = (field) => {
        if (editing.value[field]) {
          cancelEdit(field)
        } else {
          startEditing(field)
        }
      }

      const cancelEdit = (field) => {
        editing.value = { ...editing.value, [field]: false }
      }

      const startEditing = (field) => {
        editing.value = { ...editing.value, [field]: true }
        editableCard.value = { ...card.value }
        
        nextTick(() => {
          switch(field) {
            case 'name':
              nameInput.value?.focus()
              nameInput.value?.select()
              break
            case 'category':
              categoryInput.value?.focus()
              categoryInput.value?.select()
              break;
            case 'description':
              descriptionInput.value?.focus()
              break
          }
        })
      }

      const saveField = async (field) => {
        saveError.value = null;
        try {
          let dataToSend = {};
          
          if (field === 'category') {
              if (editableCard.value.category && editableCard.value.category.length > 20) {
                  categoryError.value = 'Category cannot exceed 20 characters.';
                  throw new Error('Validation failed on frontend.');
              }
              dataToSend = { [field]: editableCard.value[field] };
          } else {
            dataToSend = {
              [field]: editableCard.value[field]
            };
          }

          const response = await fetch(`/api/cards/${card.value.id}`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            },
            body: JSON.stringify(dataToSend)
          });

          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to update card');
          }

          card.value[field] = editableCard.value[field];
          editing.value = { ...editing.value, [field]: false };
          
          // Reload sorted cards if category was changed
          if (field === 'category') {
            await loadSortedCards();
          }
        } catch (err) {
          console.error('Error updating card:', err);
          saveError.value = err.message || 'Failed to update card';
        }
      }

      const handleImageDoubleClick = () => {
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
          
          card.value = await fetchCardInfo(props.id);
          editableCard.value = { ...card.value };
          
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
          
          setTimeout(adjustFontSize, 0)
        } catch (err) {
          error.value = err.message || 'Failed to load card details'
          console.error('Error loading card:', err)
        } finally {
          loading.value = false
        }
      }

      const goToPreviousCard = () => {
        if (isFirstCard.value || currentCardIndex.value === -1) return;
        showTransition.value = true;
        transitionName.value = 'slide-right';
        const prevCard = sortedCards.value[currentCardIndex.value - 1];
        
        if (prevCard && preloadedCards.value[prevCard.id]) {
          card.value = preloadedCards.value[prevCard.id];
          editableCard.value = { ...card.value };
          currentCardIndex.value = currentCardIndex.value - 1;
          
          router.replace(`/card/${prevCard.id}`);
          
          // Add this line
          setTimeout(adjustFontSize, 300);
          
          preloadAdjacentCards();
        } else if (prevCard) {
          router.push(`/card/${prevCard.id}`);
        }
      }

      const goToNextCard = () => {
        if (isLastCard.value || currentCardIndex.value === -1) return;
        showTransition.value = true;
        transitionName.value = 'slide-left';
        const nextCard = sortedCards.value[currentCardIndex.value + 1];
        
        if (nextCard && preloadedCards.value[nextCard.id]) {
          card.value = preloadedCards.value[nextCard.id];
          editableCard.value = { ...card.value };
          currentCardIndex.value = currentCardIndex.value + 1;
          
          router.replace(`/card/${nextCard.id}`);
          
          // Add this line
          setTimeout(adjustFontSize, 300);
          
          preloadAdjacentCards();
        } else if (nextCard) {
          router.push(`/card/${nextCard.id}`);
        }
      }

      onMounted(() => {
        window.addEventListener('resize', adjustFontSize)
        loadData()
      })

      onUnmounted(() => {
        window.removeEventListener('resize', adjustFontSize)
      })

      // Watch for card changes to preload new adjacent cards
      watch(() => card.value.id, (newId) => {
        if (newId) {
          preloadAdjacentCards();
        }
      })

      watch(() => props.id, async (newId) => {
        if (newId && card.value?.id !== newId) {
          await loadData()
          showTransition.value = false; // Reset after navigation
        }
      })

      watch(() => editableCard.value.name, (newName) => {
        if (newName && newName.length > 100) {
          nameError.value = 'Name cannot exceed 100 characters.';
        } else {
          nameError.value = null;
        }
      });

      watch(() => editableCard.value.description, (newDescription) => {
        if (newDescription && newDescription.length > 1000) {
          descriptionError.value = 'Description cannot exceed 1000 characters.';
        } else {
          descriptionError.value = null;
        }
      });

      watch(() => editableCard.value.category, (newCategory) => {
        if (newCategory && newCategory.length > 20) {
          categoryError.value = 'Category cannot exceed 20 characters.';
        } else {
          categoryError.value = null;
        }
      });

      // Add this to your existing watchers
      watch(() => card.value.name, (newName, oldName) => {
        if (newName !== oldName) {
          setTimeout(adjustFontSize, 100);
        }
      });

      watch(showTransition, (newVal) => {
        if (!newVal) {
          // Transition ended, adjust font size
          setTimeout(adjustFontSize, 50);
        }
      });

      // Add this to your existing watchers
      watch(() => loading.value, (newLoading) => {
        if (!newLoading) {
          // Component finished loading, adjust font size with delays
          setTimeout(adjustFontSize, 100);
          setTimeout(adjustFontSize, 500);
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
        imageError,
        cardNameRef,
        editing,
        isUserAllowed,
        nameInput,
        descriptionInput,
        categoryInput,
        fileInput,
        handleImageDoubleClick,
        handleFileChange,
        startEditing,
        saveField,
        toggleEdit,
        cancelEdit,
        fileInput,  
        handleImageDoubleClick,
        handleFileChange,
        isFirstCard,
        isLastCard,
        goToPreviousCard,
        goToNextCard,
        transitionName,
        preloadedCards,
        isPreloading,
        preloadError,
        showTransition,
        formatShopInfo,
        isShopAvailable,
        formatDescription,
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
    transform: translateX(100%) translateY(-100%); /* Added translateY */
    opacity: 0;
  }

  .slide-left-enter-to {
    transform: translateX(0) translateY(-100%); /* Added translateY */
    opacity: 1;
  }

  .slide-left-leave-from {
    transform: translateX(0) translateY(0);
    opacity: 1;
  }

  .slide-left-leave-to {
    transform: translateX(-100%) translateY(0);
    opacity: 0;
  }

  .slide-right-enter-from {
    transform: translateX(-100%) translateY(-100%); /* Added translateY */
    opacity: 0;
  }

  .slide-right-enter-to {
    transform: translateX(0) translateY(-100%); /* Added translateY */
    opacity: 1;
  }

  .slide-right-leave-from {
    transform: translateX(0) translateY(0);
    opacity: 1;
  }

  .slide-right-leave-to {
    transform: translateX(100%) translateY(0);
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