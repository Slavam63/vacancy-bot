import os
from PIL import Image, ImageDraw, ImageFont

def generate_vacancy_card(vacancy: dict, output_path: str):
    bg_path = os.path.join("images", "background.jpg")
    background = Image.open(bg_path).convert("RGBA")
    W, H = background.size

    card = Image.new("RGBA", background.size)
    card.paste(background, (0, 0))

    draw = ImageDraw.Draw(card)

    font_path = os.path.join("fonts", "Roboto-Bold.ttf")
    title_font = ImageFont.truetype(font_path, size=40)
    field_font = ImageFont.truetype(font_path, size=30)

    y = 80
    spacing = 60

    draw.text((80, y), f"📌 {vacancy['title']}", font=title_font, fill="black"); y += spacing
    draw.text((80, y), f"💰 {vacancy['salary']}", font=field_font, fill="black"); y += spacing
    draw.text((80, y), f"📍 {vacancy['location']}", font=field_font, fill="black"); y += spacing
    draw.text((80, y), f"🏢 {vacancy['employer']}", font=field_font, fill="black"); y += spacing
    draw.text((80, y), f"⚙️ {vacancy['conditions']}", font=field_font, fill="black"); y += spacing
    draw.text((80, y), f"📞 {vacancy['contact']}", font=field_font, fill="black"); y += spacing
    draw.text((80, y), f"🔗 {vacancy['source']}", font=field_font, fill="black")

    card.save(output_path, "PNG")
