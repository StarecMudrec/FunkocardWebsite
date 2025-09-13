<template>
  <div class="add-card-background">
    <!-- Модальное окно для ошибок -->
    <div v-if="showErrorModal" class="modal-overlay">
      <div class="modal-content">
        <h3 class="error-title">Error</h3>
        <p>{{ errorMessage }}</p>
        <button @click="closeModal" class="modal-button">ok</button>
      </div>
    </div>

    <div v-if="!isUserAllowed" class="permission-denied-message">
      <p>You do not have permission to add cards.</p>
    </div>

    <div v-if="isUserAllowed"  class="add-card-container">
      <h1>Add New Card</h1>
      <form @submit.prevent="submitForm" class="card-form">
        <div class="form-group">
          <label for="name">Card Name:</label>
          <input type="text" id="name" v-model="card.name" required>
        </div>
        <div class="form-group">
          <label for="description">Description:</label>
          <textarea id="description" v-model="card.description" required></textarea>
        </div>
        <div class="form-group">
          <label for="category">Category:</label>
          <input type="text" id="category" v-model="card.category" required>
        </div>
        <div class="form-group">
          <label for="season">Season:</label>
          <select id="season" v-model="card.season" required>
            <option disabled value="">Select a season</option>
            <option v-for="seasonId in seasonIds" :key="seasonId" :value="seasonId">
              Season {{ seasonId }}
            </option>
          </select>
        </div>
        <div class="form-group file-upload-group">
          <label for="image" class="file-upload-label">
            <span class="file-upload-text">
              {{ card.image ? card.image.name : 'Choose card image...' }}
            </span>
            <span class="file-upload-button">Browse</span>
            <input 
              type="file" 
              id="image" 
              @change="handleFileUpload" 
              accept="image/*" 
              required
              class="file-upload-input"
            >
          </label>
        </div>
        <button type="submit" class="submit-button">
          <span class="submit-button-text">Add Card</span>
        </button>
      </form>
      <router-link to="/" class="back-link">← Back to home</router-link>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { checkUserPermission, fetchUserInfo } from '@/api';
import imageCompression from 'browser-image-compression';
export default {
  data() {
    return {
      card: {
        name: '',
        description: '',
        category: '',
        season: '',
        image: null
      },
      seasonIds: [], // Будем хранить только ID сезонов
      showErrorModal: false,
      errorMessage: '',
      isUserAllowed: false, // Add this variable
    }
  },
  created() {
    this.fetchSeasonIds();
  },
  methods: {
    async fetchSeasonIds() {
      try {
        const response = await axios.get('/api/seasons');
        this.seasonIds = response.data; // Предполагаем, что API возвращает массив ID
      } catch (error) {
        this.errorMessage = 'Failed to load seasons: ' + (error.response?.data?.message || error.message);
        this.showErrorModal = true;
        console.error('Error loading seasons:', error);
      }
    },
    handleFileUpload(event) {
      const file = event.target.files[0];
      if (file && file.type.startsWith('image/')) {
        this.card.image = file;
      } else {
        this.errorMessage = 'Please select an image file (JPEG, PNG, GIF, etc.).';
        this.showErrorModal = true;
        event.target.value = '';
        this.card.image = null;
      }
    },
    closeModal() {
      this.showErrorModal = false;
      this.errorMessage = '';
    },
    async submitForm() {
      if (!this.card.image) {
        this.errorMessage = 'Please select an image file.';
        this.showErrorModal = true;
        return;
      }

      try {
        // Сжимаем изображение перед отправкой
        const options = {
          maxSizeMB: 1,          // Максимальный размер после сжатия (1MB)
          maxWidthOrHeight: 1920,// Максимальная ширина/высота
          useWebWorker: true     // Использовать WebWorker для лучшей производительности
        };
        
        const compressedFile = await imageCompression(this.card.image, options);
        
        const formData = new FormData();
        const cardUuid = this.uuidv4();
        formData.append('uuid', cardUuid);
        formData.append('name', this.card.name);
        formData.append('description', this.card.description);
        formData.append('category', this.card.category);
        formData.append('season_id', this.card.season);
        formData.append('img', compressedFile, compressedFile.name); // Используем сжатый файл

        const response = await axios.post('/api/cards', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        
        console.log('Card added successfully:', response.data);
        this.resetForm();
      } catch (error) {
        this.errorMessage = 'Error adding card: ' + (error.response?.data?.message || error.message);
        this.showErrorModal = true;
        console.error('Error adding card:', error);
      }
    },
    resetForm() {
      this.card = {
        name: '',
        description: '',
        category: '',
        season: '',
        image: null
      };
      const fileInput = document.getElementById('image');
      if (fileInput) {
        fileInput.value = '';
      }
    },
    // You'll need a method to check if the user is allowed.
    // This could involve making an API call to your backend.
    async checkUserPermission() {
      try {
        // Fetch user info to get the Telegram username
        const userInfo = await fetchUserInfo();
        const username = userInfo ? userInfo.username : null;

        if (username) {
          const permissionResponse = await checkUserPermission(username);
          this.isUserAllowed = permissionResponse.is_allowed;
        }
      } catch (error) {
        console.error('Error checking user permission:', error);
        this.isUserAllowed = false; // Assume not allowed on error
      }
    }
  },
  setup() {
    const uuidv4 = () => {
      return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
      });
    };
    return {
      uuidv4
    };
  }
  ,
  mounted() {
    // Call the permission check when the component is mounted
    this.checkUserPermission();
  }
};
</script>

