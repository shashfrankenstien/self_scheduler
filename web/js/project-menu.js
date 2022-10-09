

const projectPropsModal = new Modal(document.getElementById("project-props-modal"), {
    width: '700px',
    height: '500px',
    displayStyle: 'flex',
    classList: ['theme-modal-container'],
    transitionStartPos: {top:'30%', left: '-30%'},
    autoClose: true,
    noCloseBtn: true,
    afterClose: ()=>{
        if (window.editor) window.editor.focus()
    }
})


const RUN_EP = (epid) => {
    projectPropsModal.close()
    RUN(epid)
}


const openProjectProperties = () => {
    projectPropsModal.open().then(popup=>{
        API.getProperties().then(props=>{
            const epElem = popup.querySelector("#entry-points")

            const headers = document.createElement("div")
            headers.classList.add("entry-point-row")
            headers.innerHTML = `
                <span class="h">Name</span>
                <span class="h">File</span>
                <span class="h">Function</span>
                <span class="h">IsDefault</span>
                <span class="h"></span>
                <span class="h"></span>
            `
            epElem.appendChild(headers)

            for (const ep of props.end_points) {
                const container = document.createElement("div")
                container.classList.add("entry-point-row")
                container.innerHTML = `
                    <span class="r">${ep.name}</span>
                    <span class="r">${ep.file}</span>
                    <span class="r">${ep.function}</span>
                    <span class="r">${ep.is_default ? "TRUE": ""}</span>
                    <button class="r" ${ep.is_default ? "disabled" : ""}>Delete</button>
                    <button class="r" onclick="RUN_EP(${ep.id})">Run</button>
                `
                epElem.appendChild(container)
                console.log(ep)
            }
        })
    })
}


const projPropsSelect = (btn, tabId) => {
    btn.parentElement.parentElement.querySelectorAll('.tab').forEach(b=>b.classList.remove('selected'))
    btn.parentElement.querySelectorAll('.tab-bar-btn').forEach(b=>b.classList.remove('selected'))
    btn.classList.add('selected')
    document.getElementById(tabId).classList.add('selected')
}


const addNewEntry = (type) => {

}


const openProjectMenu = (ev) => {
    sz = ev.target.getBoundingClientRect()
    let menu = new ContextMenu(sz.x, sz.y)

    menu.addNewOption("Save (ctrl+s)", ()=>{
        // commonRename(item)
        SAVE()
        menu.close()
    })
    menu.addNewOption("Run (ctrl+b)", ()=>{
        // commonRename(item)
        RUN()
        menu.close()
    })
    menu.addNewOption("Properties", ()=>{
        openProjectProperties()
        menu.close()
    })
    menu.open()

}

// openProjectProperties()
