<template>
  <div class="profile-background">
    <!-- Scroll arrow button -->
    <div class="cover-arrow" @click="scrollToContent">
      <div class="cover-arrow__inner">
        <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 106 65" fill="none">
          <path xmlns="http://www.w3.org/2000/svg" d="M54.4142 39.1858C53.6332 39.9669 52.3668 39.9669 51.5858 39.1858L13.7809 1.38091C12.9998 0.59986 11.7335 0.59986 10.9525 1.38091L1.41421 10.9192C0.633164 11.7002 0.633165 12.9665 1.41421 13.7476L51.5858 63.9192C52.3668 64.7002 53.6332 64.7002 54.4142 63.9192L104.586 13.7476C105.367 12.9665 105.367 11.7002 104.586 10.9192L95.0475 1.38091C94.2665 0.599859 93.0002 0.59986 92.2191 1.38091L54.4142 39.1858Z" fill="#FFFFFF"/>
        </svg>
      </div>
    </div>

    <div class="avatar-and-username">
      <div class="avatar-section">
        <img 
          :src="userAvatar" 
          alt="User Avatar" 
          class="avatar"
          @load="handleAvatarLoad"
          @error="handleAvatarError"
        />
        <div v-if="avatarLoading" class="avatar-loading">
          <div class="spinner"></div>
          <span>Loading avatar...</span>
        </div>
      </div>
      <div class="username-section">
        <div class="username-container">
          <h2 ref="usernameRef" class="username-text">
            {{ userData.first_name }} {{ userData.last_name }}
          </h2>
        </div>
        <div class="user-info">
          <div class="user-details">
            <!-- Stats Section -->
            <div class="stats-section" v-if="userStats.length > 0">
              <h3 class="stats-title">User Statistics:</h3>
              <div class="stats-list">
                <div 
                  v-for="(stat, index) in userStats" 
                  :key="index" 
                  class="stat-item"
                >
                  {{ stat }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Categories Section (similar to Home.vue) -->
    <div id="content-section" class="content">
      <div class="profile-container">
        <div class="cards-container">
          <div class="profile-header">
            <h1>Your Cards:</h1>
          </div>
        </div>

        <!-- Categories Grid -->
        <div id="categories-container" class="categories-grid">
          <div v-if="loading" class="loading">Loading categories...</div>
          <div v-else-if="error" class="error-message">Error loading data: {{ error.message || error }}. Please try again later.</div>
          <div v-else-if="filteredCategories.length === 0" class="no-categories-message">
            {{ searchQuery ? 'No categories match your search' : 'No categories found' }}
          </div>
          
          <!-- Category Cards -->
          <transition-group name="search-animation" tag="div" class="categories-grid-transition">
            <div 
              v-for="(category, index) in filteredCategories" 
              :key="category.id"
              class="category-card"
              :class="getCategoryBackgroundClass(category, index)"
              @click="navigateToCategory(category)"
            >
              <!-- Video background for Limited category -->
              <video 
                v-if="category.name === 'Limited ⚠️' && getLimitedVideoSource(category)"
                class="category-card__video"
                :src="getLimitedVideoSource(category)"
                autoplay
                muted
                loop
                playsinline
              ></video>
              <div 
                v-else
                class="category-card__background" 
                :style="getCategoryBackgroundStyle(category)"
              ></div>
              <div class="category-card__content">
                <div class="category-card__header">
                  <h3 class="category-card__title">{{ category.name }}</h3>
                </div>
              </div>
            </div>
          </transition-group>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, nextTick, watch, computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'

// Debounce function for search
const debounce = (func, wait) => {
  let timeout
  const debounced = function(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
  
  debounced.cancel = function() {
    clearTimeout(timeout)
  }
  
  return debounced
}

export default {
  name: 'Profile',
  setup() {
    const store = useStore()
    const router = useRouter()
    
    // User data
    const userData = ref({})
    const userAvatar = ref('')
    const userStats = ref([])
    const avatarLoading = ref(false)
    const debugInfo = ref('')
    const defaultAvatar = '/placeholder.jpg'
    const usernameRef = ref(null)

    // Categories data (from Home.vue)
    const rarityOrder = {
      'Vinyl Figure💫': 1,
      'Legendary🧡': 2,
      'Special 🌟': 3,
      'Nameless 📛': 4,
      'Limited ⚠️': 5,
      'SuperCool🤟': 6,
      'Cool👍': 7,
      'Plain😼': 8,
      'Force🤷‍♂️': 9,
      'Scarface - Tony Montana': 10
    }
    const rarityNewestCards = ref({})
    const allCategoriesNewestCards = ref({})
    const searchQuery = ref('')
    const filteredCategories = ref([])
    const debouncedSearch = ref(null)
    const showSortDropdown = ref(false)
    const currentSort = ref({ field: 'default', direction: 'asc' })
    const loading = ref(false)
    const error = ref(null)

    // Computed categories (from Home.vue)
    const categories = computed(() => store.state.categories || [])
    
    const rarityCategories = computed(() => {
      return categories.value.filter(category => {
        const name = category.name.toLowerCase();
        return !name.includes('all') && !name.includes('general') && !name.includes('shop');
      });
    })
    
    const sortedCategories = computed(() => {
      if (!categories.value || categories.value.length === 0) return [];
      
      return [...categories.value].sort((a, b) => {
        const orderA = rarityOrder[a.name] || 999;
        const orderB = rarityOrder[b.name] || 999;
        
        if (a.name.toLowerCase().includes('all') || a.name.toLowerCase().includes('general')) return -1;
        if (b.name.toLowerCase().includes('all') || b.name.toLowerCase().includes('general')) return 1;
        if (a.name.toLowerCase().includes('shop')) return -1;
        if (b.name.toLowerCase().includes('shop')) return 1;
        
        return orderA - orderB;
      });
    })

    // Font size adjustment for username
    const adjustUsernameFontSize = () => {
      nextTick(() => {
        if (!usernameRef.value) {
          console.log('Username ref not found')
          return
        }
        
        const element = usernameRef.value
        const container = element.parentElement
        const text = element.textContent
        
        console.log('Adjusting font size for:', text)
        console.log('Container dimensions:', container.offsetWidth, container.offsetHeight)
        
        if (!text || !container) return
        
        // Reset styles
        element.style.fontSize = ''
        element.style.whiteSpace = 'nowrap'
        element.style.lineHeight = '1'
        element.style.width = 'auto'
        element.style.height = 'auto'
        element.classList.remove('wrapped')
        
        const maxWidth = 1000
        const maxHeight = 150
        let fontSize = 100 // Start with large font
        
        // Create a temporary span to measure text
        const tempSpan = document.createElement('span')
        tempSpan.style.fontFamily = getComputedStyle(element).fontFamily
        tempSpan.style.fontWeight = getComputedStyle(element).fontWeight
        tempSpan.style.position = 'absolute'
        tempSpan.style.visibility = 'hidden'
        tempSpan.style.whiteSpace = 'nowrap'
        tempSpan.style.fontSize = fontSize + 'px'
        tempSpan.textContent = text
        
        document.body.appendChild(tempSpan)
        
        // Reduce font size until it fits
        while ((tempSpan.offsetWidth > maxWidth || tempSpan.offsetHeight > maxHeight) && fontSize > 20) {
          fontSize -= 2
          tempSpan.style.fontSize = fontSize + 'px'
        }
        
        document.body.removeChild(tempSpan)
        
        console.log('Final font size:', fontSize)
        element.style.fontSize = fontSize + 'px'
        
        // Check if we need to wrap
        if (fontSize <= 32) {
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

    // User data methods
    const fetchUserData = async () => {
      try {
        avatarLoading.value = true
        
        // Fetch basic user data
        const userResponse = await fetch('/api/user', {
          credentials: 'include'
        })
        
        if (userResponse.ok) {
          const data = await userResponse.json()
          userData.value = data
          console.log('Full user data:', data)
          
          // Set avatar URL
          if (data.photo_url) {
            debugInfo.value = `Photo URL: ${data.photo_url}`
            const proxyUrl = `/proxy/avatar?url=${encodeURIComponent(data.photo_url)}&t=${Date.now()}`
            userAvatar.value = proxyUrl
            
            testImageLoad(proxyUrl).then(success => {
              if (!success) {
                userAvatar.value = data.photo_url
                testImageLoad(data.photo_url).then(directSuccess => {
                  if (!directSuccess) {
                    userAvatar.value = defaultAvatar
                  }
                })
              }
            })
          } else {
            debugInfo.value = 'No photo_url in user data'
            userAvatar.value = defaultAvatar
          }
          
          // Fetch user stats
          await fetchUserStats()
          
        } else {
          debugInfo.value = `API response: ${userResponse.status}`
          console.error('Failed to fetch user data:', userResponse.status)
          router.push('/login')
        }
      } catch (error) {
        debugInfo.value = `Fetch error: ${error.message}`
        console.error('Error fetching user data:', error)
        router.push('/login')
      } finally {
        // Note: avatarLoading is set to false in handleAvatarLoad or handleAvatarError
      }
    }

    const fetchUserStats = async () => {
      try {
        const statsResponse = await fetch('/api/user/stats', {
          credentials: 'include'
        })
        
        if (statsResponse.ok) {
          const statsData = await statsResponse.json()
          console.log('User stats:', statsData)
          
          if (statsData.stats && Array.isArray(statsData.stats)) {
            userStats.value = statsData.stats
          }
        } else {
          console.error('Failed to fetch user stats:', statsResponse.status)
        }
      } catch (error) {
        console.error('Error fetching user stats:', error)
      }
    }

    // Categories methods (from Home.vue)
    const fetchRarityNewestCards = async () => {
      try {
        const response = await fetch('/api/rarity_newest_cards');
        if (response.ok) {
          rarityNewestCards.value = await response.json();
          console.log('Newest rarity cards:', rarityNewestCards.value);
        } else {
          console.error('Failed to fetch newest rarity cards');
        }
      } catch (error) {
        console.error('Error fetching newest rarity cards:', error);
      }
    }
    
    const fetchAllCategoriesNewestCards = async () => {
      try {
        const response = await fetch('/api/all_categories_newest_cards');
        if (response.ok) {
          allCategoriesNewestCards.value = await response.json();
          console.log('Newest cards for all categories:', allCategoriesNewestCards.value);
        } else {
          console.error('Failed to fetch newest cards for all categories');
        }
      } catch (error) {
        console.error('Error fetching newest cards for all categories:', error);
      }
    }
    
    const navigateToCategory = (category) => {
      console.log('Navigating to category:', category);
      
      // Clear any existing category state when navigating to a new category
      Object.keys(sessionStorage).forEach(key => {
        if (key.startsWith('category_state_')) {
          sessionStorage.removeItem(key);
        }
      });
      
      router.push(`/category/${category.id}`);
    }
    
    const getCategoryBackgroundClass = (category, index) => {
      const name = category.name.toLowerCase();
      
      if (name.includes('all') || name.includes('general')) {
        return 'all-cards';
      } else if (name.includes('shop')) {
        return 'shop';
      } else {
        return 'rarity';
      }
    }
    
    const getLimitedVideoSource = (category) => {
      const newestCard = rarityNewestCards.value[category.name] || allCategoriesNewestCards.value[category.name];
      if (newestCard && newestCard.photo) {
        return `/api/card_image/${newestCard.photo}`;
      }
      return null;
    }
    
    const getCategoryBackgroundStyle = (category) => {
      const name = category.name.toLowerCase();
      
      // For all categories, use the newest card image
      const newestCard = rarityNewestCards.value[category.name] || allCategoriesNewestCards.value[category.name];
      if (newestCard && newestCard.photo) {
        return {
          backgroundImage: `url(/api/card_image/${newestCard.photo})`
        };
      }
      
      // Fallback to static images if no newest card found
      if (name.includes('all') || name.includes('general')) {
        return {
          backgroundImage: `url('/All.png')`
        };
      } else if (name.includes('shop')) {
        return {
          backgroundImage: `url('/shop.png')`
        };
      }
      
      return {};
    }

    // Search methods
    const handleSearch = () => {
      debouncedSearch.value();
    }
    
    const performSearch = () => {
      if (!searchQuery.value.trim()) {
        filteredCategories.value = [...sortedCategories.value];
        return;
      }
      
      const query = searchQuery.value.toLowerCase().trim();
      
      requestAnimationFrame(() => {
        filteredCategories.value = sortedCategories.value.filter(category => 
          category.name?.toLowerCase().includes(query)
        );
      });
    }
    
    const clearSearch = () => {
      searchQuery.value = '';
      filteredCategories.value = [...sortedCategories.value];
      debouncedSearch.value?.cancel();
    }

    // Scroll method
    const scrollToContent = () => {
      const contentSection = document.querySelector('.content');
      if (contentSection) {
        contentSection.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start'
        });
      }
    }

    // Avatar methods
    const testImageLoad = (url) => {
      return new Promise((resolve) => {
        const img = new Image()
        img.onload = () => resolve(true)
        img.onerror = () => resolve(false)
        img.src = url
      })
    }

    const handleAvatarLoad = () => {
      console.log('Avatar loaded successfully')
      avatarLoading.value = false
      debugInfo.value = 'Avatar loaded'
    }

    const handleAvatarError = (event) => {
      console.error('Avatar failed to load:', event)
      avatarLoading.value = false
      debugInfo.value = 'Avatar load failed'
      
      if (userData.value.photo_url && userAvatar.value !== userData.value.photo_url) {
        userAvatar.value = userData.value.photo_url
      } else {
        userAvatar.value = defaultAvatar
      }
    }

    const refreshAvatar = () => {
      if (userData.value.photo_url) {
        avatarLoading.value = true
        userAvatar.value = `/proxy/avatar?url=${encodeURIComponent(userData.value.photo_url)}&t=${Date.now()}`
      }
    }

    const logout = async () => {
      try {
        await store.dispatch('logout')
        router.push('/')
      } catch (error) {
        console.error('Logout error:', error)
      }
    }

    // Initialize debounced search
    debouncedSearch.value = debounce(performSearch, 300)

    // Watch for user data changes
    watch(() => userData.value.first_name, () => {
      if (userData.value.first_name && userData.value.last_name) {
        setTimeout(adjustUsernameFontSize, 100)
      }
    })

    watch(() => userData.value.last_name, () => {
      if (userData.value.first_name && userData.value.last_name) {
        setTimeout(adjustUsernameFontSize, 100)
      }
    })

    onMounted(async () => {
      if (!store.state.isAuthenticated) {
        router.push('/login')
        return
      }
      
      await fetchUserData()
      
      // Fetch categories data
      try {
        loading.value = true
        await store.dispatch('fetchCategories')
        await fetchRarityNewestCards()
        await fetchAllCategoriesNewestCards()
        
        // Initialize filtered categories with all sorted categories
        filteredCategories.value = [...sortedCategories.value]
        
        console.log('Categories after fetch:', categories.value)
        console.log('Sorted categories:', sortedCategories.value)
        console.log('Rarity categories:', rarityCategories.value)
      } catch (error) {
        console.error('Failed to fetch categories:', error)
        error.value = error
      } finally {
        loading.value = false
      }
      
      // Also adjust on window resize
      window.addEventListener('resize', adjustUsernameFontSize)
    })

    return {
      userData,
      userAvatar,
      userStats,
      avatarLoading,
      debugInfo,
      usernameRef,
      // Categories data
      loading,
      error,
      searchQuery,
      filteredCategories,
      showSortDropdown,
      // Methods
      handleAvatarError,
      handleAvatarLoad,
      refreshAvatar,
      logout,
      navigateToCategory,
      getCategoryBackgroundClass,
      getLimitedVideoSource,
      getCategoryBackgroundStyle,
      handleSearch,
      clearSearch,
      scrollToContent
    }
  }
}
</script>

<style scoped>
/* Fixed background container */
.profile-background {
  position: relative;
  width: 100%;
  min-height: 100vh;
  font-family: 'Afacad', sans-serif;
}

/* Fixed background layer */
.profile-background::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: url('/background.jpg');
  background-size: cover;
  background-position: center 95%;
  background-attachment: fixed;
  filter: blur(10px);
  z-index: 1;
}

/* Content wrapper - everything that scrolls */
.profile-background::after {
  content: '';
  position: relative;
  display: block;
  z-index: 2;
}

/* Scroll Arrow Styles (from Home.vue) */
.cover-arrow {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  cursor: pointer;
  z-index: 10;
  width: 80px;
  height: 80px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.cover-arrow__inner {
  width: 80%;
  height: 80%;
  display: flex;
  justify-content: center;
  align-items: center;
  animation: bounce 2s infinite;
}

.arrow-icon {
  width: 144px;
  height: 144px;
  shape-rendering: geometricPrecision;
  transition: all 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  will-change: transform;
  pointer-events: none;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.4));
}

.cover-arrow:hover .arrow-icon {
  transform: scale(0.85);
  opacity: 0.9;
  filter: drop-shadow(0 6px 12px rgba(0, 0, 0, 0.5));
}

.cover-arrow:hover .cover-arrow__inner {
  animation-play-state: paused;
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-10px);
  }
  60% {
    transform: translateY(-5px);
  }
}

