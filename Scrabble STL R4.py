import csv
import math
import os
import madcad # For 3D STL generation with pymadcad
import numpy as np # madcad often uses numpy

# --- SVG Configuration ---
SVG_TILE_SIZE = 100
SVG_TILE_COLOR = "#F8F8D8"
SVG_BORDER_COLOR = "red"
SVG_BORDER_WIDTH = 4
SVG_TEXT_COLOR = "black"
SVG_FONT_FAMILY = "Arial, Helvetica, sans-serif" # For SVG, not 3D
SVG_CORNER_RADIUS = 8
SVG_LETTER_FONT_SIZE_RATIO = 0.50
SVG_SUBSCRIPT_FONT_SIZE_RATIO = 0.20
SVG_LETTER_X_RATIO = 0.5
SVG_LETTER_Y_RATIO = 0.48
SVG_SUBSCRIPT_X_RATIO = 0.75
SVG_SUBSCRIPT_Y_RATIO = 0.78
SVG_TILES_PER_ROW = 10
SVG_PADDING = 10

# --- 3D STL Configuration (pymadcad) ---
STL_OUTPUT_DIR = "scrabble_stl_files_pymadcad"
TILE_3D_WIDTH = 19.0    # mm
TILE_3D_DEPTH = 19.0    # mm (Corresponds to Y in pymadcad's default XY plane for text)
TILE_3D_HEIGHT = 4.0    # mm (Corresponds to Z, extrusion direction)

EMBOSS_TYPE = "emboss"  # "emboss" or "deboss"
LETTER_EXTRUSION_HEIGHT = 0.8 # mm
NUMBER_EXTRUSION_HEIGHT = 0.6 # mm
TEXT_DEBOSS_OFFSET = 0.05 # mm, slight extra depth for debossing

# IMPORTANT: pymadcad's madcad.text requires a full path to a .ttf or .otf font file.
# YOU MUST REPLACE THIS WITH AN ACTUAL FONT FILE PATH ON YOUR SYSTEM.
STL_FONT_PATH = "C:/Windows/Fonts/Arial.ttf" # EXAMPLE for Windows
# STL_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf" # EXAMPLE for Linux
# STL_FONT_PATH = "/System/Library/Fonts/Supplemental/Arial.ttf" # EXAMPLE for macOS

# pymadcad's text size is more like a traditional font point size. These will need tuning.
STL_LETTER_FONT_SIZE = 10.0  # Adjust this based on visual results (e.g., for a 19mm tile)
STL_NUMBER_FONT_SIZE = 5.0   # Adjust this

# Text positioning ratios (relative to tile dimensions).
# (0,0) for text position in madcad.text is often bottom-left of the text.
# These ratios help position the text block's reference point on the tile.
STL_LETTER_POS_X_RATIO = 0.5  # 0.5 for horizontal centering attempt
STL_LETTER_POS_Y_RATIO = 0.55 # Attempt to center vertically, adjust as needed

STL_NUMBER_POS_X_RATIO = 0.75 # Towards the right
STL_NUMBER_POS_Y_RATIO = 0.25 # Towards the bottom

