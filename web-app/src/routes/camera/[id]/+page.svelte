<script lang="ts">
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import { goto } from "$app/navigation";
  import * as Accordion from "$lib/components/ui/accordion/index.js";

  const serverBase = "http://192.168.255.125:5000";
  const FRAME_WIDTH = 1280;
  const FRAME_HEIGHT = 720;
  const STREAM_WIDTH = 640;
  const STREAM_HEIGHT = 480;

  let camId: number;
  let threshold = 0.5;
  let recentAlertPhoto: { src: string; detections: any[] } | null = null;
  let alertTimeout: ReturnType<typeof setTimeout> | null = null;
  let overlayCanvas: HTMLCanvasElement | null = null;
  let alertCanvas: HTMLCanvasElement | null = null;

  $: camId = Number($page.params.id);

  $: {
    const t = Number($page.url.searchParams.get("threshold"));
    if (!isNaN(t)) threshold = t;
  }

  function terminatePrint() {
    alert(`Terminating print on camera ${camId}`);
  }

  function goHome() {
    goto("/");
  }

  const drawOverlay = async () => {
    if (!overlayCanvas) return;
    const ctx = overlayCanvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);

    try {
      const res = await fetch(`${serverBase}/detections/${camId}`);
      if (!res.ok) return;
      const detections = await res.json();

      const scaleX = overlayCanvas.width / FRAME_WIDTH;
      const scaleY = overlayCanvas.height / FRAME_HEIGHT;
      const alertDetections = detections.filter((det: any) => det.confidence >= threshold);

      if (alertDetections.length > 0 && !recentAlertPhoto) {
        recentAlertPhoto = {
          src: `${serverBase}/video/${camId}?t=${Date.now()}`,
          detections: alertDetections
        };

        if (alertTimeout) clearTimeout(alertTimeout);
        alertTimeout = setTimeout(() => {
          recentAlertPhoto = null;
        }, 5000);
      }

      detections.forEach((det: any) => {
        if (!det.bbox || det.bbox.length !== 4) return;
        const [x1, y1, x2, y2] = det.bbox.map(Number);

        ctx.strokeStyle = "lime";
        ctx.lineWidth = 2;
        ctx.strokeRect(x1 * scaleX, y1 * scaleY, (x2 - x1) * scaleX, (y2 - y1) * scaleY);

        ctx.fillStyle = "lime";
        ctx.font = "14px sans-serif";
        ctx.fillText(
          `${det.class} (${(det.confidence * 100).toFixed(1)}%)`,
          x1 * scaleX,
          Math.max(12, y1 * scaleY - 2)
        );
      });
    } catch (err) {
      console.error("Error fetching detections:", err);
    }
  };

  const drawAlertSnapshot = () => {
    if (!recentAlertPhoto || !alertCanvas) return;

    const img = new Image();
    img.src = recentAlertPhoto.src;
    img.onload = () => {
      if (!alertCanvas) return;
      const ctx = alertCanvas.getContext("2d");
      if (!ctx) return;

      ctx.clearRect(0, 0, alertCanvas.width, alertCanvas.height);
      ctx.drawImage(img, 0, 0, alertCanvas.width, alertCanvas.height);

      const scaleX = alertCanvas.width / FRAME_WIDTH;
      const scaleY = alertCanvas.height / FRAME_HEIGHT;

      recentAlertPhoto!.detections.forEach((det: any) => {
        const [x1, y1, x2, y2] = det.bbox.map(Number);

        ctx.strokeStyle = "red";
        ctx.lineWidth = 2;
        ctx.strokeRect(x1 * scaleX, y1 * scaleY, (x2 - x1) * scaleX, (y2 - y1) * scaleY);

        ctx.fillStyle = "red";
        ctx.font = "14px sans-serif";
        ctx.fillText(
          `${det.class} (${(det.confidence * 100).toFixed(1)}%)`,
          x1 * scaleX,
          Math.max(12, y1 * scaleY - 2)
        );
      });
    };
  };

  onMount(() => {
    const interval = setInterval(drawOverlay, 200);
    const alertInterval = setInterval(drawAlertSnapshot, 200);

    return () => {
      clearInterval(interval);
      clearInterval(alertInterval);
      if (alertTimeout) clearTimeout(alertTimeout);
    };
  });
</script>

<style>
  .page-container {
    display: flex;
    flex-direction: row;
    justify-content: center;
    align-items: flex-start;
    min-height: 100vh;
    gap: 2rem;
    padding: 2rem;
    background: #111;
    color: white;
  }

  .info-box {
    flex: 1 1 50%;
    max-width: 50%;
    background: #222;
    padding: 1rem;
    border-radius: 0.5rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    align-items: center;
    text-align: center;
  }

  .video-container {
    width: 640px;
    height: 480px;
    position: relative;
    background: black;
    border-radius: 1rem;
    overflow: hidden;
  }

  .video-container img,
  .video-container canvas {
    width: 100%;
    height: 100%;
    object-fit: fill;
    position: absolute;
    top: 0;
    left: 0;
    border-radius: 1rem;
  }

  .home-button,
  .info-box button {
    cursor: pointer;
    border: none;
    border-radius: 0.25rem;
    background: #444;
    color: white;
    padding: 0.5rem 1rem;
    transition: background 0.2s;
  }

  .home-button:hover,
  .info-box button:hover {
    background: #555;
  }

  .alert-snapshot {
    position: relative;
    width: 100%;
    border-radius: 0.5rem;
    margin-top: 0.5rem;
  }

  .alert-snapshot img {
    width: 100%;
    border-radius: 0.5rem;
    display: block;
  }

  .alert-snapshot canvas {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    border-radius: 0.5rem;
  }
</style>

<div class="page-container">
  <div class="info-box">
    <h2>Camera {camId}</h2>
    <button on:click={terminatePrint}>Terminate Print</button>

    <Accordion.Root type="single" class="w-full" value="item-1">
      <Accordion.Item value="item-1">
        <Accordion.Trigger class="accordion-trigger">More Details</Accordion.Trigger>
        <Accordion.Content class="accordion-content">
          <p>Threshold: {threshold.toFixed(2)}</p>
          {#if recentAlertPhoto}
            <p>Recent Detection:</p>
            <div class="alert-snapshot">
              <img src={recentAlertPhoto.src} alt="Alert Snapshot" />
              <canvas
                width={STREAM_WIDTH}
                height={STREAM_HEIGHT}
                bind:this={alertCanvas}
              ></canvas>
            </div>
          {/if}
        </Accordion.Content>
      </Accordion.Item>
    </Accordion.Root>

    <button class="home-button" on:click={goHome}>Home / Back to Carousel</button>
  </div>

  <div class="video-container">
    <img src={`${serverBase}/video/${camId}`} alt={`Camera ${camId}`} />
    <canvas width={STREAM_WIDTH} height={STREAM_HEIGHT} bind:this={overlayCanvas}></canvas>
  </div>
</div>
