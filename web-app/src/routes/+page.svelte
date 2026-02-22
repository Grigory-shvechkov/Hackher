<script lang="ts">
  import * as Card from "$lib/components/ui/card/index.js";
  import * as Carousel from "$lib/components/ui/carousel/index.js";
</script>

<div class="flex items-center justify-center min-h-screen">
  <Carousel.Root class="w-full max-w-sm">
    <Carousel.Content>
      {#each Array(5) as _, i (i)}
        <Carousel.Item>
          <Card.Root>
            <Card.Content class="flex aspect-square items-center justify-center p-6">
              <span class="text-2xl font-semibold">{i + 1}</span>
            </Card.Content>
          </Card.Root>
        </Carousel.Item>
      {/each}
    </Carousel.Content>
    <Carousel.Previous />
    <Carousel.Next />
  </Carousel.Root>
</div>