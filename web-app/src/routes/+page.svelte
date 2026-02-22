<script lang="ts">
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { fade } from "svelte/transition";
  import * as Accordion from "$lib/components/ui/accordion/index.js";
  import { Slider } from "$lib/components/ui/slider/index.js";
  import { Switch } from "$lib/components/ui/switch/index.js";
  import { Label } from "$lib/components/ui/label/index.js";

  const serverBase = "http://192.168.255.125:5000";

  // Camera state
  let cameras: { index: number; device: string }[] = [];
  let currentIndex = 0;

  // Control panel state
  let threshold = 0.5;
  let autoTerminate = false;

  // Fetch the camera list from backend
  async function fetchCameras() {
    try {
      const res = await fetch(`${serverBase}/cameras`);
      if (!res.ok) throw new Error("Failed to fetch cameras");
      cameras = await res.json();
      // Reset index if cameras exist
      if (cameras.length > 0) currentIndex = 0;
    } catch (err) {
      console.error("Failed to fetch cameras:", err);
      cameras = [];
    }
  }

  onMount(() => {
    fetchCameras();
    // Optional: refresh every 10 seconds
    // const interval = setInterval(fetchCameras, 10000);
    // return () => clearInterval(interval);
  });

  function next() {
    if (cameras.length === 0) return;
    currentIndex = (currentIndex + 1) % cameras.length;
  }

  function prev() {
    if (cameras.length === 0) return;
    currentIndex = (currentIndex - 1 + cameras.length) % cameras.length;
  }

  function goToCam(camId: number) {
    // Pass threshold as a query parameter
    goto(`/camera/${camId}?threshold=${threshold}`);
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

  .info-box {
    background: #2a2a2a;
    border-radius: 1rem;
    padding: 1.5rem 2rem;
    width: 100%;
    max-width: 1000px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);

    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
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
  <!-- Info -->
  <div class="info-box">
    <h2>Smart Extruder</h2>
    <Accordion.Root type="single" class="w-full sm:max-w-[70%]" value="item-1">
      <Accordion.Item value="item-1">
        <Accordion.Trigger class="accordion-trigger">
          How It Works
        </Accordion.Trigger>
        <Accordion.Content class="accordion-content">
          <p>Our Smart Extruder uses a YOLO model to detect printer failures in real-time.</p>
          <p>Key features: advanced detection, intuitive interface, and automated alerts.</p>
        </Accordion.Content>
      </Accordion.Item>
    </Accordion.Root>
  </div>

  <!-- Video carousel -->
  {#if cameras.length > 0}
    <div class="center-panel">
      <div class="camera-card">
        <div class="video-container" on:click={() => goToCam(cameras[currentIndex].index)}>
          {#key currentIndex}
            <img
              src={`${serverBase}/video/${cameras[currentIndex].index}`}
              alt={`Camera ${cameras[currentIndex].index}`}
              transition:fade={{ duration: 400 }}
            />
          {/key}
        </div>
        <div class="controls">
          <button on:click={prev}>⏮ Previous</button>
          <span class="slide-number">{currentIndex + 1} / {cameras.length}</span>
          <button on:click={next}>Next ⏭</button>
        </div>
      </div>
    </div>
  {:else}
    <p>Loading cameras...</p>
  {/if}

  <!-- Settings -->
  <div class="control-panel">
    <div style="flex:1; min-width:200px;">
      <label>Detection Threshold: {threshold.toFixed(2)}</label>
      <Slider type="single" min={0} max={1} step={0.01} bind:value={threshold} />
    </div>

    <div class="flex items-center space-x-2">
      <Switch bind:checked={autoTerminate} id="auto-terminate" />
      <Label for="auto-terminate">Enable Auto Terminate</Label>
    </div>

    <button on:click={applySettings}>Apply Settings</button>
  </div>
</div>