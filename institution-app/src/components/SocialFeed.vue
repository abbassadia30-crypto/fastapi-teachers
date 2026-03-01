<template>
  <div class="video-feed">
    <div v-if="isLoading" class="loading-overlay">
      <div class="spinner"></div>
      <p>Fetching Starlight Challenges...</p>
    </div>

    <div v-else v-for="post in challenges" :key="post.id" class="video-container">
      <video class="vjs-tech" autoplay loop muted playsinline>
        <source :src="post.videoUrl" type="video/mp4">
      </video>

      <div class="overlay">
        <div class="institution-tag">🏛️ {{ post.institution }}</div>

        <div class="challenge-info">
          <h3>{{ post.title }}</h3>
          <p>{{ post.description }}</p>
        </div>

        <div class="actions">
          <button @click="openSolver(post.id)" class="solve-btn">
            Solve Challenge 📝
          </button>
          <div class="grant-btn" @click="sendGrant(post.id)">
            💰 Grant
          </div>
        </div>
      </div>
    </div>

    <div v-if="!isLoading && challenges.length === 0" class="no-data">
      <p>No challenges found. Be the first to post!</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { api } from '../services/api'; // 🏛️ Using the service we created

const challenges = ref([]);
const isLoading = ref(true);

// 🏛️ Real App Logic: Fetching from the Live Super Console
onMounted(async () => {
  try {
    const data = await api.getChallenges();
    // Use real data if available, otherwise fallback to empty list
    challenges.value = data || [];
  } catch (error) {
    console.error("Feed Error:", error);
  } finally {
    isLoading.value = false;
  }
});

function openSolver(id) {
  // Dispatches to the Math Solving Console
  window.dispatchEvent(new CustomEvent('open-math-console', { detail: { challengeId: id } }));
}

function sendGrant(id) {
  // Dispatches to the In-App Wallet for the Grant Animation
  window.dispatchEvent(new CustomEvent('trigger-grant-animation', {
    detail: { amount: 100, targetId: id }
  }));
}
</script>

<style scoped>
/* 🏛️ Root CSS inside the Head/Component as requested */
.video-feed {
  height: 100vh;
  overflow-y: scroll;
  scroll-snap-type: y mandatory;
  background: black;
}

.video-container {
  height: 100vh;
  width: 100%;
  position: relative;
  scroll-snap-align: start;
}

video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.overlay {
  position: absolute;
  bottom: 80px; /* Adjusted for mobile navigation space */
  left: 20px;
  right: 20px;
  color: white;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
}

.institution-tag {
  background: rgba(40, 167, 69, 0.8); /* Green for Institutional Trust */
  padding: 5px 12px;
  border-radius: 20px;
  display: inline-block;
  font-size: 0.8rem;
  margin-bottom: 10px;
}

.solve-btn {
  background: #1a73e8;
  color: white;
  border: none;
  padding: 15px 25px;
  border-radius: 30px;
  font-weight: bold;
  box-shadow: 0 4px 15px rgba(0,0,0,0.3);
  cursor: pointer;
  transition: transform 0.2s;
}

.solve-btn:active {
  transform: scale(0.95);
}

.grant-btn {
  margin-top: 15px;
  font-size: 1.2rem;
  cursor: pointer;
  display: inline-block;
  background: rgba(255, 255, 255, 0.2);
  padding: 8px 15px;
  border-radius: 15px;
  margin-left: 10px;
}

/* 🏛️ Loading & Empty States */
.loading-overlay, .no-data {
  height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #28a745;
  text-align: center;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(40, 167, 69, 0.2);
  border-top: 4px solid #28a745;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>