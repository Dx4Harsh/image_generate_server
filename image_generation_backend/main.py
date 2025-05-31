from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for Flutter app

# Together AI configuration
TOGETHER_API_KEY = 'ad01e67e82c42a9eaae5c7c1759b1e5efae0b7ce89b665cd049e046d0b43419e'
TOGETHER_API_URL = "https://api.together.xyz/v1/images/generations"

# Available models (you can add more as needed)
AVAILABLE_MODELS = [
    "black-forest-labs/FLUX.1-schnell-Free",
    "black-forest-labs/FLUX.1-dev",
    "stabilityai/stable-diffusion-xl-base-1.0",
    "stabilityai/stable-diffusion-2-1",
    "runwayml/stable-diffusion-v1-5"
]

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Together AI Image Generation Server'
    })

@app.route('/models', methods=['GET'])
def get_available_models():
    """Get list of available models"""
    return jsonify({
        'models': AVAILABLE_MODELS,
        'default': AVAILABLE_MODELS[0]
    })

def _generate_image_core(data):
    """Core image generation logic"""
    # Check if API key is configured
    if not TOGETHER_API_KEY:
        return {
            'error': 'Together AI API key not configured',
            'message': 'Please set TOGETHER_API_KEY environment variable'
        }, 500

    # Extract parameters
    prompt = data.get('prompt')
    if not prompt:
        return {'error': 'Prompt is required'}, 400
    
    model = data.get('model', AVAILABLE_MODELS[0])
    width = data.get('width', 1024)
    height = data.get('height', 1024)
    steps = data.get('steps', 12)  # Use maximum steps for better quality
    n = data.get('n', 1)  # Number of images to generate
    
    # Validate model
    if model not in AVAILABLE_MODELS:
        return {
            'error': f'Invalid model. Available models: {AVAILABLE_MODELS}'
        }, 400
    
    # Validate dimensions
    if width < 256 or width > 2048 or height < 256 or height > 2048:
        return {
            'error': 'Width and height must be between 256 and 2048 pixels'
        }, 400
    
    # Validate steps (Together AI requirement)
    if steps < 1 or steps > 12:
        return {
            'error': 'Steps must be between 1 and 12 for Together AI models'
        }, 400
    
    # Prepare request to Together AI
    headers = {
        'Authorization': f'Bearer {TOGETHER_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'model': model,
        'prompt': prompt,
        'width': width,
        'height': height,
        'steps': steps,
        'n': n
    }
    
    # Add optional parameters if provided
    if 'negative_prompt' in data:
        payload['negative_prompt'] = data['negative_prompt']
    else:
        # Add default negative prompt for better quality
        payload['negative_prompt'] = "blurry, low quality, distorted, pixelated, artifacts, bad anatomy"
    
    if 'seed' in data:
        payload['seed'] = data['seed']
        
    if 'guidance_scale' in data:
        payload['guidance_scale'] = data['guidance_scale']
    else:
        # Add default guidance scale for better prompt adherence
        payload['guidance_scale'] = 7.5
    
    logger.info(f"Generating image with prompt: {prompt[:100]}...")
    
    try:
        # Make request to Together AI
        response = requests.post(
            TOGETHER_API_URL,
            headers=headers,
            json=payload,
            timeout=120  # 2 minutes timeout
        )
        
        if response.status_code != 200:
            error_msg = f"Together AI API error: {response.status_code}"
            if response.text:
                error_msg += f" - {response.text}"
            logger.error(error_msg)
            return {'error': error_msg}, response.status_code
        
        result = response.json()
        
        # Process the response
        if 'data' in result and len(result['data']) > 0:
            images_data = []
            
            for i, image_data in enumerate(result['data']):
                logger.info(f"Processing image {i}: keys={list(image_data.keys())}")
                if 'url' in image_data:
                    # If Together AI returns URLs
                    logger.info(f"Found URL for image {i}: {image_data['url']}")
                    images_data.append({
                        'url': image_data['url'],
                        'index': i
                    })
                elif 'b64_json' in image_data:
                    # If Together AI returns base64 data
                    logger.info(f"Found base64 data for image {i}: {len(image_data['b64_json'])} chars")
                    images_data.append({
                        'b64_json': image_data['b64_json'],
                        'index': i
                    })
                else:
                    logger.warning(f"Image {i} has no URL or base64 data: {image_data}")
            
            logger.info(f"Final images_data: {len(images_data)} images processed")
            
            return {
                'success': True,
                'images': images_data,
                'prompt': prompt,
                'model': model,
                'parameters': {
                    'width': width,
                    'height': height,
                    'steps': steps,
                    'n': n,
                    'guidance_scale': payload.get('guidance_scale'),
                    'negative_prompt': payload.get('negative_prompt')
                },
                'timestamp': datetime.now().isoformat()
            }, 200
        else:
            logger.error(f"No image data found in result: {result}")
            return {'error': 'No images generated'}, 500
            
    except requests.exceptions.Timeout:
        return {'error': 'Request timeout - image generation took too long'}, 408
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return {'error': f'Request failed: {str(e)}'}, 500

@app.route('/generate', methods=['POST'])
def generate_image():
    """Generate image using Together AI"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        result, status_code = _generate_image_core(data)
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/generate-simple', methods=['POST'])
def generate_image_simple():
    """Simplified endpoint for quick image generation"""
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        # Create enhanced data with default parameters
        enhanced_data = {
            'prompt': prompt,
            'model': AVAILABLE_MODELS[0],
            'width': 1024,
            'height': 1024,
            'steps': 12,
            'n': 1
        }
        
        # Use the core generation function
        result, status_code = _generate_image_core(enhanced_data)
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Check if API key is set
    if not TOGETHER_API_KEY:
        print("WARNING: TOGETHER_API_KEY environment variable not set!")
        print("Please set it with: export TOGETHER_API_KEY='your-api-key-here'")
    
    print("Starting Together AI Image Generation Server...")
    print(f"Available models: {AVAILABLE_MODELS}")
    print("Endpoints:")
    print("  GET  /health - Health check")
    print("  GET  /models - List available models")
    print("  POST /generate - Generate images with full parameters")
    print("  POST /generate-simple - Generate images with minimal parameters")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )