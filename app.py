import os
from flask import Flask, request, jsonify, render_template_string
import requests

app = Flask(__name__)

# ==========================================
# CLOUD SETTINGS
# ==========================================
APP_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbw3hFEiAXWzoxOrMiorWe8c642d9S76WxYmLgQBDQiCLcEyTHScxismgN0ZgfeUrefX/exec"

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
                    <button onclick="goToCheckout()" id="checkout-btn" class="w-full bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-4 rounded mb-4 transition">Checkout & Order</button>
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
        let currentPrompt = "";

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
                return await res.json();
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

        function generatePrompt() {
            let f = document.getElementById('flavor').value;
            let theme = document.getElementById('theme').value;
            let top = parseInt(document.getElementById('topping').value);
            let txt = document.getElementById('custom-text').value.trim();
            
            let textPrompt = txt ? `, featuring the exact text "${txt}" beautifully written on top in frosting` : '';
            let topDesc = top < 30 ? "smooth texture, minimal elegant decoration" : (top < 70 ? "decorated with fresh real toppings, piped frosting" : "maximalist, heavily loaded with rich toppings, intricate details");
            
            return `A highly realistic 3D render of a ${f} cake, ${theme} style, ${topDesc}${textPrompt}, 8k resolution, cinematic lighting, professional bakery photography, isolated`;
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
            
            currentPrompt = generatePrompt();
            
            img.classList.add('hidden');
            status.classList.remove('hidden');
            status.innerText = "⏳ Contacting Devse Cloud...";
            btn.disabled = true;

            let res = await callCloud({action: "generate_image", prompt: currentPrompt});
            
            if(res.status === "success" && res.image_data) {
                img.src = "data:image/jpeg;base64," + res.image_data;
                img.classList.remove('hidden');
                status.classList.add('hidden');
            } else {
                status.innerText = "Render Error. Please try again.";
            }
            btn.disabled = false;
        }

        async function goToCheckout() {
            let btn = document.getElementById('checkout-btn');
            btn.innerText = "Fetching Bakeries...";
            
            if(!currentPrompt) currentPrompt = generatePrompt();
            
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
            btn.innerText = "Checkout & Order";
        }

        async function placeOrder() {
            let address = document.getElementById('address').value.trim();
            if(!address) return alert("Please enter a delivery address.");
            
            let bakeryId = document.getElementById('bakery-select').value;
            let f = document.getElementById('flavor').value;
            let theme = document.getElementById('theme').value;
            let top = parseInt(document.getElementById('topping').value);
            let txt = document.getElementById('custom-text').value.trim();
            
            document.getElementById('place-order-btn').innerText = "Sending...";
            
            // Sync history
            orderHistory.push({topping_level: top, flavor: f, theme: theme, text: txt});
            callCloud({action: "update_user", username: currentUser, history: JSON.stringify(orderHistory)});
            updateConfidence();
            
            // Send Order
            let orderData = {
                action: "place_order",
                customer: currentUser, address: address, flavor: f, theme: theme, text: txt,
                prompt: currentPrompt, time: new Date().toLocaleTimeString(), bakery_id: bakeryId
            };
            
            let res = await callCloud(orderData);
            if(res.status === "success") {
                alert("Order confirmed! Routed to the bakery terminal.");
                document.getElementById('address').value = "";
                showScreen('builder-screen');
            } else {
                alert("Failed to send order.");
            }
            document.getElementById('place-order-btn').innerText = "Place Order";
        }

        function trainAI() {
            let f = document.getElementById('flavor').value;
            let theme = document.getElementById('theme').value;
            let top = parseInt(document.getElementById('topping').value);
            let txt = document.getElementById('custom-text').value.trim();
            
            orderHistory.push({topping_level: top, flavor: f, theme: theme, text: txt});
            callCloud({action: "update_user", username: currentUser, history: JSON.stringify(orderHistory)});
            updateConfidence();
            alert("Data captured! Your AI profile is learning.");
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
        return jsonify(res.json())
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    # Binds to the port Render provides
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)