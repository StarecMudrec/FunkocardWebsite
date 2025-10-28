<template>
  <div class="about-view">
    <!-- Background with blur effect -->
    <div class="background-blur"></div>
    
    <!-- Content container -->
    <div class="content">
      <!-- Logo in the center -->
      <div class="logo-container">
        <img src="/logo_noph.png" alt="Logo" class="logo">
      </div>
      
      <div class="info-container">
        <h1>ABOUT US:</h1>
        <div class="columns-container">
          <div class="column">
            <p><strong>FUNKO CHANNEL</strong> - <a href="https://t.me/FUNKOCARD" target="_blank" rel="noopener noreferrer">@FUNKOCARD</a></p>
            <p><strong>FUNKO CARD</strong> - <a href="https://t.me/Funko_Cards_Bot" target="_blank" rel="noopener noreferrer">@Funko_Cards_Bot</a></p>
            <p><strong>COMMUNITY</strong> - <a href="https://t.me/COMMUNITYFUNKO" target="_blank" rel="noopener noreferrer">@COMMUNITYFUNKO</a></p>
          </div>
          <div class="column">
            <p><strong>THE COLLECTORS CLUB</strong> - <a href="https://t.me/FUNKOOTHER" target="_blank" rel="noopener noreferrer">@FUNKOOTHER</a></p>
            <p><strong>ARCHIVE CARD</strong> - <a href="https://t.me/funkocardsall" target="_blank" rel="noopener noreferrer">@funkocardsall</a></p>
            <p><strong>ADMIN BLOG</strong> - <a href="https://t.me/btcfflife" target="_blank" rel="noopener noreferrer">@btcfflife</a></p>
          </div>
        </div>
        <!-- <p class="discord-link">
          <svg class="discord-icon" width="30" height="30" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19.27 5.33C17.94 4.71 16.5 4.26 15 4a.09.09 0 0 0-.07.03c-.18.33-.39.76-.53 1.09a16.09 16.09 0 0 0-4.8 0c-.14-.34-.35-.76-.54-1.09c-.01-.02-.04-.03-.07-.03c-1.5.26-2.93.71-4.27 1.33c-.01 0-.02.01-.03.02c-2.72 4.07-3.47 8.03-3.1 11.95c0 .02.01.04.03.05c1.8 1.32 3.53 2.12 5.24 2.65c.03.01.06 0 .07-.02c.4-.55.76-1.13 1.07-1.74c.02-.04 0-.08-.04-.09c-.57-.22-1.11-.48-1.64-.78c-.04-.02-.04-.08-.01-.11c.11-.08.22-.17.33-.25c.02-.02.05-.02.07-.01c3.44 1.57 7.15 1.57 10.55 0c.02-.01.05-.01.07.01c.11.09.22.17.33.26c.04.03.04.09-.01.11c-.52.31-1.07.56-1.64.78c-.04.01-.05.06-.04.09c.32.61.68 1.19 1.07 1.74c.03.01.06.02.09.01c1.72-.53 3.45-1.33 5.25-2.65c.02-.01.03-.03.03-.05c.44-4.53-.73-8.46-3.1-11.95c-.01-.01-.02-.02-.04-.02zM8.52 14.91c-1.03 0-1.89-.95-1.89-2.12s.84-2.12 1.89-2.12c1.06 0 1.9.96 1.89 2.12c0 1.17-.84 2.12-1.89 2.12zm6.97 0c-1.03 0-1.89-.95-1.89-2.12s.84-2.12 1.89-2.12c1.06 0 1.9.96 1.89 2.12c0 1.17-.83 2.12-1.89 2.12z"/>
          </svg>
          <strong>DISCORD</strong> - <a href="https://discord.gg/your-invite-link" target="_blank" rel="noopener noreferrer">FUNKOCARD</a>
        </p> -->
        <p class="signature">
          WEBSITE BY <a href="https://t.me/StarecMudrec" target="_blank" rel="noopener noreferrer" class="signature-link">@StarecMudrec</a>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AboutView'
}
</script>

<style scoped>
/* .base */
.about-view {
  position: relative;
  min-height: 100vh;
  padding: 20px;
  /* max-width: 1200px;
  margin: 0 auto; */
  /* overflow: hidden; */
  font-family: 'Afacad', sans-serif;
}

.background-blur {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: url('/background.jpg');
  background-size: cover;
  background-position: center;
  filter: blur(10px);
  z-index: -1;
}

