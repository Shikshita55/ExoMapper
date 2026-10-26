b64_1 = array_to_base64_png(img1)
    b64_2 = array_to_base64_png(img2)
    
    # Change f""" to """ since no Python variables are used inside this HTML/JS string
    blink_html = """
    <div style="background:#040c24; border:1px solid rgba(0,229,255,0.4); border-radius:12px; padding:15px; text-align:center;">
        <div style="position:relative; width:340px; height:340px; margin:0 auto; overflow:hidden; border-radius:8px;">
            <img id="img1" src="data:image/png;base64,""" + b64_1 + """" style="position:absolute; top:0; left:0; width:100%; height:100%; object-fit:contain;" />
            <img id="img2" src="data:image/png;base64,""" + b64_2 + """" style="position:absolute; top:0; left:0; width:100%; height:100%; object-fit:contain; opacity:0; transition: opacity 0.2s;" />
        </div>
        <div style="margin-top:15px; display:flex; justify-content:center; gap:10px; align-items:center;">
            <button onclick="toggleBlink()" id="blinkBtn" style="background:#00e5ff; color:#010409; border:none; padding:8px 16px; border-radius:6px; font-weight:700; cursor:pointer;">▶ START BLINK</button>
            <span style="color:#00ffcc; font-family:Space Mono; font-size:0.9rem;" id="statusLabel">⏸ PAUSED</span>
        </div>
        <div style="margin-top:10px;">
            <label style="color:#84ffff; font-size:0.9rem;">Manual Blend Scrubber (Epoch 1 ⟷ Epoch 2):</label><br>
            <input type="range" min="0" max="100" value="0" oninput="blendImages(this.value)" style="width:300px; accent-color:#00ffcc; cursor:pointer;">
        </div>
    </div>
    <script>
        let blinking = false;
        let timer = null;
        let showEp2 = false;
        const img2El = document.getElementById('img2');
        const btn = document.getElementById('blinkBtn');
        const status = document.getElementById('statusLabel');

        function toggleBlink() {
            blinking = !blinking;
            if(blinking) {
                btn.innerText = "⏸ STOP BLINK";
                status.innerText = "🟢 BLINKING ACTIVE";
                timer = setInterval(() => {
                    showEp2 = !showEp2;
                    img2El.style.opacity = showEp2 ? "1" : "0";
                }, 500);
            } else {
                btn.innerText = "▶ START BLINK";
                status.innerText = "⏸ PAUSED";
                clearInterval(timer);
            }
        }

        function blendImages(val) {
            blinking = false;
            clearInterval(timer);
            btn.innerText = "▶ START BLINK";
            status.innerText = "⏸ MANUAL BLEND";
            img2El.style.opacity = val / 100.0;
        }
    </script>
    """
