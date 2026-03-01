<template>
  <div class="wallet-card">
    <div class="balance-section">
      <span>Current Balance</span>
      <h2>Rs. {{ balance.toLocaleString() }}</h2>
    </div>

    <button @click="handlePayment" class="pay-btn">
      Verify & Pay Fee
    </button>

    <div v-if="status.show" :class="['status-box', status.type]">
      {{ status.msg }}
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { BiometricAuth } from '@aparajita/capacitor-biometric-auth';

const balance = ref(15000); // Example initial balance
const status = ref({ show: false, msg: '', type: '' });

async function handlePayment() {
  try {
    const auth = await BiometricAuth.authenticate({
      reason: "Confirm payment to Starlight Institution",
      cancelTitle: "Cancel"
    });

    // Logic: Deduction
    balance.value -= 5000;
    showFeedback("Fee Paid Successfully!", "success");
  } catch (e) {
    showFeedback("Authentication Failed", "error");
  }
}

function showFeedback(msg, type) {
  status.value = { show: true, msg, type };
  setTimeout(() => status.value.show = false, 3000);
}
</script>

<style scoped>
.wallet-card { background: #1a1a1a; color: white; padding: 20px; border-radius: 15px; border-left: 6px solid #28a745; }
.pay-btn { background: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; width: 100%; margin-top: 15px; font-weight: bold; }
.status-box { position: absolute; bottom: 10px; right: 10px; padding: 10px; border-radius: 5px; }
.success { background: #28a745; }
.error { background: #dc3545; }
</style>
