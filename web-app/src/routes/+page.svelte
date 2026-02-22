<script lang="ts">
  import { goto } from "$app/navigation";
  import { fade } from "svelte/transition";

  const serverBase = "http://172.31.88.33:5000";
  const CAM_COUNT = 3;
  let currentIndex = 0;

  // Control panel state
  let threshold = 0.5;
  let autoTerminate = false;

  function next() {
    currentIndex = (currentIndex + 1) % CAM_COUNT;
  }

  function prev() {
    currentIndex = (currentIndex - 1 + CAM_COUNT) % CAM_COUNT;
  }

  function goToCam(camId: number) {
    goto(`/camera/${camId}`);
  }

  function applySettings() {
    alert(`Settings applied:\nThreshold: ${threshold}\nAuto Terminate: ${autoTerminate}`);
  }
</script>

<style>
  /* Global body background */
  :global(body) {
    margin: 0;
    font-family: 'Segoe UI', sans-serif;
    background: #1a1a1a; /* dark grey */
    color: #fff;
  }

  /* Page container */
  .page-container {
    display: flex;
    justify-content: center;
    align-items: flex-start;
    gap: 2rem;
    min-height: 100vh;
    padding: 2rem;
  }

  /* Left Info Box */
  .info-box {
    background: #2a2a2a;
    border-radius: 1rem;
    padding: 2rem;
    width: 250px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
  }

  .info-box h2 {
    margin-top: 0;
    margin-bottom: 1rem;
    font-size: 1.5rem;
  }

  .info-box p {
    margin-bottom: 1rem;
    line-height: 1.5;
    color: #ccc;
  }

  /* Center Video Carousel */
  .center-panel {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1.5rem;
  }

  .camera-card {
    background: #222; /* slightly lighter dark */
    border-radius: 1rem;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
  }

  .video-container {
    width: 360px;
    aspect-ratio: 16/9;
    overflow: hidden;
    border-radius: 1rem;
    cursor: pointer;
  }

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 1rem;
  }

  .controls {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  button {
    padding: 0.5rem 1rem;
    font-size: 1rem;
    cursor: pointer;
    background: #333;
    color: #fff;
    border: 1px solid #555;
    border-radius: 0.5rem;
    transition: background 0.2s ease;
  }

  button:hover {
    background: #555;
  }

  .slide-number {
    font-weight: bold;
    color: #ddd;
  }

  /* Right Control Panel */
  .control-panel {
    background: #2a2a2a;
    border-radius: 1rem;
    padding: 2rem;
    width: 250px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .control-panel label {
    display: flex;
    flex-direction: column;
    font-size: 0.9rem;
    color: #ccc;
  }

  input[type="number"], input[type="checkbox"] {
    margin-top: 0.3rem;
    padding: 0.4rem 0.6rem;
    border-radius: 0.25rem;
    border: none;
    outline: none;
    font-size: 0.9rem;
  }

  .control-panel button {
    margin-top: 0.5rem;
  }

  /* Responsive */
  @media (max-width: 1000px) {
    .page-container {
      flex-direction: column;
      align-items: center;
    }

    .info-box, .control-panel {
      width: 100%;
    }

    .video-container {
      width: 90%;
    }
  }
</style>

<div class="page-container">
  <!-- Left Info Box -->
  <div class="info-box">
    <h2>Smart Extruder</h2>
    <p>This tool uses a <strong>YOLO model</strong> to detect printer failures in real-time.</p>
    <p>It helps prevent filament loss and ensures prints stay on track.</p>
  </div>

  <!-- Center Video Carousel with Fade Transition -->
  <div class="center-panel">
    <div class="camera-card">
      <div class="video-container" on:click={() => goToCam(currentIndex)}>
        {#key currentIndex}
          <img
            src={`${serverBase}/video/${currentIndex}`}
            alt={`Camera ${currentIndex}`}
            transition:fade={{ duration: 400 }}
          />
        {/key}
      </div>

      <div class="controls">
        <button on:click={prev}>⏮ Previous</button>
        <span class="slide-number">{currentIndex + 1} / {CAM_COUNT}</span>
        <button on:click={next}>Next ⏭</button>
      </div>
    </div>
  </div>

  <!-- Right Control Panel -->
  <div class="control-panel">
    <label>
      Detection Threshold
      <input type="number" min="0" max="1" step="0.01" bind:value={threshold} />
    </label>

    <label>
      <input type="checkbox" bind:checked={autoTerminate} />
      Enable Auto Terminate
    </label>

    <button on:click={applySettings}>Apply Settings</button>
  </div>
</div>