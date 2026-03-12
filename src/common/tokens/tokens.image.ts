import type { DLLM } from '~/common/stores/llms/llms.types';


export function imageTokensForLLM(width: number | undefined, height: number | undefined, debugTitle: string | undefined, llm: DLLM) {
  // for the guidelines, see `attachment.pipeline.ts` (lists the latest URLs)
  // Note: we may resolve the service or use the access, for non-OpenAI services even if they're on the OpenAI protocol
  switch (llm.vId) {
    case 'openai':
      // missing values
      if (!width || !height) {
        console.log(`Missing width or height for openai image tokens calculation (${debugTitle || 'no title'})`);
        return 85;
      }
      // 'detail: low' mode, has an image of (or up to) 512x512 -> 85 tokens
      if (width <= 512 && height <= 512)
        return 85;
      // 'detail: high' mode, cover the image with 512x512 patches of 170 tokens, in addition to the 85
      const patchesX = Math.ceil(width / 512);
      const patchesY = Math.ceil(height / 512);
      return 85 + patchesX * patchesY * 170;

    case 'anthropic':
      // Anthropic Vision API token calculation
      // https://docs.anthropic.com/en/docs/build-with-claude/vision
      // - Recommended: ≤1.15 megapixels (e.g., 1092x1092, 951x1268, 896x1344, 819x1456, 784x1568)
      // - Max: 1568px on long edge
      //
      // NOTE: Real-world token costs are significantly higher than initial estimates suggested.
      // Images can cost 2,000-8,000+ tokens depending on size and complexity.
      // Using conservative estimates to prevent unexpected context limit hits.

      // Fallback for missing dimensions - use conservative estimate
      if (!width || !height) {
        // console.log(`Missing width or height for Anthropic image tokens calculation (${debugTitle || 'no title'})`);
        return 4000; // Conservative fallback (was 1600)
      }

      // Calculate tokens based on image size
      // Using divisor of 400 (was 750) for more realistic estimates based on empirical data
      const pixels = width * height;
      const tokens = Math.round(pixels / 400);

      // Cap at reasonable maximum for very large images
      return Math.min(tokens, 8000);

    case 'googleai':
      // Inferred from the Gemini Videos description, but not sure
      return 258;

    default:
      console.log(`[DEV] Unhandled token preview for image with llm: ${llm.vId}`);
      return 0;
  }
}