<style scoped>
.add-card-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: url('/background.jpg');
  background-size: cover;
  background-position: center 95%;
  z-index: 1;
}

.add-card-container {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  box-sizing: border-box;
  max-width: 500px;
  padding: 30px;
  background-color: var(--card-bg);
  border-radius: 17px;
  border: 1px solid var(--card-bg);
  text-align: center;
}
.permission-denied-message {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: var(--text-color);
  font-size: 20px;
  text-align: center;
  padding: 20px;
  background-color: rgba(0, 0, 0, 0.6);
}

/* Стили для модального окна */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(5px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: var(--card-bg);
  padding: 30px;
  border-radius: 12px;
  max-width: 400px;
  width: 90%;
  text-align: center;
  border: 1px solid var(--card-bg);
}

.error-title {
  color: var(--text-color);
  font-weight: 500;
  margin-bottom: 15px;
  font-size: 28px;
}

.modal-content p {
  color: white;
  margin-bottom: 20px;
  font-size: 22px;
}

.modal-button {
  display: inline-block;
  color: white;
  text-decoration: none;
  font-size: 17px;
  background: none;
  border: none;
  cursor: pointer;
  position: relative;
  padding-bottom: 2px;
  font-family: var(--font-family-main);
}

.modal-button::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 0;
  height: 1px;
  background-color: white;
  transition: width 0.3s ease;
  color: white;
}

.modal-button:hover::after {
  width: 100%;
  color: white;
}
.modal-button:hover {
  color: white;
}

/* Остальные стили формы */
h1 {
  color: white;
  font-weight: 500;
  margin: 0px;
  margin-bottom: 22px;
  font-size: 32px;
}

.card-form {
  text-align: left;
}

.form-group {
  margin-bottom: 15px;
}

label {
  display: block;
  margin-bottom: 6px;
  color: var(--text-color);
  font-weight: 500;
  font-size: 14px;
}

input[type="text"],
input[type="number"],
textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--card-bg);
  border-radius: 8px;
  background-color: rgba(255, 255, 255, 0.05);
  color: white;
  font-size: 14px;
}

textarea {
  min-height: 80px;
  resize: vertical;
}

/* Стили для загрузки файлов */
.file-upload-group {
  margin-bottom: 20px;
}

.file-upload-label {
  display: flex;
  align-items: center;
  width: 100%;
  cursor: pointer;
}

.file-upload-text {
  flex-grow: 1;
  padding: 10px;
  border: 1px solid var(--card-bg);
  border-radius: 8px 0 0 8px;
  background-color: rgba(255, 255, 255, 0.05);
  color: var(--text-color);
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-upload-button {
  padding: 10px 15px;
  background-color: rgba(255, 255, 255, 0.1);
  color: var(--text-color);
  border: 1px solid var(--card-bg);
  border-radius: 0 8px 8px 0;
  font-size: 14px;
  transition: background-color 0.2s;
}

.file-upload-button:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.file-upload-input {
  display: none;
}

.submit-button {
  width: 100%;
  padding: 12px;
  background: none;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 22px;
  font-weight: 500;
  cursor: pointer;
  position: relative;
  font-family: var(--font-family-main);
  margin-top: 10px;
}

.submit-button-text {
  position: relative;
  display: inline-block;
}

.submit-button-text::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 0;
  height: 1px;
  background-color: white;
  transition: width 0.3s ease;
}

.submit-button:hover .submit-button-text::after {
  width: 100%;
}

.submit-button:hover {
  color: white;
}

.back-link {
  display: inline-block;
  margin-top: 20px;
  color: white;
  text-decoration: none;
  font-size: 14px;
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
  background-color: white;
  transition: width 0.3s ease;
}

.back-link:hover {
  color: white;
}
.back-link:hover::after {
  width: 100%;
  color: white;
}

select {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--card-bg);
  border-radius: 8px;
  background-color: rgba(255, 255, 255, 0.05);
  color: white;
  font-size: 14px;
  font-family: var(--font-family-main);
  appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 10px center;
  background-size: 16px;
  cursor: pointer;
}
select:focus {
  outline: none;
  border-color: var(--accent-color);
}

option {
  background-color: var(--card-bg);
  color: white;
  font-family: var(--font-family-main);
}
@media (max-width: 768px) {
  .add-card-container {
    padding: 25px 20px;
    max-width: 90%;
  }
  h1 {
    font-size: 24px;
    margin-bottom: 15px;
  }
  
  .error-title {
    font-size: 24px;
  }
  select {
    padding: 8px;
    font-size: 14px;
  }
  
  input[type="text"],
  input[type="number"],
  textarea {
    padding: 8px;
    font-size: 14px;
  }
  .submit-button {
    font-size: 16px;
    padding: 10px;
  }
  
  .back-link {
    font-size: 13px;
  }
  .modal-content {
    padding: 20px;
  }
  
  .modal-content p {
    font-size: 14px;
  }
  .modal-button {
    font-size: 15px;
  }
}
</style>