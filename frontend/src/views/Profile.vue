<template>
  <div class="profile-background">
    <div class="profile-container">
      <div class="profile-header">
        <h1>Your Profile</h1>
        <div class="user-info">
          <div class="avatar-section">
            <img 
              :src="userAvatar" 
              alt="User Avatar" 
              class="avatar"
              @error="handleAvatarError"
            />
          </div>
          <div class="user-details">
            <h2>{{ userData.first_name }} {{ userData.last_name }}</h2>
            <p class="username">@{{ userData.username }}</p>
            <p class="user-id">ID: {{ userData.id }}</p>
          </div>
        </div>
      </div>

      <div class="profile-actions">
        <button @click="logout" class="logout-btn">
          Logout
        </button>
      </div>

      <router-link to="/" class="back-link">← Back to cards</router-link>
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
    const defaultAvatar = '/placeholder.jpg'

    const fetchUserData = async () => {
      try {
        const response = await fetch('/api/user', {
          credentials: 'include'
        })
        
        if (response.ok) {
          const data = await response.json()
          userData.value = data
          console.log('User data:', data) // Debug log
          
          // Set avatar URL - use proxy endpoint
          if (data.photo_url) {
            userAvatar.value = `/proxy/avatar?url=${encodeURIComponent(data.photo_url)}`
            console.log('Avatar URL:', userAvatar.value) // Debug log
          } else {
            userAvatar.value = defaultAvatar
          }
        } else {
          console.error('Failed to fetch user data:', response.status)
          router.push('/login')
        }
      } catch (error) {
        console.error('Error fetching user data:', error)
        router.push('/login')
      }
    }

    const handleAvatarError = (event) => {
      console.error('Avatar failed to load, using default')
      event.target.src = defaultAvatar
      userAvatar.value = defaultAvatar
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
      // Check if user is authenticated
      if (!store.state.isAuthenticated) {
        router.push('/login')
        return
      }
      fetchUserData()
    })

    return {
      userData,
      userAvatar,
      handleAvatarError,
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
  max-width: 500px;
  padding: 40px;
  background-color: var(--card-bg);
  border-radius: 20px;
  border: 1px solid #333;
  text-align: center;
  box-shadow: 2px 4px 5px rgba(0, 0, 0, 0.24);
  z-index: 2;
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
  text-align: left;
}

.avatar-section {
  flex-shrink: 0;
}

.avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--accent-color);
}

.user-details h2 {
  color: var(--accent-color);
  font-size: 24px;
  margin: 0 0 5px 0;
  font-weight: 500;
}

.username {
  color: #888;
  font-size: 16px;
  margin: 0 0 5px 0;
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
  background: linear-gradient(45deg, var(--accent-color), var(--hover-color));
  color: white;
  border: none;
  padding: 12px 30px;
  border-radius: 25px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: 'Afacad', sans-serif;
}

.logout-btn:hover {
  transform: scale(1.05);
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