# --- SVG Generation Functions ---
def create_svg_tile_element(letter_char, value_str, x_pos, y_pos):
    """Generates the SVG code for a single Scrabble tile."""
    letter_font_size = SVG_TILE_SIZE * SVG_LETTER_FONT_SIZE_RATIO
    subscript_font_size = SVG_TILE_SIZE * SVG_SUBSCRIPT_FONT_SIZE_RATIO

    rect_svg = (
        f'<rect x="{x_pos}" y="{y_pos}" '
        f'width="{SVG_TILE_SIZE}" height="{SVG_TILE_SIZE}" '
        f'fill="{SVG_TILE_COLOR}" stroke="{SVG_BORDER_COLOR}" stroke-width="{SVG_BORDER_WIDTH}" '
        f'rx="{SVG_CORNER_RADIUS}" ry="{SVG_CORNER_RADIUS}" />'
    )
    text_elements = []
    if letter_char and letter_char != '_': # Don't draw letter for blank tile
        letter_x = x_pos + SVG_TILE_SIZE * SVG_LETTER_X_RATIO
        letter_y = y_pos + SVG_TILE_SIZE * SVG_LETTER_Y_RATIO
        text_elements.append(
            f'<text x="{letter_x}" y="{letter_y}" '
            f'font-family="{SVG_FONT_FAMILY}" font-size="{letter_font_size}" font-weight="bold" '
            f'fill="{SVG_TEXT_COLOR}" text-anchor="middle" dominant-baseline="middle">'
            f'{letter_char.upper()}</text>'
        )
    subscript_x = x_pos + SVG_TILE_SIZE * SVG_SUBSCRIPT_X_RATIO
    subscript_y = y_pos + SVG_TILE_SIZE * SVG_SUBSCRIPT_Y_RATIO
    text_elements.append(
        f'<text x="{subscript_x}" y="{subscript_y}" '
        f'font-family="{SVG_FONT_FAMILY}" font-size="{subscript_font_size}" '
        f'fill="{SVG_TEXT_COLOR}" text-anchor="middle" dominant-baseline="middle">'
        f'{value_str}</text>'
    )
    joined_text_elements = "\n  ".join(text_elements)
    return f'<g>\n  {rect_svg}\n  {joined_text_elements}\n</g>'

def load_scrabble_data_from_csv(csv_filepath):
    """Loads Scrabble letter data from a CSV file, skipping the header row."""
    tile_definitions = []
    try:
        with open(csv_filepath, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            try:
                header = next(reader) # Skip header
            except StopIteration:
                print(f"Warning: CSV file {csv_filepath} is empty or contains only a header.")
                return None
            for i, row in enumerate(reader):
                line_number_in_file = i + 2
                if len(row) == 3:
                    letter = row[0].strip()
                    try:
                        value = int(row[1].strip())
                        count = int(row[2].strip())
                        if count < 0 or value < 0:
                             print(f"Warning: Skipping row {line_number_in_file} in {csv_filepath} due to negative value/count: {row}")
                             continue
                        tile_definitions.append((letter, value, count))
                    except ValueError:
                        print(f"Warning: Skipping row {line_number_in_file} in {csv_filepath} (non-integer value/count): {row}")
                else:
                    print(f"Warning: Skipping row {line_number_in_file} in {csv_filepath} (expected 3 columns, got {len(row)}): {row}")
    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_filepath}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while reading {csv_filepath}: {e}")
        return None
    if not tile_definitions:
        print(f"Warning: No valid tile data loaded from data rows in {csv_filepath}.")
        return None
    return tile_definitions

def generate_scrabble_svg(csv_filepath, tile_data):
    """Generates an SVG file with all Scrabble tiles."""
    base_name, _ = os.path.splitext(csv_filepath)
    output_svg_filename = base_name + ".svg"

    all_letters_with_values_for_svg = []
    for letter, points, count in tile_data:
        for _ in range(count):
            all_letters_with_values_for_svg.append((letter, str(points)))

    if not all_letters_with_values_for_svg:
        print(f"No tiles to generate for SVG based on data from {csv_filepath}.")
        return

    total_tiles = len(all_letters_with_values_for_svg)
    num_rows = math.ceil(total_tiles / SVG_TILES_PER_ROW)
    
    svg_width = SVG_TILES_PER_ROW * (SVG_TILE_SIZE + SVG_PADDING) - SVG_PADDING + (2 * SVG_PADDING)
    svg_height = num_rows * (SVG_TILE_SIZE + SVG_PADDING) - SVG_PADDING + (2 * SVG_PADDING)

    all_tile_elements_svg = []
    current_x = SVG_PADDING
    current_y = SVG_PADDING
    tile_count_in_row = 0

    for i, (letter_char, value_str) in enumerate(all_letters_with_values_for_svg):
        tile_svg = create_svg_tile_element(letter_char, value_str, current_x, current_y)
        all_tile_elements_svg.append(tile_svg)
        tile_count_in_row += 1
        if tile_count_in_row >= SVG_TILES_PER_ROW and i < total_tiles - 1:
            current_x = SVG_PADDING
            current_y += SVG_TILE_SIZE + SVG_PADDING
            tile_count_in_row = 0
        elif i < total_tiles - 1:
            current_x += SVG_TILE_SIZE + SVG_PADDING
            
    joined_all_tile_elements = "\n\n".join(all_tile_elements_svg)
    svg_content = (
        f'<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">\n'
        f'<rect width="100%" height="100%" fill="#DDD" />\n' 
        f'{joined_all_tile_elements}\n'
        f'</svg>'
    )
    try:
        with open(output_svg_filename, "w", encoding='utf-8') as f:
            f.write(svg_content)
        print(f"Successfully generated SVG: {output_svg_filename}")
    except IOError:
        print(f"Error: Could not write to SVG file {output_svg_filename}")

