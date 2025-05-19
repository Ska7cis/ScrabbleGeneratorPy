#Gemini AI 2.5 prompt
#(1) i would like to create a python script to generate a scrabble tiles in an svg file. Each letter has a number subscript and a red square on the outside.
#(2) now i would like to same code but for the german language. the SVG file will be laser scanning and engraving where the tiles will be cut, so there is no need for tile background. Also make the letters black and the edge of the the red

import math

# --- Configuration Constants ---
TILE_SIZE = 50  # Pixels for one side of the square tile
GAP = 5         # Pixels between tiles
TILES_PER_ROW = 13 # How many tiles before wrapping to the next row

# Tile appearance for laser cutting
TILE_OUTLINE_COLOR = "red"  # Color for the cutting outline (e.g., RGB(255,0,0))
TILE_OUTLINE_WIDTH = 1      # Stroke width for the outline.
                            # For many laser cutters, this needs to be very thin
                            # (e.g., 0.1, 0.01, or a "hairline" setting in your software).
                            # 1px is used here for better visibility in SVG viewers. Adjust as needed.

# Letter appearance (for engraving)
LETTER_FONT_FAMILY = "Arial, Helvetica, sans-serif" # Choose a font available to your system/laser
LETTER_FONT_WEIGHT = "bold"
LETTER_COLOR = "black"       # Color for engraved letters
LETTER_FONT_SIZE_RATIO = 0.5 # Relative to TILE_SIZE

# Value (subscript) appearance (for engraving)
VALUE_FONT_FAMILY = "Arial, Helvetica, sans-serif" # Choose a font available to your system/laser
VALUE_COLOR = "black"        # Color for engraved values
VALUE_FONT_SIZE_RATIO = 0.25 # Relative to TILE_SIZE
VALUE_X_OFFSET_RATIO = 0.90  # % from left edge of tile for text-anchor:end
VALUE_Y_OFFSET_RATIO = 0.92  # % from top edge of tile for dominant-baseline:alphabetic

# Output filename
OUTPUT_SVG_FILENAME = "scrabble_tiles_german_laser.svg"

# --- German Scrabble Data (102 tiles, common distribution) ---
# Sources: Various, e.g., spielregeln.de for Mattel distribution
SCRABBLE_TILES_DATA = {
    # Letter: {'value': points, 'count': number_of_tiles}
    # 1 Punkt
    'E': {'value': 1, 'count': 15}, 'N': {'value': 1, 'count': 9},
    'S': {'value': 1, 'count': 7},  'I': {'value': 1, 'count': 6},
    'R': {'value': 1, 'count': 6},  'T': {'value': 1, 'count': 6},
    'U': {'value': 1, 'count': 6},  'A': {'value': 1, 'count': 5},
    'D': {'value': 1, 'count': 4}, 'ß': {'value': 1, 'count': 2},
    # 2 Punkte
    'H': {'value': 2, 'count': 4}, 'G': {'value': 2, 'count': 3},
    'L': {'value': 2, 'count': 3}, 'O': {'value': 2, 'count': 3},
    # 3 Punkte
    'M': {'value': 3, 'count': 4}, 'B': {'value': 3, 'count': 2},
    'W': {'value': 3, 'count': 1}, 'Z': {'value': 3, 'count': 1},
    # 4 Punkte
    'C': {'value': 4, 'count': 2}, 'F': {'value': 4, 'count': 2},
    'K': {'value': 4, 'count': 2}, 'P': {'value': 4, 'count': 1},
    # 6 Punkte
    'Ä': {'value': 6, 'count': 1}, 'J': {'value': 6, 'count': 1},
    'Ü': {'value': 6, 'count': 1}, 'V': {'value': 6, 'count': 1},
    # 8 Punkte
    'Ö': {'value': 8, 'count': 1}, 'X': {'value': 8, 'count': 1},
    # 10 Punkte
    'Q': {'value': 10, 'count': 1},'Y': {'value': 10, 'count': 1},
    # 0 Punkte (Blank)
    ' ': {'value': 0, 'count': 2}  # Blank tile
}

