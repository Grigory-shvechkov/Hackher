<script lang="ts">
  import { page } from "$app/stores";
  const serverBase = "http://172.31.88.33:5000";

  // Get camera ID from URL
  $: camId = Number($page.params.id);

  // Build the live MJPEG URL
  $: camSrc = `${serverBase}/video/${camId}`;
</script>

<div class="flex items-center justify-center min-h-screen bg-gray-900">
  <img
    src={camSrc}
    alt={`Live camera ${camId}`}
    class="w-full max-w-lg rounded-lg shadow-lg"
  />
</div>