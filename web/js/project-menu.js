

const projectPropsModal = new ModalDrawerRight(document.getElementById("project-props-modal"), {
    width: '500px',
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


const newEntryPointModal = new Modal(document.getElementById("new-entry-point-modal"), {
    width: '300px',
    height: '280px',
    displayStyle: 'flex',
    classList: ['theme-modal-container'],
})


const RUN_EP = (epid) => {
    projectPropsModal.close()
    RUN(epid)
}


const displayEntryPoints = (eps, epElem) => {
    epElem = epElem || document.getElementById("entry-points")
    if(epElem) {
        epElem.innerHTML = ""
        // const headers = document.createElement("div")
        // headers.classList.add("entry-point-header")
        // headers.innerHTML = `
        //     <span>Name</span>
        //     <span>File</span>
        //     <span>Function</span>
        // `
        // epElem.appendChild(headers)

        for (const ep of eps) {
            const container = document.createElement("div")
            container.classList.add("entry-point-row")
            container.innerHTML = `
                <span>${ep.name}</span>
                <span>${ep.is_default ? "Default": "-"}</span>
                <button ${ep.is_default ? "disabled" : ""} onclick="deleteEntryPoint(${ep.id}, this)">Delete</button>
                <button onclick="RUN_EP(${ep.id})">Run</button>
            `
            epElem.appendChild(container)
        }

        epElem.innerHTML = epElem.innerHTML + `
            <button class="new-entry" onclick="newEntryPointModal.open()">&plus;</button>`
    }
}




const addNewEntryPoint = (btn) => {
    const file = btn.parentElement.querySelector('input[name="file"]').value.trim()
    const func = btn.parentElement.querySelector('input[name="func"]').value.trim()
    const make_default = btn.parentElement.querySelector('input[name="make_default"]').checked
    API.newEntryPoint(file, func, make_default).then(res=>{
        displayEntryPoints(res)
        newEntryPointModal.close()
    }).catch(err=>AlertModal.open(err))
}


const deleteEntryPoint = (epid, btn) => {
    ConfirmModal.open("Are you sure you want to delete this entry point?",
        ()=>{
            API.deleteEntryPoint(epid).then(()=>{
                btn.parentElement.remove()
            }).catch(err=>AlertModal.open(err))
        }
    )

}


const openProjectProperties = () => {
    projectPropsModal.open().then(popup=>{
        API.getProperties().then(props=>{
            console.log(props)
            const epElem = popup.querySelector("#entry-points")
            displayEntryPoints(props.entry_points, epElem)
            // displaySchedule(props.schedule, epElem)
        })
    })
}


const projPropsSelect = (btn, tabId) => {
    btn.parentElement.parentElement.querySelectorAll('.tab').forEach(b=>b.classList.remove('selected'))
    btn.parentElement.querySelectorAll('.tab-bar-btn').forEach(b=>b.classList.remove('selected'))
    btn.classList.add('selected')
    document.getElementById(tabId).classList.add('selected')
}



const openProjectMenu = (ev) => {
    sz = ev.target.getBoundingClientRect()
    let menu = new ContextMenu(sz.x, sz.y)

    menu.addNewOption("Save (ctrl+s)", ()=>{
        SAVE()
        menu.close()
    })
    menu.addNewOption("Run (ctrl+b)", ()=>{
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
