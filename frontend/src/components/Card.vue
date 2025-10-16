<template>
  <div
    class="card"
    :class="{ 
      'selected': isSelected,
      'selected-animation': isSelected && !isMobile,
      'limited-card': isLimitedCard
    }"
    v-if="card"
    @click="handleCardClick"
  >
    <div class="card-inner-content">
      <div class="image-wrapper">
        <!-- Video for Limited cards -->
        <video
          v-if="isLimitedCard && card.img"
          :src="getMediaUrl(card.img)"
          class="card-media video-media"
          muted
          loop
          playsinline
          preload="metadata"
          @loadeddata="onVideoLoad"
          @error="onMediaError"
        ></video>
        
        <!-- Image for other cards -->
        <img
          v-else-if="card.img"
          :src="getMediaUrl(card.img)"
          :alt="card.name"
          class="card-media image-media"
          @error="handleImageError"
        />
        
        <!-- Placeholder when no media -->
        <img
          v-else
          src="/placeholder.jpg"
          alt="Placeholder"
          class="card-media placeholder-media"
        />
      </div>
      <div class="card-content">
        <div class="card-info">
          <h3 class="card-title">{{ card.name }}</h3>
        </div>
        <div class="card-meta">
          <p class="card-category">{{ card.category || card.rarity || 'Unknown' }}</p>
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
    allowSelection: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      isSelected: false,
      isMobile: false,
      videoObserver: null
    };
  },
  computed: {
    isLimitedCard() {
      return this.card.rarity === 'Limited ⚠️' || this.card.category === 'Limited ⚠️'
    }
  },
  mounted() {
    this.checkMobile();
    window.addEventListener('resize', this.checkMobile);
    
    // Setup video autoplay for Limited cards
    if (this.isLimitedCard) {
      this.setupVideoAutoplay();
    }
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.checkMobile);
    
    // Clean up video observer
    if (this.videoObserver) {
      this.videoObserver.disconnect();
    }
  },
  methods: {
    getMediaUrl(fileId) {
      return `/api/card_image/${fileId}`;
    },
    
    checkMobile() {
      this.isMobile = window.innerWidth <= 768;
    },
    
    handleImageError(e) {
      e.target.src = '/placeholder.jpg';
    },
    
    onVideoLoad(event) {
      // Video loaded successfully
      console.log('Video loaded for Limited card:', this.card.name);
      const video = event.target;
      
      // Try to play the video
      video.play().catch(error => {
        console.log('Autoplay prevented, will play when visible:', error);
      });
    },
    
    onMediaError(event) {
      console.error('Failed to load media for card:', this.card.name);
      // Fallback to placeholder
      if (event.target.tagName === 'VIDEO') {
        const videoElement = event.target;
        const imgElement = document.createElement('img');
        imgElement.src = '/placeholder.jpg';
        imgElement.className = 'card-media image-media';
        imgElement.alt = this.card.name;
        videoElement.parentNode.replaceChild(imgElement, videoElement);
      } else {
        event.target.src = '/placeholder.jpg';
      }
    },
    
    setupVideoAutoplay() {
      // Use Intersection Observer to play videos only when they're visible
      this.videoObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          const video = entry.target;
          if (entry.isIntersecting) {
            video.play().catch(error => {
              console.log('Video autoplay prevented:', error);
            });
          } else {
            video.pause();
          }
        });
      }, { threshold: 0.5 });
      
      // Observe the video element when it's added to DOM
      this.$nextTick(() => {
        const videoElement = this.$el.querySelector('.video-media');
        if (videoElement) {
          this.videoObserver.observe(videoElement);
        }
      });
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

    toggleSelection() {
      this.isSelected = !this.isSelected;
      this.$emit('card-selected', this.card.id, this.isSelected);
    },
    
    deleteCard() {
      this.$emit('delete-card', this.card.id);
    }
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

/* Special styling for Limited cards */
.card.limited-card {
  /*border: 2px solid rgba(255, 193, 7, 0.3);*/
  box-shadow: 0 4px 12px rgba(255, 193, 7, 0.2);
  transition: 0.3s ease;
}

.card.limited-card:hover {
  box-shadow: 0 6px 16px rgba(255, 193, 7, 0.3);
}

/* Добавляем новые стили для анимации */
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

/* Style for the selection checkbox */
.selection-checkbox {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 2;
  width: 20px;
  height: 20px;
  cursor: pointer;
  display: none;
}

/* Show on desktop */
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
}

/* Unified media styles */
.card-media {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
  display: block;
}

/* Video specific styles */
.video-media {
  background: #000;
}

.image-media {
  background: #f0f0f0;
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
  z-index: 1;
  filter: blur(4px);
}

.card.selected .card-inner-content {
  filter: blur(4px) opacity(0.5);
}

.card-content {
  padding: 10px 16px 10px 16px;
}

.card-info {
  display: flex;
}

.card-category {
  font-size: 0.9rem;
  color: #888;
  margin: 0;
}

/* New styles for card info layout */
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
}

.card-rarity {
  font-size: 0.9rem;
  color: #888;
}

/* 🟡 НОВЫЕ СТИЛИ ДЛЯ КОМПАКТНОГО ВИДА */
.card.compact {
  --card-width: 180px;
  margin: 8px;
  
  .card-content {
    padding: 8px;
  }
  
  .card-title {
    font-size: 0.9rem;
    margin-right: 8px;
  }
}

@media (max-width: 768px) {
  .card {
    --card-width: 48vw;
    margin: 8px 4px;

    .selection-checkbox {
      display: block;
    }
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

    .selection-checkbox {
      display: block;
      width: 30px;
      height: 30px;
    }
  }
}

/* Video loading state */
.video-media:not([src]) {
  background: linear-gradient(45deg, #f0f0f0 25%, transparent 25%), 
              linear-gradient(-45deg, #f0f0f0 25%, transparent 25%), 
              linear-gradient(45deg, transparent 75%, #f0f0f0 75%), 
              linear-gradient(-45deg, transparent 75%, #f0f0f0 75%);
  background-size: 20px 20px;
  background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
}
</style>