def generate_single_tile_svg(letter_char, value_num):
    """
    Generates the SVG elements for a single Scrabble tile outline and its content.
    These elements are positioned relative to (0,0) and should be
    placed inside a <g transform="translate(x,y)"> tag.
    """
    svg_elements = []

    # 1. Red square outline (for laser cutting)
    svg_elements.append(
        f'<rect x="0" y="0" width="{TILE_SIZE}" height="{TILE_SIZE}" '
        f'fill="none" stroke="{TILE_OUTLINE_COLOR}" stroke-width="{TILE_OUTLINE_WIDTH}"/>'
    )

    # 2. Letter (for engraving)
    letter_font_size = TILE_SIZE * LETTER_FONT_SIZE_RATIO
    # For blank tile, don't print the space character
    display_letter = letter_char if letter_char != ' ' else ''
    
    svg_elements.append(
        f'<text x="{TILE_SIZE / 2}" y="{TILE_SIZE / 2}" '
        f'font-family="{LETTER_FONT_FAMILY}" font-weight="{LETTER_FONT_WEIGHT}" '
        f'font-size="{letter_font_size}" fill="{LETTER_COLOR}" '
        f'text-anchor="middle" dominant-baseline="central">'
        f'{display_letter}</text>'
    )

    # 3. Value (subscript-like, for engraving)
    # Only show value if it's not a blank tile (value 0)
    if letter_char != ' ':
        value_font_size = TILE_SIZE * VALUE_FONT_SIZE_RATIO
        value_x = TILE_SIZE * VALUE_X_OFFSET_RATIO
        value_y = TILE_SIZE * VALUE_Y_OFFSET_RATIO
        svg_elements.append(
            f'<text x="{value_x}" y="{value_y}" '
            f'font-family="{VALUE_FONT_FAMILY}" font-size="{value_font_size}" '
            f'fill="{VALUE_COLOR}" text-anchor="end" dominant-baseline="alphabetic">'
            f'{value_num}</text>'
        )
    
    return "\n".join(svg_elements)

def main():
    all_tile_svg_groups = []
    
    current_x = GAP
    current_y = GAP
    tile_idx_in_row = 0
    total_tiles_generated = 0

    # Iterate through letters based on data.
    # Sorting ensures a consistent (alphabetical) order in the SVG if that's desired,
    # though it doesn't affect the final set of tiles.
    sorted_letters = sorted(SCRABBLE_TILES_DATA.keys())
    
    for letter_char in sorted_letters:
        data = SCRABBLE_TILES_DATA[letter_char]
        value_num = data['value']
        count = data['count']
        
        for _ in range(count):
            tile_content_svg = generate_single_tile_svg(letter_char, value_num)
            
            # Group for this tile with translation
            tile_group_svg = (
                f'<g transform="translate({current_x}, {current_y})">\n'
                f'{tile_content_svg}\n'
                f'</g>'
            )
            all_tile_svg_groups.append(tile_group_svg)
            
            total_tiles_generated += 1
            tile_idx_in_row += 1
            
            if tile_idx_in_row >= TILES_PER_ROW:
                current_x = GAP
                current_y += TILE_SIZE + GAP
                tile_idx_in_row = 0
            else:
                current_x += TILE_SIZE + GAP

    # Calculate overall SVG dimensions
    if total_tiles_generated == 0:
        svg_width = GAP * 2
        svg_height = GAP * 2
    else:
        num_rows = math.ceil(total_tiles_generated / TILES_PER_ROW)
        # Width is determined by TILES_PER_ROW or fewer if total is less
        actual_tiles_in_widest_row = min(total_tiles_generated, TILES_PER_ROW)
        svg_width = (actual_tiles_in_widest_row * (TILE_SIZE + GAP)) + GAP
        svg_height = (num_rows * (TILE_SIZE + GAP)) + GAP

    # Assemble the final SVG
    svg_output = (
        f'<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">\n'
        # Optional: add a background to the whole SVG for viewing, laser will ignore if not a cut color
        # f'  <rect width="100%" height="100%" fill="#FAFAFA"/>\n'
        + "\n".join(all_tile_svg_groups) +
        '\n</svg>'
    )

    # Write to file with UTF-8 encoding
    try:
        with open(OUTPUT_SVG_FILENAME, "w", encoding="utf-8") as f:
            f.write(svg_output)
        print(f"Successfully generated '{OUTPUT_SVG_FILENAME}' with {total_tiles_generated} German tiles.")
        print(f"Outline color: {TILE_OUTLINE_COLOR}, Outline width: {TILE_OUTLINE_WIDTH}px (adjust for laser).")
        print(f"Letter/Value color: {LETTER_COLOR}.")
    except IOError as e:
        print(f"Error writing file: {e}")

if __name__ == "__main__":
    # Ensure the script file itself is saved as UTF-8 if you have Ä, Ö, Ü in comments or strings.
    main()