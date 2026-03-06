import os
from flask import Flask, request, jsonify, render_template_string
import requests

app = Flask(__name__)

# ==========================================
# CLOUD SETTINGS
# ==========================================
APP_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwoCdyOrAcQSafTERbHkDsci3Ce-OEYmVDZXrlZrzBD4wx7x1iNN2yBa8JSozQhdBI/exec"

# ==========================================
# EMBEDDED FRONTEND (HTML/CSS/JS)
# ==========================================
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Devse - Emotive Bakery AI</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #0B0F19; color: white; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
        .card { background-color: #1A2235; border: 1px solid #2A3B5C; border-radius: 8px; }
        .hidden { display: none !important; }
    </style>
</head>
<body class="p-4 md:p-8">

    <div id="app-container" class="max-w-5xl mx-auto">
        
        <div id="login-screen" class="screen card p-8 max-w-md mx-auto mt-20 text-center shadow-xl">
            <h1 class="text-3xl font-bold text-[#00E5FF] mb-2">Welcome to Devse</h1>
            <p class="text-gray-400 mb-8">Enter your name to load your AI profile</p>
            <input type="text" id="username" placeholder="Username" class="w-full p-3 mb-6 bg-[#0B0F19] text-white border-none rounded focus:ring-2 focus:ring-[#00E5FF] outline-none text-center text-lg">
            <button onclick="login()" id="login-btn" class="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-4 rounded transition">Login / Create Profile</button>
        </div>

        <div id="builder-screen" class="screen hidden">
            <div class="mb-8">
                <h1 class="text-3xl font-bold text-[#00E5FF]">Live 3D Cake Engine - <span id="user-display"></span></h1>
                <p id="ai-stats" class="text-sm mt-2"></p>
            </div>

            <div class="flex flex-col md:flex-row gap-8">
                <div class="card p-6 flex-1 shadow-lg">
                    <h2 class="font-bold text-gray-300 mb-2">1. Base Flavor Matrix:</h2>
                    <select id="flavor" class="w-full p-2 mb-6 bg-[#004A8F] text-white rounded outline-none border-none">
                        <option>Chocolate</option><option>Vanilla</option><option>Red Velvet</option><option>Matcha</option>
                    </select>

                    <h2 class="font-bold text-gray-300 mb-2">2. Topping Density:</h2>
                    <input type="range" id="topping" min="0" max="100" value="20" class="w-full mb-6 accent-[#00E5FF]">

                    <h2 class="font-bold text-gray-300 mb-2">3. Design Theme:</h2>
                    <select id="theme" class="w-full p-2 mb-6 bg-[#004A8F] text-white rounded outline-none border-none">
                        <option>Elegant</option><option>Cyberpunk</option><option>Rustic</option><option>Minimalist</option>
                    </select>

                    <h2 class="font-bold text-gray-300 mb-2">4. Custom Text:</h2>
                    <input type="text" id="custom-text" placeholder="e.g. Happy Birthday" class="w-full p-2 mb-8 bg-[#0B0F19] text-white rounded outline-none border-none">

                    <button onclick="renderPreview()" id="render-btn" class="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-4 rounded mb-4 transition">Render 3D Preview</button>
                    <button onclick="goToCheckout('builder')" id="checkout-btn" class="w-full bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-4 rounded mb-4 transition">Checkout & Order</button>
                    <button onclick="trainAI()" class="w-full bg-gray-700 hover:bg-gray-600 text-white font-bold py-3 px-4 rounded transition">Generate AI Recommendations</button>
                </div>

                <div class="card p-6 flex-1 flex flex-col items-center justify-center min-h-[400px] shadow-lg">
                    <h2 class="text-xl font-bold text-[#00E5FF] mb-4 self-start">Live 3D Render Output</h2>
                    <div id="image-container" class="w-full max-w-[350px] aspect-square bg-[#0B0F19] flex items-center justify-center rounded-lg overflow-hidden border border-[#2A3B5C]">
                        <p id="image-status" class="text-gray-400 text-center px-4">Configure settings and click 'Render 3D Preview'</p>
                        <img id="cake-preview" class="hidden w-full h-full object-cover">
                    </div>
                </div>
            </div>
        </div>

        <div id="loading-screen" class="screen hidden card p-12 max-w-md mx-auto mt-20 text-center shadow-xl">
            <h2 class="text-3xl font-bold text-[#00E5FF] mb-6">Neural Network Compiling...</h2>
            <div class="w-full bg-gray-700 rounded-full h-4 overflow-hidden">
                <div id="progress-bar" class="bg-[#00E5FF] h-4 w-0 transition-all duration-300"></div>
            </div>
        </div>

        <div id="recommendation-screen" class="screen hidden max-w-5xl mx-auto">
            <h1 class="text-3xl font-bold text-[#00E5FF] mb-6">AI Recommendations</h1>
            <div class="flex flex-col md:flex-row gap-8">
                
                <div class="card p-6 flex-1 shadow-lg flex flex-col items-center">
                    <h2 id="rec1-title" class="text-xl font-bold mb-4 text-center">The Neural Match</h2>
                    <div class="w-full max-w-[250px] aspect-square bg-[#0B0F19] flex items-center justify-center rounded border border-[#2A3B5C] mb-6">
                        <p id="rec1-status" class="text-[#00E5FF]">⏳ Rendering...</p>
                        <img id="rec1-img" class="hidden w-full h-full object-cover rounded">
                    </div>
                    <div class="flex gap-2 w-full mt-auto">
                        <button onclick="goToCheckout('rec1')" class="flex-1 bg-green-500 hover:bg-green-600 font-bold py-2 rounded text-white">Checkout</button>
                        <button onclick="editRec(1)" class="flex-1 bg-gray-600 hover:bg-gray-500 font-bold py-2 rounded text-white">Modify</button>
                    </div>
                </div>

                <div class="card p-6 flex-1 shadow-lg flex flex-col items-center">
                    <h2 id="rec2-title" class="text-xl font-bold mb-4 text-center">The Premium Evolution</h2>
                    <div class="w-full max-w-[250px] aspect-square bg-[#0B0F19] flex items-center justify-center rounded border border-[#2A3B5C] mb-6">
                        <p id="rec2-status" class="text-[#00E5FF]">⏳ Rendering...</p>
                        <img id="rec2-img" class="hidden w-full h-full object-cover rounded">
                    </div>
                    <div class="flex gap-2 w-full mt-auto">
                        <button onclick="goToCheckout('rec2')" class="flex-1 bg-green-500 hover:bg-green-600 font-bold py-2 rounded text-white">Checkout</button>
                        <button onclick="editRec(2)" class="flex-1 bg-gray-600 hover:bg-gray-500 font-bold py-2 rounded text-white">Modify</button>
                    </div>
                </div>

            </div>
            <button onclick="showScreen('builder-screen')" class="mt-8 bg-gray-700 hover:bg-gray-600 text-white font-bold py-3 px-6 rounded transition">← Back to Builder</button>
        </div>

        <div id="checkout-screen" class="screen hidden card p-8 max-w-md mx-auto mt-20 text-center shadow-xl">
            <h2 class="text-2xl font-bold text-[#00E5FF] mb-6">Secure Checkout</h2>
            
            <h3 class="font-bold text-gray-300 mb-2 text-left">Select a Bakery:</h3>
            <select id="bakery-select" class="w-full p-3 mb-6 bg-[#004A8F] text-white rounded outline-none border-none"></select>

            <h3 class="font-bold text-gray-300 mb-2 text-left">Delivery Address:</h3>
            <input type="text" id="address" placeholder="Enter full address" class="w-full p-3 mb-8 bg-[#0B0F19] text-white border-none rounded focus:ring-2 focus:ring-[#00E5FF] outline-none">

            <div class="flex gap-4">
                <button onclick="showScreen('builder-screen')" class="flex-1 bg-gray-600 hover:bg-gray-500 text-white font-bold py-3 px-4 rounded transition">Back</button>
                <button onclick="placeOrder()" id="place-order-btn" class="flex-1 bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-4 rounded transition">Place Order</button>
            </div>
        </div>

    </div>

    <script>
        // --- App State ---
        let currentUser = "";
        let orderHistory = [];
        let bakeriesList = [];
        let checkoutData = {}; // Stores the prompt and details for the item being checked out

        // --- Core Functions ---
        function showScreen(screenId) {
            document.querySelectorAll('.screen').forEach(el => el.classList.add('hidden'));
            document.getElementById(screenId).classList.remove('hidden');
        }

        async function callCloud(data) {
            try {
                const res = await fetch('/api/proxy', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                let json = await res.json();
                if(json.status === "error" && json.message.includes("Google")) {
                    alert(json.message); // Alerts if Google is blocking the script
                }
                return json;
            } catch (err) {
                alert("Network connection error.");
                return {status: "error"};
            }
        }

        function updateConfidence() {
            let pts = orderHistory.length;
            let conf = Math.min(pts * 15, 99);
            let color = pts >= 2 ? '#2ECC71' : '#E74C3C';
            document.getElementById('ai-stats').innerHTML = `Emotive Data Points: ${pts} | AI Confidence: <span style="color:${color}">${conf}%</span>`;
        }

        function generatePrompt(f, top, theme, txt) {
            let textPrompt = txt ? `, featuring the exact text "${txt}" beautifully written on top in frosting` : '';
            let topDesc = top < 30 ? "smooth texture, minimal elegant decoration" : (top < 70 ? "decorated with fresh real toppings, piped frosting" : "maximalist, heavily loaded with rich toppings, intricate details");
            return `A highly realistic 3D render of a ${f} cake, ${theme} style, ${topDesc}${textPrompt}, 8k resolution, cinematic lighting, professional bakery photography, isolated`;
        }

        function getBuilderData() {
            return {
                flavor: document.getElementById('flavor').value,
                theme: document.getElementById('theme').value,
                topping: parseInt(document.getElementById('topping').value),
                text: document.getElementById('custom-text').value.trim()
            };
        }

        // Helper to find most common item in array
        function getMode(arr) {
            return arr.sort((a,b) => arr.filter(v => v===a).length - arr.filter(v => v===b).length).pop();
        }

        // --- Button Actions ---
        async function login() {
            let name = document.getElementById('username').value.trim();
            if(!name) return;
            
            document.getElementById('login-btn').innerText = "Syncing with Cloud...";
            let res = await callCloud({action: "get_user", username: name});
            
            if(res.status === "success") {
                orderHistory = JSON.parse(res.history || "[]");
            } else {
                orderHistory = [];
                await callCloud({action: "update_user", username: name, history: "[]"});
            }
            
            currentUser = name;
            document.getElementById('user-display').innerText = currentUser;
            updateConfidence();
            showScreen('builder-screen');
        }

        async function renderPreview() {
            let status = document.getElementById('image-status');
            let img = document.getElementById('cake-preview');
            let btn = document.getElementById('render-btn');
            
            let d = getBuilderData();
            let prompt = generatePrompt(d.flavor, d.topping, d.theme, d.text);
            
            img.classList.add('hidden');
            status.classList.remove('hidden');
            status.innerText = "⏳ Contacting Devse Cloud...";
            btn.disabled = true;

            let res = await callCloud({action: "generate_image", prompt: prompt});
            
            if(res.status === "success" && res.image_data) {
                img.src = "data:image/jpeg;base64," + res.image_data;
                img.classList.remove('hidden');
                status.classList.add('hidden');
            } else {
                status.innerText = "Render Error. Check Google Apps Script Auth.";
            }
            btn.disabled = false;
        }

        function trainAI() {
            let d = getBuilderData();
            orderHistory.push({topping_level: d.topping, flavor: d.flavor, theme: d.theme, text: d.text});
            callCloud({action: "update_user", username: currentUser, history: JSON.stringify(orderHistory)});
            updateConfidence();
            
            if (orderHistory.length >= 2) {
                runRecommendations();
            } else {
                alert("Data captured! Need 1 more design to build AI profile.");
            }
        }

        async function runRecommendations() {
            showScreen('loading-screen');
            let bar = document.getElementById('progress-bar');
            bar.style.width = "0%";
            
            // Fake progress animation
            setTimeout(() => bar.style.width = "40%", 500);
            setTimeout(() => bar.style.width = "80%", 1000);
            setTimeout(() => bar.style.width = "100%", 1500);

            // Calculate AI profile
            let avgTop = orderHistory.reduce((a, b) => a + b.topping_level, 0) / orderHistory.length;
            let favFlavor = getMode(orderHistory.map(o => o.flavor));
            let favTheme = getMode(orderHistory.map(o => o.theme));
            let texts = orderHistory.filter(o => o.text).map(o => o.text);
            let favText = texts.length > 0 ? texts[texts.length - 1] : "";

            let p1 = generatePrompt(favFlavor, avgTop, favTheme, favText);
            let p2 = generatePrompt(favFlavor, avgTop + 20, favTheme, favText);

            // Save data to window for checkout/edit later
            window.rec1Data = {flavor: favFlavor, topping: avgTop, theme: favTheme, text: favText, prompt: p1};
            window.rec2Data = {flavor: favFlavor, topping: avgTop + 20, theme: favTheme, text: favText, prompt: p2};

            document.getElementById('rec1-title').innerText = `Neural Match: ${favFlavor}`;

            // Fetch images
            setTimeout(async () => {
                showScreen('recommendation-screen');
                
                // Fetch Rec 1
                let res1 = await callCloud({action: "generate_image", prompt: p1});
                if(res1.status === "success" && res1.image_data) {
                    document.getElementById('rec1-img').src = "data:image/jpeg;base64," + res1.image_data;
                    document.getElementById('rec1-img').classList.remove('hidden');
                    document.getElementById('rec1-status').classList.add('hidden');
                } else { document.getElementById('rec1-status').innerText = "Render Error"; }

                // Fetch Rec 2
                let res2 = await callCloud({action: "generate_image", prompt: p2});
                if(res2.status === "success" && res2.image_data) {
                    document.getElementById('rec2-img').src = "data:image/jpeg;base64," + res2.image_data;
                    document.getElementById('rec2-img').classList.remove('hidden');
                    document.getElementById('rec2-status').classList.add('hidden');
                } else { document.getElementById('rec2-status').innerText = "Render Error"; }

            }, 1600);
        }

        async function goToCheckout(source) {
            // Set checkout data based on where they clicked
            if (source === 'builder') {
                let d = getBuilderData();
                checkoutData = {...d, prompt: generatePrompt(d.flavor, d.topping, d.theme, d.text)};
            } else if (source === 'rec1') {
                checkoutData = window.rec1Data;
            } else if (source === 'rec2') {
                checkoutData = window.rec2Data;
            }

            let btn = event.target;
            let originalText = btn.innerText;
            btn.innerText = "Fetching...";
            
            let res = await callCloud({action: "get_bakeries"});
            if(res.status === "success" && res.bakeries.length > 0) {
                bakeriesList = res.bakeries;
                let select = document.getElementById('bakery-select');
                select.innerHTML = "";
                bakeriesList.forEach(b => {
                    let opt = document.createElement('option');
                    opt.value = b.id;
                    opt.innerText = b.name;
                    select.appendChild(opt);
                });
                showScreen('checkout-screen');
            } else {
                alert("No bakeries currently registered on the platform.");
            }
            btn.innerText = originalText;
        }

        function editRec(num) {
            let data = num === 1 ? window.rec1Data : window.rec2Data;
            document.getElementById('flavor').value = data.flavor;
            document.getElementById('theme').value = data.theme;
            document.getElementById('topping').value = data.topping;
            document.getElementById('custom-text').value = data.text;
            
            // Bring image over
            let imgData = document.getElementById(`rec${num}-img`).src;
            if(imgData && !imgData.includes("hidden")) {
                document.getElementById('cake-preview').src = imgData;
                document.getElementById('cake-preview').classList.remove('hidden');
                document.getElementById('image-status').classList.add('hidden');
            }
            showScreen('builder-screen');
        }

        async function placeOrder() {
            let address = document.getElementById('address').value.trim();
            if(!address) return alert("Please enter a delivery address.");
            
            let bakeryId = document.getElementById('bakery-select').value;
            
            document.getElementById('place-order-btn').innerText = "Sending...";
            
            // Send Order
            let orderData = {
                action: "place_order",
                customer: currentUser, address: address, flavor: checkoutData.flavor, 
                theme: checkoutData.theme, text: checkoutData.text,
                prompt: checkoutData.prompt, time: new Date().toLocaleTimeString(), bakery_id: bakeryId
            };
            
            let res = await callCloud(orderData);
            if(res.status === "success") {
                alert("Order confirmed! Routed to the bakery terminal.");
                document.getElementById('address').value = "";
                
                // Clear the preview image
                document.getElementById('cake-preview').classList.add('hidden');
                document.getElementById('image-status').classList.remove('hidden');
                document.getElementById('image-status').innerText = "Configure settings and click 'Render 3D Preview'";

                showScreen('builder-screen');
            } else {
                alert("Failed to send order.");
            }
            document.getElementById('place-order-btn').innerText = "Place Order";
        }
    </script>
</body>
</html>
"""

# ==========================================
# FLASK ROUTES
# ==========================================
@app.route('/')
def home():
    # Serves the HTML frontend
    return render_template_string(HTML_PAGE)

@app.route('/api/proxy', methods=['POST'])
def proxy():
    # Acts as a secure middleman between the web frontend and Google Apps Script
    try:
        req_data = request.json
        res = requests.post(APP_SCRIPT_URL, json=req_data, timeout=90)
        
        # SAFETY CHECK: Did Google return an HTML Error Page?
        if "text/html" in res.headers.get("Content-Type", ""):
            print("GOOGLE AUTH ERROR:", res.text) # Logs to Render console
            return jsonify({
                "status": "error", 
                "message": "Backend Error: Google Apps Script requires authorization. Please 'Deploy as New Version' in your Google Apps Script editor."
            })

        return jsonify(res.json())
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    # Binds to the port Render provides
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)



