<template>
  <div class="login-background">
    <div class="login-container">
      <h1>Please log in</h1>
      <p></p>
      <div ref="telegramWidget"></div>

      <router-link to="/" class="back-link">← Back to home</router-link>
    </div>
  </div>
</template>

<script>
import { onMounted, ref } from 'vue'

export default {
  setup() {
    const telegramWidget = ref(null)

    onMounted(() => {
      // Dynamically load the Telegram widget script
      const script = document.createElement('script')
      script.async = true
      script.src = 'https://telegram.org/js/telegram-widget.js?22'
      script.dataset.telegramLogin = 'cardswoodwebbot'
      script.dataset.authUrl = 'https://cardswood.ru/auth/telegram-callback'
      script.dataset.requestAccess = 'write'
      
      // Add the script to our container div
      telegramWidget.value.appendChild(script)

      // Handle auth success message
      window.addEventListener('message', handleAuthMessage)
    })
    
    const handleAuthMessage = (event) => {
      if (event.data === 'auth-success') {
        window.location.href = '/' // Or use Vue Router if needed
      }
    }
    
    return {
      telegramWidget
    }
  }
}
</script>

<style scoped>
.login-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: url('/background.jpg');
  background-size: cover;
  background-position: center 95%; /* Position the vertical center 80% down from the top, center horizontally */
  z-index: 1; /* Ensure it's behind the content */
}
.login-container {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  box-sizing: border-box; /* Include padding and border in the element's total width and height */
  max-width: 400px;
  padding: 40px;
  background-color: var(--card-bg);
  border-radius: 17px;
  border: 1px solid var(--border-color);
  text-align: center;
}
h1 {
  color: var(--accent-color);
  font-weight: 500;
  margin-bottom: 15px;
  font-size: 28px;
}

.back-link {
  display: inline-block;
  margin-top: 25px;
  color: var(--accent-color);
  text-decoration: none;
  font-size: 17px;
  position: relative;
  padding-bottom: 2px;
}

.back-link::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 0;
  height: 1px;
  background-color: var(--accent-color);
  transition: width 0.3s ease;
}

.back-link:hover::after {
  width: 100%;
}

@media (max-width: 480px) {
  .login-container {
    padding: 30px 20px;
    margin: auto;
    max-width: 300px;
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
  }
  
  h1 {
    font-size: 20px;
  }
  
  p {
    font-size: 14px;
  }
}
</style>
