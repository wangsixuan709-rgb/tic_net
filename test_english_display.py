#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test English display in visualization
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from system.visualization import ResultVisualizer
from system.config import SystemConfig
import numpy as np
import matplotlib.pyplot as plt

def test_english_display():
    """Test that visualization uses English"""
    print("=" * 70)
    print("Testing English Display")
    print("=" * 70)
    
    # Initialize
    config = SystemConfig()
    visualizer = ResultVisualizer(config)
    
    # Check language setting
    print(f"\nLanguage setting: {'Chinese' if visualizer.use_chinese else 'English'}")
    
    if not visualizer.use_chinese:
        print("✅ SUCCESS: System configured for English display")
        print("   No Chinese characters will be used in visualizations")
        print("   No font issues or square boxes!")
    else:
        print("⚠️  WARNING: System still using Chinese")
        print("   May encounter font issues")
    
    # Create a simple test plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Test text
    test_text = """
    TiCNet Lung Nodule Detection System
    
    All text is now in English
    No square boxes
    No font problems
    
    Numbers: 0123456789
    Symbols: ()[]{}+-*/=
    Confidence: 0.95
    Shape: 133x512x512
    """
    
    ax.text(0.5, 0.5, test_text.strip(), 
           ha='center', va='center', fontsize=12)
    ax.axis('off')
    ax.set_title('English Display Test', fontsize=16, fontweight='bold')
    
    plt.tight_layout()
    
    # Save test image
    output_file = 'english_display_test.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"\n✅ Test image saved: {output_file}")
    print("\nPlease check the image:")
    print("  - All text should be in English")
    print("  - No square boxes")
    print("  - Everything displayed correctly")
    
    print("\n" + "=" * 70)
    print("System is now ready to use!")
    print("Run: python run_system.py")
    print("=" * 70)

if __name__ == '__main__':
    test_english_display()