.content {
  position: absolute;
  z-index: 1;
  text-align: center;
  bottom: 0;
  left: 0;
  right: 0;
  width: 100%;
}

.logo-container {
  display: flex;
  justify-content: center;
  align-items: center;
  /* margin-bottom: 40px; */
}

.logo {
  width: 50vh;
  aspect-ratio: 1;
  /* background-color: rgba(255, 255, 255, 0.9); */
  /* border-radius: 50%; */
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 24px;
  font-weight: bold;
  color: #333;
  /* box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3); */
}

.info-container {
  background-color: rgb(30, 30, 30, 0.95);
  backdrop-filter: blur(5px);
  border-color: #2B2B2B;
  border-width: 2px;
  border-top-left-radius: 10px;
  border-top-right-radius: 10px;
  border-top: 2px solid #333;
  width: 100vw;
  /* height: 34vh; */
}

h1 {
  color: white;
  font-size: 3rem;
  margin: 0;
  padding-top: 30px;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
}

.columns-container {
  display: flex;
  justify-content: center;
  gap: 140px;
  margin-top: 26px;
  margin-bottom: 10px;
}

.column {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

p {
  color: white;
  font-size: 1.4rem;
  line-height: 1.6;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.discord-link {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.discord-icon {
  color: #5865F2; /* Discord brand color */
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.signature {
  color: #ffffff;
  text-shadow: none;
  font-weight: bold;
  justify-content: center;
  margin-right: 3vw;
  font-size: 1.4rem;
  padding-bottom: 30px;
}

.signature-link {
  color: #4fc3f7 !important;
  text-decoration: none;
  position: relative;
  transition: all 0.3s ease;
  display: inline-block;
  font-weight: normal;
}

/* Custom underline for signature link */
.signature-link::after {
  content: '';
  position: absolute;
  width: 0;
  height: 2px; 
  bottom: -2px;
  left: 50%;
  background-color: #29b6f6; /* Same color as signature */
  transition: all 0.3s ease;
  transform: translateX(-50%);
}

.signature-link:hover {
  color: #29b6f6 !important;
  transform: scale(1.05);
}

.signature-link:hover::after {
  width: 100%;
}

strong {
  color: #fff;
  font-weight: bold;
}

a {
  color: #4fc3f7; /* Light blue color for links */
  text-decoration: none;
  position: relative;
  transition: all 0.3s ease;
  display: inline-block; /* Required for transform to work properly */
}

/* Animated underline from center */
a::after {
  content: '';
  position: absolute;
  width: 0;
  height: 2px;
  bottom: -2px;
  left: 50%;
  background-color: #29b6f6;
  transition: all 0.3s ease;
  transform: translateX(-50%);
}

a:hover {
  color: #29b6f6;
  transform: scale(1.05); /* Text expansion effect */
}

a:hover::after {
  width: 100%;
}

/* Discord icon hover effects */
.discord-link:hover .discord-icon {
  color: #29b6f6;
  transform: scale(1.1);
}

.discord-link:hover a {
  color: #29b6f6;
  transform: scale(1.05);
}

/* Alternative more pronounced scale effect */
/*
a:hover {
  color: #29b6f6;
  transform: scale(1.1);
  text-shadow: 0 0 10px rgba(41, 182, 246, 0.3);
}
*/

/* Smooth transition for the parent paragraph to prevent layout shift */
p {
  transition: transform 0.3s ease;
}

/* Responsive design */
@media (max-width: 890px) {
  .logo {
    width: 40vh;
    aspect-ratio: 1;
    font-size: 20px;
  }

  .content {
    top: 90px;
  }
  
  h1 {
    font-size: 2.7rem;
  }
  
  p {
    font-size: 1.4rem;
    flex-wrap: wrap;
    gap: 5px;
  }
  
  .columns-container {
    flex-direction: column;
    gap: 20px;
  }
  
  a::after {
    height: 1px;
    bottom: -1px;
  }
  
  .signature-link::after {
    height: 1px;
    bottom: -1px;
  }
  
  .discord-icon {
    width: 16px;
    height: 16px;
  }
  
  /* Slightly smaller scale on mobile for better UX */
  a:hover {
    transform: scale(1.03);
  }
  
  .signature-link:hover {
    transform: scale(1.03);
  }
  
  .discord-link:hover .discord-icon {
    transform: scale(1.05);
  }
}
</style>