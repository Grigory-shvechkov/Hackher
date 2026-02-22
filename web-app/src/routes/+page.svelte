<script lang="ts">
  import { onMount } from "svelte";

  const serverBase = "http://172.31.88.33:5000";

  // Frame dimensions from backend
  const FRAME_WIDTH = 320;
  const FRAME_HEIGHT = 240;

  let camIdx = 0; // choose which camera to show
  let overlayInterval: ReturnType<typeof setInterval>;

  onMount(() => {
    const canvas = document.getElementById(`overlay`) as HTMLCanvasElement;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const drawOverlay = async () => {
      // clear previous drawings
      ctx.clearRect(0, 0, canvas.width, canvas.height);

    
      try {
        const res = await fetch(`${serverBase}/detections/${camIdx}`);
        if (!res.ok) return;
        const detections = await res.json();

        const scaleX = canvas.width / FRAME_WIDTH;
        const scaleY = canvas.height / FRAME_HEIGHT;

        // draw YOLO boxes
        detections.forEach((det: any) => {
          if (!det.bbox || det.bbox.length !== 4) return;
          const [x1, y1, x2, y2] = det.bbox.map(Number);

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
        });
      } catch (err) {
        console.error("Error fetching detections:", err);
      }
    };

    drawOverlay(); // draw immediately
    overlayInterval = setInterval(drawOverlay, 200); // update every 200ms

    return () => {
      clearInterval(overlayInterval);
    };
  });
</script>

<style>
  .video-container {
    position: relative;
    width: 320px;
    height: 240px;
    background: black;
  }
  canvas {
    position: absolute;
    top: 0;
    left: 0;
    z-index: 10;
    pointer-events: none;
    width: 100%;
    height: 100%;
  }
  img {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    z-index: 0;
  }
</style>

<div class="flex items-center justify-center min-h-screen bg-gray-900">
  <div class="video-container">
    <img src={`${serverBase}/video/${camIdx}`} alt="Camera feed" />
    <canvas id="overlay" width={FRAME_WIDTH} height={FRAME_HEIGHT}></canvas>
  </div>
</div>