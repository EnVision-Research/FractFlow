import replicate
from mcp.server.fastmcp import FastMCP
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("replicate_imagen")

def normalize_path(path: str) -> str:
    """
    Normalize a file path by expanding ~ to user's home directory
    and resolving relative paths.
    """
    expanded_path = os.path.expanduser(path)
    if not os.path.isabs(expanded_path):
        expanded_path = os.path.abspath(expanded_path)
    return expanded_path

@mcp.tool()
async def enhance_children_drawing(
    save_path: str,
    input_image: str,
    description: str
) -> str:
    """
    Enhance a child's drawing to picture book quality using Replicate's Flux Kontext Pro model.
    
    Args:
        save_path: Full path where the enhanced image will be saved (including filename)
        input_image: Path to the child's original drawing (local file path)
        description: Description of what the child intended to draw
        
    Returns:
        Image file path as a string where the enhanced image is saved
    """
    
    # Normalize paths
    save_path = normalize_path(save_path)
    input_image_path = normalize_path(input_image)
    
    # Check if input image exists
    if not os.path.exists(input_image_path):
        raise FileNotFoundError(f"Input image not found: {input_image_path}")
    
    # Ensure the save directory exists
    save_dir = os.path.dirname(save_path)
    if save_dir and not os.path.exists(save_dir):
        os.makedirs(save_dir, exist_ok=True)
    
    # Create enhancement prompt
    enhancement_prompt = f"""Transform this child's drawing into a beautiful picture book illustration while preserving the original composition, characters, and innocent charm. 

Style: Soft watercolor technique, warm and gentle colors, professional children's book art quality, storybook illustration aesthetics.

Content: {description}

Requirements:
- Maintain the exact same composition and character positions as the original
- Preserve the child's creative vision and emotional expression
- Use soft, child-friendly colors and smooth lines
- Add subtle details that enhance without overwhelming
- Keep the innocent and playful atmosphere
- Ensure the result looks like a professional picture book page

The final image should be recognizable as the same drawing but elevated to professional illustration quality."""

    # Run the Replicate model
    with open(input_image_path, "rb") as f:
        output = replicate.run(
            "black-forest-labs/flux-kontext-pro",
            input={
                "prompt": enhancement_prompt,
                "input_image": f,
                "aspect_ratio": "match_input_image",
                "output_format": "jpg",
                "safety_tolerance": 2
            }
        )
    
    # Save the generated image directly from Replicate output
    with open(save_path, 'wb') as f:
        # Handle both single FileOutput and list of FileOutput objects
        if hasattr(output, 'read'):
            # Single FileOutput object
            f.write(output.read())
        elif isinstance(output, list) and len(output) > 0:
            # List of FileOutput objects
            f.write(output[0].read())
        else:
            raise Exception(f"Unexpected output format from Replicate: {type(output)}")
    
    return save_path

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio') 