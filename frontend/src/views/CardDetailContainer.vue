<template>  
  <div class="card-detail-container" :class="{ 'active': isActive }" ref="containerRef">
    <div class="card-detail">
      <div class="card-content-wrapper">
        <!-- Card Name and Main Divider -->
        <div class="card-header-section">
          <div class="title-container">
            <h1 ref="cardNameRef">
              <span v-if="!editing.name">{{ card.name }}</span>
              <input
                v-else
                ref="nameInput"
                v-model="editableCard.name"
                class="edit-input"
                @blur="saveField('name')"
                @keyup.enter="saveField('name')"
                @keyup.escape="cancelEdit('name')"
              />
            </h1>
            <div v-if="isUserAllowed && isActive" class="edit-icon" @click="toggleEdit('name')">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </div>
          </div>
          <div v-if="nameError" class="error-message">{{ nameError }}</div>
          <div class="main-divider"></div>
        </div>
        
        <!-- Rarity and Points section -->
        <h3 class="rarity" style="margin: 60px 0px 10px;font-size: 24px;line-height: 1.6;color: var(--text-color);text-align: start;left: 30px;position: relative;font-weight: normal;text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.5);">
          <strong>Rarity: </strong>
          <span v-if="!editing.category">{{ card.category }}</span>
          <select
            v-else
            ref="categoryInput"
            v-model="editableCard.category"
            class="edit-input-select"
            @blur="saveField('category')"
            @keyup.enter="saveField('category')"
            @keyup.escape="cancelEdit('category')"
          >
            <option value="Common">Common</option>
            <option value="Uncommon">Uncommon</option>
            <option value="Rare">Rare</option>
            <option value="Epic">Epic</option>
            <option value="Legendary">Legendary</option>
            <option value="Limited ⚠️">Limited ⚠️</option>
          </select>
          <div v-if="isUserAllowed && isActive" class="edit-icon" @click="toggleEdit('category')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </div>
        </h3>
        <div v-if="categoryError" class="error-message">{{ categoryError }}</div>
        
        <p class="points" style="margin: 0;margin-bottom: 10px;font-size: 24px;line-height: 1.6;color: var(--text-color);text-align: start;left: 30px;position: relative;font-weight: normal;text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.5);">
          <span v-if="!editing.description" v-html="formatDescription(card.description)"></span>
          <textarea
            v-else
            ref="descriptionInput"
            v-model="editableCard.description"
            class="edit-textarea"
            @blur="saveField('description')"
            @keyup.enter="saveField('description')"
            @keyup.escape="cancelEdit('description')"
            rows="4"
          ></textarea>
          <div v-if="isUserAllowed && isActive" class="edit-icon" @click="toggleEdit('description')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </div>
        </p>
        <div v-if="descriptionError" class="error-message">{{ descriptionError }}</div>

        <!-- Season section - ADDED THIS -->
        <div class="season-section">
          <h3 style="margin: 0px;font-size: 24px;line-height: 1.6;color: var(--text-color);text-align: start;left: 30px;position: relative;font-weight: normal;text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.5);">
            <strong>Season: </strong>
            <span>{{ formatSeasonInfo(card.season, card.upload_date) }}</span>
          </h3>
          <p v-if="card.upload_date" style="margin: 0;font-size: 18px;line-height: 1.6;color: #888888;text-align: start;left: 40px;position: relative;font-weight: normal;text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.5);">
            Uploaded: {{ formatUploadDate(card.upload_date) }}
          </p>
        </div>

        <div class="secondary-divider"></div>
        
        <!-- Available at shop section -->
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
          <button @click="$emit('go-back')" class="back-to-category-button">
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
          @dblclick="$emit('media-double-click')"
          disablePictureInPicture
        ></video>
        
        <!-- Image for non-Limited cards -->
        <img 
          v-else-if="card.img && !mediaError" 
          :src="`/api/card_image/${card.img}`" 
          :alt="card.name" 
          class="card-detail-media"
          @error="mediaError = true"
          @dblclick="$emit('media-double-click')"
        />
        
        <div v-else class="image-placeholder">No media available</div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { fetchUserInfo, checkUserPermission } from '@/api'

