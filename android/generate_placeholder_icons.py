#!/usr/bin/env python3
"""
Generate placeholder launcher icons for Android app.
This creates simple colored square PNGs without requiring PIL or ImageMagick.
"""

import os
import struct

def create_png(width, height, color_rgb, output_path):
    """
    Create a simple PNG file with solid color.
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        color_rgb: Tuple of (r, g, b) values (0-255)
        output_path: Path where to save the PNG
    """
    # PNG signature
    png_signature = b'\x89PNG\r\n\x1a\n'
    
    # IHDR chunk (image header)
    ihdr_data = struct.pack('>IIBBBBB', 
        width,        # width
        height,       # height
        8,            # bit depth
        2,            # color type (2 = truecolor RGB)
        0,            # compression method
        0,            # filter method
        0             # interlace method
    )
    ihdr_chunk = _make_chunk(b'IHDR', ihdr_data)
    
    # IDAT chunk (image data)
    # Each row: filter byte (0) + RGB pixels
    row = b'\x00' + (struct.pack('BBB', *color_rgb) * width)
    raw_data = row * height
    
    # Compress using zlib
    import zlib
    compressed = zlib.compress(raw_data, 9)
    idat_chunk = _make_chunk(b'IDAT', compressed)
    
    # IEND chunk (image end)
    iend_chunk = _make_chunk(b'IEND', b'')
    
    # Write PNG file
    with open(output_path, 'wb') as f:
        f.write(png_signature)
        f.write(ihdr_chunk)
        f.write(idat_chunk)
        f.write(iend_chunk)
    
    print(f"✓ Created: {output_path}")

def _make_chunk(chunk_type, data):
    """Create a PNG chunk with length, type, data, and CRC."""
    import zlib
    length = struct.pack('>I', len(data))
    crc = struct.pack('>I', zlib.crc32(chunk_type + data) & 0xffffffff)
    return length + chunk_type + data + crc

def main():
    """Generate all required launcher icons."""
    # SoptraLoc brand color
    color = (102, 126, 234)  # #667eea
    
    # Icon sizes for each density
    sizes = {
        'mdpi': 48,
        'hdpi': 72,
        'xhdpi': 96,
        'xxhdpi': 144,
        'xxxhdpi': 192,
    }
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    res_dir = os.path.join(base_dir, 'app', 'src', 'main', 'res')
    
    print("🎨 Generating placeholder launcher icons...")
    print(f"   Color: RGB{color} (SoptraLoc brand)")
    print()
    
    for density, size in sizes.items():
        # Create directory
        mipmap_dir = os.path.join(res_dir, f'mipmap-{density}')
        os.makedirs(mipmap_dir, exist_ok=True)
        
        # Generate both ic_launcher and ic_launcher_round
        for icon_name in ['ic_launcher.png', 'ic_launcher_round.png']:
            output_path = os.path.join(mipmap_dir, icon_name)
            create_png(size, size, color, output_path)
    
    print()
    print("✅ All placeholder icons generated successfully!")
    print()
    print("📝 Note: These are simple colored squares for testing.")
    print("   For production, create proper icons using:")
    print("   - Android Asset Studio: https://romannurik.github.io/AndroidAssetStudio/")
    print("   - Or Android Studio: Right-click res → New → Image Asset")
    print()
    print("   See SETUP_ICONS.md for detailed instructions.")

if __name__ == '__main__':
    main()
