#!/usr/bin/env python3
"""
Simple test to verify English display configuration
"""

import matplotlib.pyplot as plt
import matplotlib

# Configure matplotlib for English
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Liberation Sans', 'Arial', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

print("=" * 70)
print("English Display Configuration Test")
print("=" * 70)

print("\nMatplotlib configuration:")
print(f"  Font family: {plt.rcParams['font.family']}")
print(f"  Sans-serif fonts: {plt.rcParams['font.sans-serif']}")

# Create test plot
fig, ax = plt.subplots(figsize=(12, 8))

# Test text with various elements
test_text = """TiCNet Lung Nodule Detection System

CT Image Preview
Slice 0/132 (0.0%)
Shape: 133x512x512

Detection Results:
- Confidence: 0.95
- Position: (123, 456, 78)
- Volume: 125.5 mm³

Numbers: 0123456789
Symbols: ()[]{}+-*/=@#%&*
Letters: ABCDEFGHIJKLMNOPQRSTUVWXYZ
        abcdefghijklmnopqrstuvwxyz
"""

ax.text(0.5, 0.5, test_text, ha='center', va='center', 
        fontsize=11, family='monospace')
ax.axis('off')
ax.set_title('English Display Test - No Square Boxes!', 
             fontsize=16, fontweight='bold')

plt.tight_layout()

# Save
output = 'english_test.png'
plt.savefig(output, dpi=150, bbox_inches='tight')
plt.close()

print(f"\n✅ Test image saved: {output}")
print("\nCheck the image:")
print("  ✓ All text in English")
print("  ✓ No square boxes")
print("  ✓ Numbers and symbols displayed correctly")

print("\n" + "=" * 70)
print("✅ System configured for English display")
print("   Run: python run_system.py")
print("=" * 70)

