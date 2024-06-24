from fastapi import FastAPI, File, Form, UploadFile, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from PIL import Image
import matplotlib.pyplot as plt
import io
import base64
import numpy as np

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

def resize_image(image: Image.Image, scale: float) -> Image.Image:
    new_size = (int(image.width * scale), int(image.height * scale))
    return image.resize(new_size)


def plot_color_distribution(image: Image.Image):
    # Convert image to numpy array
    image_array = np.array(image.convert('RGB'))

    # Flatten the array
    reshaped_array = image_array.reshape(-1, 3)

    # Get unique colors and their counts
    unique_colors, counts = np.unique(reshaped_array, axis=0, return_counts=True)

    if len(counts) == 0:
        print("No colors found in the image.")
        return io.BytesIO()

    # Debugging output
    print(f"Unique colors count: {len(unique_colors)}")
    print(f"Counts: {counts[:10]}")  # Print first 10 counts for debugging
    print(f"Color Values: {unique_colors[:10]}")  # Print first 10 color values for debugging

    # Sort colors by frequency
    sorted_indices = np.argsort(counts)[::-1]
    sorted_colors = unique_colors[sorted_indices]
    sorted_counts = counts[sorted_indices]

    # Plot each color as a separate bar
    plt.figure(figsize=(10, 5))
    for i, color in enumerate(sorted_colors):
        plt.bar(i, sorted_counts[i], color=color / 255, edgecolor='none')

    plt.xlabel('Color Index')
    plt.ylabel('Count (Log Scale)')
    plt.yscale('log')
    plt.title('Color Distribution')

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf


@app.get("/", response_class=HTMLResponse)
async def main(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/resize", response_class=HTMLResponse)
async def resize(request: Request, image: UploadFile = File(...), scale: float = Form(...)):
    try:
        original_image = Image.open(image.file)
        resized_image = resize_image(original_image, scale)

        original_histogram = plot_color_distribution(original_image)
        resized_histogram = plot_color_distribution(resized_image)

        original_buf = io.BytesIO()
        resized_buf = io.BytesIO()
        original_image.save(original_buf, format='PNG')
        resized_image.save(resized_buf, format='PNG')

        original_buf.seek(0)
        resized_buf.seek(0)

        original_image_data = base64.b64encode(original_buf.getvalue()).decode('utf-8')
        resized_image_data = base64.b64encode(resized_buf.getvalue()).decode('utf-8')
        original_histogram_data = base64.b64encode(original_histogram.getvalue()).decode('utf-8')
        resized_histogram_data = base64.b64encode(resized_histogram.getvalue()).decode('utf-8')

        return templates.TemplateResponse("result.html", {
            "request": request,
            "original_image": original_image_data,
            "resized_image": resized_image_data,
            "original_histogram": original_histogram_data,
            "resized_histogram": resized_histogram_data
        })
    except Exception as e:
        return HTMLResponse(content=f"An error occurred: {str(e)}", status_code=500)
