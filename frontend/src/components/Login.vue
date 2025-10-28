<template>
  <div class="login-background">
    <div class="login-container">
      <h1>Please Log in</h1>
      <p></p>
      <div ref="telegramWidget"></div>

      <router-link to="/" class="back-link">← Back to cards</router-link>
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
      script.dataset.telegramLogin = 'funkocardwebbot'
      script.dataset.authUrl = 'https://dahole.ru/auth/telegram-callback'
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
  font-family: 'Afacad', sans-serif;
}

.login-background::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: url('/background.jpg');
  background-size: cover;
  background-position: center 95%;
  filter: blur(10px); /* Blur only the background */
  z-index: 1;
}

.login-container {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  box-sizing: border-box;
  max-width: 400px;
  padding: 30px 40px;
  background-color: var(--card-bg);
  border-radius: 20px;
  border: 1px solid #333;
  text-align: center;
  box-shadow: 2px 4px 5px rgba(0, 0, 0, 0.24);
  z-index: 2; /* Ensure it's above the blurred background */
}
h1 {
  color: var(--accent-color);
  font-weight: 500;
  margin-bottom: 15px;
  margin-top: 10px;
  font-size: 38px;
  border-bottom-width: 1px;
  border-bottom-style: solid;
  border-bottom-color: #333;
  padding-bottom: 12px;
}

.back-link {
  display: inline-block;
  margin-top: 25px;
  color: var(--accent-color);
  text-decoration: none;
  font-size: 17px;
  position: relative;
  padding-bottom: 2px;
  transition: all 0.3s ease; /* Added transition for smooth scaling */
}

.back-link::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%; /* Start from center */
  width: 0;
  height: 1px;
  background-color: var(--accent-color);
  transition: all 0.3s ease;
  transform: translateX(-50%); /* Center the underline */
}

.back-link:hover {
  transform: scale(1.05); /* Expand size on hover */
  color: var(--accent-color); /* Ensure color stays consistent */
}

.back-link:hover::after {
  width: 100%; /* Expand from center to full width */
  left: 50%; /* Maintain center origin */
}

@media (max-width: 480px) {
  .login-container {
    padding: 20px 20px;
    margin: auto;
    max-width: 300px;
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
  }
  
  h1 {
    font-size: 30px;
  }
  
  p {
    font-size: 14px;
  }
}
</style>