/* Content Section */
.content {
  position: relative;
  width: 100%;
  min-height: 52vh;
  left: 0;
  top: 4px;
  flex: 1;
  z-index: 2;
}

.profile-container {
  position: relative;
  width: 100%;
  box-sizing: border-box;
  padding: 40px;
  padding-top: 0;
  background-color: var(--card-bg);
  border-top: 2px solid #333;
  text-align: center;
  box-shadow: 2px 4px 5px rgba(0, 0, 0, 0.24);
  margin-top: 50vh;
  height: auto;
  min-height: 100%;
  font-family: 'Afacad', sans-serif;
}

.profile-header h1 {
  color: var(--accent-color);
  font-weight: 500;
  margin-bottom: 30px;
  margin-top: calc(50vh + 100px);
  font-size: 100px; 
  border-bottom-width: 1px;
  border-bottom-style: solid;
  border-bottom-color: #333;
  padding-bottom: 12px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 30px;
  margin-left: 30px;
  text-align: left;
  position: relative;
  justify-content: center;
}

.avatar-section {
  flex-shrink: 0;
  position: relative;
  display: flex;
  align-items: flex-end;
}

.username-section { 
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: flex-end;
  max-width: 1000px;
  min-height: 150px;
  min-width: 740px;
  width: auto;
  height: auto;
  overflow: visible;
  position: relative;
  margin-bottom: -175px; /* Half of avatar height to align bottom with avatar middle */
}

