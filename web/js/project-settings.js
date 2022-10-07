

const projectPropsModal = new Modal(document.getElementById("project-properties-modal"), {
    width: '600px',
    height: '500px',
    displayStyle: 'flex',
    classList: ['theme-modal-container'],
    transitionStartPos: {top:'30%', left: '-30%'},
    autoClose: true,
    afterClose: ()=>{
        if (window.editor) window.editor.focus()
    }
})


const openProjectProperties = () => {
    projectPropsModal.open().then(r=>{
        API.getProperties().then(props=>{
            r.innerHTML = JSON.stringify(props, null, '\t')
            for (const ep of props.end_points) {
                console.log(ep)
            }
        })
    })
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

