<template>
  <div class="video-feed">
    <div v-for="post in challenges" :key="post.id" class="video-container">

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
  </div>
</template>

<script setup>
import { ref } from 'vue';

// Mock data for the Global Platform
const challenges = ref([
  {
    id: 1,
    institution: "Starlight Academy",
    title: "The Calculus Race",
    description: "Solve this derivative in 30 seconds!",
    videoUrl: "https://vjs.zencdn.net/v/oceans.mp4"
  },
  {
    id: 2,
    institution: "Punjab Science Tech",
    title: "Chemical Bonds",
    description: "Identify the covalent bond in this animation.",
    videoUrl: "https://vjs.zencdn.net/v/oceans.mp4"
  }
]);

function openSolver(id) {
  window.dispatchEvent(new CustomEvent('open-math-console', { detail: { challengeId: id } }));
}

function sendGrant(id) {
  // This talks to our Wallet component
  window.dispatchEvent(new CustomEvent('trigger-grant-animation', { detail: { amount: 100 } }));
}
</script>

<style scoped>
.video-feed {
  height: 100vh;
  overflow-y: scroll;
  scroll-snap-type: y mandatory; /* Makes it "snap" like TikTok */
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
  bottom: 50px;
  left: 20px;
  right: 20px;
  color: white;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
}

.institution-tag {
  background: rgba(40, 167, 69, 0.8);
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
}

.grant-btn {
  margin-top: 15px;
  font-size: 1.2rem;
  cursor: pointer;
}
</style>