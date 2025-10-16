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

              <!-- Back to category button -->
              <div class="back-to-category-section">
                <button @click="goBackToCategory" class="back-to-category-button">
                  <svg class="back-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="m15 18-6-6 6-6"/>
                  </svg>
                  Back to {{ card.category }}
                </button>
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
          
          // For navigation, we need to use the category ID format that matches the API
          // The API expects categories in the format "rarity_{categoryName}"
          const categoryId = `rarity_${card.value.category}`;
          console.log('Loading cards for category ID:', categoryId);
          
          const cards = await fetchCardsByCategory(categoryId, 'id', 'asc');
          
          // Ensure cards is an array, fallback to empty array if not
          sortedCards.value = Array.isArray(cards) ? cards : [];
          currentCardIndex.value = findCurrentCardIndex();
          
          console.log('Loaded cards by category:', sortedCards.value);
          console.log('Current card ID:', card.value.id);
          console.log('Current card index:', currentCardIndex.value);
          console.log('Card IDs in sortedCards:', sortedCards.value.map(c => c.id));
          
          // Preload adjacent cards after we have the sorted list
          preloadAdjacentCards();
        } catch (error) {
          console.error('Error loading sorted cards by category:', error);
          // Set to empty array on error to prevent future errors
          sortedCards.value = [];
          // Don't throw the error here, just log it
          // This allows the card detail to still load even if navigation fails
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

      // Add the goBackToCategory method
      const goBackToCategory = () => {
        // Use the navigation type to indicate we're returning to category
        if (router.meta) {
          router.meta.navigationType = 'to-category'
        }
        
        // Navigate back to the category page
        if (card.value?.category) {
          const categoryId = `rarity_${card.value.category}`
          router.push(`/category/${categoryId}`)
        } else {
          // Fallback: go back in history
          router.go(-1)
        }
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
          
          // Load sorted cards for navigation, but don't block the UI if it fails
          loadSortedCards().catch(err => {
            console.error('Failed to load sorted cards for navigation:', err);
            // Continue loading the card detail even if navigation fails
          });
          
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
        if (isFirstCard.value || currentCardIndex.value === -1 || sortedCards.value.length === 0) {
          console.log('Cannot go to previous card - no cards loaded or at beginning');
          return;
        }
        
        showTransition.value = true;
        transitionName.value = 'slide-right';
        const prevCard = sortedCards.value[currentCardIndex.value - 1];
        
        if (prevCard) {
          console.log('Navigating to previous card:', prevCard.id);
          // Set navigation type before navigating
          router.push(`/card/${prevCard.id}`);
        } else {
          console.log('No previous card available');
        }
      }

      const goToNextCard = () => {
        if (isLastCard.value || currentCardIndex.value === -1 || sortedCards.value.length === 0) {
          console.log('Cannot go to next card - no cards loaded or at end');
          return;
        }
        
        showTransition.value = true;
        transitionName.value = 'slide-left';
        const nextCard = sortedCards.value[currentCardIndex.value + 1];
        
        if (nextCard) {
          console.log('Navigating to next card:', nextCard.id);
          // Set navigation type before navigating
          router.push(`/card/${nextCard.id}`);
        } else {
          console.log('No next card available');
        }
      }

      onMounted(() => {
        window.addEventListener('resize', adjustFontSize)
        loadData()
        
        // Set navigation type when entering card detail
        if (router.meta) {
          router.meta.navigationType = 'from-card-detail';
        }
      })

      onUnmounted(() => {
        window.removeEventListener('resize', adjustFontSize)
        
        // Set navigation type when leaving card detail to return to category
        // This is handled by the router navigation guard now
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
        goBackToCategory, // Add this to the return object
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
  /* ... (all existing styles remain the same) ... */

  /* Back to category button styles */
  .back-to-category-section {
    text-align: center;
    margin-top: 20px;
  }

  .back-to-category-button {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid #333;
    border-radius: 8px;
    color: var(--text-color);
    padding: 10px 20px;
    cursor: pointer;
    font-size: 16px;
    font-family: 'Afacad', sans-serif;
    transition: all 0.3s ease;
    text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.5);
  }

  .back-to-category-button:hover {
    background: rgba(255, 255, 255, 0.15);
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  }

  .back-to-category-button:active {
    transform: translateY(0);
  }

  .back-icon {
    width: 16px;
    height: 16px;
  }

  /* Mobile responsive adjustments */
  @media (max-width: 768px) {
    .back-to-category-button {
      padding: 8px 16px;
      font-size: 14px;
    }
    
    .back-icon {
      width: 14px;
      height: 14px;
    }
  }
</style>