def create_3d_text_pymadcad(text_string, font_path, font_size, extrusion_height,
                             target_pos_x_ratio, target_pos_y_ratio, tile_width, tile_depth,
                             is_deboss):
    """Helper function to create a positioned 3D text object with pymadcad."""
    if not font_path or not os.path.exists(font_path):
        print(f"Font path invalid or not set: {font_path}. Cannot create 3D text '{text_string}'.")
        return None

    # +++ Madcad Core Component Check +++
    # This is to ensure basic madcad structures are available as expected
    try:
        _ = madcad.vec2(0,0)
        _ = madcad.vec3(0,0,0)
        if not callable(madcad.operations.extrude):
            print("ERROR: madcad.operations.extrude is not callable!")
            return None
        # Attempt to reference types that might be in madcad.kernel
        _Wire = getattr(madcad, 'Wire', getattr(madcad.kernel, 'Wire', None))
        _Face = getattr(madcad, 'Face', getattr(madcad.kernel, 'Face', None))
        _Mesh = getattr(madcad, 'Mesh', getattr(madcad.kernel, 'Mesh', None))
        if not all([_Wire, _Face, _Mesh]):
            missing = [name for name, var in [('Wire', _Wire), ('Face', _Face), ('Mesh', _Mesh)] if not var]
            print(f"ERROR: Could not find core madcad types: {missing}. Check pymadcad installation/version.")
            return None
    except AttributeError as e_attr_check:
        print(f"ERROR: Basic madcad attribute missing, check installation: {e_attr_check}")
        return None
    except Exception as e_check:
        print(f"ERROR during madcad component check: {e_check}")
        return None
    # --- End Madcad Core Component Check ---


    try:
        text_output_from_madcad = madcad.text.text(text_string, font='C:/Windows/Fonts/Arial.ttf', align=('left', 0), fill=True)
        
        if not text_output_from_madcad:
             print(f"Warning: pymadcad.text for '{text_string}' returned None or an empty result.")
             return None

        if not isinstance(text_output_from_madcad, list):
            text_2d_elements = [text_output_from_madcad]
        else:
            text_2d_elements = text_output_from_madcad

        if not text_2d_elements:
             print(f"Warning: No 2D elements found for text '{text_string}' after processing madcad.text output.")
             return None
        
        all_text_3d_parts = []
        for element_2d in text_2d_elements:
            face_to_extrude = None
            # Use the resolved _Wire and _Face types
            if isinstance(element_2d, _Wire) and element_2d.is_closed:
                try:
                    face_to_extrude = madcad.face(element_2d) # madcad.face() is usually a top-level function
                except Exception as e_face:
                    print(f"Warning: Could not create face from wire part of text '{text_string}': {e_face}")
            elif isinstance(element_2d, _Face):
                face_to_extrude = element_2d
            # Removed the _Mesh check here for 2D elements as madcad.text should give Wires/Faces for 2D.

            if face_to_extrude:
                try:
                    extruded_part = madcad.operations.extrude(face_to_extrude, madcad.vec3(0, 0, extrusion_height))
                    if extruded_part:
                        all_text_3d_parts.append(extruded_part)
                except Exception as e_extrude:
                    print(f"Warning: Extrusion failed for a part of text '{text_string}': {e_extrude}")
            else:
                if not (isinstance(element_2d, _Wire) and not element_2d.is_closed): # Don't warn for open wires
                    print(f"Notice: No valid face to extrude for an element of text '{text_string}'. Element was: {type(element_2d)}")


        if not all_text_3d_parts:
            print(f"Warning: Extrusion failed for all parts of text '{text_string}'.")
            return None
        
        if len(all_text_3d_parts) == 1:
            text_3d_unplaced = all_text_3d_parts[0]
        else:
            try:
                text_3d_unplaced = madcad.union(all_text_3d_parts)
            except Exception as e_union_3d:
                print(f"Warning: Could not union 3D text parts for '{text_string}': {e_union_3d}. Using concatenation.")
                text_3d_unplaced = madcad.concatenate(all_text_3d_parts) if all_text_3d_parts else None

        if not text_3d_unplaced:
            print(f"Warning: No unplaced 3D text generated for '{text_string}'.")
            return None
        
        # Use the resolved _Mesh type
        if not isinstance(text_3d_unplaced, _Mesh):
            final_text_mesh = madcad.mesh(text_3d_unplaced, tolerance=0.01, angular=0.1)
            if not final_text_mesh:
                 print(f"Warning: Meshing of 3D text object failed for '{text_string}'.")
                 return None
        else:
            final_text_mesh = text_3d_unplaced

        bb = final_text_mesh.boundingbox
        if bb is None or bb.volume == 0:
            print(f"Warning: Bounding box for 3D text '{text_string}' is invalid or empty.")
            return None

        text_width = bb.width
        text_actual_height = bb.depth

        pos_x = (tile_width * target_pos_x_ratio) - (text_width * 0.5)
        pos_y = (tile_depth * target_pos_y_ratio) - (text_actual_height * 0.5)

        if is_deboss:
            pos_z = TILE_3D_HEIGHT - extrusion_height - TEXT_DEBOSS_OFFSET
        else: # Emboss
            pos_z = TILE_3D_HEIGHT

        transform = madcad.translate(madcad.vec3(pos_x, pos_y, pos_z))
        text_3d_placed = final_text_mesh.transform(transform)
        return text_3d_placed

    except TypeError as te:
        if "'module' object is not callable" in str(te) and 'madcad.text' in str(te):
            print(f"CRITICAL TypeError for madcad.text: {te}")
        else:
            print(f"TypeError in create_3d_text_pymadcad for '{text_string}': {te}")
        import traceback
        traceback.print_exc()
        return None
    except Exception as e:
        print(f"Error in create_3d_text_pymadcad for '{text_string}': {e}")
        import traceback
        traceback.print_exc()
        return None

