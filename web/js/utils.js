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


const AlertModal = new ModalAlert({
    css: {
        backgroundColor: 'rgb(39,40,34)',
        color: 'white',
    },

    classList: ['btn-dark']
})

const ConfirmModal = new ModalConfirm({
    css: {
        backgroundColor: 'rgb(39,40,34)',
        color: 'white',
    },
    classList: ['btn-dark']
})
