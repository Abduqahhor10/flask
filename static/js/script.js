// Like via fetch
async function sendLike(blogId, btn) {
    try {
        const resp = await fetch(`/like/${blogId}`, {method: 'POST', headers: {'Content-Type':'application/json'}});
        if (!resp.ok) throw new Error('Network');
        const data = await resp.json();
        const likesEl = document.querySelector(`#likes-${blogId}`);
        if (likesEl) likesEl.textContent = data.likes;
        // quick pulse
        btn.animate([{transform:'scale(1.3)'},{transform:'scale(1)'}], {duration:200});
    } catch (e) {
        alert("Please login to like or something went wrong.");
    }
}