.username-container {
  max-width: 1000px;
  width: auto;
  height: 175px;
  display: flex;
  align-items: flex-end;
  justify-content: flex-start;
  overflow: visible;
}

.username-text {
  color: white;
  font-size: 100px;
  text-shadow: 3px 4px 10px rgba(0, 0, 0, 0.7);
  margin: 0;
  white-space: nowrap;
  transition: all 0.3s ease;
  word-break: break-word;
  max-width: 1000px;
  max-height: 150px;
  width: auto;
  height: auto;
  display: inline-block;
  line-height: 1;
  overflow: visible;
  text-align: left;
  vertical-align: bottom;
}

.username-text.wrapped {
  white-space: normal;
  line-height: 1.1;
  word-break: break-word;
  overflow-wrap: break-word;
  hyphens: auto;
}

.avatar-and-username {
  display: flex;
  flex-direction: row;
  align-content: flex-end;
  justify-content: flex-start;
  gap: 70px;
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -175px);
  z-index: 3;
  align-items: flex-start;
  width: auto;
  max-width: 90%;
}

.avatar {
  width: 350px;
  aspect-ratio: 1;
  border-radius: 50%;
  object-fit: cover;
  border: 0px solid #333;
  box-shadow: 0px 7px 10px 2px rgba(0, 0, 0, 0.1);
  flex-shrink: 0;
}