export default {
  props: {
    card: {
      type: Object,
      required: true
    },
    isActive: {
      type: Boolean,
      default: false
    }
  },
  emits: ['media-double-click', 'go-back', 'save-error'],
  setup(props, { emit }) {
    const mediaError = ref(false)
    const cardNameRef = ref(null)
    const nameInput = ref(null)
    const descriptionInput = ref(null)
    const categoryInput = ref(null)
    const containerRef = ref(null)

    const editableCard = ref({})
    const saveError = ref(null)
    const nameError = ref(null)
    const descriptionError = ref(null)
    const categoryError = ref(null)
    const isUserAllowed = ref(false)
    const editing = ref({
      name: false,
      description: false,
      category: false
    })

    const isLimitedCard = computed(() => {
      return props.card.category === 'Limited ⚠️'
    })

    const formatDescription = (description) => {
      if (!description) return ''
      return description.replace(/Points:/g, '<strong>Points:</strong>')
    }

    const formatShopInfo = (shopData) => {
      if (!shopData || shopData === '-' || shopData === 'null' || shopData === 'None') {
        return 'Not available'
      }
      if (typeof shopData === 'string') {
        return "Available"
      }
      return shopData.toString()
    }
    
    const isShopAvailable = (shopData) => {
      if (!shopData || shopData === '-' || shopData === 'null' || shopData === 'None') {
        return false
      }
      if (typeof shopData === 'string') {
        return shopData !== '-' && shopData !== 'null' && shopData !== 'None'
      }
      return false
    }

    // ADDED: Season formatting functions
    const formatSeasonInfo = (season, uploadDate) => {
      if (season && season !== 1) {
        return `Season ${season}`
      }
      if (uploadDate) {
        return 'Season 1'
      }
      return 'Unknown Season'
    }

    const formatUploadDate = (uploadDate) => {
      if (!uploadDate) return 'Unknown date'
      
      try {
        const date = new Date(uploadDate)
        return date.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        })
      } catch (error) {
        console.error('Error formatting upload date:', error)
        return 'Invalid date'
      }
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
        return props.card?.category || 'Category'
      }
    }

    // ... rest of the existing functions remain the same (isOverflown, resizeText, adjustFontSize, etc.)

    // Font size adjustment functions
    const isOverflown = ({ clientWidth, clientHeight, scrollWidth, scrollHeight }) => 
      scrollWidth > clientWidth || scrollHeight > clientHeight

    const resizeText = ({ 
      element, 
      minSize = 32, 
      maxSize = 60, 
      step = 1,
      maxWidth = 350,
      maxHeight = 120
    }) => {
      const tempParent = document.createElement('div')
      tempParent.style.width = `${maxWidth}px`
      tempParent.style.height = `${maxHeight}px`
      tempParent.style.visibility = 'hidden'
      tempParent.style.position = 'absolute'
      tempParent.style.top = '0'
      tempParent.style.left = '0'
      tempParent.style.overflow = 'hidden'
      
      const tempElement = element.cloneNode(true)
      tempElement.style.whiteSpace = 'nowrap'
      tempElement.style.width = 'auto'
      tempElement.style.height = 'auto'
      tempElement.style.lineHeight = '1'
      
      tempParent.appendChild(tempElement)
      document.body.appendChild(tempParent)
      
      let i = minSize
      let overflow = false
      let needsWrap = false
      
      while (!overflow && i < maxSize) {
        tempElement.style.fontSize = `${i}px`
        void tempElement.offsetWidth
        
        overflow = isOverflown({
          clientWidth: maxWidth,
          clientHeight: maxHeight,
          scrollWidth: tempElement.scrollWidth,
          scrollHeight: tempElement.scrollHeight
        })
        
        if (!overflow) i += step
      }
      
      let optimalSize = overflow ? i - step : i
      
      if (optimalSize <= minSize && overflow) {
        tempElement.style.whiteSpace = 'normal'
        tempElement.style.lineHeight = '1.1'
        tempElement.style.width = '100%'
        
        i = minSize
        overflow = false
        
        while (!overflow && i < maxSize) {
          tempElement.style.fontSize = `${i}px`
          void tempElement.offsetWidth
          overflow = tempElement.scrollHeight > maxHeight
          
          if (!overflow) i += step
        }
        
        optimalSize = overflow ? i - step : i
        needsWrap = true
      }
      
      document.body.removeChild(tempParent)
      
      return { optimalSize, needsWrap }
    }

    const adjustFontSize = () => {
      nextTick(() => {
        if (!cardNameRef.value) return
        
        const element = cardNameRef.value
        
        element.style.fontSize = ''
        element.style.whiteSpace = 'nowrap'
        element.style.lineHeight = '1'
        element.style.width = 'auto'
        element.style.height = 'auto'
        element.classList.remove('wrapped')
        
        const { optimalSize, needsWrap } = resizeText({
          element: element,
          minSize: 32,
          maxSize: 60,
          step: 1,
          maxWidth: 350,
          maxHeight: 120
        })
        
        element.style.fontSize = `${optimalSize}px`
        
        if (needsWrap) {
          element.classList.add('wrapped')
          element.style.whiteSpace = 'normal'
          element.style.lineHeight = '1.1'
          element.style.width = '100%'
        } else {
          element.style.whiteSpace = 'nowrap'
          element.style.lineHeight = '1'
          element.style.width = 'auto'
        }
      })
    }

    // Editing functions
    const toggleEdit = (field) => {
      if (editing.value[field]) {
        cancelEdit(field)
      } else {
        startEditing(field)
      }
    }

    const cancelEdit = (field) => {
      editing.value = { ...editing.value, [field]: false }
      editableCard.value = { ...props.card }
    }

    const startEditing = (field) => {
      if (!isUserAllowed.value || !props.isActive) return
      
      editing.value = { ...editing.value, [field]: true }
      editableCard.value = { ...props.card }
      
      nextTick(() => {
        switch(field) {
          case 'name':
            nameInput.value?.focus()
            nameInput.value?.select()
            break
          case 'category':
            categoryInput.value?.focus()
            categoryInput.value?.select()
            break
          case 'description':
            descriptionInput.value?.focus()
            break
        }
      })
    }

    const saveField = async (field) => {
      if (!isUserAllowed.value || !props.isActive) return
      
      saveError.value = null
      try {
        let dataToSend = {}
        
        if (field === 'category') {
          if (editableCard.value.category && editableCard.value.category.length > 20) {
            categoryError.value = 'Category cannot exceed 20 characters.'
            throw new Error('Validation failed on frontend.')
          }
          dataToSend = { [field]: editableCard.value[field] }
        } else {
          dataToSend = {
            [field]: editableCard.value[field]
          }
        }

        const response = await fetch(`/api/cards/${props.card.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`
          },
          body: JSON.stringify(dataToSend)
        })

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.error || 'Failed to update card')
        }

        // Update the card prop (parent will handle this)
        props.card[field] = editableCard.value[field]
        editing.value = { ...editing.value, [field]: false }
        
        emit('save-error', null)
      } catch (err) {
        console.error('Error updating card:', err)
        saveError.value = err.message || 'Failed to update card'
        emit('save-error', saveError.value)
      }
    }

    // Check user permissions
    const checkPermissions = async () => {
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

    // Validation watchers
    watch(() => editableCard.value.name, (newName) => {
      if (newName && newName.length > 100) {
        nameError.value = 'Name cannot exceed 100 characters.'
      } else {
        nameError.value = null
      }
    })

    watch(() => editableCard.value.description, (newDescription) => {
      if (newDescription && newDescription.length > 1000) {
        descriptionError.value = 'Description cannot exceed 1000 characters.'
      } else {
        descriptionError.value = null
      }
    })

    watch(() => editableCard.value.category, (newCategory) => {
      if (newCategory && newCategory.length > 20) {
        categoryError.value = 'Category cannot exceed 20 characters.'
      } else {
        categoryError.value = null
      }
    })

    // Watch for card name changes to adjust font size
    watch(() => props.card.name, () => {
      if (props.isActive) {
        setTimeout(adjustFontSize, 100)
      }
    })

    onMounted(() => {
      editableCard.value = { ...props.card }
      checkPermissions()
      
      if (props.isActive) {
        setTimeout(adjustFontSize, 100)
        setTimeout(adjustFontSize, 500)
      }
    })

    return {
      mediaError,
      cardNameRef,
      nameInput,
      descriptionInput,
      categoryInput,
      editableCard,
      saveError,
      nameError,
      descriptionError,
      categoryError,
      isUserAllowed,
      editing,
      isLimitedCard,
      formatDescription,
      formatShopInfo,
      isShopAvailable,
      formatSeasonInfo, // ADDED
      formatUploadDate, // ADDED
      getCategoryDisplayName,
      toggleEdit,
      cancelEdit,
      saveField,
      containerRef,
      adjustFontSize
    }
  }
}
</script>

