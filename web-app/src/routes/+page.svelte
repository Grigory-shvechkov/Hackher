<script lang="ts">
  import { goto } from "$app/navigation";
  import { fade } from "svelte/transition";
  import * as Accordion from "$lib/components/ui/accordion/index.js";

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
  :global(body) {
    margin: 0;
    font-family: 'Segoe UI', sans-serif;
    background: #1a1a1a;
    color: #fff;
  }

  .page-container {
    display: flex;
    flex-direction: column;
    gap: 2rem;
    min-height: 100vh;
    padding: 2rem;
    align-items: center;
  }

  /* Accordion Info Banner */
  .info-box {
    background: #2a2a2a;
    border-radius: 1rem;
    padding: 1.5rem 2rem;
    width: 100%;
    max-width: 1000px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
  }

  .info-box h2 {
    margin-top: 0;
    margin-bottom: 1rem;
    font-size: 1.8rem;
  }

  .accordion-trigger {
    cursor: pointer;
    font-weight: bold;
    padding: 0.5rem 0;
    border-bottom: 1px solid #444;
  }

  .accordion-content {
    padding: 0.5rem 0 1rem 0;
    color: #ccc;
  }

  /* Video carousel */
  .center-panel {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1.5rem;
    width: 100%;
  }

  .camera-card {
    background: #222;
    border-radius: 1rem;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
  }

  .video-container {
    width: 640px;
    aspect-ratio: 16/9;
    overflow: hidden;
    border-radius: 1rem;
    cursor: pointer;
  }

  .video-container img {
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

  .slide-number {
    font-weight: bold;
    color: #ddd;
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

  /* Settings panel */
  .control-panel {
    background: #2a2a2a;
    border-radius: 1rem;
    padding: 1.5rem 2rem;
    width: 100%;
    max-width: 1000px;
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 2rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
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
    margin-top: 1rem;
  }

  @media (max-width: 700px) {
    .video-container {
      width: 90%;
    }

    .control-panel {
      flex-direction: column;
      align-items: center;
    }
  }
</style>

<div class="page-container">
  <!-- Top row: Accordion Info -->
  <div class="info-box">
    <h2>Smart Extruder</h2>

    <Accordion.Root type="single" class="w-full sm:max-w-[70%]" value="item-1">
  <Accordion.Item value="item-1">
    <Accordion.Trigger class="accordion-trigger">
      <div style="text-align: center; width: 100%;">
        How It Works
      </div>
    </Accordion.Trigger>
    <Accordion.Content class="accordion-content">
      <p>
        Our Smart Extruder uses a YOLO model to detect printer failures in real-time.
        It prevents filament loss and keeps prints on track.
      </p>
      <p>
        Key features: advanced detection, intuitive interface, and automated alerts.
      </p>
    </Accordion.Content>
  </Accordion.Item>
</Accordion.Root>
  </div>

  <!-- Middle row: Video carousel -->
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

  <!-- Bottom row: Settings panel -->
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