.user-details h2 {
  color: var(--accent-color);
  font-size: 24px;
  margin: 0 0 5px 0;
  font-weight: 500;
}

.username {
  color: var(--text-color);
  font-size: 36px;
  margin: 0;
  transform: translate(2%, 50%);
}

.user-id {
  color: #666;
  font-size: 14px;
  margin: 0;
}

/* Stats Section Styles */
.stats-section {
  margin-top: 30px;
  text-align: left;
  text-shadow: 3px 4px 2px rgba(0, 0, 0, 0.1);
}

.stats-title {
  color: var(--accent-color);
  font-size: 34px;
  margin-bottom: 15px;
  font-weight: 500;
  border-bottom: 1px solid #333;
  padding-bottom: 8px;
}

.stats-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 30vh;
  flex-wrap: wrap;
}

.stat-item {
  color: var(--text-color);
  font-size: 26px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  border-left: 3px solid var(--accent-color);
  transition: all 0.3s ease;
}

.stat-item:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateX(5px);
}

.profile-actions {
  margin: 30px 0;
}

.logout-btn {
  padding: 12px 30px;
  cursor: pointer;
  transition: all 0.3s ease;
  transform: translateY(calc(-50% - 20px));
  background: none;
  border: none;
  color: white;
}

.logout-btn:hover {
  transform: translateY(calc(-50% - 20px)) scale(1.05);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.back-link {
  display: inline-block;
  margin-top: 25px;
  color: var(--accent-color);
  text-decoration: none;
  font-size: 17px;
  position: relative;
  padding-bottom: 2px;
  transition: all 0.3s ease;
}

.back-link::after {
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

.back-link:hover {
  transform: scale(1.05);
  color: var(--accent-color);
}

.back-link:hover::after {
  width: 100%;
  left: 50%;
}

.avatar-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 15px 20px;
  border-radius: 15px;
  font-size: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  z-index: 10;
  min-width: 150px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
}

.spinner {
  width: 30px;
  height: 30px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top: 3px solid white;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.avatar-section {
  position: relative;
  flex-shrink: 0;
}

.refresh-btn {
  background: #666;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 15px;
  font-size: 14px;
  cursor: pointer;
  margin-left: 10px;
  transition: all 0.3s ease;
  font-family: 'Afacad', sans-serif;
}

.refresh-btn:hover {
  background: #777;
  transform: scale(1.05);
}

.debug-info {
  font-size: 12px;
  color: #888;
  margin: 5px 0 0 0;
  word-break: break-all;
}

/* Categories Grid Styles (from Home.vue) */
.categories-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  row-gap: 40px;
  column-gap: 67px;
  padding: 30px 20px;
  max-width: 1200px;
  margin: 0 auto;
  margin-top: 50px;
}

/* Transition group wrapper */
.categories-grid-transition {
  display: contents;
}

/* Search animation styles */
.search-animation-enter-active,
.search-animation-leave-active {
  transition: all 0.5s ease;
}

.search-animation-move {
  transition: transform 0.5s ease;
}

.search-animation-enter-from {
  opacity: 0;
  transform: scale(0.8) translateY(20px);
}

.search-animation-leave-to {
  opacity: 0;
  transform: scale(0.8) translateY(-20px);
}

.search-animation-leave-active {
  position: absolute;
}

.category-card {
  border-radius: 20px;
  box-shadow: 2px 7px 10px 2px rgba(0, 0, 0, 0.4);
  cursor: pointer;
  transition: all 0.3s ease;
  overflow: hidden;
  aspect-ratio: 0.8;
  position: relative;
  border: 3px solid #dadada;
}

/* Background element for better control */
.category-card__background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-size: cover;
  background-position: center;
  z-index: 0;
  transition: all 0.3s ease;
}

/* Video background for Limited category */
.category-card__video {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 0;
  transition: all 0.3s ease;
  filter: blur(2px); /* Apply same blur as rarity cards */
}

/* Apply specific backgrounds and blur effects */
.category-card.all-cards .category-card__background,
.category-card.shop .category-card__background,
.category-card.rarity .category-card__background {
  filter: blur(2px); /* Consistent blur for all category types */
}

/* Gradient overlay for better text readability */
.category-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(0,0,0,0.3) 0%, rgba(0,0,0,0.1) 50%, rgba(0,0,0,0.4) 100%);
  z-index: 1;
}

.category-card__content {
  padding: 20px;
  position: relative;
  z-index: 2;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.category-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
}

.category-card:hover .category-card__background,
.category-card:hover .category-card__video {
  transform: scale(1.02);
}

.category-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  flex-direction: column;
}

.category-card__title {
  font-size: 3.3rem;
  text-align: center;
  font-weight: 600;
  color: white;
  margin: 0;
  flex: 1;
  text-shadow: 0px 7px 16px rgba(0, 0, 0, 1);
}

.category-card__count {
  background: rgba(30, 30, 30, 0.7);
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  font-size: 0.9rem;
  font-weight: 600;
  min-width: 40px;
  text-align: center;
  backdrop-filter: blur(5px);
}

