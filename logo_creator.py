# logo_creator.py
from PIL import Image, ImageDraw, ImageFont

def create_logo(text, font_size=60, output_file='logo.png'):
    """Create a simple logo with the specified text and save it as an image."""
    # Create a new image with white background
    width, height = 800, 300
    image = Image.new('RGBA', (width, height), 'white')
    draw = ImageDraw.Draw(image)

    # Define the font and size
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    # Calculate text size and position
    text_width, text_height = draw.textsize(text, font=font)
    position = ((width - text_width) // 2, (height - text_height) // 2)

    # Draw the text
    draw.text(position, text, fill='black', font=font)

    # Save the image
    image.save(output_file)

def display_logo(image_path, width=200):
    """Display the logo image using PIL."""
    image = Image.open(image_path)
    image.show()
