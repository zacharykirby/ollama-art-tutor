# Local AI Art Tutor (WIP)
---
![Screenshot of AI Tutor window over rough sketch drawing, example interaction](https://github.com/zacharykirby/ollama-art-tutor/blob/main/img/art-tutor-v1.png?raw=true)

**Interactive art tutor using local Ollama vision capable models (e.g. llama3.2-vision)**

You *could* use any multimodal API but that will get expensive.

---
## But why?

I've tried countless times watching video tutorials on how to do X, Y, Z, but lack the direct feedback on my work and burn out too fast.

AI assistants revolutionized my code- can they make me a better artist?

Art is something everyone should pick up, so here's me trying to make it more accessible :)

---
## Requirements
1. Decent PC Hardware
    - Runs best on Nvidia GPUs (sadly)
        - Tested/Developed on a GTX 1070ti (8GB VRAM) 
3. Python 3.X
    - `pip install PyQt6 Pillow requests`
    - or use the requests file, will update as we expand
4. Ollama ([found here](https://ollama.com))
    - llama3.2-vision (11b / 90b) : Best overall performance
    - llava (7b / 13b / 34b) : Decent Performance
    - llava-phi3 (3.8b) : Budget Performance

---
## Usage
1. Start up ollama
   - `ollama run model-name`
   - `ollama serve model-name` (if remote hosting)
1. Run the application
   - `python main.py`
  
The application will be an overlaying window with a chat box. There's two functions here:
1. Send - chat with the AI, ask followup questions
   - will attach most recent screengrab with prompt
3. Review - focus the AI specifically on art critique
   - also attaches most recent screengrab

---
## TODO
1. MAKE IT PRETTY (work never done)
2. Adjustable screenshot interval
3. Screenshot region selection (instead of full screen)
4. Progress tracking over time
5. Save/load/export conversation history
6. Custom prompts for different types of exercises