.error-message {
  text-align: center;
  margin: 50px 0;
  color: #ff5555;
  grid-column: 1 / -1;
}

.loading {
  text-align: center;
  margin: 50px 0;
  color: var(--text-color);
  grid-column: 1 / -1;
}

.no-categories-message {
  text-align: center;
  color: var(--text-color);
  opacity: 0.7;
  font-size: 1.2rem;
  padding: 40px 0;
  grid-column: 1 / -1;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .categories-grid {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    padding: 20px 15px;
    gap: 15px;
  }
  
  .category-card__content {
    padding: 15px;
  }
  
  .category-card__title {
    font-size: 1.1rem;
  }
  
  .cover-arrow {
    width: 210px;
    height: 165px;
    bottom: 20px;
  }
  
  .arrow-icon {
    width: 108px;
    height: 108px;
  }

  .profile-container {
    padding: 30px 20px;
    max-width: 350px;
  }
  
  .profile-header h1 {
    font-size: 28px;
  }
  
  .user-info {
    flex-direction: column;
    text-align: center;
    gap: 15px;
    margin-left: 0;
    width: 100%;
    justify-content: center;
  }
  
  .user-details h2 {
    font-size: 20px;
  }
  
  .stats-title {
    font-size: 20px;
  }
  
  .stat-item {
    font-size: 14px;
  }
  
  .username-section {
    max-width: 100%;
    min-height: 120px;
    margin-bottom: -100px; /* Adjust for smaller avatar on mobile */
    min-width: auto;
  }
  
  .username-container {
    max-width: 100%;
    max-height: 120px;
  }
  
  .username-text {
    font-size: 36px;
    max-width: 100%;
    max-height: 120px;
  }
  
  .avatar-and-username {
    flex-direction: column;
    gap: 30px;
    text-align: center;
    align-items: center;
  }
  
  .avatar {
    width: 200px;
  }
  
  .avatar-loading {
    padding: 10px 15px;
    font-size: 14px;
    min-width: 120px;
  }
  
  .spinner {
    width: 20px;
    height: 20px;
    border-width: 2px;
  }
}

@media (max-width: 480px) {
  .categories-grid {
    grid-template-columns: 1fr;
  }
}
</style>