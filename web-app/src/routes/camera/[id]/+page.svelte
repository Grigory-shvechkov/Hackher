<script lang="ts">
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import { goto } from "$app/navigation";
  import * as Accordion from "$lib/components/ui/accordion/index.js";

  const serverBase = "http://192.168.255.125:5000";
  const FRAME_WIDTH = 320;
  const FRAME_HEIGHT = 240;

  let camId: number;
  let overlayInterval: ReturnType<typeof setInterval>;
  let threshold = 0.5; // default threshold

  // Get camId from route params
  $: camId = Number($page.params.id);

  // Get threshold from query params
  $: {
    const urlParams = new URLSearchParams($page.url.search);
    const t = urlParams.get("threshold");
    if (t) threshold = Number(t);
  }

  function terminatePrint() {
    alert(`Terminating print on camera ${camId}`);
    console.log(`[DEBUG] Terminate print triggered for camera ${camId}`);
    // TODO: call backend API to terminate print
  }

  function goHome() {
    console.log("[DEBUG] Navigating back to home carousel");
    goto("/");
  }

  onMount(() => {
    const canvas = document.getElementById(`overlay`) as HTMLCanvasElement;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Keep track of which detections we've alerted on to prevent spam
    const alertedDetections = new Set<string>();

    const drawDetections = async () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      try {
        const res = await fetch(`${serverBase}/detections/${camId}`);
        if (!res.ok) return;
        const detections = await res.json();

        const scaleX = canvas.width / FRAME_WIDTH;
        const scaleY = canvas.height / FRAME_HEIGHT;

        detections.forEach((det: any) => {
          if (!det.bbox || det.bbox.length !== 4) return;
          const [x1, y1, x2, y2] = det.bbox.map(Number);

          // Draw bounding box
          ctx.strokeStyle = "lime";
          ctx.lineWidth = 2;
          ctx.strokeRect(
            x1 * scaleX,
            y1 * scaleY,
            (x2 - x1) * scaleX,
            (y2 - y1) * scaleY
          );

          ctx.fillStyle = "lime";
          ctx.font = "12px sans-serif";
          ctx.fillText(
            `${det.class} (${(det.confidence * 100).toFixed(1)}%)`,
            x1 * scaleX,
            Math.max(0, y1 * scaleY - 2)
          );

          // Alert if detection exceeds threshold (only once per detection)
          const detKey = `${det.class}-${det.bbox.join(",")}`;
          if (det.confidence >= threshold && !alertedDetections.has(detKey)) {
            alert(
              `Alert! ${det.class} detected with confidence ${(det.confidence * 100).toFixed(
                1
              )}% (threshold: ${(threshold * 100).toFixed(1)}%)`
            );
            alertedDetections.add(detKey);
          }
        });
      } catch (err) {
        console.error("Error fetching detections:", err);
      }
    };

    drawDetections();
    overlayInterval = setInterval(drawDetections, 200);

    return () => clearInterval(overlayInterval);
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
    flex: 1;
    max-width: 350px;
    background: #222;
    padding: 1rem;
    border-radius: 0.5rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .info-box h2 {
    margin: 0;
  }

  .info-box button {
    padding: 0.5rem 1rem;
    font-size: 1rem;
    cursor: pointer;
    border-radius: 0.25rem;
    border: none;
    background: #444;
    color: white;
  }

  .info-box button:hover {
    background: #555;
  }

  .video-container {
    width: 640px;
    height: 480px;
    position: relative;
    background: black;
  }

  .video-container img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }

  .video-container canvas {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 10;
  }

  /* Accordion overrides */
  .accordion-trigger {
    cursor: pointer;
    background: #333;
    padding: 0.5rem;
    border-radius: 0.25rem;
    font-weight: bold;
  }

  .accordion-content {
    background: #222;
    padding: 0.5rem 1rem;
    border-left: 2px solid #555;
  }

  .home-button {
    margin-top: 1rem;
    padding: 0.5rem 1rem;
    font-size: 1rem;
    cursor: pointer;
    border-radius: 0.25rem;
    border: none;
    background: #444;
    color: white;
  }

  .home-button:hover {
    background: #555;
  }
</style>

<div class="page-container">
  <!-- Info / Controls -->
  <div class="info-box">
    <h2>Camera {camId}</h2>
    <button on:click={terminatePrint}>Terminate Print</button>
    <button class="home-button" on:click={goHome}>Back to Home</button>

    <Accordion.Root type="single" class="w-full" value="item-1">
      <Accordion.Item value="item-1">
        <Accordion.Trigger class="accordion-trigger">More Details</Accordion.Trigger>
        <Accordion.Content class="accordion-content">
          <p>Current print status: Active</p>
          <p>Printer temperature: 210°C</p>
          <p>Filament remaining: 120g</p>
          <!-- Add any other dynamic info you fetch from backend -->
        </Accordion.Content>
      </Accordion.Item>
    </Accordion.Root>
  </div>

  <!-- Video Feed -->
  <div class="video-container">
    <img src={`${serverBase}/video/${camId}`} alt={`Camera ${camId}`} />
    <canvas id="overlay" width={FRAME_WIDTH} height={FRAME_HEIGHT}></canvas>
  </div>
</div>