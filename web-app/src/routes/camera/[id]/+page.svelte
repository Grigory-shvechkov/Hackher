<script lang="ts">
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import { goto } from "$app/navigation";
  import * as Accordion from "$lib/components/ui/accordion/index.js";

  const serverBase = "http://172.31.88.33:5000";
  const FRAME_WIDTH = 640;  // fixed display width
  const FRAME_HEIGHT = 480; // fixed display height

  let camId: number;
  let overlayInterval: ReturnType<typeof setInterval>;

  $: camId = Number($page.params.id);

  function terminatePrint() {
    alert(`Terminating print on camera ${camId}`);
    // TODO: call backend API to terminate print
  }

  function goHome() {
    goto("/"); // replace with your carousel route
  }

  onMount(() => {
    const canvas = document.getElementById("overlay") as HTMLCanvasElement;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

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

          ctx.save();
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
          ctx.restore();
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
    flex: 1 1 50%;
    max-width: 50%;
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
    width: 640px;   /* fixed width */
    height: 480px;  /* fixed height */
    position: relative;
    background: black;
    border-radius: 1rem;
    overflow: hidden;
    display: flex;
    justify-content: center;
    align-items: center;
  }

  .video-container img,
  .video-container canvas {
    width: 100%;
    height: 100%;
    object-fit: cover; /* keeps aspect ratio, crops if needed */
    display: block;
    border-radius: 1rem;
    position: absolute;
    top: 0;
    left: 0;
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

  /* Home button at bottom */
  .home-button {
    margin-top: auto; /* push to bottom */
    padding: 0.5rem 1rem;
    font-size: 1rem;
    cursor: pointer;
    border-radius: 0.25rem;
    border: none;
    background: #666;
    color: white;
  }

  .home-button:hover {
    background: #777;
  }
</style>

<div class="page-container">
  <!-- Info / Controls -->
  <div class="info-box">
    <h2>Camera {camId}</h2>
    <button on:click={terminatePrint}>Terminate Print</button>

    <Accordion.Root type="single" class="w-full" value="item-1">
      <Accordion.Item value="item-1">
        <Accordion.Trigger class="accordion-trigger">More Details</Accordion.Trigger>
        <Accordion.Content class="accordion-content">
          <p>Current print status: Active</p>
          <p>Printer temperature: 210°C</p>
          <p>Filament remaining: 120g</p>
        </Accordion.Content>
      </Accordion.Item>
    </Accordion.Root>

    <!-- Home button -->
    <button class="home-button" on:click={goHome}>
      Home / Back to Carousel
    </button>
  </div>

  <!-- Video Feed -->
  <div class="video-container">
    <img src={`${serverBase}/video/${camId}`} alt={`Camera ${camId}`} />
    <canvas id="overlay" width={FRAME_WIDTH} height={FRAME_HEIGHT}></canvas>
  </div>
</div>