<style scoped>
.card-detail-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 67px;
  height: 100%;
  display: flex;
  align-items: center;
}

.card-detail {
  display: grid;
  grid-template-columns: 400px 1fr;
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

.card-detail-media {
  max-height: 100%;
  max-width: 100%;
  width: auto;
  height: auto;
  object-fit: contain;
  background-color: #1e1e1e;
  -webkit-touch-callout: none;
  -webkit-user-select: none;
  -khtml-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  user-select: none;
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
  -webkit-touch-callout: none;
  -webkit-user-select: none;
  -khtml-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  user-select: none;
}

.card-content-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-width: 400px;
  justify-content: center;
  /* padding-top: 30px; */
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
  /* bottom: 17px; */
  width: 100%;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
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

.secondary-divider {
  height: 2px;
  width: 90%;
  transform: translateX(-50%);
  margin-left: 50%;
  background-color: #333;
  margin-top: 20px;
}

/* ADDED: Season section styles */
.season-section {
  margin-bottom: 10px;
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

.back-to-category-section {
  text-align: center;
  margin-top: -17px;
  margin-bottom: 40px;
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

/* Edit icon styles */
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

/* Edit input styles */
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

.edit-input-select:focus {
  outline: none;
  box-shadow: none;
  background-color: transparent;
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

.error-message {
  color: #ff6b6b;
  font-size: 14px;
  margin-top: 5px;
  text-align: center;
}

@media (max-width: 1150px) {
  .card-detail {
    grid-template-columns: 300px 1fr;
  }
}

@media (max-width: 1050px) {
  .card-detail {
    height: auto;
    display: flex;
    flex-direction: column-reverse;
    align-items: center;
    padding: 0;
    gap: 10px;
    border-radius: 30px;
    margin-top: 100px;
    min-height: auto;
  }

  .card-detail-container {
    align-items: flex-start;
    overflow-y: auto;
    scrollbar-width: none;
    padding: 20px;
  }

  .card-content-wrapper {
    max-width: 100%;
    width: 100%;
    justify-content: flex-start;
    padding: 0px 30px;
    min-height: auto;
  }

  .card-header-section {
    position: relative;
    min-height: 120px; /* Reduce minimum height */
    height: auto; /* Allow height to adjust */
    display: flex;
    flex-direction: column;
    justify-content: flex-start; /* Align to top */
    margin-bottom: 20px; /* Add spacing */
  }

  .title-container {
    position: relative; /* Change from absolute to relative */
    bottom: auto; /* Remove absolute positioning */
    width: 100%;
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    margin-bottom: 15px; /* Add spacing */
  }

  .main-divider {
    position: relative; /* Change positioning */
    top: auto;
    bottom: auto;
    margin: 15px 0; /* Add margin instead of absolute positioning */
  }

  .shop-info p {
    font-size: 30px;
  }
  
  .shop-info h3 {
    font-size: 35px;
  }

  .rarity {
    font-size: 34px !important;
  }

  .points {
    font-size: 34px !important;
  }

  .season-section h3 {
    font-size: 34px !important;
  }

  .season-section p {
    font-size: 28px !important;
  }

  .back-to-category-button {
    font-size: 27px;
  }
}

@media (max-width: 800px) {
  .shop-info p {
    font-size: 20px;
  }
  
  .shop-info h3 {
    font-size: 25px;
  }

  .rarity {
    font-size: 24px !important;
  }

  .points {
    font-size: 24px !important;
  }

  .season-section h3 {
    font-size: 24px !important;
  }

  .season-section p {
    font-size: 18px !important;
  }

  .back-to-category-button {
    font-size: 17px;
  }

  .card-detail-container {
    padding: 27px;
  }

  .card-content-wrapper {
    padding: 0px 30px;
  }
}
</style>