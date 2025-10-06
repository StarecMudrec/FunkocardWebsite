<template>
  <div
    class="card"
    :class="{ 
      'selected': isSelected,
      'selected-animation': isSelected && !isMobile
    }"
    v-if="card"
    @click="handleCardClick"
  >
    <div class="card-inner-content">
      <div class="image-wrapper">
        <img
          :src="imageUrl"
          :alt="card.name"
          :loading="priority ? 'eager' : 'lazy'"
          class="card-image"
          @load="handleImageLoad"
          @error="handleImageError"
          v-show="imageLoaded && !imageError"
        />
        <div v-if="!imageLoaded && !imageError" class="image-loading">
          <div class="loading-spinner-small"></div>
        </div>
        <div v-if="imageError" class="image-error">
          <span>Image not available</span>
        </div>
      </div>
      <div class="card-content">
        <div class="card-info">
          <h3 class="card-title">{{ card.name }}</h3>
          <!-- <span class="card-rarity">{{ card.rarity }}</span> -->
        </div>
        <div class="card-meta">
          <p class="card-category">{{ card.category || card.rarity }}</p>
        </div>
      </div>
    </div>
    <input
      type="checkbox"
      class="selection-checkbox"
      :checked="isSelected"
      @change="handleCheckboxChange"
      @click.stop
      v-if="allowSelection"
    >
  </div>
</template>

<script>
export default {
  props: {
    card: {
      type: Object,
      required: true,
      validator: card => 'name' in card && 'img' in card
    },
    priority: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      isSelected: false,
      isMobile: false,
      imageLoaded: false,
      imageError: false
    };
  },
  computed: {
    imageUrl() {
      if (!this.card.img) {
        console.warn('No image ID for card:', this.card.id, this.card.name);
        return '/placeholder.jpg';
      }
      return `/api/card_image/${this.card.img}`;
    },
    allowSelection() {
      return false;
    }
  },
  mounted() {
    this.checkMobile();
    window.addEventListener('resize', this.checkMobile);
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.checkMobile);
  },
  methods: {
    checkMobile() {
      this.isMobile = window.innerWidth <= 768;
    },
    handleImageLoad() {
      console.log('Image loaded successfully:', this.card.img, 'for card:', this.card.name);
      this.imageLoaded = true;
      this.imageError = false;
    },
    handleImageError(e) {
      console.error('Error loading image:', this.card.img, 'for card:', this.card.name);
      this.imageError = true;
      this.imageLoaded = false;
      
      // Retry loading after a short delay with a different approach
      setTimeout(() => {
        if (this.imageError) {
          console.log('Retrying image load for:', this.card.name);
          // Force reload by updating the src
          const img = e.target;
          img.src = `/api/card_image/${this.card.img}?retry=${Date.now()}`;
        }
      }, 1000);
    },
    handleCardClick(event) {
      if (this.isSelected) {
        return;
      }
      if (event.target.classList.contains('selection-checkbox')) {
        return;
      }
      this.$emit('card-clicked', this.card.id);
    },
    handleCheckboxChange(event) {
      this.isSelected = event.target.checked;
      this.$emit('card-selected', this.card.id, this.isSelected);
    },
  }
}
</script>

<style scoped>
.card {
  --card-width: 220px;
  width: var(--card-width);
  background: var(--card-bg);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  position: relative;
  transition: transform 0.2s ease, border 0.2s ease;
  margin: 15px;
}

.card:hover {
  transform: translateY(-5px) !important;
  cursor: pointer;
}

.card.selected-animation {
  animation: float-shake 2s ease-in-out infinite;
  transform: translateY(-15px);
  z-index: 10;
}

@keyframes float-shake {
  0%, 100% {
    transform: translateY(-20px) rotate(-2deg);
  }
  25% {
    transform: translateY(-25px) rotate(2deg);
  }
  50% {
    transform: translateY(-20px) rotate(0deg);
  }
  75% {
    transform: translateY(-25px) rotate(-2deg);
  }
}

.selection-checkbox {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 1;
  width: 20px;
  height: 20px;
  cursor: pointer;
  display: none;
}

@media (min-width: 769px) {
  .selection-checkbox {
    display: block;
  }
}

.image-wrapper {
  position: relative;
  width: 100%;
  height: calc(var(--card-width) * 1.3);
  overflow: hidden;
  background: rgba(0, 0, 0, 0.05);
}

.card-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
}

.image-loading, .image-error {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.1);
  color: var(--text-color);
  font-size: 0.8rem;
}

.image-error {
  background: rgba(255, 0, 0, 0.05);
  color: #888;
}

.loading-spinner-small {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: var(--accent-color);
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.card-inner-content {
  transition: filter 0.3s ease;
}

.card.selected {
  border: 4px solid rgba(255, 42, 42, 0.32);
}

.card.selected::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 42, 42, 0.24);
  z-index: 0;
  filter: blur(4px);
}

.card.selected .card-inner-content {
  filter: blur(4px) opacity(0.5);
}

.card-content {
  padding: 10px 16px 2px 16px;
}

.card-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.card-title {
  font-size: 1.1rem;
  margin: 0;
  color: var(--accent-color);
  flex: 1;
  margin-right: 8px;
}

.card-rarity {
  font-size: 0.9rem;
  color: #888;
}

.card-category {
  font-size: 0.9rem;
  color: #888;
  margin: 0;
}

.card.compact {
  --card-width: 180px;
  margin: 8px;
}

.card.compact .card-content {
  padding: 8px;
}

.card.compact .card-title {
  font-size: 0.9rem;
  margin-right: 8px;
}

@media (max-width: 768px) {
  .card {
    --card-width: 48vw;
    margin: 8px 4px;
  }
  
  .card .selection-checkbox {
    display: block;
  }
  
  .card.selected-animation {
    animation: none;
    transform: none;
  }
  
  .image-wrapper {
    height: calc(var(--card-width) * 1.4);
  }
}

@media (max-width: 480px) {
  .card {
    --card-width: 90vw;
    margin: 8px auto;
  }
  
  .card .selection-checkbox {
    display: block;
    width: 30px;
    height: 30px;
  }
}
</style>