# --- generate_stl_for_tile_pymadcad function needs to use _Mesh too ---
def generate_stl_for_tile_pymadcad(letter_char, value_str):
    # ... (initial part of the function is the same) ...
    # Resolve _Mesh type at the beginning or ensure it's globally resolved if needed
    _Mesh = getattr(madcad, 'Mesh', getattr(madcad.kernel, 'Mesh', None))
    if not _Mesh:
        print("CRITICAL ERROR: madcad.Mesh (or madcad.kernel.Mesh) not found. Aborting STL generation for this tile.")
        return

    # ... (base brick creation) ...
    try:
        corner1 = madcad.vec3(0, 0, 0)
        corner2 = madcad.vec3(TILE_3D_WIDTH, TILE_3D_DEPTH, TILE_3D_HEIGHT)
        final_obj = madcad.brick(corner1, corner2)
    except Exception as e:
        print(f"Error creating pymadcad base brick: {e}")
        return
    # ... (text creation and boolean ops, which use create_3d_text_pymadcad) ...
    # (Ensure this part is copied from the previous full script version)
    if letter_char and letter_char != '_':
        letter_3d = create_3d_text_pymadcad(
            letter_char.upper(), STL_FONT_PATH, STL_LETTER_FONT_SIZE, LETTER_EXTRUSION_HEIGHT,
            STL_LETTER_POS_X_RATIO, STL_LETTER_POS_Y_RATIO,
            TILE_3D_WIDTH, TILE_3D_DEPTH,
            is_deboss=(EMBOSS_TYPE == "deboss")
        )
        if letter_3d:
            try:
                if EMBOSS_TYPE == "emboss":
                    final_obj = madcad.union(final_obj, letter_3d)
                elif EMBOSS_TYPE == "deboss":
                    final_obj = madcad.difference(final_obj, letter_3d)
            except Exception as e:
                print(f"Boolean op failed for letter '{letter_char}': {e}.")

    if value_str:
        number_3d = create_3d_text_pymadcad(
            value_str, STL_FONT_PATH, STL_NUMBER_FONT_SIZE, NUMBER_EXTRUSION_HEIGHT,
            STL_NUMBER_POS_X_RATIO, STL_NUMBER_POS_Y_RATIO,
            TILE_3D_WIDTH, TILE_3D_DEPTH,
            is_deboss=(EMBOSS_TYPE == "deboss")
        )
        if number_3d:
            try:
                if EMBOSS_TYPE == "emboss":
                    final_obj = madcad.union(final_obj, number_3d)
                elif EMBOSS_TYPE == "deboss":
                    final_obj = madcad.difference(final_obj, number_3d)
            except Exception as e:
                print(f"Boolean op failed for number '{value_str}': {e}.")


    # 4. Export to STL
    if final_obj:
        try:
            current_mesh = None
            if isinstance(final_obj, _Mesh): # Use the resolved _Mesh type
                current_mesh = final_obj
            else:
                print(f"Notice: Final object for {tile_label} is type {type(final_obj)}, attempting to mesh it.")
                current_mesh = madcad.mesh(final_obj, tolerance=0.05, angular=0.2)

            if current_mesh and isinstance(current_mesh, _Mesh) and current_mesh.count_vertices() > 0:
                 madcad.io.write(current_mesh, stl_filename)
            else:
                print(f"Error: Final object for {tile_label} is not a valid mesh or is empty after meshing attempt. Not exporting STL.")
        except Exception as e:
            print(f"Error exporting STL with pymadcad for {stl_filename}: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"Final object for {tile_label} is None. Not exporting STL.")


# --- The rest of your full script (SVG functions, load_csv, main)
# --- should follow here, using these corrected functions.
# --- Make sure to replace the old versions in your full script.
def main():
    """Main function to drive SVG and STL generation."""
    csv_file_path = "EasternSecwepemc2Letters.csv"

    if not STL_FONT_PATH or not os.path.exists(STL_FONT_PATH):
        print(f"FATAL ERROR: STL_FONT_PATH ('{STL_FONT_PATH}') is not valid or does not exist.")
        print("Please update this path in the script. Aborting STL generation.")
        return

    tile_data = load_scrabble_data_from_csv(csv_file_path)
    if not tile_data:
        print("Could not load tile data from CSV. Aborting.")
        return

    print("\n--- Generating SVG File ---")
    generate_scrabble_svg(csv_file_path, tile_data)

    print("\n--- Generating STL Files (pymadcad) ---")
    unique_tiles_for_stl = {}
    for letter, points, count in tile_data:
        unique_tiles_for_stl[(letter, str(points))] = True

    if not unique_tiles_for_stl:
        print("No unique tile types found for STL generation.")
        return

    for letter_char, value_str in unique_tiles_for_stl.keys():
        generate_stl_for_tile_pymadcad(letter_char, value_str)
    
    print("\n--- All operations complete ---")

if __name__ == "__main__":
    main()