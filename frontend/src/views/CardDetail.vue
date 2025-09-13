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
            <div class="card-image-container">
              <img 
                v-if="card.img && !imageError" 
                :src="`/card_imgs/${card.img}`" 
                :alt="card.name" 
                class="card-detail-image"
                @error="imageError = true"
                @dblclick="handleImageDoubleClick"
              />
              <!-- <button v-if="isUserAllowed" class="replace-image-button">Replace Image</button> -->
              <div v-else class="image-placeholder">No image available</div>
            </div>
            
            <div class="card-content-wrapper">
              <!-- Название карточки и главная разделительная линия -->
              <div class="card-header-section">
                <div class="title-container">
                  <h1 ref="cardNameRef">
                    
                    <span v-if="!editing.name">{{ card.name }}</span>
                    <input 
                      v-else
                      v-model="editableCard.name"
                      @blur="saveField('name')"
                      @keyup.enter="saveField('name')"
                      ref="nameInput"
                      class="edit-input"
                      maxlength="100"
                    >
                    <span v-if="isUserAllowed" class="edit-icon" @click="startEditing('name')">
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                      </svg>
                    </span>
                  </h1>
                </div>
                <div v-if="nameError" class="error-message">{{ nameError }}</div>
                <div class="main-divider"></div>
              </div>
              
              <!-- Описание карточки -->
              <div class="card-description-section">
                <div class="card-description">
                  <p v-if="!editing.description">{{ card.description }}</p>
                  <textarea
                    v-else
                    v-model="editableCard.description"
                    @blur="saveField('description')"
                    @keyup.enter="saveField('description')"
                    ref="descriptionInput"
                    maxlength="1000"
                    class="edit-textarea"
                  ></textarea>
                  <span v-if="isUserAllowed" class="edit-icon" @click="startEditing('description')">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                    </svg>
                  </span>
                </div>
                <div v-if="descriptionError" class="error-message">{{ descriptionError }}</div>
                <div class="secondary-divider"></div>
              </div>
              
              <!-- Информация о категории и сезоне -->
              <div class="card-info-section">
                <div class="card-info-columns">
                  <div class="card-info-column">
                    <h3>
                      Rarity:
                      <span v-if="isUserAllowed" class="edit-icon" @click.stop="toggleEdit('category')">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                        </svg>
                      </span>
                    </h3>
                    <div class="category-container">
                      <p v-if="!editing.category">{{ card.category }}</p>
                      <input
                        v-else
                        v-model="editableCard.category"
                        @blur="saveField('category')"
                        @keyup.enter="saveField('category')"
                        @keyup.esc="cancelEdit('category')"
                        ref="categoryInput"
                        class="edit-input"
                        maxlength="20"
                      >
                    </div>
                    <div v-if="categoryError" class="error-message">{{ categoryError }}</div>
                  </div>
                  <div class="card-info-column">
                    <h3>
                      Season:
                      <span v-if="isUserAllowed" class="edit-icon" @click.stop="toggleEdit('season')">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                        </svg>
                      </span>
                    </h3>
                    <div v-if="!isUserAllowed">
                      <p>{{ seasonName }}</p>
                    </div>
                    <select
                      v-else
                      v-if="isUserAllowed" 
                      v-model="editableCard.season_uuid"
                      @change="saveField('season')"
                      @blur="cancelEdit('season')"
                      ref="seasonInput"
                      class="edit-input-select"
                    >
                      <option class="edit-input-option" v-for="season in allSeasons" :key="season.uuid" :value="season.uuid">
                        {{ season.name }}
                      </option>
                    </select>
                  </div>
                </div>
              </div>
              
              <!-- Комментарии -->
              <div class="comments-section">
                <div v-if="comments.length === 0" class="no-comments">
                  No comments yet
                </div>
                <div v-else class="comments-list">
                  <div v-for="comment in comments" :key="comment.id" class="comment">
                    <div class="comment-text">{{ comment.text }}</div>
                    <div class="comment-meta">User #{{ comment.user_id }}</div>
                  </div>
                </div>
              </div>
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
  import { fetchCardInfo, fetchSeasonInfo, fetchComments, checkUserPermission, fetchUserInfo, fetchSeasons, fetchCardsForSeason } from '@/api'
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
      const seasonInput = ref(null)

      const card = ref({})
      const editableCard = ref({})
      const seasonName = ref('')
      const allSeasons = ref([])
      const comments = ref([])
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
        category: false,
        season: false
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

      const loadSortedCards = async () => {
        try {
          if (!card.value?.season_id) {
            console.log('No season_id on card:', card.value);
            return;
          }
          
          const cards = await fetchCardsForSeason(card.value.season_id, 'id', 'asc');
          sortedCards.value = cards;
          currentCardIndex.value = findCurrentCardIndex();
          
          console.log('Loaded cards:', cards);
          console.log('Current card ID:', card.value.id);
          console.log('Current card index:', currentCardIndex.value);
          console.log('Card IDs in sortedCards:', sortedCards.value.map(c => c.id));
          
          // Preload adjacent cards after we have the sorted list
          preloadAdjacentCards();
        } catch (error) {
          console.error('Error loading sorted cards:', error);
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

      const adjustFontSize = () => {
        nextTick(() => {
          if (!cardNameRef.value) return;
          
          const element = cardNameRef.value;
          const container = element.parentElement;
          
          element.style.fontSize = '';
          element.style.whiteSpace = 'nowrap';
          
          const containerWidth = container.clientWidth;
          let fontSize = 100;
          
          element.style.fontSize = `${fontSize}px`;
          void element.offsetWidth;
          
          if (element.scrollWidth > containerWidth) {
            const ratio = containerWidth / element.scrollWidth;
            fontSize = Math.max(
              28,
              Math.min(
                fontSize, 
                Math.floor(fontSize * ratio * 0.85)
              )
            );
            element.style.fontSize = `${fontSize}px`;
            
            if (element.scrollWidth > containerWidth * 1.05) {
              element.style.whiteSpace = 'normal';
              element.style.lineHeight = '1.2';
            }
          }
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
            case 'category':
              categoryInput.value?.focus()
              break
          }
        })
      }

      const saveField = async (field) => {
        saveError.value = null;
        try {
          let dataToSend = {};
          
          if (field === 'season') {
            dataToSend = {
              season_uuid: editableCard.value.season_uuid
            };
          } else if (field === 'category') {
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

          if (field === 'season') {
            const season = allSeasons.value.find(s => s.uuid === editableCard.value.season_uuid);
            seasonName.value = season?.name || '';
            card.value.season_uuid = editableCard.value.season_uuid;
          } else {
            card.value[field] = editableCard.value[field];
          }

          editing.value = { ...editing.value, [field]: false };
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
          
          const seasons = await fetchSeasons();
          allSeasons.value = seasons.map(season => ({
            uuid: season.uuid,
            name: season.name
          }));
          
          // Загружаем текущий сезон
          if (card.value.season_id) {
            const season = await fetchSeasonInfo(card.value.season_id);
            seasonName.value = season.name;
            editableCard.value.season_uuid = season.uuid;

            await loadSortedCards()
          }
          
          // Load comments
          comments.value = await fetchComments(card.value.id)
          
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
        showTransition.value = true; // Set flag before navigation
        transitionName.value = 'slide-right';
        const prevCard = sortedCards.value[currentCardIndex.value - 1];
        
        if (prevCard && preloadedCards.value[prevCard.id]) {
          // Use preloaded data if available
          card.value = preloadedCards.value[prevCard.id];
          editableCard.value = { ...card.value };
          currentCardIndex.value = currentCardIndex.value - 1;
          
          // Update URL without triggering a full reload
          router.replace(`/card/${prevCard.id}`);
          
          // Load season info and comments for the new card
          loadSeasonAndComments();
          
          // Preload new adjacent cards
          preloadAdjacentCards();
        } else if (prevCard) {
          // Fallback to regular navigation if not preloaded
          router.push(`/card/${prevCard.id}`);
        }
      }

      const goToNextCard = () => {
        if (isLastCard.value || currentCardIndex.value === -1) return;
        showTransition.value = true; // Set flag before navigation
        transitionName.value = 'slide-left';
        const nextCard = sortedCards.value[currentCardIndex.value + 1];
        
        if (nextCard && preloadedCards.value[nextCard.id]) {
          // Use preloaded data if available
          card.value = preloadedCards.value[nextCard.id];
          editableCard.value = { ...card.value };
          currentCardIndex.value = currentCardIndex.value + 1;
          
          // Update URL without triggering a full reload
          router.replace(`/card/${nextCard.id}`);
          
          // Load season info and comments for the new card
          loadSeasonAndComments();
          
          // Preload new adjacent cards
          preloadAdjacentCards();
        } else if (nextCard) {
          // Fallback to regular navigation if not preloaded
          router.push(`/card/${nextCard.id}`);
        }
      }

      const loadSeasonAndComments = async () => {
        try {
          if (card.value.season_id) {
            const season = await fetchSeasonInfo(card.value.season_id);
            seasonName.value = season.name;
            editableCard.value.season_uuid = season.uuid;
          }
          
          comments.value = await fetchComments(card.value.id);
          adjustFontSize();
        } catch (err) {
          console.error('Error loading season or comments:', err);
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

      return {
        card,
        editableCard,
        seasonName,
        categoryError, // Return categoryError
        allSeasons,
        comments,
        loading,
        error,
        nameError, // Return nameError
        descriptionError, // Return descriptionError
        saveError, // Return saveError
        imageError,
        cardNameRef,
        editing,
        isUserAllowed,
        nameInput,
        descriptionInput,
        categoryInput,
        seasonInput,
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
        loadSeasonAndComments,
        showTransition,
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
  .category-container p {
    color: white;
    font-size: 20px;
    margin: 0;
    word-break: break-word;
    text-align: center;
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
    height: 400px;
    background-image: url('/background.jpg');
    background-size: cover;
    background-position: center 57%;
    z-index: -1;
  }

  .card-detail-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 30px;
  }

  .card-detail {
    display: grid;
    grid-template-columns: 1fr 2fr;
    gap: 40px;
    margin-top: 140px;
  }

  .card-image-container {
    position: relative;
    /* cursor: pointer;  */
  }

  .card-detail-image {
    width: 100%;
    height: 571px;
    object-fit: fill;
    border-radius: 17px;
    border: 10px solid var(--bg-color);
    background-color: #1e1e1e;
    /* cursor: pointer;  */
  }

  .image-placeholder {
    width: 100%;
    height: 400px;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #1e1e1e;
    color: #666;
    border-radius: 17px;
    border: 10px solid var(--bg-color);
  }

  .card-content-wrapper {
    display: flex;
    flex-direction: column;
  }

  .card-header-section {
    margin-top: 64px;
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
  }

  .card-header-section h1 {
    margin: 0;
    padding: 0;
    white-space: nowrap;
    font-size: 100px;
    line-height: 1;
    color: var(--text-color);
    display: inline-block;
    vertical-align: bottom;
    transform-origin: left bottom;
    transition: font-size 0.2s ease;
    transition: color 0.3s ease, box-shadow 0.3s ease;
    text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.7);
  }

  .main-divider {
    height: 2px;
    width: 100%;
    background-color: var(--card-border-color);
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
    height: 1px;
    width: 100%;
    background-color: var(--card-border-color);
    margin-top: 30px;
  }

  .card-info-section {
    padding: 0px 0;
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
    }
    .card-header-section {
      text-align: center;
      margin-top: -10px;
      min-height: 57px;
    }

    .card-content-wrapper {
      padding: 0 15px;
    }
    .title-container {
      width: 100%;
      overflow: hidden;
      position: relative;
      bottom: auto;
    }

    .card-header-section h1 {
      font-size: 100px;
      line-height: 1.1;
      margin: 0;
      padding: 0;
      white-space: nowrap;
      transition: all 0.3s ease;
      word-break: break-word;
    }
    .card-header-section h1.force-wrap {
      white-space: normal;
      line-height: 1.3;
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
      border: 10px solid var(--bg-color);
    }

    .edit-input {
      width: 100%;
    }
  }
</style>