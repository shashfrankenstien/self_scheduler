const modFetch = async (endpoint, method, body) => {
    if (body) {
        body = JSON.stringify(body)
    }
    return fetch(endpoint, {
        method,
        headers: {'Content-Type': 'application/json'},
        credentials: "same-origin",
        body: body || null
    }).then(resp=>{
        return resp.json()
    }).then(rj=>{
        if (rj.success) {
            return rj.success
        } else {
            throw new Error(rj.error)
        }
    })
}


const streamFetch = async (endpoint, method, body, streamcb) => {
    const response = await fetch(endpoint, {
        method,
        headers: {'Content-Type': 'application/json'},
        credentials: "same-origin",
        body: body || null
    });
    const reader = response.body.getReader();

    while (true) {
        const {value, done} = await reader.read();
        if (done) break;
        // console.log('Received', value);
        streamcb(String.fromCharCode.apply(null, value))
    }

    // console.log('Response fully received');
    // return "Success!"
}


const AlertModal = new ModalAlert({
    classList: ['theme-modal-container']
})

const ConfirmModal = new ModalConfirm({
    classList: ['theme-modal-container']
})
