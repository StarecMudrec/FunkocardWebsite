<template>
  <div class="profile-background">
    <div  class="avatar-and-username">
      <div class="avatar-section">
        <img 
          :src="userAvatar" 
          alt="User Avatar" 
          class="avatar"
          @load="handleAvatarLoad"
          @error="handleAvatarError"
        />
        <div v-if="avatarLoading" class="avatar-loading">Loading...</div>
      </div>
      <div class ="username-section">
          <h2 class="username-text">
            {{ userData.first_name }} {{ userData.last_name }}
          </h2>
          <p class="username">@{{ userData.username }}</p>
          <!-- <button @click="logout" class="logout-btn">
            <svg width="54px" height="54px" viewBox="0 0 24.00 24.00" fill="none" xmlns="http://www.w3.org/2000/svg" stroke="#ffffff" transform="matrix(-1, 0, 0, 1, 0, 0)"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round" stroke="#CCCCCC" stroke-width="0.288"></g><g id="SVGRepo_iconCarrier"> <path d="M14 4L18 4C19.1046 4 20 4.89543 20 6V18C20 19.1046 19.1046 20 18 20H14M3 12L15 12M3 12L7 8M3 12L7 16" stroke="#ffffff" stroke-width="1.9919999999999998" stroke-linecap="round" stroke-linejoin="round"></path> </g></svg>
          </button> -->
      </div>
    </div>
    <div class="profile-container">
      <div class="user-info">
        <div class="user-details">
          <!--<p class="user-id">ID: {{ userData.id }}</p>
          <p class="debug-info" v-if="debugInfo">Debug: {{ debugInfo }}</p>-->
        </div>
      </div>
      
      <div class="cards-container">
        <div class="profile-header">
          <h1>Your Cards:</h1>
        </div>
      </div>
<!-- 
      <div class="profile-actions">
        <button @click="refreshAvatar" class="refresh-btn" v-if="!avatarLoading">
          Refresh Avatar
        </button>
      </div>

      <router-link to="/" class="back-link">← Back to cards</router-link> -->
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'

export default {
  name: 'Profile',
  setup() {
    const store = useStore()
    const router = useRouter()
    const userData = ref({})
    const userAvatar = ref('')
    const avatarLoading = ref(false)
    const debugInfo = ref('')
    const defaultAvatar = '/placeholder.jpg'

    const fetchUserData = async () => {
      try {
        avatarLoading.value = true
        const response = await fetch('/api/user', {
          credentials: 'include'
        })
        
        if (response.ok) {
          const data = await response.json()
          userData.value = data
          console.log('Full user data:', data)
          
          // Set avatar URL - try multiple approaches
          if (data.photo_url) {
            debugInfo.value = `Photo URL: ${data.photo_url}`
            
            // Approach 1: Use proxy endpoint
            const proxyUrl = `/proxy/avatar?url=${encodeURIComponent(data.photo_url)}&t=${Date.now()}`
            userAvatar.value = proxyUrl
            console.log('Trying proxy URL:', proxyUrl)
            
            // Test if the image loads
            testImageLoad(proxyUrl).then(success => {
              if (!success) {
                // Approach 2: Try direct URL (might work if no CORS issues)
                console.log('Proxy failed, trying direct URL')
                userAvatar.value = data.photo_url
                testImageLoad(data.photo_url).then(directSuccess => {
                  if (!directSuccess) {
                    // Approach 3: Use default
                    console.log('Direct URL also failed, using default')
                    userAvatar.value = defaultAvatar
                  }
                })
              }
            })
            
          } else {
            debugInfo.value = 'No photo_url in user data'
            userAvatar.value = defaultAvatar
          }
        } else {
          debugInfo.value = `API response: ${response.status}`
          console.error('Failed to fetch user data:', response.status)
          router.push('/login')
        }
      } catch (error) {
        debugInfo.value = `Fetch error: ${error.message}`
        console.error('Error fetching user data:', error)
        router.push('/login')
      } finally {
        avatarLoading.value = false
      }
    }

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
      
      // Try fallback approaches
      if (userData.value.photo_url && userAvatar.value !== userData.value.photo_url) {
        console.log('Trying direct URL as fallback')
        userAvatar.value = userData.value.photo_url
      } else {
        userAvatar.value = defaultAvatar
      }
    }

    const refreshAvatar = () => {
      if (userData.value.photo_url) {
        avatarLoading.value = true
        // Add cache busting parameter
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

    onMounted(() => {
      if (!store.state.isAuthenticated) {
        router.push('/login')
        return
      }
      fetchUserData()
    })

    return {
      userData,
      userAvatar,
      avatarLoading,
      debugInfo,
      handleAvatarError,
      handleAvatarLoad,
      refreshAvatar,
      logout
    }
  }
}
</script>

<style scoped>
.profile-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  font-family: 'Afacad', sans-serif;
}

.profile-background::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: url('/background.jpg');
  background-size: cover;
  background-position: center 95%;
  filter: blur(10px);
  z-index: 1;
}

.profile-container {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  box-sizing: border-box;
  /* max-width: 500px; */
  padding: 40px;
  background-color: var(--card-bg);
  /* border-radius: 20px; */
  border-top: 2px solid #333;
  text-align: center;
  box-shadow: 2px 4px 5px rgba(0, 0, 0, 0.24);
  z-index: 2;
  margin-top: 50vh;
  height: 100%;
}

.profile-header h1 {
  color: var(--accent-color);
  font-weight: 500;
  margin-bottom: 30px;
  margin-top: 10px;
  font-size: 38px;
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
  margin-top: 50px;
  margin-left: calc(33vh + 110px);
  text-align: left;
  position: relative;
  justify-content: center;
}

.avatar-section {
  flex-shrink: 0;
  position: relative;
  /* z-index: 2; */
}

.username-section { 
  display: grid;
  grid-template-rows: 1fr 1fr;
  position: relative;
  /* gap: 20px; */
  /* z-index: 2; */
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
}

.username-text {
  /* transform: translateY(-50%); */
  color: white;
  font-size: 100px;
  text-shadow: 3px 4px 10px rgba(0, 0, 0, 0.7);
  margin: 0;
}

.avatar-and-username {
  display: flex;
  flex-direction: row;
  align-content: center;
  justify-content: flex-start;
  gap: 50px;
  position: absolute;
  left: 100px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 3;
  align-items: center;
}

.avatar {
  width: 33vh;
  aspect-ratio: 1;
  border-radius: 50%;
  object-fit: cover;
  border: 0px solid #333;
  box-shadow: 0px 7px 10px 2px rgba(0, 0, 0, 0.1);
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
  transform: translateY(2%, 50%);
}

.user-id {
  color: #666;
  font-size: 14px;
  margin: 0;
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
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 5px 10px;
  border-radius: 10px;
  font-size: 12px;
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

@media (max-width: 480px) {
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
  }
  
  .user-details h2 {
    font-size: 20px;
  }
}
</style>