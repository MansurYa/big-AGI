"""
Entity Preservation Validation Test

Tests the actual entity preservation rate of the compression system.
Target: >99% preservation (acceptable: >95%)
"""

import re
from typing import List, Dict, Set
import anthropic
import os


class EntityExtractor:
    """Extract entities from text for comparison."""

    @staticmethod
    def extract_formulas(text: str) -> Set[str]:
        """Extract mathematical formulas and equations."""
        # LaTeX-style formulas
        latex = set(re.findall(r'\$[^\$]+\$', text))
        latex.update(re.findall(r'\\\[[^\]]+\\\]', text))
        latex.update(re.findall(r'\\\([^\)]+\\\)', text))

        # Common math expressions
        equations = set(re.findall(r'[a-zA-Z]\s*=\s*[^,\.\s]+', text))

        return latex | equations

    @staticmethod
    def extract_numbers(text: str) -> Set[str]:
        """Extract numbers (integers, floats, scientific notation)."""
        # Scientific notation
        scientific = set(re.findall(r'\d+\.?\d*[eE][+-]?\d+', text))

        # Regular numbers (with context to avoid false positives)
        numbers = set(re.findall(r'\b\d+\.?\d*\b', text))

        return scientific | numbers

    @staticmethod
    def extract_code(text: str) -> Set[str]:
        """Extract code snippets and identifiers."""
        # Code blocks
        code_blocks = set(re.findall(r'```[^`]+```', text, re.DOTALL))
        code_blocks.update(re.findall(r'`[^`]+`', text))

        # Function calls
        functions = set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\([^\)]*\)', text))

        # Variable assignments
        variables = set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*[^,\.\s]+', text))

        return code_blocks | functions | variables

    @staticmethod
    def extract_technical_terms(text: str) -> Set[str]:
        """Extract technical terms and acronyms."""
        # Acronyms (2+ uppercase letters)
        acronyms = set(re.findall(r'\b[A-Z]{2,}\b', text))

        # CamelCase identifiers
        camel_case = set(re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b', text))

        return acronyms | camel_case

    @classmethod
    def extract_all(cls, text: str) -> Dict[str, Set[str]]:
        """Extract all entity types."""
        return {
            'formulas': cls.extract_formulas(text),
            'numbers': cls.extract_numbers(text),
            'code': cls.extract_code(text),
            'technical_terms': cls.extract_technical_terms(text)
        }


def create_test_text() -> str:
    """Create test text with known entities."""
    return """
# Monte Carlo Simulation Analysis

## Mathematical Formulas
The probability density function is given by:
$f(x) = \\frac{1}{\\sigma\\sqrt{2\\pi}} e^{-\\frac{(x-\\mu)^2}{2\\sigma^2}}$

Expected value: E[X] = μ = 42.5
Variance: Var(X) = σ² = 12.34
Standard deviation: σ = 3.51

## Numerical Results
- Sample size: N = 10000
- Convergence threshold: ε = 1e-6
- Learning rate: α = 0.001
- Temperature: T = 298.15 K
- Pressure: P = 101325 Pa

## Code Implementation
```python
def monte_carlo_simulation(n_samples=10000, seed=42):
    np.random.seed(seed)
    samples = np.random.normal(loc=42.5, scale=3.51, size=n_samples)
    return samples.mean(), samples.std()

result_mean, result_std = monte_carlo_simulation()
print(f"Mean: {result_mean:.4f}, Std: {result_std:.4f}")
```

## Technical Details
- Algorithm: MCMC (Markov Chain Monte Carlo)
- Framework: TensorFlow 2.15.0
- Hardware: NVIDIA RTX 4090
- Memory: 24GB GDDR6X
- Precision: FP32 (32-bit floating point)

## Error Analysis
Relative error: δ = |x_true - x_approx| / |x_true| = 0.0023
Absolute error: Δ = 0.097
Confidence interval: [41.8, 43.2] at 95% CI

## Performance Metrics
- Execution time: t = 3.14 seconds
- Throughput: 3184 samples/second
- Memory usage: 512 MB
- CPU utilization: 87.3%
- GPU utilization: 92.1%
"""


def compress_text(text: str, api_key: str, base_url: str) -> str:
    """Compress text using Agent 2 (Compressor)."""
    client = anthropic.Anthropic(
        api_key=api_key,
        base_url=base_url
    )

    # Load Agent 2 prompt
    with open('prompts/agent2_compressor_v0.2.txt', 'r') as f:
        system_prompt = f.read()

    # Prepare request
    user_prompt = f"""Compress the following text 4x while preserving ALL entities (formulas, numbers, code, technical terms).

<AREA_TO_COMPRESS>
{text}
</AREA_TO_COMPRESS>

Compress to approximately {len(text.split()) // 4} words."""

    # Call API
    response = client.messages.create(
        model="claude-sonnet-4",
        max_tokens=4000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )

    # Extract text from response (skip thinking blocks)
    text_parts = []
    for block in response.content:
        if hasattr(block, 'text'):
            text_parts.append(block.text)

    return '\n'.join(text_parts)


def calculate_preservation_rate(
    original_entities: Dict[str, Set[str]],
    compressed_entities: Dict[str, Set[str]]
) -> Dict[str, float]:
    """Calculate preservation rate for each entity type."""
    rates = {}

    for entity_type in original_entities:
        original = original_entities[entity_type]
        compressed = compressed_entities[entity_type]

        if len(original) == 0:
            rates[entity_type] = 1.0  # No entities to preserve
        else:
            preserved = len(original & compressed)
            rates[entity_type] = preserved / len(original)

    return rates


def run_entity_preservation_test():
    """Run entity preservation validation test."""
    print("=" * 80)
    print("ENTITY PRESERVATION VALIDATION TEST")
    print("=" * 80)
    print()

    # Setup
    api_key = os.getenv('ANTHROPIC_API_KEY')
    base_url = os.getenv('ANTHROPIC_BASE_URL', 'https://api.anthropic.com')

    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY not set")
        return

    # Create test text
    print("📝 Creating test text with known entities...")
    original_text = create_test_text()
    print(f"   Original length: {len(original_text)} chars, {len(original_text.split())} words")
    print()

    # Extract original entities
    print("🔍 Extracting entities from original text...")
    original_entities = EntityExtractor.extract_all(original_text)

    total_entities = sum(len(entities) for entities in original_entities.values())
    print(f"   Found {total_entities} entities:")
    for entity_type, entities in original_entities.items():
        print(f"   - {entity_type}: {len(entities)}")
    print()

    # Compress text
    print("🗜️  Compressing text using Agent 2...")
    try:
        compressed_text = compress_text(original_text, api_key, base_url)
        print(f"   Compressed length: {len(compressed_text)} chars, {len(compressed_text.split())} words")
        compression_ratio = len(original_text.split()) / len(compressed_text.split())
        print(f"   Compression ratio: {compression_ratio:.2f}x")
        print()
    except Exception as e:
        print(f"❌ ERROR during compression: {e}")
        return

    # Extract compressed entities
    print("🔍 Extracting entities from compressed text...")
    compressed_entities = EntityExtractor.extract_all(compressed_text)

    compressed_total = sum(len(entities) for entities in compressed_entities.values())
    print(f"   Found {compressed_total} entities:")
    for entity_type, entities in compressed_entities.items():
        print(f"   - {entity_type}: {len(entities)}")
    print()

    # Calculate preservation rates
    print("📊 Calculating preservation rates...")
    rates = calculate_preservation_rate(original_entities, compressed_entities)

    overall_preserved = sum(
        len(original_entities[t] & compressed_entities[t])
        for t in original_entities
    )
    overall_rate = overall_preserved / total_entities if total_entities > 0 else 0

    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    for entity_type, rate in rates.items():
        status = "✅" if rate >= 0.99 else "⚠️" if rate >= 0.95 else "❌"
        print(f"{status} {entity_type}: {rate*100:.1f}% preserved")

    print()
    print(f"{'✅' if overall_rate >= 0.99 else '⚠️' if overall_rate >= 0.95 else '❌'} "
          f"OVERALL: {overall_rate*100:.1f}% preserved ({overall_preserved}/{total_entities})")
    print()

    # Verdict
    if overall_rate >= 0.99:
        print("🎉 SUCCESS: Entity preservation meets target (>99%)")
    elif overall_rate >= 0.95:
        print("⚠️  ACCEPTABLE: Entity preservation meets minimum (>95%)")
    else:
        print("❌ FAILURE: Entity preservation below acceptable threshold")

    print()
    print("=" * 80)

    # Show examples of lost entities
    if overall_rate < 1.0:
        print()
        print("LOST ENTITIES:")
        print("-" * 80)
        for entity_type in original_entities:
            lost = original_entities[entity_type] - compressed_entities[entity_type]
            if lost:
                print(f"\n{entity_type}:")
                for entity in list(lost)[:5]:  # Show first 5
                    print(f"  - {entity}")
                if len(lost) > 5:
                    print(f"  ... and {len(lost) - 5} more")

    return {
        'overall_rate': overall_rate,
        'rates_by_type': rates,
        'compression_ratio': compression_ratio,
        'original_text': original_text,
        'compressed_text': compressed_text
    }


if __name__ == '__main__':
    run_entity_preservation_test()
